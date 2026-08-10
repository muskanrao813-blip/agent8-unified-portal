#!/usr/bin/env python3
"""Diagnose capacity calculation discrepancy"""
import sys
sys.path.insert(0, '.')

import os
from dotenv import load_dotenv
import psycopg
from datetime import datetime

load_dotenv()

print("=" * 80)
print("DIAGNOSE CAPACITY CALCULATION ISSUE")
print("=" * 80)

# Current config
from app import PROVIDER_CAPACITY

print("\n[CONFIG] Current PROVIDER_CAPACITY:")
print(f"  IN-HOUSE AI: {PROVIDER_CAPACITY.get('IN-HOUSE AI')} slots/day")
print(f"  IN-HOUSE OTHERS: {PROVIDER_CAPACITY.get('IN-HOUSE OTHERS')} slots/day")
print(f"  IN-HOUSE MC: {PROVIDER_CAPACITY.get('IN-HOUSE MC')} slots/day")
print(f"  CONTRACTUAL: {PROVIDER_CAPACITY.get('CONTRACTUAL')} slots/day")

# What's stored in database
print("\n[DATABASE] Checking stored capacity for July 2026:")

try:
    db_url = os.getenv('DATABASE_URL')
    conn = psycopg.connect(db_url, connect_timeout=10)
    cursor = conn.cursor()

    # Check Ambika Rode specifically
    cursor.execute("""
        SELECT
            provider_name,
            cohort,
            metric_date,
            capacity,
            appts_count,
            ROUND(capacity / COUNT(*) OVER (PARTITION BY provider_name ORDER BY metric_date), 1) as slots_per_day_calc
        FROM professional_daily_metrics
        WHERE provider_name = 'Ambika Rode'
        AND metric_date >= '2026-07-01' AND metric_date <= '2026-07-31'
        ORDER BY metric_date
        LIMIT 5
    """)

    print("\nAmbika Rode - Sample daily records:")
    print("Date          Capacity  Appts  (Implied slots/day based on capacity)")
    print("-" * 70)

    results = cursor.fetchall()
    if results:
        for row in results:
            date_str = str(row[2])
            capacity = row[3]
            appts = row[4]
            print(f"{date_str}  {capacity:>8}  {appts:>5}")

        # Calculate what slots per day would be needed
        first_capacity = results[0][3]
        implied_days = 20 if first_capacity == 1680 else 24 if first_capacity == 2016 else None

        print(f"\nIf capacity = {first_capacity}, then:")
        print(f"  - Using 84 slots/day: {first_capacity}/84 = {first_capacity/84:.1f} working days")
        print(f"  - Using different formula to get {first_capacity}?")

    # Check all IN-HOUSE AI providers for July
    print("\n[PATTERN] Checking all IN-HOUSE AI capacity values for July:")
    cursor.execute("""
        SELECT DISTINCT
            provider_name,
            capacity,
            COUNT(*) as num_days
        FROM professional_daily_metrics
        WHERE cohort = 'IN-HOUSE AI'
        AND metric_date >= '2026-07-01' AND metric_date <= '2026-07-31'
        GROUP BY provider_name, capacity
        ORDER BY capacity
    """)

    print("Provider                    Capacity  Days_Count")
    print("-" * 50)
    for row in cursor.fetchall():
        provider = row[0][:25]
        capacity = row[1]
        days = row[2]
        implied_slots = capacity / days if days > 0 else 0
        print(f"{provider:<25} {capacity:>8}  {days:>4}  (implies {implied_slots:.1f} slots/day)")

    # Check what working days count was used
    print("\n[CALCULATION] Reverse-engineering working days used:")
    print("If Ambika Rode IN-HOUSE AI has 1,680 capacity:")
    print("  - 1,680 / 84 slots = 20 working days (NOT 24!)")
    print("  - This suggests backfill used different working days logic")

    print("\n" + "=" * 80)
    print("ROOT CAUSE ANALYSIS")
    print("=" * 80)

    cursor.execute("""
        SELECT
            COUNT(DISTINCT metric_date) as unique_dates,
            MIN(metric_date) as min_date,
            MAX(metric_date) as max_date,
            COUNT(*) as total_records
        FROM professional_daily_metrics
        WHERE provider_name = 'Ambika Rode'
        AND metric_date >= '2026-07-01' AND metric_date <= '2026-07-31'
    """)

    row = cursor.fetchone()
    print(f"\nAmbika Rode - July records:")
    print(f"  Total daily records: {row[3]}")
    print(f"  Unique dates: {row[0]}")
    print(f"  Date range: {row[1]} to {row[2]}")

    if row[0] and row[0] < 24:
        print(f"\n  ISSUE: Only {row[0]} days of data, not full July (31 days)")
        print(f"  If capacity formula is: slots_per_day × num_days_in_data")
        print(f"  Then: 84 × 20 = 1,680 (matches what we see!)")

    cursor.close()
    conn.close()

except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("""
The 1,680 capacity appears because the backfill only stored 20 days of data
per provider for July, not all 24 working days.

FIXES NEEDED:
1. Verify actual days of data per provider in database
2. Either:
   a) Recalculate capacity for full 24 working days (2,016)
   b) Investigate why only 20 days were stored

3. Re-run complete backfill with correct working days calculation
4. Ensure all utilities calculations match 24/26 day pattern
""")
