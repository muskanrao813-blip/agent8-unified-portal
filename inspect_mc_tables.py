#!/usr/bin/env python3
"""Inspect Managed Care table schemas"""
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

db_url = os.getenv('DATABASE_URL')
conn = psycopg.connect(db_url, connect_timeout=10)
cursor = conn.cursor()

tables_to_inspect = [
    'program_allocation_2026',
    'hra_stats',
    'camp_phrs',
    'vytal_appt_flat',
    'impact_scores_2026',
    'vytal_appointments'
]

for table in tables_to_inspect:
    print(f"\n{'='*70}")
    print(f"TABLE: {table}")
    print(f"{'='*70}")

    try:
        cursor.execute(f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'managed_care' AND table_name = '{table}'
            ORDER BY ordinal_position
        """)
        cols = cursor.fetchall()

        if cols:
            print(f"Columns ({len(cols)}):")
            for col_name, col_type in cols:
                print(f"  {col_name:<30} {col_type}")

            # Try to peek at data
            cursor.execute(f"SELECT * FROM managed_care.{table} LIMIT 1")
            print(f"\nSample row: {cursor.fetchone()}")
        else:
            print("No columns found")
    except Exception as e:
        print(f"Error: {e}")

cursor.close()
conn.close()
