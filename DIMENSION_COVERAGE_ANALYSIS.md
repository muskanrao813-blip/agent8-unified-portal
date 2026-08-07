# Agent 8 Dashboard - Dimension Coverage Analysis (Aug 1 2026)

## EXISTING 3 TABS (Already Implemented)

### ✅ TAB 1: OVERVIEW
**Features Implemented:**
- Professional list (26 dieticians with rank, name, cohort, appts, capacity, utilization, outcomes, QA call score)
- KPIs: Total team size, booked appts (30-day), capacity, avg utilization %, avg QA score
- Cohort breakdown with donut chart
- Date range selector (start_date / end_date)
- Filters by programme

**Data Sources:**
- `/api/agent8/professionals` → Professional metrics with KPIs
- `/api/agent8/qa-scores` → QA scores from Dietician QA system
- `/api/agent8/cohort-performance` → Cohort metrics

**Coverage:**
- ✅ Individual provider utilization metrics
- ✅ QA scores per provider
- ✅ Patient count (outcomes)
- ✅ Cohort-level aggregates
- ✅ Team-level KPIs

---

### ✅ TAB 2: CLINICAL OUTCOMES
**Features Implemented:**
- Patient count per dietician
- Biomarker improvement % (from Trino)
- Patient split by programme (Diabetes, Dyslipidemia, etc.)
- "With Lab Data" vs "Without Lab Data" breakdown
- Health outcome tables per programme

**Data Sources:**
- `/api/agent8/health-outcomes` → MC patient outcomes + biomarker improvements
- `/api/agent8/mc-programmes` → Programme-specific patient metrics

**Coverage:**
- ✅ Patient metrics (count, improvement %)
- ✅ Programme breakdown
- ✅ Lab data availability status
- ✅ Biomarker trends per programme
- ✅ Clinical effectiveness per dietician

---

### ✅ TAB 3: UTILIZATION
**Features Implemented:**
- Capacity analysis (total capacity, booked appts, utilization % per provider)
- Cohort-level utilization (IN-HOUSE AI, IN-HOUSE MC, IN-HOUSE OTHERS, CONTRACTUAL)
- Donut chart showing cohort % split
- Provider status: CRITICAL (<50%), HIGH (50-95%), OPTIMAL (≥95%)
- Hardcoded peak hours heatmap (24-hour distribution)
- Hardcoded 7-day forecast chart (MON-SUN)

**Data Sources:**
- `/api/agent8/capacity-analysis` → Provider utilization + cohort distribution
- Hardcoded: Peak hours, 7-day forecast (NOT YET DYNAMIC)

**Coverage:**
- ✅ Utilization % per provider
- ✅ Capacity planning (30-day window)
- ✅ Cohort aggregates
- ✅ Status rubric (critical/high/optimal)
- ⚠️ Peak hours: HARDCODED (needs backend data)
- ⚠️ 7-day forecast: HARDCODED (needs backend calculation)

---

## MISSING 9 DIMENSIONS (Ready to Implement)

### ⏳ DIMENSION 4: DEMAND FORECASTING
**Purpose:** Predict next 7 days appointment volume based on trends

**What's Already Available:**
- Backend endpoint: `/api/agent8/forecast-7day` ✅ CREATED
- Algorithm implemented: DOW-based averaging + trend factor
- Data in: professional_metrics (30-day history)

**What's Missing:**
- ❌ React component (DemandForecast.jsx)
- ❌ Integration with frontend
- ❌ Chart rendering (line chart with confidence intervals)
- ❌ Display in tab

**Effort:** 2-3 hours (endpoint ready, just need UI)

---

### ⏳ DIMENSION 5: SCHEDULING OPTIMIZATION
**Purpose:** Hourly load distribution + peak hour identification

**What's Already Available:**
- Backend endpoint: `/api/agent8/peak-hours` ✅ CREATED
- Algorithm: Hourly appointment grouping + intensity mapping (1-5 scale)
- Data in: f_appointmentflattable (hourly distribution)

**What's Missing:**
- ❌ React component (SchedulingOptimization.jsx)
- ❌ 24-hour heatmap rendering
- ❌ Peak/off-peak highlighting
- ❌ Load balancing recommendations UI

**Effort:** 2-3 hours (endpoint ready, just need UI)

---

### ⏳ DIMENSION 6: QA ANALYTICS
**Purpose:** QA scorecard + anomaly detection

**What's Already Available:**
- Backend endpoint: `/api/agent8/qa-analytics` ✅ CREATED
- Anomaly thresholds: >150% (impossible), 120-150% (extreme overbooking), <20% (underutilized), QA<70
- Data in: professional_metrics (QA scores + utilization)

