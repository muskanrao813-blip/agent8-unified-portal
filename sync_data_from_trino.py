#!/usr/bin/env python3
"""
Local Data Sync Script
Runs on your machine with Trino OAuth access
Fetches data from Trino → Stores in PostgreSQL (Neon)
Render backend reads from PostgreSQL (no Trino access needed)
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
from trino.auth import BasicAuthentication
import trino

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Trino Config (runs locally with your OAuth)
TRINO_HOST = os.getenv('TRINO_HOST', 'trino-prod.healthrx.co.in')
TRINO_PORT = int(os.getenv('TRINO_PORT', 443))
TRINO_USER = os.getenv('TRINO_USER')
TRINO_PASSWORD = os.getenv('TRINO_PASSWORD')
TRINO_CATALOG = 'deltalake'

# PostgreSQL Config (Neon - same DB that Render reads from)
DATABASE_URL = os.getenv('DATABASE_URL')

# MC Dietician List
MC_DIETICIANS = [
    'Prachi More', 'Ambika Rode', 'Geeta Maggu', 'Gitanjali Malik sachdeva', 'Chandni Sharma', 'Tejashree Thorat',
    'Chaithra B', 'Shefali Dindorkar',
    'Sweta Naik', 'Divya Pandey', 'Trupti Nakar', 'Mekala Reddy',
    'Bhoomika Gur', 'Harpreet Kaur', 'Priya Sharma', 'Ritika Patel', 'Sneha Gupta', 'Tanya Malhotra',
    'Ushma Patel', 'Vedavati Kapoor', 'Vibha Sharma', 'Vrinda Nair', 'Yamini Desai', 'Zara Khan', 'Dr Ajit Sharma'
]

def connect_trino():
    """Connect to Trino with OAuth credentials"""
    try:
        conn = trino.dbapi.connect(
            host=TRINO_HOST,
            port=TRINO_PORT,
            user=TRINO_USER,
            auth=BasicAuthentication(TRINO_USER, TRINO_PASSWORD),
            catalog=TRINO_CATALOG,
            schema='healthrx',
        )
        logger.info("✅ Connected to Trino")
        return conn
    except Exception as e:
        logger.error(f"❌ Trino connection failed: {e}")
        raise

def connect_postgres():
    """Connect to PostgreSQL (Neon)"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("✅ Connected to PostgreSQL")
        return conn
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        raise

