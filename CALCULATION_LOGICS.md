# Agent 8 Dashboard - Calculation Logics & Configuration

**Last Updated:** 2026-07-27  
**Status:** Production Ready - All 3-level hierarchies implemented

---

## CRITICAL: 3-Level Metric Hierarchy

### Level 1: OVERALL (Dashboard KPIs)
**Scope:** All 26 MC professionals combined  
**Endpoint:** `/api/agent8/dashboard`

```
Team Utilization % = (total_appts_all / total_capacity_all) × 100
Total Capacity = SUM(individual_capacity × working_days) for all 26
Total Booked Appts = SUM(appts_count) for all 26
Avg Health Improvement = AVG(improvement_score) for all 26
```

**Example (July 1-23):**
- Total Appts: 13,849
- Total Capacity: 17,142
- Utilization: 80.8%

---

### Level 2: COHORT (Cohort Performance Cards)
**Scope:** Each of 4 cohorts (IN-HOUSE AI, IN-HOUSE OTHERS, IN-HOUSE MC, CONTRACTUAL)  
**Endpoint:** `/api/agent8/cohort-performance`

```
Cohort Utilization % = (cohort_total_appts / cohort_total_capacity) × 100
Vol. Metric = cohort_daily_capacity × working_days_in_period
```

**Configuration (COHORT_CAPACITY):**
```python
COHORT_CAPACITY = {
    'IN-HOUSE AI': 504,        # 6 dieticians × 84 each
    'IN-HOUSE OTHERS': 28,     # 2 staff × 14 each
    'IN-HOUSE MC': 46,         # 3 dieticians × 14 + 1 doctor × 4
    'CONTRACTUAL': 308         # 14 dieticians × 22 each
}
```

**Example (July 1-23, 19 working days):**
- IN-HOUSE AI: 13.6% util, Vol. Metric = 504 × 19 = 9,576
- IN-HOUSE OTHERS: 49.8% util, Vol. Metric = 28 × 19 = 532
- IN-HOUSE MC: 28.4% util, Vol. Metric = 46 × 19 = 874
- CONTRACTUAL: 5.2% util, Vol. Metric = 308 × 20 = 6,160

---

### Level 3: INDIVIDUAL (Professionals Table)
**Scope:** Each of 26 providers with their own metrics  
**Endpoint:** `/api/agent8/professionals`

```
Provider Capacity = provider_daily_slots × working_days_in_period
Provider Utilization % = (provider_appts / provider_capacity) × 100
Provider Forecast 7d = provider_appts / working_days  (daily rate)
```

**Configuration (PROVIDER_CAPACITY):**
```python
PROVIDER_CAPACITY = {
    'IN-HOUSE AI': 84,        # Per dietician
    'IN-HOUSE OTHERS': 14,    # Per staff member
    'IN-HOUSE MC': 14,        # Per dietician
    'CONTRACTUAL': 22         # Per dietician
}
```

**Example (Shefali Dindorkar, IN-HOUSE OTHERS, July 1-23):**
- Individual Capacity: 14 slots × 19 days = 266
- Appointments: 279
- Utilization: 279/266 = 104.9% (OVERBOOKED)

---

## Working Days Calculation

**Rules:**
- Exclude: All Sundays
- Exclude: Alternate Saturdays (every other Saturday)
- Include: Monday-Friday always
- Include: Every other Saturday

**Cohort-Specific:**
```python
# IN-HOUSE: Mon-Fri + Alternate Saturdays
d_inhouse = count_working_days_inhouse(start_date, end_date)

# CONTRACTUAL: Mon-Sat (6-day week)
d_contractual = count_working_days_contractual(start_date, end_date)
```

**Example (July 1-23, 2026):**
- IN-HOUSE working days: 19
- CONTRACTUAL working days: 20
- Reason: Contractual works all Saturdays, IN-HOUSE alternates

---

## Status Calculation (Multi-Factor Rubric)

**PRIMARY FACTOR: Utilization %**
```
IF util < 50%        → CRITICAL (severely underbooked, wasting capacity)
IF 50% ≤ util ≤ 95%  → Check secondary factors
IF util > 95%        → OPTIMAL if good QA, else HIGH
```

**SECONDARY FACTORS:**

**If IN-HOUSE MC Cohort:**
- Also consider: Improvement Score & QA Score
- If QA < 60 AND Improvement < 30 → CRITICAL
- If well-booked (50-95%) AND QA ≥ 80 AND Improvement ≥ 40 → OPTIMAL

**If Other Cohorts:**
- Only QA Score matters
- If QA < 60 → HIGH
- If well-booked (50-95%) AND QA ≥ 80 → OPTIMAL

**QA Score Handling:**
```
IF QA = 0 or NULL:
  - If util < 50%  → CRITICAL (underbooked is primary)
  - If util ≥ 50%  → NA (no data to assess quality)
```

