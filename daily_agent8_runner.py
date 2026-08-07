#!/usr/bin/env python3
"""
Daily Agent 8 Runner
1. Export metrics to Excel (query Trino locally)
2. Sync Excel to Neon (production database)
Runs daily at 6 AM via Task Scheduler
"""
import subprocess
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_daily_agent8():
    """Execute daily Agent 8 pipeline"""

    logger.info("=" * 50)
    logger.info(f"DAILY AGENT 8 RUNNER - {datetime.now()}")
    logger.info("=" * 50)

    # Step 1: Export to Excel
    logger.info("\n[1/2] Exporting metrics to Excel...")
    try:
        result = subprocess.run(
            ["python", "agent8_export_to_excel.py"],
            capture_output=True,
            text=True,
            timeout=600
        )
        logger.info(f"Export output: {result.stdout}")
        if result.returncode != 0:
            logger.error(f"Export failed: {result.stderr}")
            return {"status": "error", "step": "export", "message": result.stderr}
    except Exception as e:
        logger.error(f"Export exception: {str(e)}")
        return {"status": "error", "step": "export", "message": str(e)}

    # Step 2: Sync to Neon
    logger.info("\n[2/2] Syncing Excel to Neon...")
    try:
        result = subprocess.run(
            ["python", "sync_excel_to_neon.py"],
            capture_output=True,
            text=True,
            timeout=300
        )
        logger.info(f"Sync output: {result.stdout}")
        if result.returncode != 0:
            logger.error(f"Sync failed: {result.stderr}")
            return {"status": "error", "step": "sync", "message": result.stderr}
    except Exception as e:
        logger.error(f"Sync exception: {str(e)}")
        return {"status": "error", "step": "sync", "message": str(e)}

    logger.info("\n" + "=" * 50)
    logger.info("DAILY RUNNER COMPLETE")
    logger.info("=" * 50)

    return {"status": "success", "message": "Export and Sync completed"}

if __name__ == "__main__":
    result = run_daily_agent8()
    print(result)
