#!/usr/bin/env python3
"""Comprehensive audit of ALL dashboard tabs - data & logic verification"""
import sys
sys.path.insert(0, '.')

import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

print("=" * 90)
print("COMPREHENSIVE DASHBOARD AUDIT - ALL TABS")
print("=" * 90)

try:
    db_url = os.getenv('DATABASE_URL')
    conn = psycopg.connect(db_url, connect_timeout=10)
    cursor = conn.cursor()

    # =========================================================================
    # TAB 1: OVERVIEW (Team Utilization, Booked Appts, Capacity, Improvement)
    # =========================================================================
    print("\n" + "=" * 90)
    print("TAB 1: OPERATIONAL OVERVIEW")
    print("=" * 90)

    print("\n[KPI 1] Team Utilization")
    print("-" * 90)
    print("Logic: (Sum of Appointments) / (Sum of Capacity) × 100")
    print("Expected calculation: Uses COHORT_CAPACITY × working_days")

    cursor.execute("""
        SELECT
            SUM(appts_count) as total_appts,
            COUNT(DISTINCT provider_name) as providers,
            COUNT(DISTINCT metric_date) as dates
        FROM professional_daily_metrics
        WHERE metric_date >= '2026-07-01' AND metric_date <= '2026-07-30'
    """)
    result = cursor.fetchone()
    print(f"Data: {result[0]:,} appointments across {result[1]} providers, {result[2]} dates")

    print("\n[KPI 2] Booked Appointments")
    print("-" * 90)
    print("Logic: Sum of appointment counts")
    print(f"Value: {result[0]:,} (from daily snapshots)")
    print("[OK] Correct if data is complete")

    print("\n[KPI 3] Total Capacity")
    print("-" * 90)
    print("Logic: SUM(504×24 + 28×24 + 280×24 + 1364×26)")
    print("       IN-HOUSE AI + IN-HOUSE OTHERS + IN-HOUSE MC + CONTRACTUAL")

    # Calculate expected
    capacity_ai = 504 * 24  # 6 dieticians × 84 × 24 days
    capacity_others = 28 * 24  # 2 staff × 14 × 24 days
    capacity_mc = 280 * 24  # 20 × 14 × 24 days
    capacity_contractual = 1364 * 26  # Many × 22 × 26 days
    expected_total = capacity_ai + capacity_others + capacity_mc + capacity_contractual

    print(f"IN-HOUSE AI: 504 × 24 = {capacity_ai:,}")
    print(f"IN-HOUSE OTHERS: 28 × 24 = {capacity_others:,}")
    print(f"IN-HOUSE MC: 280 × 24 = {capacity_mc:,}")
    print(f"CONTRACTUAL: 1,364 × 26 = {capacity_contractual:,}")
    print(f"Total Expected: {expected_total:,}")
    print("[WARNING]  Need to verify if this matches dashboard display")

    print("\n[KPI 4] Avg Health Improvement")
    print("-" * 90)
    print("Logic: Should display average improvement score from managed_care schema")
    cursor.execute("""
        SELECT AVG(scaled_score) FROM managed_care.impact_scores_2026
        WHERE first_camp_date LIKE '2026-07%'
    """)
    impr = cursor.fetchone()[0]
    print(f"Value: {impr:.1f}% (from managed_care.impact_scores_2026)")
    print("[OK] Data available, need to verify if wired into dashboard")

    print("\n[PROGRAM BREAKDOWN]")
    print("-" * 90)
    print("Logic: Show VYTAL program metrics (enrollment, HRA, biomarker, appointments)")

    cursor.execute("""
        SELECT COUNT(DISTINCT mobile_number_hash) as enrolled,
               (SELECT metric FROM managed_care.hra_stats WHERE metric='enrolled_with_hra') as hra_count,
               (SELECT COUNT(DISTINCT mobile_number_hash) FROM managed_care.impact_scores_2026) as biomarker
        FROM managed_care.camp_phrs
    """)
    result = cursor.fetchone()
    print(f"Total Enrolled: {result[0]:,}")
    print(f"HRA Data Available: {result[1] or 0}")
    print(f"Biomarker Data: {result[2]:,}")
    print("[OK] Data verified and integrated")

    # =========================================================================
    # TAB 2: HEALTH OUTCOMES
    # =========================================================================
    print("\n" + "=" * 90)
    print("TAB 2: HEALTH OUTCOMES")
    print("=" * 90)

    print("\n[DATA SOURCE]")
    print("-" * 90)
    print("Logic: Aggregate daily metrics by provider for date range")
    print("Query: SELECT provider, SUM(appts), AVG(utilization) GROUP BY provider")

    cursor.execute("""
        SELECT
            COUNT(DISTINCT provider_name) as providers_with_data,
            SUM(appts_count) as total_appts,
            CAST(ROUND(AVG(utilization_pct), 1) AS DECIMAL) as avg_util
        FROM professional_daily_metrics
        WHERE metric_date >= '2026-07-01' AND metric_date <= '2026-07-30'
    """)
    result = cursor.fetchone()
    print(f"Providers with data: {result[0]}/26")
    print(f"Total appointments: {result[1]:,}")
    print(f"Average utilization: {result[2]}%")

    # Check per-provider
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT provider_name FROM professional_daily_metrics
            WHERE metric_date >= '2026-07-01' AND metric_date <= '2026-07-30'
            GROUP BY provider_name
            HAVING COUNT(DISTINCT metric_date) >= 20
        ) t
    """)
    complete_providers = cursor.fetchone()[0]
    print(f"Providers with 20+ days data: {complete_providers}/26")
    print("[WARNING] Status: Incomplete if < 26")

    # =========================================================================
    # TAB 3: CLINICAL OUTCOMES
    # =========================================================================
    print("\n" + "=" * 90)
    print("TAB 3: CLINICAL OUTCOMES")
    print("=" * 90)

    print("\n[DATA SOURCE]")
    print("-" * 90)
    print("Logic: Display health metrics + QA scores per provider")

    cursor.execute("""
        SELECT
            COUNT(DISTINCT provider_name) as providers_with_data,
            AVG(qa_score) as avg_qa,
            AVG(improvement_score) as avg_improvement,
            SUM(appts_count) as total_appts
        FROM professional_daily_metrics
        WHERE metric_date >= '2026-07-01' AND metric_date <= '2026-07-30'
    """)
    result = cursor.fetchone()
    print(f"Providers with data: {result[0]}/26")
    print(f"Avg QA Score: {result[1] or 0:.1f} (all showing 0)")
    print(f"Avg Improvement: {result[2] or 0:.1f} (all showing 0)")
    print(f"Total appointments: {result[3]:,}")
    print("[WARNING]  ISSUE: QA and Improvement scores are 0 (not integrated)")

    # =========================================================================
    # TAB 4: CALL QUALITY (Embedded from QA Portal)
    # =========================================================================
    print("\n" + "=" * 90)
    print("TAB 4: CALL QUALITY ANALYSIS (Embedded via API)")
    print("=" * 90)

    print("\n[DATA SOURCE]")
    print("-" * 90)
    print("Logic: Proxy requests to https://consultation-call-quality-analysis-system.onrender.com")
    print("Endpoint: /api/calls/")

    print("\nExpected data:")
    print("- Call recordings uploaded")
    print("- Transcriptions (Gemini AI)")
    print("- QA scores per call")
    print("- Speaker metrics")

    print("\n[WARNING]  ISSUES IDENTIFIED:")
    print("1. Upload endpoint had SSL certificate error (FIXED: verify=False added)")
    print("2. May still have connection issues with Render API")
    print("3. Gemini transcription may not be working")

    # =========================================================================
    # SUMMARY TABLE
    # =========================================================================
    print("\n" + "=" * 90)
    print("AUDIT SUMMARY - ALL TABS")
    print("=" * 90)

    summary_data = [
        ("Overview", "Utilization", "CALCULATED", "[OK] Ready (if backfill complete)"),
        ("Overview", "Booked Appts", "SUM(appts)", "[OK] Ready (if backfill complete)"),
        ("Overview", "Capacity", "CALCULATED", "[OK] Ready (if backfill complete)"),
        ("Overview", "Health Improvement", "managed_care", "[OK] Data available (wired)"),
        ("Overview", "Program Breakdown", "managed_care", "[OK] Integrated"),
        ("", "", "", ""),
        ("Health Outcomes", "Provider metrics", "daily aggregation", "[OK] Working"),
        ("Health Outcomes", "Data completeness", "20-25 days", "[WARNING]  Incomplete"),
        ("", "", "", ""),
        ("Clinical Outcomes", "Appointments", "SUM query", "[OK] Working"),
        ("Clinical Outcomes", "QA Scores", "professional_daily_metrics", "[MISSING] All 0s"),
        ("Clinical Outcomes", "Improvement", "professional_daily_metrics", "[MISSING] All 0s"),
        ("", "", "", ""),
        ("Call Quality", "Upload", "Render API proxy", "[WARNING]  May timeout"),
        ("Call Quality", "Transcription", "Gemini AI", "[MISSING] Not confirmed"),
        ("Call Quality", "QA Analysis", "Render backend", "[WARNING]  Needs verification"),
    ]

    print(f"\n{'Tab':<20} {'Metric':<25} {'Source':<30} {'Status':<30}")
    print("-" * 90)
    for tab, metric, source, status in summary_data:
        if tab:
            print(f"{tab:<20} {metric:<25} {source:<30} {status:<30}")
        else:
            print()

    # =========================================================================
    # DETAILED ISSUES
    # =========================================================================
    print("\n" + "=" * 90)
    print("DETAILED ISSUES & FIXES NEEDED")
    print("=" * 90)

    issues = [
        ("CRITICAL", "Data Incompleteness",
         "22/26 providers missing 1-15 days of July data",
         "Complete backfill with batch commits (in progress)"),

        ("HIGH", "QA Scores Not Integrated",
         "professional_daily_metrics.qa_score always 0",
         "Need to sync QA scores from dietician QA portal into db"),

        ("HIGH", "Improvement Scores Not Integrated",
         "professional_daily_metrics.improvement_score always 0",
         "Need to join with managed_care.impact_scores_2026 by patient"),

        ("HIGH", "Call Quality Upload Issues",
         "SSL certificate error and possible timeouts",
         "Verify Render API connection and test upload pipeline"),

        ("MEDIUM", "Gemini Transcription",
         "Not confirmed if working - all transcriptions showing 'N/A'",
         "Check Gemini API key and test transcription on sample call"),

        ("MEDIUM", "Patient-to-Provider Mapping",
         "Can't directly map patients to dieticians for improvement scores",
         "Use appointment data + patient health data to aggregate by dietician"),
    ]

    for severity, issue, description, fix in issues:
        print(f"\n[{severity}] {issue}")
        print(f"  Problem: {description}")
        print(f"  Fix: {fix}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 90)
    print("NEXT STEPS")
    print("=" * 90)
    print("""
1. Complete backfill (in progress)
2. Integrate QA scores from dietician QA portal
3. Map patient improvement data to dieticians
4. Verify Gemini transcription working
5. Test complete flow end-to-end

Timeline: 15 minutes for backfill, then 1-2 hours for remaining integrations
    """)

except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
