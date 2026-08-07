#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import psycopg2
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NEON_URL = "postgresql://neondb_owner:npg_RnjMpJ4DsKY7@ep-icy-tree-af8719ti-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

try:
    conn = psycopg2.connect(NEON_URL)
    cursor = conn.cursor()

    # Create professional_metrics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professional_metrics (
            provider_name VARCHAR(255) NOT NULL,
            cohort VARCHAR(100),
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            appts_count INTEGER DEFAULT 0,
            capacity INTEGER DEFAULT 0,
            utilization_pct FLOAT DEFAULT 0,
            qa_score FLOAT DEFAULT 0,
            improvement_score FLOAT DEFAULT 0,
            improvement_total INTEGER DEFAULT 0,
            status VARCHAR(50),
            forecast_7d INTEGER DEFAULT 0,
            patient_count INTEGER DEFAULT 0,
            with_lab_data INTEGER DEFAULT 0,
            without_lab_data INTEGER DEFAULT 0,
            PRIMARY KEY (provider_name, start_date, end_date)
        )
    """)

    print("✓ professional_metrics table created")

    # Create other required tables if missing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professional_metrics_log (
            id SERIAL PRIMARY KEY,
            provider_name VARCHAR(255),
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    print("✓ professional_metrics_log table created")

    conn.commit()
    cursor.close()
    conn.close()

    print("\n✓ Schema initialization complete!")

except Exception as e:
    print(f"ERROR: {e}")
