# Agent 8 - Unified Clinical Operations Portal

**Status**: Ready for Frontend Integration  
**Architecture**: Separate from Dietician QA Portal (no code changes)  
**Backend Port**: 5001  
**Dietician QA Port**: 8000 (proxied)

---

## 📋 Project Overview

Agent 8 is a unified portal that combines:
- **AI Clinical Operations Intelligence** - Recommendations for provider management
- **Dietician Call Quality Analysis** - Embedded QA portal (proxied)
- **Clinical Outcomes Dashboard** - Programme performance tracking
- **Utilization Analytics** - Capacity analysis and forecasting

**Key Difference**: This is a SEPARATE project from Dietician QA Portal. No modifications to existing code.

---

## 🏗️ Architecture

```
Agent 8 Unified Portal (Port 5001)
├── Backend (Flask app.py)
│   ├── /api/agent8/recommendations - AI recommendations engine
│   ├── /api/agent8/dashboard - KPI metrics
│   ├── /api/calls/* - Proxy to Dietician QA Backend
│   ├── /api/agent8/clinical-outcomes
│   └── /api/agent8/capacity-analysis
│
└── Frontend (templates/index.html)
    ├── Overview Tab
    │   ├── KPI Cards
    │   └── AI Recommendations Section
    ├── Call Quality Tab (Embedded QA Portal)
    ├── Clinical Outcomes Tab
    └── Utilization Tab

↓ Integration Point
Dietician QA Portal (Port 8000) - Unchanged, proxied via API
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip

### Setup (Local Development)

**1. Navigate to project directory**
```bash
cd C:\Users\muskan.rao\Documents\claude\agent8-unified-portal
```

**2. Create virtual environment**
```bash
python -m venv venv
```

**3. Activate virtual environment**
```bash
# Windows
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

**4. Install dependencies**
```bash
pip install -r requirements.txt
```

**5. Create .env file** (optional)
```bash
# .env
DIETICIAN_QA_BACKEND=http://localhost:8000
```

**6. Start the backend**
```bash
python app.py
```

The portal will be available at: **http://localhost:5001**

---

## 📡 Running Both Systems

### Terminal 1: Start Dietician QA Portal
```bash
cd C:\Users\muskan.rao\Documents\claude\dietician-qa
# Follow setup from dietician-qa README
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Terminal 2: Start Agent 8 Unified Portal
```bash
cd C:\Users\muskan.rao\Documents\claude\agent8-unified-portal
.\venv\Scripts\Activate.ps1
python app.py
```

**Access:**
- Agent 8 Portal: http://localhost:5001/
- Dietician QA Portal: http://localhost:8000/
- Agent 8 API Docs: http://localhost:5001/api/

---

## 📊 Tab Structure

### Tab 1: Overview (AI Intelligence)
**Content:**
- KPI Cards (Team Utilization, Booked Appts, Capacity, Improvement)
- AI Agent Recommendations:
  - Training Required (with mentoring suggestions)
  - Capacity Rebalancing (load optimization)
  - Quality Interventions (performance improvement plans)
  - Peer Mentoring (skill development pairings)
  - Provider Segmentation (Stars, High Performers, Rising Talent, etc.)

**Example Recommendation:**
```json
{
  "id": "rec_001",
  "type": "Training Required",
  "provider_name": "Dr. James Wilson",
  "issue": "Low QA Score: 2.8/5 (benchmark: 4.2/5)",
  "recommended_training": "Motivational Interviewing",
  "mentor": "Dr. Sarah Jenkins",
  "timeline_days": 30,
  "success_metrics": [
    "QA score: 2.8 → 3.5+",
    "Patient adherence: +15%"
  ]
}
```

### Tab 2: Call Quality Analysis
**Note:** Currently shows placeholder. Will embed Dietician QA Portal when ready.

**Planned Content:**
- Dashboard (QA scores by dietician)
- Call Upload (Excel batch processing)
- Transcriptions (with entity extraction)
- Scorecard & Insights (5-dimension analysis)
- Dietician Dashboard (performance tracking)
- Coaching Pointers (AI-generated training)

**Access Live QA Portal:** http://localhost:8000/

### Tab 3: Clinical Outcomes
- Patient health metrics
- Programme performance by condition
- Outcome trends and comparisons

### Tab 4: Utilization
- Capacity analysis
- 7-Day forecast
- Professional performance matrix

---

## 🔌 API Endpoints

### Agent 8 Intelligence APIs

**Get Recommendations**
```
GET /api/agent8/recommendations

Response:
{
  "training_required": [...],
  "capacity_rebalancing": [...],
  "quality_interventions": [...],
  "peer_mentoring": [...],
  "provider_segmentation": [...]
}
```

**Get Dashboard KPIs**
```
GET /api/agent8/dashboard

