# Agent 8 Unified Portal - Production Documentation

## 🎯 Overview

**Complete Clinical Provider Management & Quality Analysis System**

Multi-professional dashboard for 26 MC (Managed Care) dieticians with:
- Real-time appointment utilization tracking
- Historical health outcomes & biomarker improvements
- Dietician call quality analysis & scoring
- AI-powered clinical recommendations
- 2-year historical data + daily automatic updates

---

## 🚀 Quick Access

| Component | URL | Status |
|-----------|-----|--------|
| **Dashboard** | https://agent8-unified-portal.vercel.app | ✅ Live |
| **Backend API** | https://agent8-unified-portal.onrender.com | ✅ Live |
| **Database** | Neon PostgreSQL (private) | ✅ Live |
| **Data Source** | Trino (Bajaj private) | ✅ Connected |

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER DASHBOARD (Vercel)                  │
│        https://agent8-unified-portal.vercel.app             │
│  ┌──────────────────┬──────────────────┬──────────────────┐ │
│  │  Professional    │  Clinical        │  Call Quality    │ │
│  │  Management      │  Outcomes        │  Analysis        │ │
│  └──────────────────┴──────────────────┴──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↕ API
┌─────────────────────────────────────────────────────────────┐
│              BACKEND SERVICES (Render Flask)                │
│        https://agent8-unified-portal.onrender.com           │
│  ┌──────────────────┬──────────────────┬──────────────────┐ │
│  │  Professional    │  Appointment     │  Recommendations │ │
│  │  Metrics API     │  Analytics API   │  & Insights API  │ │
│  └──────────────────┴──────────────────┴──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│              CACHED DATA LAYER (Neon PostgreSQL)            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  52 Rows: 26 Professionals × 2 Periods                │ │
│  │  • Full Backfill: 2024-01-01 to Today                 │ │
│  │  • Recent 23 Days: Last 23 Days                       │ │
│  │  Updated Daily at 6 AM                                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│           SOURCE DATA (Trino - Bajaj Internal)             │
│  • f_appointmentflattable (16M+ rows)                       │
│  • managed_care_programme_results                          │
│  • Health outcomes & biomarker data                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 Data Flow

### Daily Automated Update (6 AM)

```
6:00 AM Task Scheduler
    ↓
[agent8_production_export.py]
    • Queries Trino for full appointment history (2024-present)
    • Calculates recent 23-day metrics
    • Generates Excel export with 52 rows
    ↓
[sync_excel_to_neon.py]
    • Reads Excel file
    • Upserts to Neon PostgreSQL
    • 52 rows synced (creates new period rows)
    ↓
[Render API]
    • Fetches latest period data on user request
    • Returns matching period for selected date range
    ↓
[Vercel Dashboard]
    • Shows real data for selected time period
    • User can select any date range 2024-present
```

### User Query Flow

```
User selects date range (e.g., "Last 23 days")
    ↓
Dashboard sends API request:
  GET /api/agent8/professionals?start_date=2026-07-15&end_date=2026-08-07
    ↓
Render Flask API:
  1. Queries Neon PostgreSQL
  2. Finds best-matching period for date range
  3. Returns 26 professionals with period-specific metrics
    ↓
Dashboard renders table with:
  • Appointment counts
  • Utilization %
  • QA scores
  • Health improvements
  • Recommendations
```

---

## 🔧 Configuration

### Production URLs

All credentials are stored in **Render Environment Variables** (not in code):

```
FLASK_ENV=production
TRINO_HOST=trino-prod.healthrx.co.in
TRINO_PORT=443
TRINO_USER=vasu.verma
TRINO_PASSWORD=****** (in Render secrets)
DATABASE_URL=postgresql://*** (Neon pooler)
GEMINI_API_KEY=****** (in Render secrets)
DIETICIAN_QA_BACKEND=https://consultation-call-quality-analysis-system.onrender.com
```

**To update credentials:**
1. Go to Render Dashboard → agent8-unified-portal
2. Settings → Environment Variables
3. Update and redeploy

---

## 📊 Dashboard Features

### Tab 1: Professional Management
- **Metrics by Provider:**
  - Total appointments (period-specific)
  - Utilization % (appointments vs capacity)
  - QA scores (call quality)
  - Health improvements (biomarker changes)
  - 7-day forecast

- **Sorting & Filtering:**
  - Sort by utilization, appointments, QA score
  - Filter by cohort (IN-HOUSE AI, CONTRACTUAL, etc)
  - Date range selector (2024-present)

### Tab 2: Clinical Outcomes
- **Health Metrics:**
  - MC vs Non-MC patient health improvements
  - Lab data availability
  - Biomarker trend analysis
  - 1-year clinical outcomes

### Tab 3: Quality Analysis
- **Call Quality Scoring:**
  - Transcription quality metrics
  - Conversation fluency scores
  - Medical accuracy checks
  - Peer benchmarking

---

## 🛠️ Maintenance

### Daily Tasks (Automated)
- ✅ Export data from Trino → 2 periods × 26 professionals
- ✅ Sync to Neon PostgreSQL
- ✅ Dashboard refreshes on next user visit

### Weekly Tasks (Manual)
- Check `automation.log` for errors
- Monitor Render build logs for failures
- Review database size (Neon free tier limits)

