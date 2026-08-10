#!/usr/bin/env python3
"""
Agent 8 Production Export - Query ALL data sources correctly
Trino queries + QA data + Improvement data + Calculate complete metrics
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

def get_production_appointments(provider_name, start_date, end_date):
    """Query Trino for REAL appointment data - ALL statuses"""

    queries = [
        # Query 1: Direct appointments table (FIXED: removed CAST)
        f"""SELECT COUNT(*) as cnt FROM deltalake.dl_standard_pbireporting.f_appointmentflattable
           WHERE doctorname = '{provider_name}'
           AND appointmentdate >= DATE '{start_date}'
           AND appointmentdate <= DATE '{end_date}'""",

        # Query 2: All claims (benefit-based appointments)
        f"""SELECT SUM(claim_count) as cnt FROM deltalake.dl_standard_pbireporting.managed_care_appt_utilization
           WHERE doctorname = '{provider_name}'
           AND appointmentdate >= DATE '{start_date}'
           AND appointmentdate <= DATE '{end_date}'""",
    ]

    logger.info(f"[TRINO-APPTS] Querying appointments for {provider_name}")

    for i, query in enumerate(queries, 1):
        try:
            result = execute_trino_query(query)
            if result and result[0].get('cnt'):
                count = result[0]['cnt']
                logger.info(f"[TRINO-APPTS] Query {i}: {count} appointments")
                return count
        except Exception as e:
            logger.warning(f"[TRINO-APPTS] Query {i} failed: {str(e)[:100]}")

    logger.warning(f"[TRINO-APPTS] No appointments found for {provider_name}")
    return 0

def get_production_improvements(provider_name, start_date, end_date):
    """Get improvement data from production sources (optional - returns 0 if fails)"""

    improvements = {
        'score': 0,
        'improved': 0,
        'total': 0
    }

    logger.info(f"[IMPROVE] Querying improvements for {provider_name}")

    # Try multiple schema paths for managed_care_programme_results
    schemas = [
        "deltalake.dl_standard_pbireporting.managed_care_programme_results",
        "public.managed_care_programme_results",
        "default.managed_care_programme_results",
        "managed_care_programme_results"
    ]

    for schema_path in schemas:
        query = f"""
            SELECT
                COUNT(DISTINCT patient_id) as total,
                COUNT(DISTINCT CASE WHEN biomarker_improvement > 0 THEN patient_id END) as improved,
                AVG(biomarker_improvement) as avg_score
            FROM {schema_path}
            WHERE provider = '{provider_name}'
            AND programme_code IN ('18', '357', '206', '10', '8')
            AND result_date >= DATE('{start_date}')
            AND result_date <= DATE('{end_date}')
        """

        try:
            result = execute_trino_query(query)
            if result and len(result) > 0 and result[0].get('total'):
                improvements = {
                    'score': float(result[0].get('avg_score', 0)) or 0,
                    'improved': int(result[0].get('improved', 0)) or 0,
                    'total': int(result[0].get('total', 0)) or 0
                }
                logger.info(f"[IMPROVE] {provider_name}: {improvements['improved']}/{improvements['total']} improved, avg={improvements['score']:.1f} (schema: {schema_path})")
                return improvements
        except Exception as e:
            logger.debug(f"[IMPROVE] Schema {schema_path} failed: {str(e)[:80]}")
            continue

    logger.warning(f"[IMPROVE] Could not find improvements for {provider_name} - using defaults")
    return improvements

def export_production_metrics(backfill=True):
    """Export metrics for MULTIPLE periods (full backfill + recent)"""

    end_date = datetime.now()
    all_rows = []

    # Define periods to export (multiple ranges so date selection returns DIFFERENT data)
    periods = [
        {'name': 'Full Backfill', 'start': datetime(2024, 1, 1), 'end': end_date},
        {'name': 'Last 90 Days', 'start': end_date - timedelta(days=90), 'end': end_date},
        {'name': 'Last 60 Days', 'start': end_date - timedelta(days=60), 'end': end_date},
        {'name': 'Last 30 Days', 'start': end_date - timedelta(days=30), 'end': end_date},
        {'name': 'Last 7 Days', 'start': end_date - timedelta(days=7), 'end': end_date},
    ]

    logger.info("=" * 80)
    logger.info("AGENT 8 PRODUCTION EXPORT - MULTI-PERIOD")
    logger.info("=" * 80)
    logger.info(f"Exporting {len(periods)} periods for {len(MC_DIETICIANS)} professionals")

    # For each period, export data
    for period_info in periods:
        start_date = period_info['start']
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = period_info['end'].strftime('%Y-%m-%d')

        logger.info(f"\n[PERIOD] {period_info['name']}: {start_str} to {end_str}")

        # Get data once for entire period
        logger.info("  [1/3] Fetching QA scores...")
        qa_scores = get_qa_scores()
        logger.info(f"    QA scores loaded: {len(qa_scores)} professionals")

        logger.info("  [2/3] Calculating working days...")
        d_inhouse = count_working_days_inhouse(start_str, end_str)
        d_contractual = count_working_days_contractual(start_str, end_str)
        logger.info(f"    IN-HOUSE: {d_inhouse} days, CONTRACTUAL: {d_contractual} days")

        logger.info("  [3/3] Processing appointments & improvements...")

        for idx, provider_name in enumerate(MC_DIETICIANS, 1):
            cohort = get_cohort_for_provider(provider_name)
            working_days = d_contractual if cohort == 'CONTRACTUAL' else d_inhouse
            slots_per_day = PROVIDER_CAPACITY_OVERRIDE.get(provider_name, PROVIDER_CAPACITY.get(cohort, 0))

            if slots_per_day <= 0:
                logger.warning(f"  [{idx}] {provider_name}: Unknown cohort {cohort}")
                continue

            # Get appointment data from Trino
            appts = get_production_appointments(provider_name, start_str, end_str)

            # Get improvement data
            improvements = get_production_improvements(provider_name, start_str, end_str)

            # Calculate metrics
            capacity = slots_per_day * working_days
            utilization = round((appts / max(capacity, 1)) * 100, 1)
            qa_score = qa_scores.get(provider_name, {}).get('score', 0) or 0
            improvement_score = improvements.get('score', 0)
            status = calculate_rubric_status(utilization, qa_score, improvement_score, cohort)
            forecast_7d = int(appts / working_days) if working_days > 0 else 0

            logger.info(f"    [{idx:2d}] {provider_name:<30} | Appts: {appts:>5} | Util: {utilization:>5.1f}% | QA: {qa_score:>5.1f} | Impr: {improvement_score:>5.1f}")

            all_rows.append({
                'provider_name': provider_name,
                'cohort': cohort,
                'start_date': start_str,
                'end_date': end_str,
                'appts_count': appts,
                'capacity': capacity,
                'utilization_pct': utilization,
                'qa_score': qa_score,
                'improvement_score': improvement_score,
                'improvement_total': improvements['total'],
                'status': status,
                'forecast_7d': forecast_7d,
                'patient_count': improvements['total'],
                'with_lab_data': improvements['improved'],
                'without_lab_data': improvements['total'] - improvements['improved']
            })

    logger.info(f"\n[4/4] Exporting to Excel...")

    if all_rows:
        df = pd.DataFrame(all_rows)
        filename = f"data/agent8_professionals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)

        # Also create latest symlink
        latest_file = "data/agent8_professionals_latest.xlsx"
        try:
            os.remove(latest_file)
        except:
            pass
        df.to_excel(latest_file, index=False)

        logger.info(f"  Exported: {len(df)} rows to {filename}")
        logger.info(f"  Latest: {latest_file}")

        # Summary stats
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY STATISTICS")
        logger.info("=" * 80)
        logger.info(f"Total Appointments: {df['appts_count'].sum():,}")
        logger.info(f"Total Capacity: {df['capacity'].sum():,}")
        logger.info(f"Overall Utilization: {(df['appts_count'].sum() / df['capacity'].sum() * 100):.1f}%")
        logger.info(f"Avg QA Score: {df['qa_score'].mean():.1f}")
        logger.info(f"Avg Improvement: {df['improvement_score'].mean():.1f}")
        logger.info(f"Status Distribution: {df['status'].value_counts().to_dict()}")
        logger.info("=" * 80)

        return {'status': 'success', 'file': latest_file, 'rows': len(df)}
    else:
        logger.error("No data to export!")
        return {'status': 'error', 'message': 'No data collected'}

if __name__ == '__main__':
    result = export_production_metrics(backfill=True)
    print(result)
