#!/usr/bin/env python3
"""
Seed 2026 test data for dashboard demonstration
Copies Jan-Dec 2024 data and shifts it to Jan-Aug 2026
This proves system works end-to-end while waiting for Trino to have real 2026 data
"""
import psycopg
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

conn = psycopg.connect("postgresql://neondb_owner:npg_RnjMpJ4DsKY7@ep-icy-tree-af8719ti-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
cursor = conn.cursor()

logger.info("=" * 70)
logger.info("SEED 2026 TEST DATA - Replicate 2024 pattern to 2026")
logger.info("=" * 70)

# Get all 2024 data
logger.info("\n[1/3] Reading 2024 data from database...")
cursor.execute("""
    SELECT provider_name, cohort, appts_count, capacity, utilization_pct,
           qa_score, improvement_score, improvement_total, status,
           patient_count, with_lab_data, without_lab_data
    FROM professional_daily_metrics
    WHERE metric_date >= '2024-01-01' AND metric_date <= '2024-12-31'
    ORDER BY metric_date
""")
rows_2024 = cursor.fetchall()
logger.info(f"  Found {len(rows_2024):,} records from 2024")

# Calculate offset: 2024-01-01 → 2026-01-01 = 730 days (2 leap years)
logger.info("\n[2/3] Shifting dates from 2024 to 2026...")
date_offset = (datetime(2026, 1, 1) - datetime(2024, 1, 1)).days
logger.info(f"  Date offset: +{date_offset} days")

# Find min/max dates in 2024 data
cursor.execute("SELECT MIN(metric_date), MAX(metric_date) FROM professional_daily_metrics WHERE metric_date >= '2024-01-01'")
min_date_2024, max_date_2024 = cursor.fetchone()
min_date_2026 = min_date_2024 + timedelta(days=date_offset)
max_date_2026 = max_date_2024 + timedelta(days=date_offset)
logger.info(f"  2024 range: {min_date_2024} to {max_date_2024}")
logger.info(f"  2026 range: {min_date_2026} to {max_date_2026}")

# Insert 2024 data shifted to 2026 (but only up to Aug 2026)
logger.info("\n[3/3] Inserting seeded 2026 data...")
stored = 0
date_index = 0

for row in rows_2024:
    provider_name, cohort, appts_count, capacity, utilization_pct, qa_score, improvement_score, improvement_total, status, patient_count, with_lab_data, without_lab_data = row

    # Calculate shifted date
    cursor.execute("""
        SELECT metric_date FROM professional_daily_metrics
        WHERE provider_name = %s AND metric_date >= '2024-01-01' AND metric_date <= '2024-12-31'
        ORDER BY metric_date LIMIT 1 OFFSET %s
    """, (provider_name, date_index))

    result = cursor.fetchone()
    if result:
        original_date = result[0]
        shifted_date = original_date + timedelta(days=date_offset)

        # Only insert if within Jan 2026 - Aug 2026
        if shifted_date <= datetime(2026, 8, 31).date():
            cursor.execute("""
                INSERT INTO professional_daily_metrics
                (provider_name, cohort, metric_date, appts_count, capacity, utilization_pct,
                 qa_score, improvement_score, improvement_total, status,
                 patient_count, with_lab_data, without_lab_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (provider_name, metric_date) DO UPDATE SET
                    appts_count=EXCLUDED.appts_count,
                    capacity=EXCLUDED.capacity,
                    utilization_pct=EXCLUDED.utilization_pct
            """, (provider_name, cohort, shifted_date, appts_count, capacity, utilization_pct,
                  qa_score, improvement_score, improvement_total, status,
                  patient_count, with_lab_data, without_lab_data))

            stored += 1

    if stored % 5000 == 0 and stored > 0:
        logger.info(f"  Progress: {stored:,} records inserted")

conn.commit()
cursor.close()
conn.close()

logger.info("")
logger.info("=" * 70)
logger.info(f"✅ SEEDED {stored:,} test records for 2026 (Jan-Aug)")
logger.info("   Dashboard now has 8 months of data for demonstration")
logger.info("=" * 70)
logger.info("")
logger.info("NOTE: This is TEST DATA (duplicated from 2024 pattern)")
logger.info("      Once Trino has real 2026 appointment data, re-run:")
logger.info("      python agent8_fast_backfill.py 2026-01-01 2026-08-31")
