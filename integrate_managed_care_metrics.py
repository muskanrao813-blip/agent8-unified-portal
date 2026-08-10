#!/usr/bin/env python3
"""Integrate Managed Care program metrics into Agent 8 dashboard"""
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

print("=" * 70)
print("MANAGED CARE METRICS INTEGRATION")
print("=" * 70)

try:
    # Connect to shared Neon PostgreSQL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("[ERROR] DATABASE_URL not set")
        exit(1)

    conn = psycopg.connect(db_url, connect_timeout=10)
    cursor = conn.cursor()

    print("\n[1] Checking available schemas...")
    cursor.execute("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'pg_temp_1')
        ORDER BY schema_name
    """)
    schemas = [row[0] for row in cursor.fetchall()]
    print(f"Available schemas: {schemas}")

    # Check for managed_care schema
    if 'managed_care' in schemas:
        print("[OK] managed_care schema found")

        # List tables in managed_care schema
        print("\n[2] Tables in managed_care schema:")
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'managed_care'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        for table in tables:
            print(f"  - {table}")

        # Try to query key metrics
        print("\n[3] Querying MC program metrics...")

        # Query enrolled patients
        try:
            cursor.execute("SELECT COUNT(*) as total FROM managed_care.vytal_enrolments")
            enrolled = cursor.fetchone()[0]
            print(f"  Total Enrolled (VYTAL): {enrolled:,}")
        except:
            print("  Could not query vytal_enrolments")

        # Query HRA completions
        try:
            cursor.execute("SELECT COUNT(*) as total FROM managed_care.hra_submissions")
            hra_total = cursor.fetchone()[0]
            print(f"  HRA Submissions: {hra_total:,}")
        except:
            print("  Could not query hra_submissions")

        # Query biomarker data
        try:
            cursor.execute("SELECT COUNT(*) as total FROM managed_care.lab_results")
            lab_total = cursor.fetchone()[0]
            print(f"  Lab Results (Biomarker): {lab_total:,}")
        except:
            print("  Could not query lab_results")

        # Query appointments by program
        try:
            cursor.execute("""
                SELECT
                    program_name,
                    COUNT(*) as appointment_count
                FROM managed_care.appointments
                GROUP BY program_name
                ORDER BY appointment_count DESC
            """)
            programs = cursor.fetchall()
            print(f"\n  Appointments by Program:")
            for prog, count in programs:
                print(f"    {prog}: {count:,}")
        except:
            print("  Could not query appointments")

    else:
        print("[WARNING] managed_care schema not found")
        print("  Available schemas:", schemas)

    cursor.close()
    conn.close()

except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
