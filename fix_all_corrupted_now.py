#!/usr/bin/env python3
"""IMMEDIATE FIX: Delete corrupted data and re-backfill correctly"""
import sys
sys.path.insert(0, '.')

import os
from dotenv import load_dotenv
import psycopg
from trino.dbapi import connect
from trino.auth import BasicAuthentication
from datetime import datetime, timedelta

load_dotenv()

CORRUPTED = [
    'Homeshwar Mandawliya',
    'Neha Suryawanshi',
    'Midhat Zehra',
    'Trupti Nakar',
    'Divya Pandey',
    'Sweta Naik',
    'Shefali Dindorkar',
    'Hemlata Alawadhi',
    'Mekala Reddy'
]

print("=" * 80)
print("IMMEDIATE FIX - DELETE CORRUPTED DATA AND RE-BACKFILL")
print("=" * 80)

# Connect to databases
pg_conn = psycopg.connect(os.getenv('DATABASE_URL'), connect_timeout=10)
pg_cursor = pg_conn.cursor()

trino_conn = connect(
    host=os.getenv('TRINO_HOST'),
    port=int(os.getenv('TRINO_PORT', 443)),
    user=os.getenv('TRINO_USER'),
    auth=BasicAuthentication(os.getenv('TRINO_USER'), os.getenv('TRINO_PASSWORD')),
    http_scheme='https',
    verify=False
)
trino_cursor = trino_conn.cursor()

# Step 1: Delete corrupted data
print("\n[1] DELETING CORRUPTED DATA")
print("-" * 80)

for provider in CORRUPTED:
    pg_cursor.execute('''
    DELETE FROM professional_daily_metrics
    WHERE provider_name = %s
    AND metric_date >= '2026-07-01' AND metric_date <= '2026-07-31'
    ''', (provider,))
    deleted = pg_cursor.rowcount
    print(f"  Deleted {deleted} records for {provider}")

pg_conn.commit()

# Step 2: Re-backfill from Trino
print("\n[2] RE-BACKFILLING FROM TRINO")
print("-" * 80)

# Get cohort info from database
pg_cursor.execute('''
SELECT DISTINCT provider_name, cohort FROM professional_daily_metrics
WHERE provider_name IN (''' + ','.join([f"'{p}'" for p in CORRUPTED]) + ''')
LIMIT 1
''')

cohort_map = {}
for prov, cohort in pg_cursor.fetchall():
    cohort_map[prov] = cohort

# If we don't have cohort info, use this mapping
default_cohorts = {
    'Homeshwar Mandawliya': 'CONTRACTUAL',
    'Neha Suryawanshi': 'CONTRACTUAL',
    'Midhat Zehra': 'CONTRACTUAL',
    'Trupti Nakar': 'IN-HOUSE MC',
    'Divya Pandey': 'IN-HOUSE MC',
    'Sweta Naik': 'IN-HOUSE MC',
    'Shefali Dindorkar': 'IN-HOUSE OTHERS',
    'Hemlata Alawadhi': 'CONTRACTUAL',
    'Mekala Reddy': 'IN-HOUSE MC'
}

capacity_map = {
    'IN-HOUSE AI': 84,
    'IN-HOUSE OTHERS': 14,
    'IN-HOUSE MC': 14,
    'CONTRACTUAL': 22
}

total_inserted = 0

for provider in CORRUPTED:
    cohort = cohort_map.get(provider, default_cohorts.get(provider, 'CONTRACTUAL'))
    daily_slots = capacity_map.get(cohort, 22)

    # Query Trino for this provider's data
    query = f"""
    SELECT
        appointmentdate,
        COUNT(*) as appt_count
    FROM default.f_appointmentflattable
    WHERE doctorname = '{provider}'
    AND appointmentdate >= '2026-07-01'
    AND appointmentdate < '2026-08-01'
    AND status IN ('COM', 'BOOKED', 'ACT', 'WIC', 'RES')
    GROUP BY appointmentdate
    ORDER BY appointmentdate
    """

    trino_cursor.execute(query)
    rows = trino_cursor.fetchall()

    print(f"  {provider} ({cohort}): {len(rows)} days")

    # Insert into PostgreSQL
    for appt_date, appt_count in rows:
        date_str = str(appt_date)
        util_pct = (appt_count / daily_slots * 100) if daily_slots > 0 else 0

        pg_cursor.execute('''
        INSERT INTO professional_daily_metrics
        (provider_name, cohort, metric_date, appts_count, capacity,
         utilization_pct, qa_score, improvement_score, improvement_total,
         status, patient_count, with_lab_data, without_lab_data)
        VALUES (%s, %s, %s, %s, %s, %s, 0, 0, 0, 'ACTIVE', 0, 0, 0)
        ON CONFLICT (provider_name, metric_date) DO NOTHING
        ''', (provider, cohort, date_str, appt_count, daily_slots, util_pct))

        total_inserted += 1

pg_conn.commit()

print(f"\n  Total inserted: {total_inserted} records")

# Step 3: Verify fix
print("\n[3] VERIFICATION")
print("-" * 80)

pg_cursor.execute('''
SELECT provider_name,
       ROUND(AVG(utilization_pct)::numeric, 1) as avg_util,
       SUM(appts_count) as total_appts,
       COUNT(*) as days
FROM professional_daily_metrics
WHERE provider_name IN (''' + ','.join([f"'{p}'" for p in CORRUPTED]) + ''')
AND metric_date >= '2026-07-01' AND metric_date <= '2026-07-31'
GROUP BY provider_name
ORDER BY avg_util DESC
''')

print("\nAfter fix:")
print(f"{'Provider':<30} {'Avg Util':<12} {'Total Appts':<15} {'Days':<8}")
print("-" * 65)

all_ok = True
for prov, util, appts, days in pg_cursor.fetchall():
    status = "✓" if util <= 100 else "✗"
    print(f"{status} {prov:<28} {util:>6.1f}%       {appts:>8}          {days:>4}")
    if util > 100:
        all_ok = False

if all_ok:
    print("\n✓ ALL PROVIDERS NOW VALID (<100% utilization)")
else:
    print("\n✗ Some providers still have issues")

pg_cursor.close()
pg_conn.close()
trino_cursor.close()
trino_conn.close()

print("\n" + "=" * 80)
print("FIX COMPLETE")
print("=" * 80)
