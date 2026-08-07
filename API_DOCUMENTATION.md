# Agent 8 Clinical Operations Portal - API Documentation

## Overview
The backend provides real-time clinical operations intelligence for 26 managed care dieticians, showing:
- Health outcomes for MC users (biomarker improvements)
- Health outcomes for non-MC users (if lab data available)
- Utilization and capacity metrics
- Recommendations and AI insights

## Base URL
```
http://localhost:5001
```

---

## Endpoints

### 1. Clinical Outcomes - Summary
**GET** `/api/agent8/clinical-outcomes`

Returns health outcomes summary for all MC dieticians.

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "doctorname": "Prachi More",
      "mc_patient_count": 145,
      "avg_improvement_pct_mc": 14.2,
      "improved_patients_mc": 128
    }
  ],
  "kpis": [
    {
      "label": "Total Patients",
      "value": "2891",
      "unit": "MC patients"
    }
  ]
}
```

---

### 2. Clinical Outcomes - Detailed (Single Dietician)
**GET** `/api/agent8/clinical-outcomes?dietician=Prachi More`

Returns detailed health outcomes for a specific dietician, including:
- MC users: biomarker improvements
- Non-MC users: lab data availability + comparison (if available)

**Response:**
```json
{
  "status": "success",
  "dietician_name": "Prachi More",
  "mc_outcomes": {
    "doctorname": "Prachi More",
    "patient_segment": "MC User",
    "patient_count": 145,
    "avg_improvement_pct": 14.2,
    "improved_patients": 128,
    "status": "Active"
  },
  "non_mc_outcomes": {
    "doctorname": "Prachi More",
    "patient_segment": "Non-MC User",
    "patient_count": 32,
    "with_lab_reports": 18,
    "without_lab_reports": 14,
    "avg_improvement_pct": 9.8,
    "lab_data_status": "Lab reports available for comparison"
  }
}
```

**Key Fields:**
- `patient_count`: Total patients in segment
- `avg_improvement_pct`: Average biomarker improvement (%)
- `improved_patients`: Count of patients with positive biomarker change
- `lab_data_status`: "Lab reports available for comparison" or "No lab reports available"
- `with_lab_reports`: Count of non-MC patients with lab data (for comparison)
- `without_lab_reports`: Count of non-MC patients without lab data

---

### 3. Capacity Analysis
**GET** `/api/agent8/capacity-analysis`

Returns utilization metrics for all MC dieticians (30-day window).

**Response:**
```json
{
  "status": "success",
  "kpis": [
    {
      "label": "Total Capacity (30-day)",
      "value": "12600",
      "unit": "slots"
    },
    {
      "label": "Booked Appointments",
      "value": "9842",
      "unit": "appts"
    },
    {
      "label": "Avg Utilization",
      "value": "78.1%",
      "status": "On target"
    }
  ],
  "providers": [
    {
      "name": "Prachi More",
      "booked": 350,
      "capacity": 420,
      "utilization": 83.3,
      "status": "high"
    }
  ]
}
```

**Status Values:**
- `optimal`: <70% utilization (underutilized)
- `high`: 70-95% utilization (ideal)
- `critical`: >95% utilization (over-booked)

---

### 4. Recommendations
**GET** `/api/agent8/recommendations`

Returns AI-generated recommendations for provider management:
- Training Required
- Capacity Rebalancing
- Quality Interventions
- Peer Mentoring

**Response:**
```json
{
  "training_required": [...],
  "capacity_rebalancing": [...],
  "quality_interventions": [...],
  "peer_mentoring": [...]
}
```

---

### 5. Dashboard KPIs
**GET** `/api/agent8/dashboard`

Returns overall operational KPIs.

**Response:**
```json
{
  "kpis": [
    {
      "label": "Team Utilization",
      "value": "94.2%",
      "trend": "+2.4% vs prev. period",
      "comparison": "Target: 85-90%"
    }
  ]
}
```

---

## Data Mapping

### MC Dieticians (26 Total)

**In-house Review (6)** - 14 slots/day each:
- Prachi More
- Ambika Rode
- Geeta Maggu
- Gitanjali Malik Sachdeva
- Chandni Sharma
- Tejashree Thorat

**In-house Regular (5)** - 14 slots/day each:
- Chaithra B
- Shefali Dindorkar
- Sweta Naik
- Divya Pandey
- Trupti Nakar

**Contractual (14)** - 22 slots/day each:
- Hemlata Alawadhi
- Ruchi Singh
- Nisha Sharma
- Hitesh Kumar
- Priyadharshini R
- Avani Mekala
- Neha Suryawanshi
- Homeshwar Mandawliya
- Trapti Bhardwaj
- Asra Jabeen
- Midhat Zehra
- Aparna Bhardwaj
- Mital Bhadania
- Shikha Singh

---

## Trino Data Sources

### 1. Appointments
**Table:** `deltalake.dl_standard_pbireporting.f_appointmentflattable`
- **Key Fields:** `doctorname`, `appointmentdate`, `appointmentstatus`, `phrid`, `claimstatus`
- **Used For:** Utilization, demand forecasting, scheduling

### 2. Biomarkers (Health Outcomes)
**Table:** `deltalake.dl_central_health_vault.phr_lab_parsed_data_parsed_data_results_readings`
- **Key Fields:** `phr_id`, `loinc_id`, `baseline_value`, `latest_value`, `test_name`
- **Used For:** Clinical outcomes, improvement tracking

### 3. MC Enrollments
**Table:** `deltalake.dl_standard_customermart.d_policy`
- **Key Fields:** `masterphrid`, `vlocity_ins_fsc__productcode__c`
- **Used For:** Filter MC vs non-MC patients
- **MC Product Codes:** PURELIFE1-5, VYTAL0126, VYTAL01026

---

## Error Handling

All endpoints return fallback mock data if Trino is unavailable:

```json
{
  "status": "fallback",
  "message": "Using mock data - Trino connection unavailable",
  "data": [...]
}
```

This ensures the UI remains functional during Trino maintenance or connectivity issues.

---

## Configuration

Set environment variables in `.env`:
```
TRINO_HOST=trino-prod.healthrx.co.in
TRINO_PORT=443
TRINO_USER=vasu.verma
TRINO_PASSWORD=<YOUR_TRINO_PASSWORD>
TRINO_CATALOG=deltalake
DIETICIAN_QA_BACKEND=https://consultation-call-quality-analysis-system.onrender.com
```

---

## Key Insights from Data

### Health Outcomes Logic (CORRECTED)

**For MC Users:**
- Always available (from Trino appointments + biomarker data)
- Shows biomarker improvement % for each dietician
- Compares against best performers

**For Non-MC Users:**
- Check if lab reports exist
- If YES → Show comparison (biomarker improvement %)
- If NO → Explicitly state "No lab reports available"

This gives complete visibility into:
1. Dietician effectiveness with MC (primary focus)
2. Dietician effectiveness with non-MC (if data available)
3. Data completeness (transparency about what's available)

---

## Testing the API

```bash
# Test clinical outcomes
curl http://localhost:5001/api/agent8/clinical-outcomes

# Test specific dietician
curl "http://localhost:5001/api/agent8/clinical-outcomes?dietician=Prachi%20More"

# Test capacity analysis
curl http://localhost:5001/api/agent8/capacity-analysis

# Test recommendations
curl http://localhost:5001/api/agent8/recommendations

# Test dashboard
curl http://localhost:5001/api/agent8/dashboard
```

---

## Troubleshooting

### Trino Connection Issues
1. Check Trino host/port connectivity
2. Verify credentials in .env
3. Check VPN connection (if required)
4. Review logs: Flask will show connection errors

### Data Issues
1. Verify MC product codes in f_appointmentflattable
2. Check biomarker LOINC codes in phr_lab_parsed_data
3. Review Trino table schemas via Trino UI

### Mock Data Fallback
- If Trino unavailable, endpoints return hardcoded mock data
- Frontend falls back to displaying mock KPIs and provider lists
- Check terminal logs for Trino error messages

---

**Last Updated:** 2026-07-21  
**Status:** Production-Ready with Trino Integration
