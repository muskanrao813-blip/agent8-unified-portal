# Gemini AI Agent Setup Guide

## Overview
The Recommendations system now uses **Google Gemini** as the primary AI agent to generate intelligent, strategic recommendations based on real appointment, quality, and capacity data.

**Architecture:**
```
Real Data (Trino + QA + Rules)
        ↓
recommendations-proper endpoint (analyzes & tiers)
        ↓
Gemini AI Agent (strategic insights)
        ↓
Dashboard (displays both: data + AI analysis)
```

---

## Step 1: Get Gemini API Key

### Option A: Google Cloud Console (Recommended for Production)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable "Generative Language API"
4. Create API key:
   - Navigate to: **Credentials** → **Create Credentials** → **API Key**
   - Copy the API key

### Option B: Google AI Studio (Quick Test)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click **Create API Key**
3. Copy the API key

---

## Step 2: Configure API Key

### Option A: Environment Variable (Recommended)
```bash
# Linux/Mac
export GEMINI_API_KEY='your-api-key-here'

# Windows (PowerShell)
$env:GEMINI_API_KEY='your-api-key-here'

# Windows (Command Prompt)
set GEMINI_API_KEY=your-api-key-here

# Permanent (Linux/Mac) - Add to ~/.bashrc or ~/.zshrc
echo "export GEMINI_API_KEY='your-api-key-here'" >> ~/.bashrc
source ~/.bashrc
```

### Option B: .env File
Create `.env` in project root:
```env
GEMINI_API_KEY=your-api-key-here
```

### Option C: Direct in Application Code (Development Only)
In `app.py`, line ~2445:
```python
gemini_api_key = 'your-api-key-here'  # NOT recommended for production
```

---

## Step 3: Restart Flask Server

```bash
# Kill existing Flask process
pkill -f "python -B app.py"

# Restart
cd C:\Users\muskan.rao\Documents\claude\agent8-unified-portal
python -B app.py
```

---

## Step 4: Test Gemini Integration

### Test 1: Check API Key Configuration
```bash
curl http://localhost:5001/api/agent8/recommendations-gemini?start_date=2026-07-01&end_date=2026-07-28
```

**Expected Response:**
```json
{
  "status": "success",
  "generated_by": "Gemini AI Agent",
  "analysis": { ... AI insights ... }
}
```

**If ERROR:**
```json
{
  "status": "error",
  "message": "Gemini API key not configured",
  "setup": "Set GEMINI_API_KEY environment variable"
}
```

### Test 2: Verify Data Flow
```bash
# 1. Get base recommendations (data analysis)
curl http://localhost:5001/api/agent8/recommendations-proper?start_date=2026-07-01&end_date=2026-07-28 | head -50

# 2. Get Gemini AI insights (strategic analysis)
curl http://localhost:5001/api/agent8/recommendations-gemini?start_date=2026-07-01&end_date=2026-07-28 | head -50
```

---

## Step 5: View in Dashboard

1. Open browser: `http://localhost:3000`
2. Navigate to **Recommendations** tab
3. You should see:
   - **Strategic Insights** (from Gemini)
   - **Provider Performance Tiers** (from real data analysis)
   - **Detailed Action Plans** (for NEEDS_HELP providers)

---

## API Endpoints Reference

### Endpoint 1: Real Data Analysis
```
GET /api/agent8/recommendations-proper
?start_date=2026-07-01
&end_date=2026-07-28
```
**Returns:**
- Provider tiers (EXCELLENT, GOOD, MONITOR, NEEDS_HELP)
- Detailed action plans
- Capacity utilization %
- QA scores
- YoY seasonality

### Endpoint 2: Gemini AI Analysis
```
GET /api/agent8/recommendations-gemini
?start_date=2026-07-01
&end_date=2026-07-28
```
**Returns:**
- Executive summary
- Strategic insights
- Root cause analysis
- System vs individual issues
- Predictive recommendations
- Quick wins
- Risk assessment

---

## What Gemini Does

### 1. **Analyzes Real Data**
- Trino appointment data (26 providers)
- QA scores (from QA system)
- Capacity benchmarks (from rule book)
- Working days consistency
- YoY seasonality

### 2. **Generates Strategic Insights**
- Root causes of underperformance
- Systemic issues vs individual problems
- Predictive trends and risks
- Data-driven resource allocation

### 3. **Provides Actionable Recommendations**
- CRITICAL/HIGH/MEDIUM/LOW priorities
- Specific actions with owners and timelines
- Success metrics
- Expected ROI/impact

### 4. **Continuous Analysis**
- On-demand: Call Gemini endpoint anytime
- Real-time: Latest data analyzed each call
- Dashboard: Updates with each refresh

---

## Troubleshooting

### Issue: "Gemini API key not configured"
**Solution:** 
- Verify environment variable: `echo $GEMINI_API_KEY`
- Or restart Flask after setting key: `python -B app.py`

### Issue: "Gemini API error: 401"
**Solution:** 
- Invalid or expired API key
- Get new key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Issue: "Gemini API error: 429 (Rate Limited)"
**Solution:**
- Waiting 1 minute usually resolves
- Check API quota in Google Cloud Console
- Free tier has limits (~60 requests/minute)

### Issue: Slow Response
**Solution:**
- Gemini API takes 10-30 seconds first call
- Subsequent calls faster (~5-15 seconds)
- This is normal - AI analysis takes time

---

## Data Privacy & Security

✅ **Safe:**
- API key in environment variable (not in code)
- Data sent only to Google Gemini API
- No data stored in 3rd party systems
- Uses HTTPS encryption

⚠️ **Considerations:**
- Gemini has access to your appointment/quality data
- Review Google's privacy policy: https://policies.google.com/privacy
- For sensitive production, consider on-premise LLM

---

## Advanced Configuration

### Custom Gemini Prompt
Edit system prompt in `/api/agent8/recommendations-gemini` endpoint (~line 2450):
```python
gemini_prompt = """Your custom instructions here..."""
```

### Change Analysis Frequency
Currently: On-demand (call endpoint anytime)

To add scheduled weekly analysis:
See `schedule_daily_recommendations.py` for scheduler setup.

### Integration with Other Systems
Gemini endpoint returns JSON - can integrate with:
- Email notifications
- Slack alerts
- Internal ticketing systems
- Data warehouses

---

## Support & Next Steps

1. **Verify Setup**: Call `/recommendations-gemini` endpoint
2. **Check Dashboard**: See Gemini insights in Recommendations tab
3. **Configure Alert**: Optional - add email/Slack notifications
4. **Customize Prompt**: Modify system prompt for your use case

---

## Quick Start Commands

```bash
# 1. Set API key
export GEMINI_API_KEY='your-api-key'

# 2. Restart Flask
cd C:\Users\muskan.rao\Documents\claude\agent8-unified-portal
python -B app.py

# 3. Test endpoint
curl http://localhost:5001/api/agent8/recommendations-gemini?start_date=2026-07-01&end_date=2026-07-28

# 4. View dashboard
# Open http://localhost:3000 → Recommendations tab
```

---

**Status:** ✅ Ready for Gemini API Key Configuration
