#!/usr/bin/env python3
import psycopg2
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NEON_URL = "postgresql://neondb_owner:npg_RnjMpJ4DsKY7@ep-icy-tree-af8719ti-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

conn = psycopg2.connect(NEON_URL)
cursor = conn.cursor()

# Check all data
cursor.execute("SELECT COUNT(*) FROM professional_metrics")
total = cursor.fetchone()[0]
print(f"Total rows: {total}")

# Check by date range
cursor.execute("""
    SELECT start_date, end_date, COUNT(*) as cnt
    FROM professional_metrics
    GROUP BY start_date, end_date
    ORDER BY start_date DESC
""")
print("\nBy date range:")
for start, end, cnt in cursor.fetchall():
    print(f"  {start} to {end}: {cnt} rows")

# Show sample
cursor.execute("""
    SELECT provider_name, cohort, start_date, end_date, utilization_pct, qa_score
    FROM professional_metrics
    LIMIT 3
""")
print("\nSample data:")
for row in cursor.fetchall():
    print(f"  {row}")

# Check what the API queries
print("\n--- API Query Check ---")
start_date = "2026-07-15"
end_date = "2026-08-06"
print(f"API queries: start_date={start_date}, end_date={end_date}")

cursor.execute("""
    SELECT COUNT(*) FROM professional_metrics
    WHERE start_date >= %s AND end_date <= %s
""", (start_date, end_date))
api_rows = cursor.fetchone()[0]
print(f"Rows matching API query: {api_rows}")

conn.close()
