#!/usr/bin/env python3
"""Resilient backfill with batch commits and connection recovery"""
import sys
sys.path.insert(0, '.')

from app import (execute_trino_query, MC_DIETICIANS, PROVIDER_CAPACITY,
                 PROVIDER_CAPACITY_OVERRIDE, get_cohort_for_provider,
                 calculate_rubric_status, count_working_days_inhouse,
                 count_working_days_contractual)
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

print("=" * 70)
print("RESILIENT BACKFILL - ALL 2026 DATA WITH BATCH COMMITS")
print("=" * 70)

BATCH_SIZE = 500  # Commit every 500 records
db_url = os.getenv('DATABASE_URL')

def get_db_connection():
    """Get fresh database connection"""
    return psycopg.connect(db_url, connect_timeout=30)

def store_batch(records, batch_num):
    """Store a batch of records with error recovery"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for provider_name, cohort, date_str, appts, cap, util, status in records:
            cursor.execute('''
                INSERT INTO professional_daily_metrics
                (provider_name, cohort, metric_date, appts_count, capacity,
                 utilization_pct, qa_score, improvement_score, improvement_total,
                 status, patient_count, with_lab_data, without_lab_data)
                VALUES (%s, %s, %s, %s, %s, %s, 0, 0, 0, %s, 0, 0, 0)
                ON CONFLICT (provider_name, metric_date) DO UPDATE
                SET appts_count = %s, capacity = %s, utilization_pct = %s, status = %s
            ''', (provider_name, cohort, date_str, appts, cap, util, status, appts, cap, util, status))

        conn.commit()
        cursor.close()
        conn.close()
        return len(records)

    except Exception as e:
        print(f"  Batch {batch_num} ERROR: {str(e)[:100]}")
        return 0

try:
    print("\n[1] Querying Trino for all 2026 records...")
    doctors = ','.join([f"'{d}'" for d in MC_DIETICIANS])

    query = f"""
    SELECT doctorname, appointmentdate, COUNT(*) as cnt
    FROM deltalake.dl_standard_pbireporting.f_appointmentflattable
    WHERE YEAR(appointmentdate) = 2026
    AND doctorname IN ({doctors})
    GROUP BY doctorname, appointmentdate
    """

    results = execute_trino_query(query)
    print(f"[OK] Retrieved {len(results):,} total records")

    print("\n[2] Processing records in batches...")
    batch_records = []
    total_stored = 0
    batch_num = 1

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

            batch_records.append((prov, cohort, date_str, appts, cap, util, status))

        # Store batch when it reaches BATCH_SIZE
        if len(batch_records) >= BATCH_SIZE:
            stored = store_batch(batch_records, batch_num)
            total_stored += stored
            print(f"  Batch {batch_num}: {stored:,} records ({total_stored:,} total)")
            batch_records = []
            batch_num += 1

        # Progress indicator
        if (i + 1) % 50000 == 0:
            print(f"  Progress: {i+1:,}/{len(results):,} records processed")

    # Store remaining records
    if batch_records:
        stored = store_batch(batch_records, batch_num)
        total_stored += stored
        print(f"  Batch {batch_num}: {stored:,} records ({total_stored:,} total)")

    print("\n" + "=" * 70)
    print("BACKFILL COMPLETE")
    print("=" * 70)
    print(f"Total Records Stored: {total_stored:,}")
    print(f"Expected: 132,912")
    print(f"Completion: {(total_stored/132912)*100:.1f}%")
    print("=" * 70)

    if total_stored == 0:
        sys.exit(1)

except Exception as e:
    import traceback
    print(f"\n[FATAL ERROR] {str(e)}")
    traceback.print_exc()
    sys.exit(1)