**What's Missing:**
- ❌ React component (QAAnalytics.jsx)
- ❌ QA scorecard table (Provider | Score | vs Benchmark | Trend | Status)
- ❌ Anomaly list with severity badges
- ❌ Comparison with 80.0 benchmark display

**Effort:** 2-3 hours (endpoint ready, just need UI)

---

### ⏳ DIMENSION 7: RECOMMENDATIONS ENGINE
**Purpose:** Daily AI-generated action plans per provider

**What's Already Available:**
- Backend endpoint: `/api/agent8/recommendations-daily` ✅ CREATED
- Logic implemented: Utilization rules + QA rules + trend analysis
- Output schema: Provider | Metrics | Actions (with owner/priority/due date)

**What's Missing:**
- ❌ React component (Briefing.jsx)
- ❌ Executive summary (top 3-5 insights)
- ❌ Per-provider action items display
- ❌ Critical count badge
- ❌ Cron job scheduling (daily at 5 AM)

**Effort:** 3-4 hours (endpoint ready, UI + scheduling needed)

---

### ⏳ DIMENSION 8: HISTORICAL ANALYTICS
**Purpose:** Year-over-year trends (2024-2026) for performance benchmarking

**What's Already Available:**
- Backend endpoint: `/api/agent8/historical-trends` ✅ CREATED
- Data structure defined: Year | Month | Utilization | QA Score | Appt Volume
- Tables created: historical_metrics, trend_metrics

**What's Missing:**
- ❌ React component (HistoricalTrends.jsx)
- ❌ Data backfill from 2024-2026 (2-3 hour Trino query)
- ❌ Year-over-year comparison chart
- ❌ Growth rate indicators
- ❌ Monthly aggregation cron job

**Effort:** 4-5 hours (backfill + UI)

---

### ⏳ DIMENSION 9: PAYOUT ANALYSIS (NEW - NOT COVERED)
**Purpose:** Contractual dietician payment tracking (100 Rs/appt, 50k/month limit)

**What's Available:** NOTHING - Brand new requirement

**What's Missing:**
- ❌ Backend endpoint (payout calculation)
- ❌ Database table (payout_tracking)
- ❌ React component (PayoutAnalysis.jsx)
- ❌ Payout table: Provider | Appts | Rate | Total | vs Budget | Status
- ❌ Monthly payout summary
- ❌ Budget variance alerts

**Data Needed:**
- Contractual provider list (filter from 14 contractual dieticians)
- Appointment count (from f_appointmentflattable)
- Fixed rate: 100 Rs/appt
- Monthly budget: 50k/month
- Payout calculation: Appts × 100

**Effort:** 3-4 hours (new feature, no backend yet)

---

### ⏳ DIMENSION 10: TARGET PLANNING (NEW - NOT COVERED)
**Purpose:** Monthly utilization targets with 100% baseline

**What's Available:** NOTHING - Brand new requirement

**What's Missing:**
- ❌ Backend endpoint (target tracking)
- ❌ Database table (monthly_targets)
- ❌ React component (TargetPlanning.jsx)
- ❌ Target table: Provider | Target | Achieved | % vs Target | Status
- ❌ Monthly target recalculation logic
- ❌ Per-cohort target rules

**Data Needed:**
- Provider list
- Monthly target: 100% utilization baseline
- Actual utilization from metrics
- Target achievement %
- Variance analysis

**Effort:** 3-4 hours (new feature, no backend yet)

---

### ⏳ DIMENSION 11: LEAVE MANAGEMENT (NEW - NOT COVERED)
**Purpose:** Leave upload API + target recalculation

**What's Available:** NOTHING - Brand new requirement

**What's Missing:**
- ❌ Leave upload endpoint (POST /api/agent8/leave-upload)
- ❌ Leave parsing logic (Excel → DB)
- ❌ Database table (provider_leaves)
- ❌ React component (LeaveManagement.jsx)
- ❌ Leave calendar UI
- ❌ Automatic target recalculation on leave upload

**Data Needed:**
- Leave sheet structure: provider_name, leave_start_date, leave_end_date, leave_type
- Two sheets: in_house_leaves, contractual_leaves (from IMPLEMENTATION_SUMMARY.md)
- Impact on capacity calculation

**Effort:** 4-5 hours (new feature, parsing + auto-recalc needed)

---

### ⏳ DIMENSION 12: ZERO-BOOKINGS RCA (NEW - NOT COVERED)
**Purpose:** Root Cause Analysis for zero appointments with bajajfinservhealth.in slot checker

**What's Available:** NOTHING - Brand new requirement

