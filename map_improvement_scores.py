#!/usr/bin/env python3
"""Map patient health improvement scores to dieticians"""
import sys
sys.path.insert(0, '.')

import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

print("=" * 70)
print("MAP PATIENT IMPROVEMENT SCORES TO DIETICIANS")
print("=" * 70)

try:
    db_url = os.getenv('DATABASE_URL')
    conn = psycopg.connect(db_url, connect_timeout=10)
    cursor = conn.cursor()

    # Step 1: Understand the data structure
    print("\n[1] AVAILABLE DATA SOURCES")
    print("-" * 70)

    # Patient improvements
    cursor.execute("""
        SELECT COUNT(*) as total FROM managed_care.impact_scores_2026
    """)
    impr_count = cursor.fetchone()[0]
    print(f"A. Patient Improvement Scores: {impr_count:,} records")
    print("   Schema: mobile_number_hash, impact, scaled_score, first_camp_date")

    # Dietician appointments
    cursor.execute("""
        SELECT COUNT(*) as total FROM managed_care.vytal_appt_flat
        WHERE appt_date_dt >= '2026-07-01' AND appt_date_dt <= '2026-08-10'
    """)
    appt_count = cursor.fetchone()[0]
    print(f"B. Dietician Appointments: {appt_count:,} records (Jul-Aug)")
    print("   Schema: phr_id, appt_date, speciality, doctorname")

    # Patient-Phone mapping
    cursor.execute("""
        SELECT COUNT(*) as total FROM managed_care.camp_phrs
    """)
    phone_count = cursor.fetchone()[0]
    print(f"C. Patient Phone Hash Map: {phone_count:,} records")
    print("   Schema: phr_id, mobile_number_hash")

    # Step 2: Create the mapping
    print("\n[2] MAPPING LOGIC")
    print("-" * 70)
    print("Match path: Patient Improvement -> Phone Hash -> Appointment -> Dietician")
    print("   Impact_Scores.mobile_hash")
    print("   -> Camp_PHRS.mobile_hash (get phr_id)")
    print("   -> Vytal_Appt.phr_id (get dietician name + date)")
    print("   -> Professional_Daily_Metrics.provider_name + metric_date")

    # Step 3: Count mappable records
    print("\n[3] MAPPING STATISTICS")
    print("-" * 70)

    cursor.execute("""
        SELECT
            COUNT(DISTINCT i.mobile_number_hash) as patients_with_improvement,
            COUNT(DISTINCT c.phr_id) as patients_with_appointments,
            COUNT(DISTINCT COALESCE(v.doctorname, 'UNMAPPED')) as dieticians
        FROM managed_care.impact_scores_2026 i
        LEFT JOIN managed_care.camp_phrs c ON i.mobile_number_hash = c.mobile_number_hash
        LEFT JOIN managed_care.vytal_appt_flat v ON c.phr_id = v.phr_id
            AND v.appt_date_dt >= '2026-07-01' AND v.appt_date_dt <= '2026-08-10'
    """)

    result = cursor.fetchone()
    print(f"Patients with improvement data: {result[0]:,}")
    print(f"Patients with appointments in Jul-Aug: {result[1]:,}")
    print(f"Unique dieticians: {result[2]}")

    # Step 4: Sample the mapping
    print("\n[4] SAMPLE MAPPING (first 5 patients)")
    print("-" * 70)

    cursor.execute("""
        SELECT
            i.mobile_number_hash,
            i.scaled_score as improvement_pct,
            v.doctorname as dietician,
            DATE(v.appt_date_dt) as appointment_date,
            COUNT(*) as appointment_count
        FROM managed_care.impact_scores_2026 i
        LEFT JOIN managed_care.camp_phrs c ON i.mobile_number_hash = c.mobile_number_hash
        LEFT JOIN managed_care.vytal_appt_flat v ON c.phr_id = v.phr_id
            AND v.appt_date_dt >= '2026-07-01' AND v.appt_date_dt <= '2026-08-10'
        WHERE v.doctorname IS NOT NULL
        GROUP BY i.mobile_number_hash, i.scaled_score, v.doctorname, DATE(v.appt_date_dt)
        LIMIT 5
    """)

    samples = cursor.fetchall()
    for mobile_hash, impr, dietician, date, appts in samples:
        print(f"  Patient {mobile_hash[:16]}... -> {dietician} ({date}): {impr:.1f}% improvement")

    # Step 5: Create aggregation SQL
    print("\n[5] AGGREGATION LOGIC")
    print("-" * 70)
    print("""
    For each professional_daily_metrics record:
    1. Get all appointments for that provider on that date
    2. Get unique patients from those appointments
    3. Find improvement scores for those patients
    4. Calculate average improvement
    5. Update professional_daily_metrics.improvement_score
    """)

    # Step 6: Create update query
    print("\n[6] UPDATE QUERY (needs manual execution or scheduled job)")
    print("-" * 70)

    update_sql = """
    UPDATE professional_daily_metrics pdm
    SET improvement_score = COALESCE(impr_data.avg_improvement, 0)
    FROM (
        SELECT
            v.doctorname,
            DATE(v.appt_date_dt) as appt_date,
            AVG(i.scaled_score) as avg_improvement,
            COUNT(DISTINCT c.phr_id) as patient_count
        FROM managed_care.vytal_appt_flat v
        LEFT JOIN managed_care.camp_phrs c ON v.phr_id = c.phr_id
        LEFT JOIN managed_care.impact_scores_2026 i ON c.mobile_number_hash = i.mobile_number_hash
        WHERE v.appt_date_dt >= '2026-07-01' AND v.appt_date_dt <= '2026-08-10'
        AND v.speciality = 'Dietitian/Nutritionist'
        GROUP BY v.doctorname, DATE(v.appt_date_dt)
    ) impr_data
    WHERE pdm.provider_name = impr_data.doctorname
    AND pdm.metric_date = impr_data.appt_date
    AND pdm.metric_date >= '2026-07-01' AND pdm.metric_date <= '2026-08-10'
    """

    print("    " + "-" * 60)
    print("    UPDATE professional_daily_metrics")
    print("    SET improvement_score = AVG(patient improvement)")
    print("    FROM appointment+patient+improvement joined data")
    print("    WHERE provider_name matches and metric_date matches")
    print("    " + "-" * 60)

    # Step 7: Check current state
    print("\n[7] CURRENT IMPROVEMENT SCORE STATE")
    print("-" * 70)

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN improvement_score > 0 THEN 1 ELSE 0 END) as populated
        FROM professional_daily_metrics
        WHERE metric_date >= '2026-07-01' AND metric_date <= '2026-08-10'
    """)

    result = cursor.fetchone()
    print(f"Total records: {result[0]:,}")
    print(f"Records with improvement score: {result[1] or 0}")
    print(f"Status: [EMPTY] - All scores are 0 (need mapping)")

    cursor.close()
    conn.close()

    print("\n" + "=" * 70)
    print("IMPLEMENTATION STEPS")
    print("=" * 70)
    print("""
1. EXECUTE the UPDATE query above to populate improvement_score
   - Maps patient improvements to dietician appointments
   - Calculates average per provider per day

2. VERIFY the update:
   SELECT AVG(improvement_score) FROM professional_daily_metrics
   WHERE metric_date >= '2026-07-01' AND metric_date <= '2026-08-10'
   -- Should show non-zero average (expect ~60-75%)

3. SCHEDULE DAILY RUN:
   - Create a Python function to run this query daily
   - Execute after Managed Care data updates
   - Ensures professional_daily_metrics has latest improvement data

4. MONITOR:
   - Track % of records with improvement data
   - Alert if < 50% of records populated (data quality issue)
    """)

except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
