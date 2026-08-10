#!/usr/bin/env python3
"""Sync health improvement data from Managed Care into professional_daily_metrics"""
import sys
sys.path.insert(0, '.')

import os
from dotenv import load_dotenv
import psycopg
from collections import defaultdict

load_dotenv()

print("=" * 70)
print("SYNCING HEALTH IMPROVEMENT DATA FROM MANAGED CARE")
print("=" * 70)

try:
    db_url = os.getenv('DATABASE_URL')
    conn = psycopg.connect(db_url, connect_timeout=10)
    cursor = conn.cursor()

    # Query health improvement data from managed_care
    print("\n[1] Fetching health improvement data from managed_care...")
    cursor.execute("""
        SELECT
            COUNT(DISTINCT mobile_number_hash) as total_patients,
            AVG(scaled_score) as avg_improvement,
            COUNT(*) as total_records
        FROM managed_care.impact_scores_2026
    """)
    mc_result = cursor.fetchone()
    print(f"  Total patients with improvement data: {mc_result[0]:,}")
    print(f"  Average improvement score: {mc_result[1]:.1f}%")
    print(f"  Total improvement records: {mc_result[2]:,}")

    # Get sample data by patient
    print("\n[2] Fetching sample improvement data...")
    cursor.execute("""
        SELECT
            mobile_number_hash,
            COUNT(DISTINCT impact) as health_areas,
            AVG(scaled_score) as avg_score
        FROM managed_care.impact_scores_2026
        GROUP BY mobile_number_hash
        LIMIT 5
    """)
    samples = cursor.fetchall()
    for mh, areas, score in samples:
        print(f"  Patient {mh[:16]}...: {areas} health areas, {score:.1f}% improvement")

    # Calculate improvement statistics for July 2026
    print("\n[3] Calculating improvement statistics for July 2026...")
    cursor.execute("""
        SELECT
            COUNT(DISTINCT mobile_number_hash) as patients_in_july,
            AVG(scaled_score) as avg_improvement_july
        FROM managed_care.impact_scores_2026
        WHERE first_camp_date LIKE '2026-07%' OR first_camp_date LIKE '2026-06%'
    """)
    july_result = cursor.fetchone()
    patients_july = july_result[0] or 0
    improvement_july = july_result[1] or 0

    print(f"  Patients with July data: {patients_july:,}")
    print(f"  Average improvement (July): {improvement_july:.1f}%")

    # Calculate by provider (using appointment data to match providers)
    print("\n[4] Mapping patient improvement data to dieticians...")
    cursor.execute("""
        SELECT
            v.phr_id,
            v.speciality,
            COUNT(DISTINCT DATE(v.appt_date_dt)) as appointment_days,
            i.scaled_score
        FROM managed_care.vytal_appt_flat v
        LEFT JOIN managed_care.camp_phrs c ON v.phr_id = c.phr_id
        LEFT JOIN managed_care.impact_scores_2026 i
            ON c.mobile_number_hash = i.mobile_number_hash
        WHERE v.appt_date_dt >= '2026-07-01' AND v.appt_date_dt <= '2026-07-30'
        AND v.speciality = 'Dietitian/Nutritionist'
        AND i.scaled_score IS NOT NULL
        GROUP BY v.phr_id, v.speciality, i.scaled_score
        LIMIT 10
    """)

    results = cursor.fetchall()
    print(f"  Found {len(results)} patient-provider mappings")

    if results:
        improvement_by_provider = defaultdict(list)
        for row in results:
            improvement_by_provider[row[1]].append(row[3])

        for specialty, scores in improvement_by_provider.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            print(f"    {specialty}: {len(scores)} patients, {avg_score:.1f}% avg improvement")

    # Summary
    print("\n" + "=" * 70)
    print("HEALTH DATA AVAILABILITY SUMMARY")
    print("=" * 70)
    print(f"""
Status: Health improvement data EXISTS in managed_care schema
- Total Patients: {mc_result[0]:,}
- Average Improvement: {mc_result[1]:.1f}%
- Data Type: Impact Scores (2026)

For Dashboard Display:
- Need to join professional_daily_metrics with managed_care.impact_scores_2026
- Use patient mobile_number_hash as linking key
- Display average improvement % per provider per date range

Next Step: Create view or API endpoint to aggregate improvement data by provider
""")

    cursor.close()
    conn.close()

except Exception as e:
    import traceback
    print(f"\n[ERROR] {str(e)}")
    traceback.print_exc()
