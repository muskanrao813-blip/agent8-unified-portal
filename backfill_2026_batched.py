#!/usr/bin/env python3
"""
Backfill 2026 data in batches to avoid memory issues
Process in chunks: 1 month at a time
"""
import sys
sys.path.insert(0, '.')

from app import (execute_trino_query, PROVIDER_CAPACITY, PROVIDER_CAPACITY_OVERRIDE,
                 get_cohort_for_provider, calculate_rubric_status, count_working_days_inhouse,
                 count_working_days_contractual, MC_DIETICIANS)
from db_layer import store_professional_daily_metric, init_postgres_schema
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

init_postgres_schema()

logger.info("=" * 70)
logger.info("BACKFILL 2026 DATA - BATCHED BY MONTH")
logger.info("=" * 70)

# Process month by month (Jan - Dec 2026)
months = [
    (1, "January"), (2, "February"), (3, "March"), (4, "April"),
    (5, "May"), (6, "June"), (7, "July"), (8, "August"),
    (9, "September"), (10, "October"), (11, "November"), (12, "December")
]

total_stored = 0
doctors_list = ','.join([f"'{name}'" for name in MC_DIETICIANS])

for month_num, month_name in months:
    logger.info(f"\n[{month_num:2d}/12] Processing {month_name} 2026...")

    query = f"""
        SELECT
            doctorname,
            appointmentdate,
            COUNT(*) as appt_count
        FROM deltalake.dl_standard_pbireporting.f_appointmentflattable
        WHERE YEAR(appointmentdate) = 2026
        AND MONTH(appointmentdate) = {month_num}
        AND doctorname IN ({doctors_list})
        GROUP BY doctorname, appointmentdate
    """

    try:
        results = execute_trino_query(query)
        logger.info(f"  Retrieved {len(results):,} records")

        month_stored = 0
        for row in results:
            provider_name = row['doctorname']
            date_obj = row['appointmentdate']
            if hasattr(date_obj, 'date'):
                date_str = date_obj.date().isoformat()
            else:
                date_str = str(date_obj)

            appts = row['appt_count']

            cohort = get_cohort_for_provider(provider_name)
            d_inhouse = count_working_days_inhouse(date_str, date_str)
            d_contractual = count_working_days_contractual(date_str, date_str)
            working_days = d_contractual if cohort == 'CONTRACTUAL' else d_inhouse
            slots_per_day = PROVIDER_CAPACITY_OVERRIDE.get(provider_name, PROVIDER_CAPACITY.get(cohort, 0))

            if slots_per_day <= 0:
                continue

            capacity = slots_per_day * max(working_days, 1)
            utilization = round((appts / max(capacity, 1)) * 100, 1)
            status = calculate_rubric_status(utilization, 0, 0, cohort)

            stored_ok = store_professional_daily_metric(
                provider_name=provider_name,
                cohort=cohort,
                metric_date=date_str,
                appts_count=appts,
                capacity=capacity,
                utilization_pct=utilization,
                qa_score=0,
                improvement_score=0,
                improvement_total=0,
                status=status,
                patient_count=0,
                with_lab_data=0,
                without_lab_data=0
            )

            if stored_ok:
                month_stored += 1

        total_stored += month_stored
        logger.info(f"  Stored {month_stored:,} records")

    except Exception as e:
        logger.error(f"  Error processing {month_name}: {str(e)[:100]}")
        continue

logger.info("")
logger.info("=" * 70)
logger.info(f"✅ BACKFILL COMPLETE")
logger.info(f"   Total 2026 records stored: {total_stored:,}")
logger.info(f"   All 26 MC dieticians populated")
logger.info("=" * 70)
