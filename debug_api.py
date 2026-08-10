import psycopg

conn = psycopg.connect("postgresql://neondb_owner:npg_RnjMpJ4DsKY7@ep-icy-tree-af8719ti-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
cursor = conn.cursor()

# What SHOULD the API return
cursor.execute("""
    SELECT
        SUM(appts_count) as total_appts
    FROM professional_daily_metrics
    WHERE metric_date BETWEEN '2026-08-01' AND '2026-08-10'
""")
result1 = cursor.fetchone()

cursor.execute("""
    SELECT
        SUM(appts_count) as total_appts
    FROM professional_daily_metrics
    WHERE metric_date BETWEEN '2026-08-08' AND '2026-08-10'
""")
result2 = cursor.fetchone()

print("Database Direct Query Results:")
print(f"  10-day range (08-01 to 08-10): {result1[0]:,} appts")
print(f"  3-day range (08-08 to 08-10):  {result2[0]:,} appts")
print(f"  Different: {'YES - Correct!' if result1[0] != result2[0] else 'NO - Problem!'}")

# Check how many days we have data for
cursor.execute("""
    SELECT COUNT(DISTINCT metric_date) as date_count,
           MIN(metric_date) as min_date,
           MAX(metric_date) as max_date
    FROM professional_daily_metrics
""")
dates = cursor.fetchone()
print(f"\nData Coverage:")
print(f"  Unique dates: {dates[0]}")
print(f"  Min date: {dates[1]}")
print(f"  Max date: {dates[2]}")

conn.close()
