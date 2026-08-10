#!/usr/bin/env python3
"""Fetch Managed Care program metrics for Agent 8 dashboard integration"""
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

print("=" * 70)
print("MANAGED CARE PROGRAM METRICS")
print("=" * 70)

try:
    db_url = os.getenv('DATABASE_URL')
    conn = psycopg.connect(db_url, connect_timeout=10)
    cursor = conn.cursor()

    # Query 1: Total VYTAL enrolled
    print("\n[1] VYTAL Enrollment")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT COUNT(DISTINCT patient_id) as total_enrolled
            FROM managed_care.program_allocation_2026
            WHERE program_code = 'VYTAL01026'
        """)
        result = cursor.fetchone()
        total_enrolled = result[0] if result else 0
        print(f"Total VYTAL Users: {total_enrolled:,}")
    except Exception as e:
        print(f"Could not fetch VYTAL enrollment: {e}")

    # Query 2: HRA Data
    print("\n[2] HRA Health Assessment Data")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT
                COUNT(*) as total_hra,
                COUNT(CASE WHEN completed_date IS NOT NULL THEN 1 END) as completed
            FROM managed_care.hra_stats
            WHERE year = 2026
        """)
        result = cursor.fetchone()
        total_hra = result[0] if result else 0
        completed_hra = result[1] if result else 0
        print(f"HRA Assessments: {total_hra:,}")
        print(f"HRA Completed: {completed_hra:,}")
        if total_hra > 0:
            pct = (completed_hra / total_hra) * 100
            print(f"HRA Completion Rate: {pct:.1f}%")
    except Exception as e:
        print(f"Could not fetch HRA data: {e}")

    # Query 3: Biomarker/Lab Data
    print("\n[3] Biomarker & Lab Data")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT
                COUNT(*) as total_lab_records,
                COUNT(DISTINCT patient_id) as patients_with_labs
            FROM managed_care.camp_phrs
            WHERE test_year = 2026
        """)
        result = cursor.fetchone()
        total_labs = result[0] if result else 0
        patients_with_labs = result[1] if result else 0
        print(f"Total Lab Records (2026): {total_labs:,}")
        print(f"Patients with Lab Data: {patients_with_labs:,}")
    except Exception as e:
        print(f"Could not fetch lab data: {e}")

    # Query 4: Appointments with Dietician
    print("\n[4] Dietician Appointments")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT COUNT(*) as total_appts
            FROM managed_care.vytal_appt_flat
            WHERE YEAR(appointment_date) = 2026
            AND appointment_status IN ('COM', 'BOOKED', 'ACT', 'WIC', 'RES')
        """)
        result = cursor.fetchone()
        total_appts = result[0] if result else 0
        print(f"Confirmed Appointments (Jun onwards): {total_appts:,}")
    except Exception as e:
        print(f"Could not fetch appointment data: {e}")

    # Query 5: Health Improvement Data
    print("\n[5] Health Improvement Metrics")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT
                COUNT(DISTINCT patient_id) as patients_improved,
                AVG(improvement_score) as avg_improvement
            FROM managed_care.impact_scores_2026
            WHERE improvement_pct IS NOT NULL
        """)
        result = cursor.fetchone()
        improved_count = result[0] if result else 0
        avg_improvement = result[1] if result else 0
        print(f"Patients with Health Improvement: {improved_count:,}")
        print(f"Avg Improvement Score: {avg_improvement:.1f}%")
    except Exception as e:
        print(f"Could not fetch improvement data: {e}")

    # Query 6: Program Breakdown
    print("\n[6] Program Enrollment Breakdown")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT
                program_code,
                COUNT(DISTINCT patient_id) as enrollment_count
            FROM managed_care.program_allocation_2026
            GROUP BY program_code
            ORDER BY enrollment_count DESC
        """)
        results = cursor.fetchall()
        for prog_code, count in results:
            print(f"  {prog_code}: {count:,}")
    except Exception as e:
        print(f"Could not fetch program breakdown: {e}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 70)
    print("SUMMARY FOR AGENT 8 DASHBOARD")
    print("=" * 70)
    print("""
These metrics should be integrated into:
1. Overview Tab - program_breakdown array
2. Clinical Outcomes Tab - HRA + Biomarker sections
3. Health Outcomes Tab - improvement tracking

Next: Create API endpoint to return these metrics aggregated.
""")

except Exception as e:
    print(f"[FATAL] {str(e)}")
    import traceback
    traceback.print_exc()