### Monthly Tasks (Manual)
- Review data quality metrics
- Archive old Excel exports
- Verify Trino connection stability

### Emergency Recovery
```bash
# Manual data export if automation fails:
cd C:\Users\muskan.rao\Documents\claude\agent8-unified-portal
python agent8_production_export.py
python sync_excel_to_neon.py

# Check Render API status:
curl https://agent8-unified-portal.onrender.com/api/agent8/professionals

# View automation logs:
cat C:\Users\muskan.rao\Documents\claude\agent8-unified-portal\automation.log
```

---

## 📝 Data Specifications

### Professional Metrics (Neon PostgreSQL)

```sql
CREATE TABLE professional_metrics (
    provider_name VARCHAR(255),      -- E.g., "Prachi More"
    cohort VARCHAR(100),             -- IN-HOUSE AI, CONTRACTUAL, etc
    start_date DATE,                 -- Period start (e.g., 2024-01-01)
    end_date DATE,                   -- Period end (e.g., today)
    appts_count INTEGER,             -- Total appointments in period
    capacity INTEGER,                -- Theoretical max slots
    utilization_pct DECIMAL(5,2),   -- % (appts / capacity * 100)
    qa_score DECIMAL(5,2),          -- 0-100 call quality score
    improvement_score DECIMAL(5,2), -- Avg biomarker improvement %
    improvement_total INTEGER,       -- Count of improved patients
    status VARCHAR(50),              -- OPTIMAL, CRITICAL, etc
    forecast_7d INTEGER,             -- Predicted appts in next 7 days
    ...
);
```

### Periods Exported

| Period | Duration | Use Case |
|--------|----------|----------|
| Full Backfill | 2024-01-01 to Today | Historical trends, full view |
| Recent 23 Days | Last 23 days | Current performance, trends |

**API selects best-matching period:**
- User queries 2024-01-01 to 2026-08-07 → Returns Full Backfill
- User queries 2026-07-15 to 2026-08-07 → Returns Recent 23 Days
- User queries 2026-07-01 to 2026-08-07 → Returns best match

---

## 🚨 Troubleshooting

### Dashboard shows no data
**Symptom:** Dashboard loads but all metrics are 0

**Fix:**
1. Clear browser cache (Ctrl+Shift+Delete)
2. Check Render logs for API errors
3. Verify Neon database has data:
   ```bash
   psql postgresql://... neondb
   SELECT COUNT(*) FROM professional_metrics;
   ```
4. Run manual export:
   ```bash
   python agent8_production_export.py
   python sync_excel_to_neon.py
   ```

### API returning wrong data
**Symptom:** Dashboard shows 0 appointments or wrong period

**Fix:**
1. Check request format:
   ```bash
   curl "https://agent8-unified-portal.onrender.com/api/agent8/professionals?start_date=2026-07-15&end_date=2026-08-07"
   ```
2. Verify Neon connection:
   ```bash
   # Check DATABASE_URL in Render Environment Variables
   # Must include: -pooler and ?channel_binding=require
   ```

### Render deployment failed
**Symptom:** Build fails, red status in Render Dashboard

**Fix:**
1. Check build logs in Render Dashboard
2. Common issues:
   - Python dependency missing → Update requirements.txt
   - Port conflict → Render uses port 10000 by default
   - ENV variable missing → Add to Render Environment Variables

### Trino connection timeout
**Symptom:** Export fails with "connection timeout" error

**Fix:**
1. Verify VPN is active (Trino is internal)
2. Check credentials in .env:
   ```
   TRINO_USER=vasu.verma
   TRINO_PASSWORD=****** (must be correct)
   TRINO_HOST=trino-prod.healthrx.co.in:443
   ```
3. Test Trino query manually:
   ```bash
   python -c "from app import get_trino_connection; conn = get_trino_connection(); print('OK')"
   ```

---

## 📞 Support

### For Technical Issues
1. Check `automation.log` for error messages
2. Review Render build logs: https://dashboard.render.com
3. Test API manually with curl
4. Check Neon database directly if needed

### Common Commands

```bash
# Check automation status
tail -50 C:\Users\muskan.rao\Documents\claude\agent8-unified-portal\automation.log

# Test export manually
python agent8_production_export.py

# Test API endpoint
curl "https://agent8-unified-portal.onrender.com/api/agent8/professionals?start_date=2024-01-01&end_date=2026-08-07"

# View current data in Neon
psql postgresql://neondb_owner:***@***-pooler.c-2.us-west-2.aws.neon.tech/neondb
> SELECT provider_name, COUNT(*) as periods FROM professional_metrics GROUP BY provider_name;
```

---

## ✅ Verification Checklist

- [x] Backend API deployed to Render
- [x] Frontend deployed to Vercel  
- [x] Neon PostgreSQL synced with 52 rows
- [x] Multi-period data export working
- [x] Date-range API queries returning correct periods
- [x] Prachi More shows 16,925 appts (full) and 1,430 appts (recent)
- [x] Daily automation script ready
- [x] All credentials in Render environment (not in code)
- [x] GitHub push successful (history cleaned)
- [x] Dashboard HTML loading at Vercel

---

**Status:** ✅ PRODUCTION READY  
**Last Updated:** 2026-08-07  
**Deployed By:** Claude Code  
**Next Review:** 2026-08-14

---
