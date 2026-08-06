#!/usr/bin/env python3
"""
Daily Runner for Agent 8 Portal
Runs daily at 6 AM to fetch latest data and update Neon
"""
import sys
from datetime import datetime, timedelta
from app import calculate_and_store_metrics
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def daily_update_agent8():
    """Update Agent 8 data for the past 23 days (rolling window)"""

    end_date = datetime.now()
    start_date = end_date - timedelta(days=23)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    logger.info(f"===== DAILY UPDATE AGENT 8 DATA =====")
    logger.info(f"Updating metrics for: {start_str} to {end_str}")

    try:
        result = calculate_and_store_metrics(start_str, end_str)
        logger.info(f"✓ Update complete: {result}")
        logger.info(f"Data updated in Neon PostgreSQL")
        return {"status": "success", "message": "Agent 8 data updated"}
    except Exception as e:
        logger.error(f"✗ Update failed: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    result = daily_update_agent8()
    print(result)
