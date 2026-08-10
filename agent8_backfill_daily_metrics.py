#!/usr/bin/env python3
"""
Agent 8 Backfill Daily Metrics - ONE TIME ONLY
Populates professional_daily_metrics table from 2024-01-01 to today
Run once, then schedule daily runner for ongoing updates
"""
import pandas as pd
from datetime import datetime, timedelta
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

from app import (MC_DIETICIANS, PROVIDER_CAPACITY, PROVIDER_CAPACITY_OVERRIDE,
                 execute_trino_query, get_qa_scores, count_working_days_inhouse,
                 count_working_days_contractual, get_cohort_for_provider,
                 calculate_rubric_status)
from db_layer import store_professional_daily_metric, init_postgres_schema

def get_daily_appointments(provider_name, date_str):
    """Query Trino for appointments on a specific date"""
    query = f"""
        SELECT COUNT(*) as cnt
        FROM deltalake.dl_standard_pbireporting.f_appointmentflattable
        WHERE doctorname = '{provider_name}'
        AND appointmentdate = DATE '{date_str}'
    """

    try:
        result = execute_trino_query(query)
        if result and result[0].get('cnt'):
            return result[0]['cnt']
    except Exception as e:
        logger.debug(f"[TRINO] No data for {provider_name} on {date_str}")

    return 0

def get_daily_improvements(provider_name, date_str):
    """Query improvements for a specific date"""
    improvements = {'score': 0, 'improved': 0, 'total': 0}

    query = f"""
        SELECT
            COUNT(DISTINCT patient_id) as total,
            COUNT(DISTINCT CASE WHEN biomarker_improvement > 0 THEN patient_id END) as improved,
            AVG(biomarker_improvement) as avg_score
        FROM managed_care_programme_results
        WHERE provider = '{provider_name}'
        AND programme_code IN ('18', '357', '206', '10', '8')
        AND result_date = DATE('{date_str}')
    """

    try:
        result = execute_trino_query(query)
        if result and result[0].get('total'):
            improvements = {
                'score': float(result[0].get('avg_score', 0)) or 0,
                'improved': int(result[0].get('improved', 0)) or 0,
                'total': int(result[0].get('total', 0)) or 0
            }
    except Exception as e:
        logger.debug(f"[TRINO] No improvements for {provider_name} on {date_str}")

    return improvements

def backfill_daily_metrics(start_date='2024-01-01', end_date=None):
    """Backfill daily metrics from start_date to end_date"""

    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    total_days = (end - start).days + 1

    logger.info("=" * 80)
    logger.info("AGENT 8 BACKFILL - DAILY SNAPSHOTS (2024-TODAY)")
    logger.info("=" * 80)
    logger.info(f"Backfilling: {start_date} to {end_date}")
    logger.info(f"Total days: {total_days}")
    logger.info(f"Professionals: {len(MC_DIETICIANS)}")
    logger.info(f"Total records to create: {total_days * len(MC_DIETICIANS):,}")
    logger.info("")

    # Initialize schema
    init_postgres_schema()

    # Get QA scores once (reuse for all dates)
    logger.info("Fetching QA scores...")
    qa_scores = get_qa_scores()

    total_stored = 0
    current_date = start

    while current_date <= end:
        date_str = current_date.strftime('%Y-%m-%d')

        # Calculate working days for this single day
        d_inhouse = count_working_days_inhouse(date_str, date_str)
        d_contractual = count_working_days_contractual(date_str, date_str)

        # Progress indicator every 30 days
        days_elapsed = (current_date - start).days
        if days_elapsed % 30 == 0:
            percent = int((days_elapsed / total_days) * 100)
            logger.info(f"[{percent:3d}%] Processing {date_str}...")

        for provider_name in MC_DIETICIANS:
            cohort = get_cohort_for_provider(provider_name)
            working_days = d_contractual if cohort == 'CONTRACTUAL' else d_inhouse
            slots_per_day = PROVIDER_CAPACITY_OVERRIDE.get(provider_name, PROVIDER_CAPACITY.get(cohort, 0))

            if slots_per_day <= 0:
                continue

            # Get daily data
            appts = get_daily_appointments(provider_name, date_str)
            improvements = get_daily_improvements(provider_name, date_str)

            # Calculate metrics
            capacity = slots_per_day * max(working_days, 1)
            utilization = round((appts / max(capacity, 1)) * 100, 1)
            qa_score = qa_scores.get(provider_name, {}).get('score', 0) or 0
            improvement_score = improvements.get('score', 0)
            status = calculate_rubric_status(utilization, qa_score, improvement_score, cohort)

            # Store in database
            stored = store_professional_daily_metric(
                provider_name=provider_name,
                cohort=cohort,
                metric_date=date_str,
                appts_count=appts,
                capacity=capacity,
                utilization_pct=utilization,
                qa_score=qa_score,
                improvement_score=improvement_score,
                improvement_total=improvements['total'],
                status=status,
                patient_count=improvements['total'],
                with_lab_data=improvements['improved'],
                without_lab_data=improvements['total'] - improvements['improved']
            )

            if stored:
                total_stored += 1

        current_date += timedelta(days=1)

    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✅ BACKFILL COMPLETE")
    logger.info(f"   Records stored: {total_stored:,}")
    logger.info(f"   Date range: {start_date} to {end_date}")
    logger.info(f"   Status: Ready for daily runner")
    logger.info("=" * 80)

    return total_stored

if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else '2024-01-01'
    end = sys.argv[2] if len(sys.argv) > 2 else None

    logger.info(f"Starting backfill from {start}...")
    count = backfill_daily_metrics(start, end)

    if count > 0:
        logger.info("✅ Backfill successful!")
        sys.exit(0)
    else:
        logger.error("❌ Backfill failed - no records stored")
        sys.exit(1)
