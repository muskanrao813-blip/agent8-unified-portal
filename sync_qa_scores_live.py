#!/usr/bin/env python3
"""Sync QA scores from Dietician QA Portal to professional_daily_metrics"""
import sys
sys.path.insert(0, '.')

import os
from dotenv import load_dotenv
import psycopg
import requests

load_dotenv()

print("=" * 80)
print("SYNCING QA SCORES FROM DIETICIAN QA PORTAL")
print("=" * 80)

QA_BACKEND = "https://consultation-call-quality-analysis-system.onrender.com"

try:
    # Step 1: Fetch QA data from Dietician QA Portal API
    print("\n[1] FETCHING QA DATA FROM DIETICIAN QA PORTAL...")
    print(f"    Endpoint: {QA_BACKEND}/api/calls/")

    response = requests.get(
        f"{QA_BACKEND}/api/calls/",
        timeout=30,
        verify=False
    )

    if response.status_code != 200:
        print(f"    ERROR: Status {response.status_code}")
        print(f"    Response: {response.text[:200]}")
        sys.exit(1)

    calls_data = response.json()
    if not isinstance(calls_data, list):
        print(f"    ERROR: Expected list, got {type(calls_data)}")
        sys.exit(1)

    print(f"    [OK] Retrieved {len(calls_data):,} call records")

    # Step 2: Parse QA scores by provider and date
    print("\n[2] PARSING QA SCORES...")

    qa_by_provider_date = {}
    qa_count = 0

    for call in calls_data:
        try:
            # Extract fields from QA Portal response
            # The response format from Dietician QA Portal includes:
            # - provider_name or dietician_name (the provider who did the call)
            # - call_date or created_at (when the call happened)
            # - qa_score or quality_score (the QA score 0-100)

            provider = (
                call.get('provider_name') or
                call.get('dietician_name') or
                call.get('doctor_name') or
                'UNKNOWN'
            )

            # Try multiple date fields
            call_date = (
                call.get('call_date') or
                call.get('created_at') or
                call.get('appointment_date')
            )

            if not call_date or not provider or provider == 'UNKNOWN':
                continue

            # Parse date (handle various formats)
            from datetime import datetime
            if isinstance(call_date, str):
                # Try ISO format first
                try:
                    dt = datetime.fromisoformat(call_date.replace('Z', '+00:00'))
                except:
                    try:
                        dt = datetime.strptime(call_date[:10], '%Y-%m-%d')
                    except:
                        continue
            else:
                continue

            date_str = dt.strftime('%Y-%m-%d')

            # Extract QA score
            qa_score = (
                call.get('qa_score') or
                call.get('quality_score') or
                call.get('score') or
                0
            )

            if not isinstance(qa_score, (int, float)):
                continue

            qa_score = float(qa_score)

            # Aggregate by provider and date
            key = (provider, date_str)
            if key not in qa_by_provider_date:
                qa_by_provider_date[key] = []
            qa_by_provider_date[key].append(qa_score)
            qa_count += 1

        except Exception as e:
            continue

    print(f"    [OK] Parsed {qa_count:,} QA score records")
    print(f"    [OK] Unique provider+date combos: {len(qa_by_provider_date):,}")

    # Step 3: Connect to database and update
    print("\n[3] UPDATING PROFESSIONAL_DAILY_METRICS...")

    db_url = os.getenv('DATABASE_URL')
    conn = psycopg.connect(db_url, connect_timeout=10)
    cursor = conn.cursor()

    updated_count = 0
    for (provider, date_str), scores in qa_by_provider_date.items():
        avg_score = sum(scores) / len(scores)
        try:
            cursor.execute('''
                UPDATE professional_daily_metrics
                SET qa_score = %s
                WHERE provider_name = %s AND metric_date = %s
            ''', (avg_score, provider, date_str))
            if cursor.rowcount > 0:
                updated_count += 1
        except Exception as e:
            pass

    conn.commit()
    cursor.close()
    conn.close()

    print(f"    [OK] Updated {updated_count:,} records with QA scores")

    # Step 4: Verification
    print("\n[4] VERIFICATION...")

    conn = psycopg.connect(db_url, connect_timeout=10)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            COUNT(*) as total_records,
            SUM(CASE WHEN qa_score > 0 THEN 1 ELSE 0 END) as with_qa,
            AVG(qa_score) as avg_qa
        FROM professional_daily_metrics
        WHERE metric_date >= '2026-07-01' AND metric_date <= '2026-07-31'
    ''')

    result = cursor.fetchone()
    total, with_qa, avg_qa = result

    print(f"    Total records in July: {total:,}")
    print(f"    Records with QA score: {with_qa or 0:,} ({((with_qa or 0)/total*100):.1f}%)")
    print(f"    Average QA score: {avg_qa or 0:.1f}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    print("QA SCORE SYNC COMPLETE")
    print("=" * 80)

except Exception as e:
    import traceback
    print(f"\nERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
