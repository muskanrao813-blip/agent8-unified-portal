#!/usr/bin/env python3
"""
Agent 8 Data Export Script
Queries Trino locally, calculates metrics, exports to Excel
Similar to Managed Care dashboard approach
"""
import pandas as pd
from datetime import datetime, timedelta
from app import calculate_and_store_metrics, query_professional_metrics
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create data folder if not exists
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    logger.info(f"Created {DATA_DIR} folder")

def export_agent8_data():
    """Export Agent 8 metrics to Excel files (23-day rolling window)"""

    end_date = datetime.now()
    start_date = end_date - timedelta(days=23)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    logger.info(f"===== EXPORT AGENT 8 DATA TO EXCEL =====")
    logger.info(f"Date range: {start_str} to {end_str}")

    try:
        # Calculate metrics
        logger.info("Calculating metrics from Trino...")
        result = calculate_and_store_metrics(start_str, end_str)
        logger.info(f"Calculation result: {result}")

        # Query professional metrics
        logger.info("Fetching professional metrics...")
        rows = query_professional_metrics(start_str, end_str)

        if not rows:
            logger.warning("No data returned")
            return {"status": "error", "message": "No data"}

        # Convert to DataFrame
        df = pd.DataFrame(rows)

        # Export to Excel
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_file = f"{DATA_DIR}/agent8_professionals_{timestamp}.xlsx"

        df.to_excel(excel_file, index=False)
        logger.info(f"Exported {len(df)} rows to {excel_file}")

        # Also keep latest copy for sync
        latest_file = f"{DATA_DIR}/agent8_professionals_latest.xlsx"
        df.to_excel(latest_file, index=False)
        logger.info(f"Updated {latest_file}")

        return {
            "status": "success",
            "file": excel_file,
            "latest": latest_file,
            "rows": len(df)
        }

    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    result = export_agent8_data()
    print(result)
