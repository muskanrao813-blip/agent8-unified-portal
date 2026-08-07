#!/usr/bin/env python3
"""
Sync Agent 8 Excel Data to Neon PostgreSQL
Reads latest Excel file and pushes to Neon
"""
import pandas as pd
import psycopg2
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NEON_URL = "postgresql://neondb_owner:npg_RnjMpJ4DsKY7@ep-icy-tree-af8719ti-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
DATA_DIR = "data"
LATEST_FILE = f"{DATA_DIR}/agent8_professionals_latest.xlsx"

def sync_to_neon():
    """Read Excel and sync to Neon"""

    logger.info("===== SYNC AGENT 8 DATA TO NEON =====")

    # Check if file exists
    if not os.path.exists(LATEST_FILE):
        logger.error(f"File not found: {LATEST_FILE}")
        return {"status": "error", "message": "Excel file not found"}

    try:
        # Read Excel
        logger.info(f"Reading {LATEST_FILE}...")
        df = pd.read_excel(LATEST_FILE)
        logger.info(f"Read {len(df)} rows")

        # Connect to Neon
        logger.info("Connecting to Neon PostgreSQL...")
        conn = psycopg2.connect(NEON_URL)
        cursor = conn.cursor()

        # Insert data
        inserted = 0
        for idx, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO professional_metrics
                    (provider_name, cohort, start_date, end_date, appts_count, capacity,
                     utilization_pct, qa_score, improvement_score, improvement_total,
                     status, forecast_7d, patient_count, with_lab_data, without_lab_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (provider_name, start_date, end_date) DO UPDATE SET
                        appts_count=EXCLUDED.appts_count,
                        utilization_pct=EXCLUDED.utilization_pct,
                        qa_score=EXCLUDED.qa_score,
                        improvement_score=EXCLUDED.improvement_score,
                        status=EXCLUDED.status,
                        forecast_7d=EXCLUDED.forecast_7d
                """, (
                    row.get('provider_name'),
                    row.get('cohort'),
                    pd.to_datetime(row.get('start_date')).date() if pd.notna(row.get('start_date')) else None,
                    pd.to_datetime(row.get('end_date')).date() if pd.notna(row.get('end_date')) else None,
                    int(row.get('appts_count', 0)),
                    int(row.get('capacity', 0)),
                    float(row.get('utilization_pct', 0)),
                    float(row.get('qa_score', 0)),
                    float(row.get('improvement_score', 0)),
                    int(row.get('improvement_total', 0)),
                    row.get('status'),
                    int(row.get('forecast_7d', 0)),
                    int(row.get('patient_count', 0)) if pd.notna(row.get('patient_count')) else 0,
                    int(row.get('with_lab_data', 0)) if pd.notna(row.get('with_lab_data')) else 0,
                    int(row.get('without_lab_data', 0)) if pd.notna(row.get('without_lab_data')) else 0
                ))
                inserted += 1
            except Exception as e:
                logger.warning(f"Row {idx}: {str(e)}")
                continue

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"Synced {inserted} rows to Neon")
        return {"status": "success", "synced": inserted}

    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    result = sync_to_neon()
    print(result)
