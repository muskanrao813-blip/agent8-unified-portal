#!/usr/bin/env python3
"""Complete backfill: Load all 132,912 2026 records"""
import sys
sys.path.insert(0, '.')

from app import (execute_trino_query, MC_DIETICIANS, PROVIDER_CAPACITY,
                 PROVIDER_CAPACITY_OVERRIDE, get_cohort_for_provider,
                 calculate_rubric_status, count_working_days_inhouse,
                 count_working_days_contractual)
from db_layer import store_professional_daily_metric, init_postgres_schema

print("=" * 70)
print("COMPLETE 2026 BACKFILL - ALL RECORDS")
print("=" * 70)

init_postgres_schema()
total = 0
doctors = ','.join([f"'{d}'" for d in MC_DIETICIANS])

query = f"""
SELECT doctorname, appointmentdate, COUNT(*) as cnt
FROM deltalake.dl_standard_pbireporting.f_appointmentflattable
WHERE YEAR(appointmentdate) = 2026
AND doctorname IN ({doctors})
GROUP BY doctorname, appointmentdate
"""

try:
    print("\n[1] Querying Trino for all 2026 records...")
    results = execute_trino_query(query)
    print(f"[OK] Retrieved {len(results):,} total records")

    print("\n[2] Processing and storing records...")
    for i, row in enumerate(results):
        prov = row['doctorname']
        date_obj = row['appointmentdate']
        if hasattr(date_obj, 'date'):
            date_str = date_obj.date().isoformat()
        else:
            date_str = str(date_obj)
        appts = row['cnt']

        cohort = get_cohort_for_provider(prov)
        d_in = count_working_days_inhouse(date_str, date_str)
        d_con = count_working_days_contractual(date_str, date_str)
        wd = d_con if cohort == 'CONTRACTUAL' else d_in
        slots = PROVIDER_CAPACITY_OVERRIDE.get(prov, PROVIDER_CAPACITY.get(cohort, 0))

        if slots > 0:
            cap = slots * max(wd, 1)
            util = round((appts / max(cap, 1)) * 100, 1)
            status = calculate_rubric_status(util, 0, 0, cohort)

            store_professional_daily_metric(
                prov, cohort, date_str, appts, cap, util, 0, 0, 0, status, 0, 0, 0
            )
            total += 1

        if (i + 1) % 30000 == 0:
            print(f"   Progress: {i+1:,}/{len(results):,} ({(i+1)/len(results)*100:.1f}%)")

    print("\n" + "=" * 70)
    print("BACKFILL COMPLETE")
    print("=" * 70)
    print(f"Records Stored: {total:,}")
    print(f"Expected: 132,912")
    print(f"Completion: {(total/132912)*100:.1f}%")
    print("=" * 70)

except Exception as e:
    import traceback
    print(f"\n[ERROR] {str(e)}")
    traceback.print_exc()
    sys.exit(1)
