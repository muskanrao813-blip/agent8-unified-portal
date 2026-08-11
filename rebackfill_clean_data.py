#!/usr/bin/env python3
"""Re-backfill removed providers with proper deduplication"""
import sys
sys.path.insert(0, '.')

import os
from dotenv import load_dotenv
import psycopg
from trino.dbapi import connect
from trino.auth import BasicAuthentication

load_dotenv()

print("=" * 80)
print("RE-BACKFILL CLEANED PROVIDERS - WITH DEDUPLICATION")
print("=" * 80)

# List of providers that were cleaned (to be re-backfilled)
# This will be identified from the cleanup results
PROVIDERS_TO_REBACKFILL = [
    'Homeshwar Mandawliya',
    'Midhat Zehra',
    'Neha Suryawanshi',
    # Will add more based on cleanup results
]

# Helper functions from app.py
def count_working_days_inhouse(start_str, end_str):
    """Count working days for IN-HOUSE (5-6 day week with alternate Saturdays)"""
    from datetime import datetime, timedelta
    start = datetime.strptime(start_str, '%Y-%m-%d').date()
    end = datetime.strptime(end_str, '%Y-%m-%d').date()

    working_days = 0
    current = start
    while current <= end:
        if current.weekday() < 6:  # Mon-Fri (not Sat/Sun)
            working_days += 1
        elif current.weekday() == 5:  # Saturday
            if (current.day - 1) // 7 % 2 == 0:  # Alternate Saturday
                working_days += 1
        current += timedelta(days=1)
    return working_days

def count_working_days_contractual(start_str, end_str):
    """Count working days for CONTRACTUAL (6-day week, all Saturdays)"""
    from datetime import datetime, timedelta
    start = datetime.strptime(start_str, '%Y-%m-%d').date()
    end = datetime.strptime(end_str, '%Y-%m-%d').date()

    working_days = 0
    current = start
    while current <= end:
        if current.weekday() < 6:  # Mon-Sat (not Sunday)
            working_days += 1
        current += timedelta(days=1)
    return working_days

PROVIDER_CAPACITY = {
    'IN-HOUSE AI': 84,
    'IN-HOUSE OTHERS': 14,
    'IN-HOUSE MC': 14,
    'CONTRACTUAL': 22
}

COHORT_MAP = {
    'Homeshwar Mandawliya': 'CONTRACTUAL',
    'Midhat Zehra': 'CONTRACTUAL',
    'Neha Suryawanshi': 'CONTRACTUAL',
}

print("\n[1] CONNECTING TO TRINO")
print("-" * 80)

try:
    trino_conn = connect(
        host=os.getenv('TRINO_HOST'),
        port=int(os.getenv('TRINO_PORT', 443)),
        user=os.getenv('TRINO_USER'),
        auth=BasicAuthentication(os.getenv('TRINO_USER'), os.getenv('TRINO_PASSWORD')),
        http_scheme='https',
        verify=False
    )

    cursor = trino_conn.cursor()
    print("✓ Connected to Trino")

    # Query Trino with proper deduplication
    print("\n[2] QUERYING TRINO WITH DEDUPLICATION")
    print("-" * 80)

    db_url = os.getenv('DATABASE_URL')
    pg_conn = psycopg.connect(db_url, connect_timeout=10)
    pg_cursor = pg_conn.cursor()

    records_inserted = 0

    for provider in PROVIDERS_TO_REBACKFILL:
        cohort = COHORT_MAP.get(provider, 'CONTRACTUAL')
        daily_slots = PROVIDER_CAPACITY.get(cohort, 22)

        # Query Trino with proper COUNT aggregation (no duplicates)
        query = f"""
        SELECT
            appointmentdate,
            COUNT(*) as appointment_count
        FROM default.f_appointmentflattable
        WHERE doctorname = '{provider}'
        AND appointmentdate >= '2026-07-01'
        AND appointmentdate < '2026-08-01'
        AND status IN ('COM', 'BOOKED', 'ACT', 'WIC', 'RES')
        GROUP BY appointmentdate
        ORDER BY appointmentdate
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        print(f"\n{provider} ({cohort}):")
        print(f"  Retrieved {len(rows)} days of data")

        if not rows:
            print(f"  WARNING: No data found in Trino")
            continue

        # Calculate working days for capacity
        date_str_first = str(rows[0][0])
        date_str_last = str(rows[-1][0])

        if cohort == 'IN-HOUSE AI' or cohort == 'IN-HOUSE OTHERS' or cohort == 'IN-HOUSE MC':
            working_days = count_working_days_inhouse('2026-07-01', '2026-07-31')
        else:
            working_days = count_working_days_contractual('2026-07-01', '2026-07-31')

        total_capacity = daily_slots * working_days

        # Insert records into PostgreSQL
        for appt_date, appt_count in rows:
            date_obj = appt_date if isinstance(appt_date, str) else str(appt_date)
            util_pct = (appt_count / daily_slots * 100) if daily_slots > 0 else 0

            pg_cursor.execute('''
                INSERT INTO professional_daily_metrics
                (provider_name, cohort, metric_date, appts_count, capacity,
                 utilization_pct, qa_score, improvement_score, improvement_total,
                 status, patient_count, with_lab_data, without_lab_data)
                VALUES (%s, %s, %s, %s, %s, %s, 0, 0, 0, 'ACTIVE', 0, 0, 0)
                ON CONFLICT (provider_name, metric_date) DO UPDATE
                SET appts_count = %s, capacity = %s, utilization_pct = %s
            ''', (provider, cohort, date_obj, appt_count, daily_slots, util_pct,
                  appt_count, daily_slots, util_pct))

            records_inserted += 1

        print(f"  Inserted {len(rows)} daily records")

    pg_conn.commit()
    pg_cursor.close()
    pg_conn.close()

    print(f"\n[3] SUMMARY")
    print("-" * 80)
    print(f"Total records inserted: {records_inserted}")

    # Verify
    pg_conn = psycopg.connect(db_url, connect_timeout=10)
    pg_cursor = pg_conn.cursor()

    pg_cursor.execute('''
    SELECT provider_name, ROUND(AVG(utilization_pct)::numeric, 1) as avg_util
    FROM professional_daily_metrics
    WHERE metric_date >= '2026-07-01' AND metric_date <= '2026-07-31'
    AND provider_name IN (''' + ','.join([f"'{p}'" for p in PROVIDERS_TO_REBACKFILL]) + ''')
    GROUP BY provider_name
    ORDER BY provider_name
    ''')

    print("\nVerification - Rebackfilled providers:")
    for prov, util in pg_cursor.fetchall():
        status = "✓" if util <= 100 else "✗"
        print(f"  {status} {prov}: {util}% avg utilization")

    pg_cursor.close()
    pg_conn.close()

    cursor.close()
    trino_conn.close()

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("RE-BACKFILL COMPLETE")
print("=" * 80)
