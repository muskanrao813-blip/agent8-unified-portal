#!/usr/bin/env python3
"""Sync QA scores from Dietician QA Portal to professional_daily_metrics"""
import sys
sys.path.insert(0, '.')

import os
from dotenv import load_dotenv
import psycopg
import requests

load_dotenv()

print("=" * 70)
print("SYNC QA SCORES FROM DIETICIAN QA PORTAL")
print("=" * 70)

QA_BACKEND = "https://consultation-call-quality-analysis-system.onrender.com"

try:
    # Step 1: Fetch QA data from Dietician QA Portal
    print("\n[1] Fetching QA data from Dietician QA Portal...")
    print(f"    Endpoint: {QA_BACKEND}/api/calls/")

    try:
        response = requests.get(
            f"{QA_BACKEND}/api/calls/",
            timeout=30,
            verify=False  # Allow self-signed certs
        )

        if response.status_code == 200:
            calls_data = response.json()
            print(f"    Retrieved {len(calls_data) if isinstance(calls_data, list) else 'unknown'} calls")

            # Process QA scores
            if isinstance(calls_data, list):
                qa_count = 0
                for call in calls_data[:5]:  # Sample first 5
                    print(f"    Sample: {call.get('id', 'N/A')} - Score: {call.get('qa_score', 0)}")

                print(f"\n    [OK] QA Portal accessible and returning data")
            else:
                print(f"    Response format: {type(calls_data)}")

        else:
            print(f"    ERROR: Status {response.status_code}")
            print(f"    Response: {response.text[:200]}")

    except requests.exceptions.Timeout:
        print(f"    TIMEOUT: QA Portal not responding (>30s)")
    except Exception as e:
        print(f"    ERROR: {str(e)[:200]}")

    # Step 2: Create QA score aggregation function
    print("\n[2] Creating QA score aggregation logic...")

    db_url = os.getenv('DATABASE_URL')
    conn = psycopg.connect(db_url, connect_timeout=10)
    cursor = conn.cursor()

    # Check if we can link calls to dieticians
    print("    Need to establish mapping: Call Recording -> Dietician -> Date")
    print("    Options:")
    print("    A) QA Portal has provider name field - direct mapping")
    print("    B) QA Portal has patient phone/ID - map via appointments")
    print("    C) QA Portal has appointment ID - direct join")

    # For now, create a placeholder that shows what needs to be mapped
    sql_template = """
    UPDATE professional_daily_metrics
    SET qa_score = (
        SELECT AVG(qa_score)
        FROM (
            -- This SQL will be populated once we know the mapping
            -- SELECT qa_score FROM qa_calls_table
            -- WHERE provider_name = professional_daily_metrics.provider_name
            -- AND DATE(call_date) = professional_daily_metrics.metric_date
            SELECT 0  -- Placeholder
        ) t
    )
    WHERE metric_date >= '2026-07-01' AND metric_date <= '2026-08-10'
    """

    print(f"\n[3] SQL Template for QA Score Update:")
    print("    " + "-" * 60)
    print("    UPDATE professional_daily_metrics")
    print("    SET qa_score = AVG(qa_score from QA Portal)")
    print("    WHERE provider matches AND date matches")
    print("    " + "-" * 60)

    # Step 3: Check current QA score state
    cursor.execute("""
        SELECT
            COUNT(*) as total_records,
            SUM(CASE WHEN qa_score > 0 THEN 1 ELSE 0 END) as with_qa,
            AVG(qa_score) as avg_qa
        FROM professional_daily_metrics
        WHERE metric_date >= '2026-07-01' AND metric_date <= '2026-08-10'
    """)

    result = cursor.fetchone()
    print(f"\n[4] Current QA Score Status:")
    print(f"    Total records: {result[0]:,}")
    print(f"    Records with QA score: {result[1] or 0}")
    print(f"    Average QA score: {result[2] or 0:.1f}")

    if result[1] == 0:
        print(f"    Status: [EMPTY] - All QA scores are 0")
    else:
        print(f"    Status: [PARTIAL] - {(result[1]/result[0])*100:.1f}% populated")

    cursor.close()
    conn.close()

    print("\n" + "=" * 70)
    print("NEXT STEPS FOR QA SCORE INTEGRATION")
    print("=" * 70)
    print("""
1. IDENTIFY MAPPING FIELD in QA Portal API response
   - Does it have: provider_name, dietician_id, appointment_id, patient_phone?
   - Check actual API response structure

2. CREATE JUNCTION QUERY
   - Join QA Portal data with professional_daily_metrics
   - Match on: provider name AND date

3. BATCH UPDATE professional_daily_metrics
   - For each provider+date combo
   - Calculate average QA score from QA Portal
   - Update professional_daily_metrics.qa_score

4. SCHEDULE DAILY SYNC
   - Run after QA Portal has new records
   - Update: professional_daily_metrics.qa_score

Example mapping (if QA has provider_name field):
UPDATE professional_daily_metrics pdm
SET qa_score = qa_data.avg_score
FROM (
    SELECT
        provider_name,
        DATE(call_date) as call_date,
        AVG(qa_score) as avg_score
    FROM qa_calls  -- or however QA Portal stores data
    GROUP BY provider_name, DATE(call_date)
) qa_data
WHERE pdm.provider_name = qa_data.provider_name
AND pdm.metric_date = qa_data.call_date
    """)

except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
