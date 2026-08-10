#!/usr/bin/env python3
"""
Agent 8 Fast Backfill - Bulk query Trino (NOT day-by-day)
Queries entire date range at once, much faster than incremental approach
"""
import pandas as pd
from datetime import datetime, timedelta
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

from app import (MC_DIETICIANS, PROVIDER_CAPACITY, PROVIDER_CAPACITY_OVERRIDE,
                 execute_trino_query, get_qa_scores, count_working_days_inhouse,
                 count_working_days_contractual, get_cohort_for_provider,
                 calculate_rubric_status)
from db_layer import store_professional_daily_metric, init_postgres_schema

def fast_backfill_daily_metrics(start_date='2024-01-01', end_date=None):
    """Fast backfill: Query Trino in bulk, then process locally"""

    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    total_days = (end - start).days + 1

    logger.info("=" * 80)
    logger.info("AGENT 8 FAST BACKFILL - BULK QUERY (2024-TODAY)")
    logger.info("=" * 80)
    logger.info(f"Backfilling: {start_date} to {end_date}")
    logger.info(f"Total days: {total_days}")
    logger.info(f"Professionals: {len(MC_DIETICIANS)}")
    logger.info("")

    # Initialize schema
    init_postgres_schema()

    # Get QA scores once
    logger.info("[1/3] Fetching QA scores...")
    qa_scores = get_qa_scores()

    logger.info("[2/3] Querying Trino for ALL appointments (bulk)...")
    # Query Trino ONCE for the entire date range
    query = f"""
        SELECT
            doctorname as provider_name,
            appointmentdate as appt_date,
            COUNT(*) as appt_count
        FROM deltalake.dl_standard_pbireporting.f_appointmentflattable
        WHERE appointmentdate >= DATE '{start_date}'
        AND appointmentdate <= DATE '{end_date}'
        AND doctorname IN ({','.join([f"'{name}'" for name in MC_DIETICIANS])})
        GROUP BY doctorname, appointmentdate
        ORDER BY appointmentdate, doctorname
    """

    try:
        results = execute_trino_query(query)
        logger.info(f"  Retrieved {len(results):,} appointment records from Trino")
    except Exception as e:
        logger.error(f"[TRINO] Bulk query failed: {str(e)}")
        return 0

    # Convert results to DataFrame for easier processing
    df = pd.DataFrame(results)
    logger.info(f"  Processing {len(df):,} rows into daily snapshots...")

    logger.info("[3/3] Storing in database...")
    total_stored = 0
    unique_dates = df['appt_date'].nunique() if len(df) > 0 else 0

    for idx, row in df.iterrows():
        provider_name = row['provider_name']
        date_str = row['appt_date'].strftime('%Y-%m-%d')
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
        qa_score = qa_scores.get(provider_name, {}).get('score', 0) or 0
        status = calculate_rubric_status(utilization, qa_score, 0, cohort)

        stored = store_professional_daily_metric(
            provider_name=provider_name,
            cohort=cohort,
            metric_date=date_str,
            appts_count=appts,
            capacity=capacity,
            utilization_pct=utilization,
            qa_score=qa_score,
            improvement_score=0,
            improvement_total=0,
            status=status,
            patient_count=0,
            with_lab_data=0,
            without_lab_data=0
        )

        if stored:
            total_stored += 1

        # Progress every 5000 rows
        if (idx + 1) % 5000 == 0:
            pct = int((idx + 1) / len(df) * 100)
            logger.info(f"  {pct}% complete ({idx + 1}/{len(df)} rows processed)")

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✅ FAST BACKFILL COMPLETE")
    logger.info(f"   Records stored: {total_stored:,}")
    logger.info(f"   Unique dates: {unique_dates}")
    logger.info(f"   Date range: {start_date} to {end_date}")
    logger.info(f"   Status: Ready for daily runner")
    logger.info("=" * 80)

    return total_stored

if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else '2024-01-01'
    end = sys.argv[2] if len(sys.argv) > 2 else None

    logger.info(f"Starting FAST backfill from {start}...")
    count = fast_backfill_daily_metrics(start, end)

    if count > 0:
        logger.info("✅ Fast backfill successful!")
        sys.exit(0)
    else:
        logger.error("❌ Fast backfill returned no records")
        sys.exit(1)
