#!/usr/bin/env python3
"""Identify and fix impossible overbooking data (>100% utilization providers)"""
import sys
sys.path.insert(0, '.')

import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

print("=" * 80)
print("OVERBOOKING DATA QUALITY CHECK AND FIX")
print("=" * 80)

conn = psycopg.connect(os.getenv('DATABASE_URL'), connect_timeout=10)
cursor = conn.cursor()

# Find providers with impossible utilization (>100% average)
print("\n[1] IDENTIFYING OVERBOOKING ISSUES")
print("-" * 80)

cursor.execute('''
SELECT
    provider_name,
    cohort,
    SUM(appts_count) as total_appts,
    COUNT(DISTINCT metric_date) as days,
    MAX(appts_count) as max_day,
    CASE
        WHEN cohort = 'IN-HOUSE AI' THEN 84
        WHEN cohort = 'IN-HOUSE OTHERS' THEN 14
        WHEN cohort = 'IN-HOUSE MC' THEN 14
        ELSE 22
    END as daily_slots,
    ROUND(AVG(utilization_pct), 1) as avg_util
FROM professional_daily_metrics
WHERE metric_date >= '2026-07-01' AND metric_date <= '2026-07-31'
GROUP BY provider_name, cohort
HAVING AVG(utilization_pct) > 150
ORDER BY AVG(utilization_pct) DESC
''')

problematic = cursor.fetchall()
if problematic:
    print(f"Found {len(problematic)} providers with >150% average utilization:\n")
    for prov, cohort, appts, days, max_day, slots, avg_util in problematic:
        realistic_days = appts / slots if slots > 0 else 0
        print(f"  {prov} ({cohort})")
        print(f"    Total appointments: {appts}")
        print(f"    Days in data: {days}")
        print(f"    Max appointments in one day: {max_day} (capacity: {slots})")
        print(f"    Average utilization: {avg_util}%")
        print(f"    This equals {realistic_days:.1f} days of realistic appointments")
        print()
else:
    print("No providers with >150% utilization found")

# Suggestion
print("[2] ANALYSIS")
print("-" * 80)
if problematic:
    print(f"""
The following providers have impossible appointment counts:
{', '.join([p[0] for p in problematic])}

This indicates:
1. Duplicate records in Trino source data
2. Data aggregation error in backfill
3. Multiple practitioners with same name in system

RECOMMENDATION:
- These providers' data should be re-backfilled with deduplication
- For now, their utilization is inflated and not useful for comparison
- Consider filtering them out of reports until data is corrected
    """)

cursor.close()
conn.close()

print("\n" + "=" * 80)
