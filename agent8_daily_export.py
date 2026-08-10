#!/usr/bin/env python3
"""
Agent 8 Daily Export - Store daily snapshots of professional metrics
Updates: Every day for TODAY's data only (fast, incremental)
No periods - just daily snapshots that accumulate over time
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
        logger.warning(f"[TRINO] Query failed for {provider_name} on {date_str}: {str(e)[:100]}")

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
        logger.warning(f"[TRINO] Improvements query failed: {str(e)[:100]}")

    return improvements

def export_daily_metrics(target_date=None):
    """Export metrics for TODAY (or specified date)"""

    if target_date is None:
        target_date = datetime.now()
    elif isinstance(target_date, str):
        target_date = datetime.strptime(target_date, '%Y-%m-%d')

    date_str = target_date.strftime('%Y-%m-%d')

    logger.info("=" * 80)
    logger.info("AGENT 8 DAILY EXPORT - DAILY SNAPSHOTS")
    logger.info("=" * 80)
    logger.info(f"Exporting data for: {date_str}")
    logger.info(f"Processing {len(MC_DIETICIANS)} professionals")

    # Initialize schema
    init_postgres_schema()

    # Get QA scores once
    logger.info("[1/3] Fetching QA scores...")
    qa_scores = get_qa_scores()
    logger.info(f"  QA scores loaded: {len(qa_scores)} professionals")

    # Calculate working days (just for this one day)
    logger.info("[2/3] Calculating capacity...")
    d_inhouse = count_working_days_inhouse(date_str, date_str)
    d_contractual = count_working_days_contractual(date_str, date_str)
    logger.info(f"  Working day check: IN-HOUSE={d_inhouse}, CONTRACTUAL={d_contractual}")

    # Process each professional
    logger.info("[3/3] Processing daily data...")
    success_count = 0

    for idx, provider_name in enumerate(MC_DIETICIANS, 1):
        cohort = get_cohort_for_provider(provider_name)
        working_days = d_contractual if cohort == 'CONTRACTUAL' else d_inhouse
        slots_per_day = PROVIDER_CAPACITY_OVERRIDE.get(provider_name, PROVIDER_CAPACITY.get(cohort, 0))

        if slots_per_day <= 0:
            logger.warning(f"  [{idx}] {provider_name}: Unknown cohort {cohort}")
            continue

        # Get daily data
        appts = get_daily_appointments(provider_name, date_str)
        improvements = get_daily_improvements(provider_name, date_str)

        # Calculate metrics
        capacity = slots_per_day * max(working_days, 1)  # At least 1 day
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
            success_count += 1
            logger.info(f"  [{idx:2d}] {provider_name:<30} | Appts: {appts:>4} | Util: {utilization:>5.1f}% | QA: {qa_score:>5.1f}")
        else:
            logger.error(f"  [{idx:2d}] {provider_name}: FAILED to store")

    # Summary
    logger.info("=" * 80)
    logger.info(f"✅ Daily export completed: {success_count}/{len(MC_DIETICIANS)} professionals")
    logger.info(f"   Data stored for: {date_str}")
    logger.info(f"   Location: Neon PostgreSQL (professional_daily_metrics)")
    logger.info("=" * 80)

    return success_count == len(MC_DIETICIANS)

if __name__ == '__main__':
    # Export today's data (or pass date as argument)
    target = sys.argv[1] if len(sys.argv) > 1 else None
    success = export_daily_metrics(target)
    sys.exit(0 if success else 1)
