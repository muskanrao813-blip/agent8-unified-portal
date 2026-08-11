#!/usr/bin/env python3
"""Remove corrupted appointment data with >100% utilization and recalculate"""
import sys
sys.path.insert(0, '.')

import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

print("=" * 80)
print("CLEANING CORRUPTED DATA - REMOVING >100% UTILIZATION RECORDS")
print("=" * 80)

conn = psycopg.connect(os.getenv('DATABASE_URL'), connect_timeout=10)
cursor = conn.cursor()

# Step 1: Find corrupted providers
print("\n[1] IDENTIFYING CORRUPTED PROVIDERS")
print("-" * 80)

cursor.execute('''
SELECT DISTINCT provider_name, cohort, ROUND(AVG(utilization_pct)::numeric, 1) as avg_util
FROM professional_daily_metrics
WHERE metric_date >= '2026-07-01' AND metric_date <= '2026-07-31'
GROUP BY provider_name, cohort
HAVING AVG(utilization_pct) > 100
ORDER BY provider_name
''')

corrupted = cursor.fetchall()

if corrupted:
    print(f"Found {len(corrupted)} corrupted providers:\n")
    for prov, cohort, avg_util in corrupted:
        print(f"  - {prov} ({cohort}): {avg_util}% avg utilization")

    # Step 2: Remove their data
    print("\n[2] REMOVING CORRUPTED DATA")
    print("-" * 80)

    providers_to_clean = [prov for prov, _, _ in corrupted]
    for prov in providers_to_clean:
        cursor.execute('''
            DELETE FROM professional_daily_metrics
            WHERE provider_name = %s
            AND metric_date >= '2026-07-01' AND metric_date <= '2026-07-31'
        ''', (prov,))
        rows_deleted = cursor.rowcount
        print(f"  Deleted {rows_deleted} records for {prov}")

    conn.commit()

    # Step 3: Verify
    print("\n[3] VERIFICATION")
    print("-" * 80)

    cursor.execute('''
    SELECT COUNT(*) FROM professional_daily_metrics
    WHERE metric_date >= '2026-07-01' AND metric_date <= '2026-07-31'
    ''')

    remaining = cursor.fetchone()[0]
    print(f"Remaining records: {remaining}")

    # Check for any >100% after cleanup
    cursor.execute('''
    SELECT provider_name, ROUND(AVG(utilization_pct)::numeric, 1)
    FROM professional_daily_metrics
    WHERE metric_date >= '2026-07-01' AND metric_date <= '2026-07-31'
    GROUP BY provider_name
    HAVING AVG(utilization_pct) > 100
    ''')

    still_corrupted = cursor.fetchall()
    if still_corrupted:
        print(f"\nWARNING: {len(still_corrupted)} providers still >100%:")
        for prov, util in still_corrupted:
            print(f"  - {prov}: {util}%")
    else:
        print("✓ All providers now have ≤100% utilization")

else:
    print("No corrupted data found - all utilization rates are valid (<100%)")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("CLEANUP COMPLETE")
print("=" * 80)
print("""
Next Steps:
1. Re-backfill the removed providers' data with proper deduplication
2. Or use cleaned Trino data without duplicates
3. Verify all providers show realistic appointment counts
""")
