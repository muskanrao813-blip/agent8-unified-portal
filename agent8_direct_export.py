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

def export_agent8_direct():
    """Export Agent 8 metrics directly from Trino to Excel"""

    end_date = datetime.now()
    start_date = end_date - timedelta(days=23)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    logger.info(f"===== DIRECT EXPORT AGENT 8 TO EXCEL =====")
    logger.info(f"Date range: {start_str} to {end_str}")
    logger.info(f"Professionals: {len(MC_DIETICIANS)}")

    try:
        # Get working days
        d_inhouse = count_working_days_inhouse(start_str, end_str)
        d_contractual = count_working_days_contractual(start_str, end_str)
        logger.info(f"Working days: inhouse={d_inhouse}, contractual={d_contractual}")

        # Get QA scores
        qa_scores = get_qa_scores()
        logger.info(f"QA scores loaded: {len(qa_scores)} providers")

        # Query improvements from Agent 8
        improvements = {}
        try:
            resp = requests.get(
                f'http://localhost:5001/api/agent8/dietician-improvement?start_date={start_str}&end_date={end_str}',
                timeout=10
            )
            if resp.status_code == 200:
                for item in resp.json().get('data', []):
                    improvements[item.get('dietician')] = {
                        'score': item.get('improvement_score', 0),
                        'improved': item.get('patients_improved', 0),
                        'total': item.get('patients_total', 0)
                    }
                logger.info(f"Improvements loaded: {len(improvements)}")
        except Exception as e:
            logger.warning(f"Couldn't load improvements: {e}")

        # Calculate for each MC dietician
        rows = []
        for provider_name in MC_DIETICIANS:
            cohort = get_cohort_for_provider(provider_name)

            # Query appointments from Trino
            q_appts = f"""SELECT COUNT(*) as appt_count
                         FROM deltalake.dl_standard_pbireporting.f_appointmentflattable
                         WHERE doctorname = '{provider_name}'
                         AND appointmentstatus IN ('COM', 'BOOKED')
                         AND CAST(appointmentdate AS DATE) >= DATE('{start_str}')
                         AND CAST(appointmentdate AS DATE) <= DATE('{end_str}')
                        """
            r_appts = execute_trino_query(q_appts)
            appts = r_appts[0]['appt_count'] if r_appts else 0

            # Calculate capacity
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
                'start_date': start_str,
                'end_date': end_str,
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

        df = pd.DataFrame(rows)
        logger.info(f"Calculated {len(df)} professionals")

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
