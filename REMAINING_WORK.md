# Remaining Development Work - Priority Order

## ✅ COMPLETED
- [x] Capacity calculation by cohort (17,142 for July 1-23)
- [x] Working days different per cohort (IN-HOUSE: 5 days/wk, CONTRACTUAL: 6 days/wk)
- [x] Booked appointments count (12,516)
- [x] Team utilization KPI (73.0%)
- [x] All 26 providers displaying

---

## ⏳ REMAINING WORK

### PRIORITY 1: Call Quality Scores Integration
**Status:** Research phase  
**Impact:** HIGH - Required for STATUS column and professional table  
**Source:** Dietician QA SQLite database

**What to fetch:**
- avg_qa_score (0-100) per provider name
- Dimension scores: communication, guideline_delivery, active_listening, empathy
- Quality flags

**Implementation:**
1. Create endpoint `/api/agent8/qa-scores` to fetch from QA SQLite
2. Cache results (dietician QA data doesn't change frequently)
3. Return format:
```json
{
  "provider_name": {
    "avg_qa_score": 82.5,
    "call_count": 12,
    "dimension_scores": {...},
    "quality_flags": [...]
  }
}
```

**Files to modify:**
- app.py: Add `/api/agent8/qa-scores` endpoint
- Overview.jsx: Fetch and display in CALL SCORE column

---

### PRIORITY 2: STATUS Column - Rubric Scoring Method
**Status:** Logic definition phase  
**Impact:** HIGH - Key metric for professional table  

**Rubric (based on 3 factors):**
1. **Utilization %** (their appt/capacity × 100)
   - >85%: High capacity usage
   - 60-85%: Optimal
   - <60%: Underutilized

2. **Call Quality Score** (from QA system, 0-100)
   - >80: Excellent
   - 70-80: Good
   - 60-70: Warning
   - <60: Critical

3. **Improvement Score** (from improvement data, 0-10)
   - >5: Excellent outcomes
   - 3-5: Good outcomes
   - 0-3: Needs improvement

**Overall Status Logic:**
- If ANY critical factor: STATUS = "CRITICAL"
- Else if ALL factors good: STATUS = "OPTIMAL"
- Else: STATUS = "HIGH" (caution)

**Implementation:**
1. Calculate rubric score: (util_norm + qa_norm + improvement_norm) / 3
2. Map to status: rubric_score determines CRITICAL/HIGH/OPTIMAL
3. Store in professional object

---

### PRIORITY 3: Dynamic Cohort Performance Cards
**Status:** Needs implementation  
**Impact:** MEDIUM - Currently hardcoded  

**What to calculate (per cohort, per date range):**
1. **Staff count:** Count of providers in cohort (should be dynamic)
2. **Utilization %:** (Booked appts in cohort) / (Capacity for cohort) × 100
3. **Patient volume:** Sum of unique patients in date range (NOT slots)

**Implementation:**
1. Create endpoint `/api/agent8/cohort-performance` returning:
```json
{
  "IN-HOUSE AI": {
    "staff": 6,
    "utilization": 72.5,
    "patients": 820,
    "capacity": 9576
  },
  ...
}
```
2. Update Overview.jsx COHORTS array from API instead of hardcoded

---

### PRIORITY 4: Professional Table Columns Fix
**Status:** Schema verification phase  

**Current columns:** RANK | NAME | COHORT | APPT | CAPACITY | UTIL% | OUTCOME IMPR. | CALL SCORE | STATUS | 7D FORECAST

**Changes needed:**
1. **APPT:** ✓ Already appointments in date range
2. **CAPACITY:** Per-provider capacity in date range (dietician's slots × working days)
3. **UTIL%:** Appt / Capacity × 100
4. **OUTCOME IMPR.:** score/total format (e.g., "7/34")
5. **CALL SCORE:** Fetch from QA system ← PRIORITY 1
6. **STATUS:** Calculate via rubric ← PRIORITY 2
7. **7D FORECAST:** Appointments in 7 days AFTER end date
8. **Footer:** "Showing 26 of 26 Managed Care Professionals"

---

### PRIORITY 5: 7-Day Forecast Window
**Status:** Query definition phase  
**Impact:** MEDIUM - Predictive metric  

**Logic:**
- User selects end date (e.g., July 23)
- 7D Forecast = appointments in July 24-30
- Show as count or percentage of capacity

**Implementation:**
1. Add endpoint `/api/agent8/forecast-7day?end_date=YYYY-MM-DD`
2. Query Trino for appointments in end_date+1 to end_date+7
3. Return per provider and aggregate

---

### PRIORITY 6: Recommendations Tab (Separate)
**Status:** Architecture phase  
**Impact:** MEDIUM - Separate from Overview  

**This should be:**
- New tab in dashboard (not in Overview)
- AI agent analysis of all data cuts
- Show training required, capacity rebalancing, quality interventions

**Not in scope for Overview**, but note for future.

---

## IMPLEMENTATION SEQUENCE

1. **Week 1:** Integrate QA scores (Priority 1)
2. **Week 1:** Implement rubric scoring for STATUS (Priority 2)
3. **Week 2:** Dynamic cohort cards (Priority 3)
4. **Week 2:** Fix professional table (Priority 4)
5. **Week 3:** 7D Forecast (Priority 5)
6. **Future:** Recommendations tab (Priority 6)

---

## QUESTIONS FOR USER

Before proceeding:

1. **QA Scores:** Should we show "N/A" if QA data not available for a provider?
2. **Rubric weights:** Should all 3 factors (util, QA, improvement) be equally weighted at 33% each? Or different weights?
3. **7D Forecast:** Should this be just appointment COUNT? Or percentage of 7-day capacity?
4. **Patient volume:** Should we count unique patients or appointment count? (These are different)
5. **Cohort patient volume:** Same question - unique or total?

---

**Status:** Ready for Priority 1 implementation once user confirms QA score structure
