#!/usr/bin/env python3
"""
Gemini Recommendations Agent
Deep-dive analysis and intelligent recommendations using Google Gemini
"""

import os
import json
import requests
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

BACKEND_URL = "http://localhost:5001/api/agent8"

# SYSTEM PROMPT FOR GEMINI
GEMINI_SYSTEM_PROMPT = """You are an expert Clinical Operations Intelligence Agent for Managed Care Dietician Management System.

Your role: Analyze real appointment, capacity, and quality data to generate intelligent, actionable recommendations.

CONTEXT:
- System: Agent 8 Clinical Operations Dashboard
- Data Source: Trino (real appointments), QA System (quality scores), Rule Book (capacity)
- Providers: 26 MC dieticians across 4 cohorts (IN-HOUSE AI, IN-HOUSE OTHERS, IN-HOUSE MC, CONTRACTUAL)
- Benchmark: Capacity-based utilization (appts ÷ allocated slots/day)

YOUR ANALYSIS FRAMEWORK:
1. **Root Cause Analysis**: Don't just identify problems, find WHY they exist
   - Low utilization: Booking constraints? Service gaps? Availability issues?
   - Low QA: Skill gaps? Process issues? Resource constraints?
   - Inconsistency: Scheduling conflicts? External factors?

2. **Systemic vs Individual Issues**: Distinguish between:
   - Individual provider performance (needs coaching)
   - System issues (need process changes)
   - Seasonal patterns (expect variation)
   - Cohort-specific challenges (different benchmarks)

3. **Predictive Insights**: Anticipate problems:
   - Which providers likely to worsen next month?
   - Where should we increase investment?
   - Risk of burnout or attrition?

4. **Prioritized Actions**: Recommend in order of impact:
   - Quick wins (high impact, low effort)
   - Strategic initiatives (high impact, medium effort)
   - Process improvements (systemic change)

ANALYSIS OUTPUT FORMAT:
```json
{
  "executive_summary": "2-3 sentence overview of key findings",
  "key_insights": [
    {
      "insight": "What you discovered",
      "impact": "Why it matters",
      "data_point": "Supporting metric"
    }
  ],
  "root_cause_analysis": {
    "issue": "Problem identified",
    "probable_causes": ["cause1", "cause2"],
    "evidence": "Data supporting analysis"
  },
  "strategic_recommendations": [
    {
      "priority": "CRITICAL/HIGH/MEDIUM",
      "action": "What to do",
      "rationale": "Why this will help",
      "expected_impact": "Measurable outcome",
      "timeline": "When to implement"
    }
  ],
  "risk_factors": ["Risk1: Description", "Risk2: Description"],
  "success_metrics": ["Metric1", "Metric2"],
  "next_steps": "Immediate actions this week"
}
```

IMPORTANT RULES:
- Base ALL recommendations on provided data only (no speculation)
- Consider provider cohort differences (MC dieticians work 12 slots/day, contractual work 22/day)
- Account for seasonality (compare YoY, not month-to-month)
- Recognize when QA score data is limited (only 4 providers have scores)
- Factor in working days consistency (reliability matters)
- Flag systemic issues vs individual performance
- Always include success metrics and timelines

TONE: Professional, data-driven, actionable. No generic advice. Specific to Bajaj Finserv Health MC operations."""

class GeminiRecommendationsAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.backend_url = BACKEND_URL

    def fetch_recommendations_data(self, start_date=None, end_date=None):
        """Fetch real data from recommendations-proper endpoint"""
        try:
            if not start_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

            response = requests.get(
                f"{self.backend_url}/recommendations-proper",
                params={'start_date': start_date, 'end_date': end_date},
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"Failed to fetch recommendations data: {response.status_code}")
                return None

            return response.json()

        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            return None

    def prepare_analysis_context(self, data):
        """Prepare data summary for Gemini analysis"""
        if not data:
            return None

        summary = data.get('summary', {})
        action_plans = data.get('detailed_action_plans', [])
        providers = data.get('provider_profiles', {})

        context = f"""
REAL DATA FOR ANALYSIS:
========================

PERIOD: {summary.get('period_dates', 'N/A')}
COMPARISON: {summary.get('comparison_period', 'N/A')}

OVERALL METRICS:
- Total Providers: {summary.get('total_providers', 0)}
- YoY Growth: {summary.get('overall_seasonality_pct', 0)}%
- Current Avg Appts/Provider: {summary.get('current_avg_appts', 0):.0f}
- Last Year Avg: {summary.get('lastyear_avg_appts', 0):.0f}
- QA Data Available: {summary.get('qa_data_available', False)}

TIER DISTRIBUTION:
- EXCELLENT: {summary.get('tier_counts', {}).get('excellent', 0)} providers
- GOOD: {summary.get('tier_counts', {}).get('good', 0)} providers
- MONITOR: {summary.get('tier_counts', {}).get('monitor', 0)} providers
- NEEDS_HELP: {summary.get('tier_counts', {}).get('needs_help', 0)} providers

PROVIDERS NEEDING HELP (NEEDS_HELP TIER):
"""
        for plan in action_plans[:10]:  # Top 10 for analysis
            context += f"\n- {plan['provider']}: {plan['priority']} | Utilization: {plan['current_metrics']['utilization_pct']:.1f}% | Issues: {len(plan['issues'])}"

        context += f"""

CAPACITY BENCHMARKS (Rule Book):
- IN-HOUSE AI: 84 slots/day each
- IN-HOUSE OTHERS: 14 slots/day each
- IN-HOUSE MC (Dieticians): 12 slots/day each
- IN-HOUSE MC (Doctor): 4 slots/day
- CONTRACTUAL: 22 slots/day each

TASK: Analyze this real data and provide intelligent, strategic recommendations beyond the generated action plans. Focus on:
1. Root causes of underperformance
2. Systemic issues vs individual problems
3. Predictive insights
4. Strategic priorities
5. Data-driven resource allocation
"""
        return context

    def analyze_with_gemini(self, data):
        """Send analysis request to Gemini"""
        if not self.api_key:
            logger.error("Gemini API key not configured")
            return None

        try:
            context = self.prepare_analysis_context(data)
            if not context:
                return None

            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": GEMINI_SYSTEM_PROMPT
                            },
                            {
                                "text": context
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048,
                    "topP": 0.9
                }
            }

            headers = {
                "Content-Type": "application/json"
            }

            response = requests.post(
                f"{GEMINI_API_URL}?key={self.api_key}",
                json=payload,
                headers=headers,
                timeout=60
            )

            if response.status_code != 200:
                logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                return None

            result = response.json()
            analysis_text = result['candidates'][0]['content']['parts'][0]['text']

            return {
                'status': 'success',
                'analysis': analysis_text,
                'timestamp': datetime.now().isoformat(),
                'model': 'gemini-pro'
            }

        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            return None

    def run_weekly_analysis(self):
        """Run complete weekly analysis"""
        logger.info("Starting weekly Gemini analysis...")

        # Fetch data
        data = self.fetch_recommendations_data()
        if not data:
            logger.error("Failed to fetch data for analysis")
            return None

        # Analyze with Gemini
        analysis = self.analyze_with_gemini(data)
        if not analysis:
            logger.error("Gemini analysis failed")
            return None

        # Save analysis
        analysis_file = f"logs/gemini_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('logs', exist_ok=True)
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)

        logger.info(f"✅ Weekly analysis complete. Saved to {analysis_file}")
        return analysis


def test_gemini_setup():
    """Test if Gemini is properly configured"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        print("Set it with: export GEMINI_API_KEY='your-key-here'")
        return False

    print("✅ Gemini API key found")
    print("✅ Agent ready to analyze recommendations data")
    return True


if __name__ == "__main__":
    print("Gemini Recommendations Agent")
    print("=" * 60)

    if test_gemini_setup():
        agent = GeminiRecommendationsAgent()
        logger.info("Agent initialized. Ready for weekly analysis.")
    else:
        logger.warning("Gemini not configured. Please set GEMINI_API_KEY.")
