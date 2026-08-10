#!/usr/bin/env python3
"""Get correct Managed Care metrics from proper tables"""
import os
from dotenv import load_dotenv
import psycopg
import json

load_dotenv()

print("=" * 70)
print("MANAGED CARE PROGRAM METRICS - CORRECT QUERIES")
print("=" * 70)

try:
    db_url = os.getenv('DATABASE_URL')
    conn = psycopg.connect(db_url, connect_timeout=10)
    cursor = conn.cursor()

    metrics = {}

    # Query 1: Total enrolled from hra_stats
    print("\n[1] HRA Enrollment Stats")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT metric, value FROM managed_care.hra_stats
            WHERE metric IN ('enrolled_with_hra', 'completed_hra', 'total_enrolled')
        """)
        results = cursor.fetchall()
        for metric, value in results:
            print(f"  {metric}: {value}")
            metrics[metric] = value
    except Exception as e:
        print(f"  Error: {e}")

    # Query 2: Count from vytal_appointments
    print("\n[2] VYTAL Appointment Statistics")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT
                COUNT(*) as total_appts,
                COUNT(DISTINCT phr_id) as unique_patients,
                COUNT(CASE WHEN status = 'COM' THEN 1 END) as completed
            FROM managed_care.vytal_appt_flat
            WHERE appt_date_dt >= '2026-06-01'
        """)
        result = cursor.fetchone()
        print(f"  Total Appointments (Jun+ 2026): {result[0]:,}")
        print(f"  Unique Patients: {result[1]:,}")
        print(f"  Completed: {result[2]:,}")
        metrics['appts_jun_onwards'] = result[0]
        metrics['appt_patients'] = result[1]
        metrics['appt_completed'] = result[2]
    except Exception as e:
        print(f"  Error: {e}")

    # Query 3: Lab data from impact_scores
    print("\n[3] Biomarker Data (Impact Scores)")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT
                COUNT(DISTINCT mobile_number_hash) as patients_with_impact,
                COUNT(*) as total_impact_records
            FROM managed_care.impact_scores_2026
        """)
        result = cursor.fetchone()
        print(f"  Patients with Impact Scores: {result[0]:,}")
        print(f"  Total Impact Records: {result[1]:,}")
        metrics['patients_with_impact'] = result[0]
        metrics['impact_records'] = result[1]

        # Get average improvement
        cursor.execute("""
            SELECT AVG(scaled_score) FROM managed_care.impact_scores_2026
        """)
        avg_score = cursor.fetchone()[0]
        print(f"  Avg Improvement Score: {avg_score:.1f}%")
        metrics['avg_improvement'] = avg_score
    except Exception as e:
        print(f"  Error: {e}")

    # Query 4: Camp participation
    print("\n[4] Health Camp Participation")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT COUNT(DISTINCT mobile_number_hash)
            FROM managed_care.camp_phrs
        """)
        result = cursor.fetchone()[0]
        print(f"  Patients with Camp/Lab Data: {result:,}")
        metrics['camp_participants'] = result
    except Exception as e:
        print(f"  Error: {e}")

    conn.close()

    # Display for dashboard integration
    print("\n" + "=" * 70)
    print("FOR AGENT 8 DASHBOARD - program_breakdown")
    print("=" * 70)

    program_breakdown = {
        'total_enrolled': metrics.get('total_enrolled', 0),
        'enrolled_with_hra': metrics.get('enrolled_with_hra', 60),
        'completed_hra': metrics.get('completed_hra', 0),
        'patients_with_biomarker': metrics.get('patients_with_impact', 0),
        'biomarker_improvement_pct': metrics.get('avg_improvement', 0),
        'appointments_since_jun': metrics.get('appts_jun_onwards', 0),
        'unique_appointment_patients': metrics.get('appt_patients', 0)
    }

    print(json.dumps(program_breakdown, indent=2))

except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