Response:
{
  "kpis": [
    { "label": "Team Utilization", "value": "94.2%", ... },
    { "label": "Booked Appointments", "value": "12,482", ... },
    ...
  ]
}
```

**Get Clinical Outcomes**
```
GET /api/agent8/clinical-outcomes
```

**Get Capacity Analysis**
```
GET /api/agent8/capacity-analysis
```

### Proxied Dietician QA APIs

These are proxied through Agent 8 backend:

```
GET /api/calls/                    # List all calls
GET /api/calls/{call_id}           # Call details
POST /api/calls/bulk-upload        # Upload Excel
```

---

## 🎨 Design System

**Material Design 3 Implementation:**
- **Colors**: Primary black (#000), Secondary gray (#5e5e5b), Error red (#ba1a1a)
- **Typography**: Playfair Display (headings), Inter (body), JetBrains Mono (data)
- **Spacing**: 4px, 8px, 16px, 24px, 32px units
- **Components**: Sidebar (240px), KPI cards, recommendation cards, tables

---

## 🔧 Configuration

### Environment Variables
```bash
# .env file (optional)
DIETICIAN_QA_BACKEND=http://localhost:8000  # URL to Dietician QA backend
FLASK_ENV=development
FLASK_DEBUG=0
```

### Backend Port
Default: `5001`
Change in `app.py`: `app.run(port=5001)`

### Dietician QA Integration
If running on different port or machine:
```python
# In app.py
DIETICIAN_QA_BACKEND = os.getenv('DIETICIAN_QA_BACKEND', 'http://your-host:your-port')
```

---

## 📂 Project Structure

```
agent8-unified-portal/
├── app.py                          # Flask backend
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (create if needed)
│
├── templates/
│   └── index.html                 # Main HTML (Material Design 3)
│
├── static/
│   ├── css/                       # Stylesheets (if needed)
│   └── js/                        # JavaScript files (if needed)
│
└── README.md                      # This file
```

---

## 🛠️ Troubleshooting

### Port Already in Use
```bash
# Check what's using port 5001
netstat -ano | findstr :5001

# Kill process (replace PID)
taskkill /PID <PID> /F
```

### Dietician QA Backend Not Responding
1. Ensure port 8000 is running: `http://localhost:8000/docs`
2. Check `DIETICIAN_QA_BACKEND` in `.env`
3. Verify CORS is enabled in Dietician QA backend

### Recommendations Not Loading
1. Check browser console for errors (F12)
2. Verify `/api/agent8/recommendations` endpoint is responding
3. Check Flask debug output for errors

### Module Not Found Error
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

---

## 📦 Frontend Integration

**Current Status**: Basic Material Design 3 HTML ready

**Ready for:**
1. ✅ Dynamic recommendation rendering
2. ✅ KPI card display
3. ✅ Tab navigation
4. ⏳ Call Quality embedding (when Dietician QA design finalized)
5. ⏳ Advanced charts and visualizations

**Next Steps:**
1. Integrate FE design from `clinical-dashboard.zip`
2. Update templates/index.html with exact design
3. Add any custom CSS/JS requirements
4. Test end-to-end with Dietician QA Portal

---

## 🧪 Testing

### Test Recommendations Endpoint
```bash
curl http://localhost:5001/api/agent8/recommendations
```

### Test Dashboard Endpoint
```bash
curl http://localhost:5001/api/agent8/dashboard
```

### Manual Browser Testing
1. Open http://localhost:5001/
2. Check Overview tab loads KPIs and recommendations
3. Click other tabs to verify navigation
4. Check browser console (F12) for any errors

---

## 📝 Implementation Checklist

- [x] Project structure created
- [x] Flask backend with recommendations engine
- [x] Basic Material Design 3 frontend
- [x] API endpoints for all tabs
- [x] Dietician QA proxy integration setup
- [ ] Frontend design from `clinical-dashboard.zip` integrated
- [ ] Call Quality tab functional
- [ ] End-to-end testing
- [ ] Deployment setup

---

## 🚢 Deployment

When ready for production:

1. **Backend Deployment** (Render, Heroku, or your platform)
   - Push to GitHub
   - Configure environment variables
   - Deploy Flask app

2. **Frontend Deployment** (Netlify, Vercel, or your CDN)
   - Extract design from HTML
   - Build if using React/Vue
   - Deploy static assets

3. **Database** (if needed for storing recommendations)
   - PostgreSQL, MongoDB, or similar
   - Update backend to persist data

---

## 📞 Support

**Backend**: Flask running on `http://localhost:5001`  
**Integrated System**: Dietician QA Portal on `http://localhost:8000`  
**Logs**: Check Flask console output for errors

---

## 📄 License

Internal Project - Bajaj Finserv Health

---

**Version**: 1.0 - Ready for Frontend Integration  
**Last Updated**: 2026-07-21
