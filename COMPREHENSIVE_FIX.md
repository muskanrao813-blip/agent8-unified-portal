# COMPREHENSIVE FIX - Capacity Calculation Issues

## ROOT CAUSE IDENTIFIED

### Issue 1: Daily vs. Period Capacity Mismatch
**Database stores:** Daily capacity values (84 per day for IN-HOUSE AI)
**Displayed in table:** Shows as period capacity (1,680 for July)
**Calculation:** 84 slots/day × 20 days stored = 1,680

**But correct should be:** 84 slots/day × 24 working days = 2,016

### Issue 2: Working Days Used in Backfill
- Backfill stored data for only ~20 days per provider in July
- Should have stored 24 days for IN-HOUSE, 26 days for CONTRACTUAL
- Suggests dates are missing from Trino data or filtering is wrong

### Issue 3: Capacity Display in Clinical Table
The performance matrix shows:
- Ambika Rode: 1,555 appts / 1,680 capacity = 92.6%

**WRONG if 1,680 is period capacity:**
- Should be 2,016 capacity (84 × 24 days)
- Correct utilization: 1,555 / 2,016 = 77.1%

**RIGHT if 1,680 is what was actually available:**
- Data only covers ~20 actual working days
- Utilization calculation correct at 92.6%
- But incomplete data coverage issue

---

## SOLUTIONS REQUIRED

### Fix 1: Verify Data Completeness
```sql
SELECT 
  provider_name,
  COUNT(DISTINCT metric_date) as days_with_data
FROM professional_daily_metrics
WHERE metric_date >= '2026-07-01' AND metric_date <= '2026-07-31'
GROUP BY provider_name
ORDER BY days_with_data
```

**If result is 20-23 days:** Data incomplete, need to check Trino source
**If result is 25+ days:** Data is complete, display logic needs fixing

### Fix 2: Recalculate Capacity Display
Option A (If data incomplete):
- Show actual capacity based on days with data
- Display: "1,680 (20 days data)"

Option B (If data complete):
- Recalculate to show full period capacity
- Display: "2,016 (24 working days)"

### Fix 3: Correct Utilization Formula
When displaying individual provider rows:
```
Utilization = Appointments / (SlotsPerDay × ActualWorkingDaysInRange)

NOT: Appointments / SUM(capacity from DB)
```

### Fix 4: Handle Overbooking Cases
Homeshwar Mandawliya showing 308.6% utilization:
- Either legitimate overbooking (data correct)
- Or capacity calculation wrong

Need to verify: Is 440 capacity correct for July for CONTRACTUAL?
- Expected: 22 slots/day × 26 days = 572
- If showing 440: only ~20 days of data

---

## IMMEDIATE ACTIONS REQUIRED

1. **Check Data Completeness:**
   - Query how many days of July data exists for each provider
   - Identify which providers are missing days

2. **Verify Trino Source:**
   - Check if Trino has appointment data for all July days
   - If missing, identify the date gaps

3. **Fix Capacity Display:**
   - Either show actual (20-day) capacity OR
   - Ensure all 24/26 days are backfilled first

4. **Update Dashboard Logic:**
   - Use working_days × slots_per_day calculation (don't rely on DB sum)
   - This ensures accurate display regardless of data storage method

---

## METRICS VERIFICATION FOR JULY 1-30, 2026

**Expected (24 working days for IN-HOUSE, 26 for CONTRACTUAL):**

| Provider | Cohort | Slots/Day | Expected Capacity | Expected Data Days |
|----------|--------|-----------|-------------------|-------------------|
| Ambika Rode | IN-HOUSE AI | 84 | 2,016 | 24 |
| Homeshwar | CONTRACTUAL | 22 | 572 | 26 |

**Currently Showing:** Different numbers suggest incomplete data or wrong calculation

**Action:** Verify actual days with data, then decide between:
1. Backfill missing data to complete all 24/26 days
2. Update display logic to calculate capacity from working days instead of summing DB values
