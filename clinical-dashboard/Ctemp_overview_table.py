import requests
import json

# Fetch all data
health_data = requests.get("http://localhost:5001/api/agent8/health-outcomes?start_date=2026-06-21&end_date=2026-07-21").json()
improvement_data = requests.get("http://localhost:5001/api/agent8/dietician-improvement?start_date=2025-07-21&end_date=2026-07-21").json()

# Build improvement map
improvement_map = {}
for item in improvement_data['data']:
    improvement_map[item['dietician']] = {
        'score': item['improvement_score'],
        'pct': item['improvement_pct'],
        'improved': item['patients_improved'],
        'total': item['patients_total']
    }

# Print all professionals
print("\n" + "="*120)
print("OVERVIEW TAB - ALL METRICS FOR ALL DIETICIANS (25 Total)")
print("="*120)
print(f"\n{'Rank':<5} {'Name':<30} {'Cohort':<20} {'Patients':<10} {'Lab Data':<10} {'Lab %':<8} {'Improvement Score':<18} {'Improvement %':<15} {'Forecast':<10}")
print("-"*120)

for idx, doc in enumerate(health_data['data'], 1):
    name = doc['doctorname']
    cohort = doc['cohort']
    patient_count = doc['patient_count']
    lab_data = doc['with_lab_data']
    lab_pct = (lab_data / patient_count * 100) if patient_count > 0 else 0
    
    # Get improvement data
    if name in improvement_map and improvement_map[name]['score'] is not None:
        score = improvement_map[name]['score']
        pct = improvement_map[name]['pct']
        improved = improvement_map[name]['improved']
        forecast = improved
        status = "OK"
    else:
        score = "N/A"
        pct = "N/A"
        forecast = 0
        status = "No Data"
    
    print(f"{idx:<5} {name:<30} {cohort:<20} {patient_count:<10} {lab_data:<10} {lab_pct:<8.1f} {str(score):<18} {str(pct):<15} {forecast:<10}")

print("\n" + "="*120)
