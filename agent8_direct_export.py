#!/usr/bin/env python3
"""
Agent 8 Direct Export to Excel
Queries Trino directly, calculates metrics, exports to Excel
No database dependency
"""
import pandas as pd
import requests
from datetime import datetime, timedelta
import logging
import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Import constants from app
from app import MC_DIETICIANS, PROVIDER_CAPACITY, PROVIDER_CAPACITY_OVERRIDE, execute_trino_query, get_qa_scores
from app import count_working_days_inhouse, count_working_days_contractual, get_cohort_for_provider, calculate_rubric_status

def export_agent8_direct(backfill=True):
    """Export Agent 8 metrics directly from Trino to Excel

    Args:
        backfill: If True, export from 2024-01-01. If False, export last 23 days.
    """

    end_date = datetime.now()
    if backfill:
        start_date = datetime(2024, 1, 1)  # Backfill from 2024
    else:
        start_date = end_date - timedelta(days=23)  # Daily update: 23-day window

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    logger.info(f"===== DIRECT EXPORT AGENT 8 TO EXCEL =====")
    logger.info(f"Date range: {start_str} to {end_str}")
    logger.info(f"Professionals: {len(MC_DIETICIANS)}")

    try:
        all_rows = []

        # Process in 30-day chunks to avoid timeout
        chunk_size = 30
        current_date = start_date
        chunk_num = 0

        while current_date < end_date:
            chunk_end = min(current_date + timedelta(days=chunk_size), end_date)
            chunk_start_str = current_date.strftime('%Y-%m-%d')
            chunk_end_str = chunk_end.strftime('%Y-%m-%d')
            chunk_num += 1

            logger.info(f"\n[CHUNK {chunk_num}] {chunk_start_str} to {chunk_end_str}")

            # Get working days for this chunk
            d_inhouse = count_working_days_inhouse(chunk_start_str, chunk_end_str)
            d_contractual = count_working_days_contractual(chunk_start_str, chunk_end_str)

            # Get QA scores (skip if not available)
            try:
                qa_scores = get_qa_scores()
            except Exception as e:
                logger.warning(f"QA scores unavailable: {e}")
                qa_scores = {}

            # Query improvements from Managed Care skill (VYTAL programmes)
            improvements = {}
            try:
                # Query Trino for MC programme biomarker improvements
                q_improvement = f"""
                    SELECT
                        provider,
                        COUNT(DISTINCT patient_id) as patients_total,
                        COUNT(DISTINCT CASE WHEN avg_biomarker_improvement > 0 THEN patient_id END) as patients_improved,
                        AVG(avg_biomarker_improvement) as avg_improvement
                    FROM hive.managed_care.programme_biomarker_improvements
                    WHERE appointment_status IN ('COM', 'BOOKED', 'ACT')
                    AND programme_code IN ('18', '357', '206', '10', '8')
                    AND appointment_date >= DATE('{chunk_start_str}')
                    AND appointment_date <= DATE('{chunk_end_str}')
                    GROUP BY provider
                """
                r_improvement = execute_trino_query(q_improvement)
                for row in r_improvement:
                    provider = row.get('provider')
                    improvements[provider] = {
                        'score': row.get('avg_improvement', 0) or 0,
                        'improved': row.get('patients_improved', 0) or 0,
                        'total': row.get('patients_total', 0) or 0
                    }
            except Exception as e:
                logger.warning(f"MC improvements unavailable for chunk {chunk_num}: {e}")

            # Calculate for each MC dietician for this chunk
            rows = []
            for provider_name in MC_DIETICIANS:
                cohort = get_cohort_for_provider(provider_name)

                # Query appointments from Trino for this chunk
                q_appts = f"""SELECT COUNT(*) as appt_count
                             FROM deltalake.dl_standard_pbireporting.f_appointmentflattable
                             WHERE doctorname = '{provider_name}'
                             AND appointmentstatus IN ('COM', 'BOOKED')
                             AND CAST(appointmentdate AS DATE) >= DATE('{chunk_start_str}')
                             AND CAST(appointmentdate AS DATE) <= DATE('{chunk_end_str}')
                            """
                r_appts = execute_trino_query(q_appts)
                appts = r_appts[0]['appt_count'] if r_appts else 0

                # Calculate capacity for this chunk
                working_days = d_contractual if cohort == 'CONTRACTUAL' else d_inhouse
                slots_per_day = PROVIDER_CAPACITY_OVERRIDE.get(provider_name, PROVIDER_CAPACITY.get(cohort, 0))

                if slots_per_day <= 0:
                    logger.warning(f"Unknown cohort {cohort} for {provider_name}")
                    continue

                capacity = slots_per_day * working_days
                utilization = round((appts / max(capacity, 1)) * 100, 1)

                # Get scores
                qa_score = qa_scores.get(provider_name, {}).get('score', 0) or 0
                improvement = improvements.get(provider_name, {})
                improvement_score = improvement.get('score', 0) or 0

                # Status
                status = calculate_rubric_status(utilization, qa_score, improvement_score, cohort)

                # Forecast
                forecast_7d = int(appts / working_days) if working_days > 0 else 0

                rows.append({
                    'provider_name': provider_name,
                    'cohort': cohort,
                    'start_date': chunk_start_str,
                    'end_date': chunk_end_str,
                    'appts_count': appts,
                    'capacity': capacity,
                    'utilization_pct': utilization,
                    'qa_score': qa_score,
                    'improvement_score': improvement_score,
                    'improvement_total': improvement.get('total', 0),
                    'status': status,
                    'forecast_7d': forecast_7d,
                    'patient_count': 0,
                    'with_lab_data': 0,
                    'without_lab_data': 0
                })

            all_rows.extend(rows)
            logger.info(f"Chunk {chunk_num}: {len(rows)} rows")

            current_date = chunk_end + timedelta(days=1)

        # Create DataFrame from all chunks
        df = pd.DataFrame(all_rows)
        logger.info(f"Calculated {len(all_rows)} total rows across {chunk_num} chunks")

        # Export
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_file = f"{DATA_DIR}/agent8_professionals_{timestamp}.xlsx"
        df.to_excel(excel_file, index=False)
        logger.info(f"Exported to {excel_file}")

        # Keep latest
        latest_file = f"{DATA_DIR}/agent8_professionals_latest.xlsx"
        df.to_excel(latest_file, index=False)
        logger.info(f"Updated {latest_file}")

        return {"status": "success", "file": excel_file, "rows": len(df)}

    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    result = export_agent8_direct()
    print(result)
