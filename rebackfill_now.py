#!/usr/bin/env python3
"""Immediately rebackfill deleted providers with clean data"""
import sys
sys.path.insert(0, '.')

import psycopg, os
from trino.dbapi import connect
from trino.auth import BasicAuthentication
from dotenv import load_dotenv

load_dotenv()

print("REBACKFILLING DELETED PROVIDERS FROM TRINO")
print("=" * 70)

# PostgreSQL connection
pg_conn = psycopg.connect(os.getenv('DATABASE_URL'))
pg_cursor = pg_conn.cursor()

# Trino connection
trino_conn = connect(
    host=os.getenv('TRINO_HOST'),
    port=int(os.getenv('TRINO_PORT', 443)),
    user=os.getenv('TRINO_USER'),
    auth=BasicAuthentication(os.getenv('TRINO_USER'), os.getenv('TRINO_PASSWORD')),
    http_scheme='https',
    verify=False
)
trino_cursor = trino_conn.cursor()

providers = [
    ('Homeshwar Mandawliya', 'CONTRACTUAL', 22),
    ('Neha Suryawanshi', 'CONTRACTUAL', 22),
    ('Midhat Zehra', 'CONTRACTUAL', 22),
    ('Trupti Nakar', 'IN-HOUSE MC', 14),
    ('Divya Pandey', 'IN-HOUSE MC', 14),
    ('Sweta Naik', 'IN-HOUSE MC', 14),
    ('Shefali Dindorkar', 'IN-HOUSE OTHERS', 14),
    ('Hemlata Alawadhi', 'CONTRACTUAL', 22),
    ('Mekala Reddy', 'IN-HOUSE MC', 14)
]

total_records = 0

for provider, cohort, slots in providers:
    query = f"""
    SELECT appointmentdate, COUNT(*) as cnt
    FROM deltalake.dl_standard_pbireporting.f_appointmentflattable
    WHERE doctorname = '{provider}'
    AND YEAR(appointmentdate) = 2026
    AND MONTH(appointmentdate) IN (7, 8)
    GROUP BY appointmentdate
    ORDER BY appointmentdate
    """

    trino_cursor.execute(query)
    rows = trino_cursor.fetchall()

    print(f"{provider}: {len(rows)} days", end="")

    for date_val, cnt in rows:
        util = (cnt / slots * 100)
        pg_cursor.execute('''
        INSERT INTO professional_daily_metrics
        (provider_name, cohort, metric_date, appts_count, capacity, utilization_pct,
         qa_score, improvement_score, improvement_total, status, patient_count, with_lab_data, without_lab_data)
        VALUES (%s, %s, %s, %s, %s, %s, 0, 0, 0, 'ACTIVE', 0, 0, 0)
        ON CONFLICT (provider_name, metric_date) DO UPDATE
        SET appts_count = %s, capacity = %s, utilization_pct = %s
        ''', (provider, cohort, str(date_val), cnt, slots, util, cnt, slots, util))
        total_records += 1

    pg_conn.commit()
    print(" [OK]")

print(f"\nTotal records inserted: {total_records}")

# Verify
print("\nVERIFICATION:")
print("-" * 70)

pg_cursor.execute('''
SELECT provider_name, SUM(appts_count) as appts, COUNT(*) as days,
       AVG(utilization_pct) as util
FROM professional_daily_metrics
WHERE provider_name IN ('Homeshwar Mandawliya', 'Neha Suryawanshi', 'Midhat Zehra',
                        'Trupti Nakar', 'Divya Pandey', 'Sweta Naik',
                        'Shefali Dindorkar', 'Hemlata Alawadhi', 'Mekala Reddy')
AND metric_date >= '2026-07-01' AND metric_date <= '2026-07-31'
GROUP BY provider_name
ORDER BY provider_name
''')

all_fixed = True
for prov, appts, days, util in pg_cursor.fetchall():
    status = "[OK]" if util <= 100 else "[BAD]"
    print(f"{status} {prov:<30} {appts:>6} appts  {days:>2} days  {util:>6.1f}% util")
    if util > 100:
        all_fixed = False

print()
if all_fixed:
    print("[OK] ALL 9 PROVIDERS NOW VALID (<100% utilization)")
else:
    print("[BAD] Some providers still have issues")

pg_cursor.close()
pg_conn.close()
trino_cursor.close()
trino_conn.close()

print("=" * 70)
