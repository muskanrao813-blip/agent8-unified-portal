#!/usr/bin/env python3
"""Comprehensive dashboard test with all data"""
import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:5001'
DATE_RANGE = {
    'start_date': '2026-01-01',
    'end_date': '2026-08-10'
}

print("\n" + "=" * 80)
print("COMPREHENSIVE DASHBOARD DATA ACCURACY TEST")
print("=" * 80)
print(f"Date Range: {DATE_RANGE['start_date']} to {DATE_RANGE['end_date']}\n")

# Test Overview
print("[1/3] OVERVIEW TAB")
print("-" * 80)
try:
    resp = requests.get(f"{BASE_URL}/api/agent8/dashboard", params=DATE_RANGE)
    if resp.status_code == 200:
        data = resp.json()
        for kpi in data.get('kpis', []):
            print(f"  {kpi['label']:<30} {kpi['value']:>15}")
        print(f"  Program Breakdown:          {len(data.get('program_breakdown', []))} programs")
    else:
        print(f"  ERROR {resp.status_code}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test Health Outcomes
print("\n[2/3] HEALTH OUTCOMES")
print("-" * 80)
try:
    resp = requests.get(f"{BASE_URL}/api/agent8/health-outcomes", params=DATE_RANGE)
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Status: {data.get('status', 'unknown')}")
        print(f"  Data rows: {len(data.get('data', []))}")
        for kpi in data.get('kpis', []):
            print(f"  {kpi['label']:<30} {kpi['value']:>15}")
    else:
        print(f"  ERROR {resp.status_code}: {resp.text[:100]}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test Clinical Outcomes
print("\n[3/3] CLINICAL OUTCOMES")
print("-" * 80)
try:
    resp = requests.get(f"{BASE_URL}/api/agent8/clinical-outcomes", params=DATE_RANGE)
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Status: {data.get('status', 'unknown')}")
        print(f"  Data rows: {len(data.get('data', []))}")
        for kpi in data.get('kpis', []):
            print(f"  {kpi['label']:<30} {kpi['value']:>15}")
    else:
        print(f"  ERROR {resp.status_code}")
except Exception as e:
    print(f"  ERROR: {e}")

# Database status
print("\n" + "=" * 80)
print("DATABASE BACKFILL STATUS")
print("=" * 80)

try:
    from dotenv import load_dotenv
    import os
    import psycopg

    load_dotenv()
    conn = psycopg.connect(os.getenv('DATABASE_URL'), connect_timeout=10)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM professional_daily_metrics WHERE metric_date >= '2026-01-01' AND metric_date <= '2026-08-10'")
    total_records = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT provider_name) FROM professional_daily_metrics WHERE metric_date >= '2026-01-01' AND metric_date <= '2026-08-10'")
    providers = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(appts_count) FROM professional_daily_metrics WHERE metric_date >= '2026-01-01' AND metric_date <= '2026-08-10'")
    total_appts = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    print(f"  Database Records: {total_records:,}")
    print(f"  Providers: {providers}/26")
    print(f"  Total Appointments: {total_appts:,} / 132,912 expected")
    print(f"  Backfill Progress: {(total_appts/132912)*100:.1f}%")

except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 80)