**What's Missing:**
- ❌ Backend endpoint (RCA detection)
- ❌ RCA logic: Check availability on bajajfinservhealth.in
- ❌ Database table (rca_log)
- ❌ React component (ZeroBookingsRCA.jsx)
- ❌ RCA layers:
  - Layer 1: On leave? (check leave_management table)
  - Layer 2: System healthy? (check team bookings > 5)
  - Layer 3: Low demand? (team avg < 1.5 per provider)
  - Layer 4: Booking issue? (check bajajfinservhealth.in slot availability)
  - Layer 5: Quality issue? (engagement score < 70)

**Data Needed:**
- Zero-booking detection query
- Leave data (from Dimension 11)
- Team booking stats
- External slot checker API (bajajfinservhealth.in)
- Quality metrics

**Effort:** 5-6 hours (complex logic + external API integration)

---

## SUMMARY: COVERAGE MATRIX

| Dimension | Backend Endpoint | Frontend Component | Database Tables | Data Source | Status |
|-----------|-----------------|-------------------|-----------------|-------------|--------|
| **Overview** | ✅ 4 endpoints | ✅ Overview.jsx | ✅ professional_metrics | professional_metrics, qa_scores | COMPLETE |
| **Clinical Outcomes** | ✅ 2 endpoints | ✅ ClinicalOutcomes.jsx | ✅ health_outcomes | Trino + SQLite | COMPLETE |
| **Utilization** | ✅ 1 endpoint | ✅ Utilization.jsx (partial) | ✅ professional_metrics | professional_metrics | 80% COMPLETE (hardcoded forecast/peak) |
| **Demand Forecast** | ✅ forecast-7day | ❌ DemandForecast.jsx | ✅ prediction_cache | professional_metrics | 50% (backend done) |
| **Scheduling Optim** | ✅ peak-hours | ❌ SchedulingOptimization.jsx | ✅ hourly_metrics_cache | f_appointmentflattable | 50% (backend done) |
| **QA Analytics** | ✅ qa-analytics | ❌ QAAnalytics.jsx | ✅ anomaly_log | professional_metrics + QA system | 50% (backend done) |
| **Recommendations** | ✅ recommendations-daily | ❌ Briefing.jsx | ✅ daily_recommendations | All metrics | 50% (backend done, no scheduling) |
| **Historical Analytics** | ✅ historical-trends | ❌ HistoricalTrends.jsx | ✅ historical_metrics, trend_metrics | Trino | 30% (backend done, no backfill) |
| **Payout Analysis** | ❌ NOT CREATED | ❌ PayoutAnalysis.jsx | ❌ payout_tracking | f_appointmentflattable | 0% (brand new) |
| **Target Planning** | ❌ NOT CREATED | ❌ TargetPlanning.jsx | ❌ monthly_targets | professional_metrics | 0% (brand new) |
| **Leave Management** | ❌ NOT CREATED | ❌ LeaveManagement.jsx | ❌ provider_leaves | Excel upload | 0% (brand new) |
| **Zero-Bookings RCA** | ❌ NOT CREATED | ❌ ZeroBookingsRCA.jsx | ❌ rca_log | Trino + Leave + Slot API | 0% (brand new) |

---

## QUICK VERDICT: What's MISSING to Complete Dashboard

### 50% DONE (Backend exists, just need React UI):
1. Demand Forecasting — 2 hrs
2. Scheduling Optimization — 2 hrs
3. QA Analytics — 2 hrs
4. Recommendations Engine — 3 hrs (+ scheduling)
5. Historical Analytics — 3 hrs (+ backfill)

**Subtotal: 12 hours**

### 0% DONE (Brand new features):
6. Payout Analysis — 4 hrs
7. Target Planning — 4 hrs
8. Leave Management — 5 hrs
9. Zero-Bookings RCA — 6 hrs

**Subtotal: 19 hours**

### 80% DONE (UI exists but hardcoded):
- Utilization tab needs: Remove hardcoded forecast/peak, integrate real endpoint data — 1 hour

---

## IMPLEMENTATION PRIORITY

**PHASE 1 (IMMEDIATE - 12 hours):** Complete backend dimensions with React UI
- [ ] Create DemandForecast.jsx
- [ ] Create SchedulingOptimization.jsx
- [ ] Create QAAnalytics.jsx
- [ ] Create Briefing.jsx (Recommendations) + setup cron
- [ ] Create HistoricalTrends.jsx + run backfill script

**PHASE 2 (NEXT - 19 hours):** Build brand-new operational dimensions
- [ ] Create payout_tracking endpoint + PayoutAnalysis.jsx
- [ ] Create monthly_targets endpoint + TargetPlanning.jsx
- [ ] Create leave-upload endpoint + LeaveManagement.jsx
- [ ] Create RCA endpoint + ZeroBookingsRCA.jsx

**TOTAL EFFORT:** ~31 hours (4 days full-time)

---

**Ready to proceed with Phase 1 UI components?** All 5 backend endpoints exist and are functional.