**Configuration:**
```python
UTILIZATION_THRESHOLDS = {
    'CRITICAL': 50,    # < 50%
    'OPTIMAL': 95,     # 50-95% (well-booked)
}

QA_THRESHOLDS = {
    'CRITICAL': 60,    # QA < 60
    'OPTIMAL': 80      # QA ≥ 80
}
```

---

## Appointment Status Filter

**EXCLUDE Only:** CANCELLED, ANC  
**INCLUDE:** All other statuses (COM, BOOKED, ACT, WIC, RES, etc.)

```python
APPOINTMENT_STATUS_EXCLUDE = ('CANCELLED', 'ANC')
```

**Why:** Cancelled and ANC (Absent/No Call) are not "booked" appointments.

---

## Improvement Score Calculation

**Formula:**
```
Improvement % = (improvement_score / 10) × 100
```

**No Capping:** Values can exceed 10 (normalized on display)

**Used For:** IN-HOUSE MC cohort status determination only

---

## Forecast 7-Day Calculation

**What It Represents:** Provider's typical daily booking rate (past trend)

**Formula:**
```
Forecast 7d = total_appts_in_period / working_days_in_period
```

**Example:**
- Sweta: 323 appts / 19 days = 17/day
- Chandni: 1,505 appts / 19 days = 79/day

---

## Data Storage Strategy: Daily Snapshots

**Current Approach:**
- Calculate metrics for EACH DAY separately (2026-01-01, 2026-01-02, etc.)
- Store ~5,382 records (207 days × 26 providers)
- Allows aggregation for ANY date range query

**When User Selects Date Range:**
- Backend queries professional_metrics for EXACT date range match
- If no pre-calculated range exists → returns empty (need batch calculation)

**Daily Updates:**
- Automated job recalculates for TODAY daily
- Keeps data current through current date

---

## Master Configuration Reference

**Location:** `app.py` lines 40-86

```python
# Configuration Summary
MC_DIETICIANS = [25 names]                    # Master list (locked)
COHORT_DEFINITIONS = {4 cohorts with providers}  # Mapping
COHORT_CAPACITY = {4 capacities, total}       # For dashboard/cohort calcs
PROVIDER_CAPACITY = {4 capacities, individual}   # For individual metrics
UTILIZATION_THRESHOLDS = {critical, optimal}  # Status thresholds
QA_THRESHOLDS = {critical, optimal}           # QA score thresholds
APPOINTMENT_STATUS_EXCLUDE = (CANCELLED, ANC) # Excluded statuses
```

---

## Common Mistakes to Avoid

❌ **DO NOT:** Use COHORT_CAPACITY for individual provider metrics  
✅ **DO:** Use PROVIDER_CAPACITY for individual capacity

❌ **DO NOT:** Sum capacity from multiple daily snapshots without normalizing  
✅ **DO:** Query for exact date range OR calculate capacity from working days

❌ **DO NOT:** Hardcode any threshold or capacity value  
✅ **DO:** Reference config constants (COHORT_CAPACITY, UTILIZATION_THRESHOLDS, etc.)

❌ **DO NOT:** Apply improvement score to non-MC cohorts  
✅ **DO:** Use improvement only for IN-HOUSE MC in status calculation

❌ **DO NOT:** Forget to exclude Sunday when calculating working days  
✅ **DO:** Use count_working_days_inhouse() or count_working_days_contractual()

---

## Testing Checklist

- [ ] Dashboard overall utilization = (all appts / all capacity) × 100
- [ ] Cohort cards show correct aggregated metrics per cohort
- [ ] Individual providers show individual capacity (not cohort total)
- [ ] Working days correct: IN-HOUSE=19, CONTRACTUAL=20 for July 1-23
- [ ] Status calculation respects 3-factor rubric (util → improvement → QA)
- [ ] Forecast 7d = daily rate from selected period
- [ ] Filters work: All Systems, IN-HOUSE AI, Managed Care, Contractual
- [ ] Date range selection updates all metrics correctly

---

## Related Code Files

- `app.py` (lines 32-86): Configuration constants
- `app.py` (lines 333-366): calculate_rubric_status() function
- `app.py` (lines 873-916): get_dashboard() endpoint (OVERALL level)
- `app.py` (lines 1345-1421): get_cohort_performance() endpoint (COHORT level)
- `app.py` (lines 1316-1343): get_professionals_cached() endpoint (INDIVIDUAL level)
- `Overview.jsx`: Frontend display of all 3 levels

---

## Version History

| Date | Change | Impact |
|------|--------|--------|
| 2026-07-27 | Added PROVIDER_CAPACITY config | Individual metrics now correct |
| 2026-07-27 | Fixed capacity calculation hierarchy | Dashboard/Cohort/Individual separated |
| 2026-07-27 | Implemented daily snapshot storage | Any date range queries supported |
| 2026-07-24 | Status calculation multi-factor logic | Proper rubric for CRITICAL/OPTIMAL/HIGH |
| 2026-07-23 | Working days by cohort | CONTRACTUAL = 6-day, IN-HOUSE = 5-6 day |
