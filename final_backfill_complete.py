#!/usr/bin/env python3
"""Final complete backfill for all 2026 data"""
import sys
sys.path.insert(0, '.')

from app import execute_trino_query, MC_DIETICIANS, PROVIDER_CAPACITY, PROVIDER_CAPACITY_OVERRIDE, get_cohort_for_provider, calculate_rubric_status, count_working_days_inhouse, count_working_days_contractual
from db_layer import store_professional_daily_metric, init_postgres_schema

print('=' * 70)
print('FINAL COMPLETE BACKFILL - ALL 2026 DATA')
print('=' * 70)

init_postgres_schema()

total = 0
doctors = ','.join([f"'{d}'" for d in MC_DIETICIANS])

# Query all 2026 data
query = f'''
SELECT doctorname, appointmentdate, COUNT(*) as cnt
FROM deltalake.dl_standard_pbireporting.f_appointmentflattable
WHERE YEAR(appointmentdate) = 2026
AND doctorname IN ({doctors})
GROUP BY doctorname, appointmentdate
ORDER BY appointmentdate
'''

print('Querying Trino for all 2026 data...')
try:
    results = execute_trino_query(query)
    print(f'Retrieved {len(results):,} records from Trino')
    print('Processing and storing...\n')

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

        if (i + 1) % 20000 == 0:
            print(f'  {i+1:,}/{len(results):,} records processed...')

    print('\n' + '=' * 70)
    print(f'BACKFILL COMPLETE')
    print(f'Total Records Stored: {total:,}')
    print(f'Expected: 132,912')
    print(f'Completion: {(total/132912)*100:.1f}%')
    print('=' * 70)

except Exception as e:
    import traceback
    print(f'ERROR: {str(e)}')
    traceback.print_exc()