def init_db(pg_conn):
    """Create tables if they don't exist"""
    cursor = pg_conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id SERIAL PRIMARY KEY,
                appointment_id VARCHAR(100) UNIQUE,
                dietician_name VARCHAR(255),
                patient_id VARCHAR(100),
                patient_name VARCHAR(255),
                appointment_date DATE,
                status VARCHAR(50),
                duration_minutes INT,
                notes TEXT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provider_metrics (
                id SERIAL PRIMARY KEY,
                dietician_name VARCHAR(255) UNIQUE,
                total_appointments INT,
                completed_appointments INT,
                avg_duration INT,
                quality_score FLOAT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        pg_conn.commit()
        logger.info("✅ Database tables initialized")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")
        pg_conn.rollback()
        raise
    finally:
        cursor.close()

def fetch_appointments(trino_conn):
    """Fetch appointments data from Trino"""
    cursor = trino_conn.cursor()
    try:
        query = """
            SELECT
                appointment_id,
                assigned_provider_name as dietician_name,
                patient_id,
                patient_name,
                appointment_date,
                appointment_status as status,
                duration as duration_minutes
            FROM f_appointmentflattable
            WHERE assigned_provider_name IN ({})
            AND appointment_date >= DATE_FORMAT(CURRENT_DATE - INTERVAL '90' DAY, '%Y-%m-%d')
            LIMIT 10000
        """.format(','.join(f"'{d}'" for d in MC_DIETICIANS))

        cursor.execute(query)
        rows = cursor.fetchall()
        logger.info(f"✅ Fetched {len(rows)} appointments from Trino")
        return rows
    except Exception as e:
        logger.error(f"❌ Failed to fetch appointments: {e}")
        return []

def sync_appointments(pg_conn, appointments):
    """Sync appointments to PostgreSQL"""
    if not appointments:
        logger.warning("⚠️ No appointments to sync")
        return

    cursor = pg_conn.cursor()
    try:
        values = [
            (
                row[0],  # appointment_id
                row[1],  # dietician_name
                row[2],  # patient_id
                row[3],  # patient_name
                row[4],  # appointment_date
                row[5],  # status
                row[6],  # duration_minutes
                None,    # notes
            )
            for row in appointments
        ]

        execute_values(
            cursor,
            """
            INSERT INTO appointments
            (appointment_id, dietician_name, patient_id, patient_name, appointment_date, status, duration_minutes, notes)
            VALUES %s
            ON CONFLICT (appointment_id) DO UPDATE SET
                status = EXCLUDED.status,
                duration_minutes = EXCLUDED.duration_minutes,
                synced_at = CURRENT_TIMESTAMP
            """,
            values,
            page_size=100
        )
        pg_conn.commit()
        logger.info(f"✅ Synced {len(appointments)} appointments to PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Failed to sync appointments: {e}")
        pg_conn.rollback()
    finally:
        cursor.close()

def fetch_provider_metrics(trino_conn):
    """Fetch provider metrics from Trino"""
    cursor = trino_conn.cursor()
    try:
        query = """
            SELECT
                assigned_provider_name as dietician_name,
                COUNT(*) as total_appointments,
                SUM(CASE WHEN appointment_status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
                AVG(CAST(duration as INT)) as avg_duration
            FROM f_appointmentflattable
            WHERE assigned_provider_name IN ({})
            GROUP BY assigned_provider_name
        """.format(','.join(f"'{d}'" for d in MC_DIETICIANS))

        cursor.execute(query)
        rows = cursor.fetchall()
        logger.info(f"✅ Fetched metrics for {len(rows)} providers from Trino")
        return rows
    except Exception as e:
        logger.error(f"❌ Failed to fetch metrics: {e}")
        return []

def sync_provider_metrics(pg_conn, metrics):
    """Sync provider metrics to PostgreSQL"""
    if not metrics:
        logger.warning("⚠️ No metrics to sync")
        return

    cursor = pg_conn.cursor()
    try:
        values = [
            (
                row[0],  # dietician_name
                row[1],  # total_appointments
                row[2],  # completed_appointments
                row[3] if row[3] else 0,  # avg_duration
                0.0,     # quality_score (will be updated by QA system)
            )
            for row in metrics
        ]

        execute_values(
            cursor,
            """
            INSERT INTO provider_metrics
            (dietician_name, total_appointments, completed_appointments, avg_duration, quality_score)
            VALUES %s
            ON CONFLICT (dietician_name) DO UPDATE SET
                total_appointments = EXCLUDED.total_appointments,
                completed_appointments = EXCLUDED.completed_appointments,
                avg_duration = EXCLUDED.avg_duration,
                synced_at = CURRENT_TIMESTAMP
            """,
            values,
            page_size=100
        )
        pg_conn.commit()
        logger.info(f"✅ Synced {len(metrics)} provider metrics to PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Failed to sync metrics: {e}")
        pg_conn.rollback()
    finally:
        cursor.close()

def main():
    """Main sync flow"""
    logger.info("🚀 Starting data sync from Trino to PostgreSQL...")

    # Validate config
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL not set in .env")
        sys.exit(1)

    if not TRINO_USER or not TRINO_PASSWORD:
        logger.error("❌ TRINO_USER or TRINO_PASSWORD not set in .env")
        sys.exit(1)

    try:
        # Connect to both databases
        trino_conn = connect_trino()
        pg_conn = connect_postgres()

        # Initialize database
        init_db(pg_conn)

        # Fetch and sync appointments
        appointments = fetch_appointments(trino_conn)
        sync_appointments(pg_conn, appointments)

        # Fetch and sync provider metrics
        metrics = fetch_provider_metrics(trino_conn)
        sync_provider_metrics(pg_conn, metrics)

        logger.info("✅ Data sync completed successfully!")

    except Exception as e:
        logger.error(f"❌ Sync failed: {e}")
        sys.exit(1)
    finally:
        if 'trino_conn' in locals():
            trino_conn.close()
        if 'pg_conn' in locals():
            pg_conn.close()

if __name__ == '__main__':
    main()
