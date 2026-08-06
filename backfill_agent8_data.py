#!/usr/bin/env python3
"""
Backfill Agent 8 Portal Data from 2024-01-01 to present
Queries Trino for all historical data and stores in Neon PostgreSQL
"""
import sys
from datetime import datetime, timedelta
from app import calculate_and_store_metrics
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backfill_agent8_data():
    """Backfill all Agent 8 metrics from 2024 to present"""

    # Date range
    start_date = datetime(2024, 1, 1)
    end_date = datetime.now()

    logger.info(f"===== BACKFILL AGENT 8 DATA =====")
    logger.info(f"Range: {start_date.date()} to {end_date.date()}")
    logger.info(f"Total days: {(end_date - start_date).days}")

    # Process in 30-day chunks to avoid timeout
    chunk_size = 30
    current_date = start_date
    chunk_count = 0

    while current_date < end_date:
        chunk_end = min(current_date + timedelta(days=chunk_size), end_date)
        chunk_count += 1

        start_str = current_date.strftime('%Y-%m-%d')
        end_str = chunk_end.strftime('%Y-%m-%d')

        logger.info(f"\n[CHUNK {chunk_count}] Processing {start_str} to {end_str}")

        try:
            result = calculate_and_store_metrics(start_str, end_str)
            logger.info(f"✓ Chunk {chunk_count} complete: {result}")
        except Exception as e:
            logger.error(f"✗ Chunk {chunk_count} failed: {str(e)}")
            # Continue with next chunk

        current_date = chunk_end + timedelta(days=1)

    logger.info(f"\n===== BACKFILL COMPLETE =====")
    logger.info(f"Processed {chunk_count} chunks")
    logger.info(f"Data now available in Neon PostgreSQL")

if __name__ == "__main__":
    backfill_agent8_data()
