# Quick Start - Agent 8 Unified Portal

## 🎯 Ready to Go

**Backend**: ✅ Flask app complete  
**Frontend**: ✅ React app provided  
**Design**: ✅ Material Design 3  
**APIs**: ✅ All endpoints implemented

---

## ⚡ Start in 2 Minutes

### Terminal 1: Backend
```bash
cd C:\Users\muskan.rao\Documents\claude\agent8-unified-portal
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
✅ Running on http://localhost:5001/

### Terminal 2: Frontend
```bash
cd C:\Users\muskan.rao\Documents\claude\agent8-unified-portal\clinical-dashboard
npm install
npm start
```
✅ Running on http://localhost:3000/

**Done!** Both systems are running.

---

## 🧪 Test It

### Test Backend:
```bash
# In another terminal or browser
curl http://localhost:5001/api/agent8/recommendations
curl http://localhost:5001/api/agent8/dashboard
```

### Test Frontend:
- Open http://localhost:3000/
- Should show navbar + pages
- Click tabs to navigate
- Overview page should show loading spinners

---

## 📝 Next Steps to Complete Integration

### Step 1: Connect React to Backend
Edit each React page to fetch from API:

**`src/pages/Overview.jsx`**
```javascript
import { useEffect, useState } from 'react';

export default function Overview() {
  const [recommendations, setRecommendations] = useState([]);
  const [kpis, setKpis] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch recommendations
    fetch('http://localhost:5001/api/agent8/recommendations')
      .then(r => r.json())
      .then(data => setRecommendations(data))
      .catch(e => console.error(e));

    // Fetch KPIs
    fetch('http://localhost:5001/api/agent8/dashboard')
      .then(r => r.json())
      .then(data => setKpis(data.kpis))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {/* KPI Cards */}
      <div className="kpi-grid">
        {kpis.map(kpi => (
          <div key={kpi.label} className="kpi-card">
            <div className="label">{kpi.label}</div>
            <div className="value">{kpi.value}</div>
          </div>
        ))}
      </div>

      {/* Recommendations */}
      <div className="recommendations">
        {recommendations.training_required?.map(rec => (
          <div key={rec.id} className="recommendation-card">
            <h4>{rec.provider_name}</h4>
            <p>Training: {rec.recommended_training}</p>
            <p>Mentor: {rec.mentor_name}</p>
            <button onClick={() => alert('Accept training')}>Accept</button>
            <button onClick={() => alert('Decline')}>Decline</button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Step 2: Implement Other Pages

**`src/pages/CallQuality.jsx`** - Link to Dietician QA Portal
```javascript
export default function CallQuality() {
  return (
    <div>
      <h2>Call Quality Analysis</h2>
      <iframe 
        src="http://localhost:8000" 
        width="100%" 
        height="800px"
        title="Dietician QA Portal"
      />
      <p>Or visit: <a href="http://localhost:8000" target="_blank">QA Portal</a></p>
    </div>
  );
}
```

**`src/pages/ClinicalOutcomes.jsx`**
```javascript
// Similar pattern: fetch from /api/agent8/clinical-outcomes
```

**`src/pages/Utilization.jsx`**
```javascript
// Similar pattern: fetch from /api/agent8/capacity-analysis
```

### Step 3: Add Environment Variable
Create `.env` in `clinical-dashboard/`:
```
REACT_APP_API_URL=http://localhost:5001
```

Use it in components:
```javascript
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';
fetch(`${API_URL}/api/agent8/recommendations`);
```

### Step 4: Test Full Flow
1. ✅ Backend running on 5001
2. ✅ Frontend running on 3000
3. ✅ Click Overview tab
4. ✅ KPIs load from backend
5. ✅ Recommendations display
6. ✅ Click "Accept" on recommendation
7. ✅ Navigate to other tabs

---

## 📁 File Locations

**Frontend**:
```
agent8-unified-portal/clinical-dashboard/src/
├── pages/Overview.jsx          ← Edit here
├── pages/CallQuality.jsx        ← Edit here
├── pages/ClinicalOutcomes.jsx  ← Edit here
└── pages/Utilization.jsx        ← Edit here
```

**Backend**:
```
agent8-unified-portal/
└── app.py                      ← Already complete
```

---

## 🔧 Common Tasks

### Change API URL (Production)
```javascript
// In any React component
const API_URL = 'https://api.yourdomain.com';
fetch(`${API_URL}/api/agent8/recommendations`);
```

Or set env variable:
```bash
REACT_APP_API_URL=https://api.yourdomain.com npm start
```

### Add Loading State
```javascript
const [loading, setLoading] = useState(true);

useEffect(() => {
  fetch(API_URL)
    .then(r => r.json())
    .then(data => { setData(data); setLoading(false); })
    .catch(e => { console.error(e); setLoading(false); });
}, []);

if (loading) return <div className="spinner">Loading...</div>;
```

### Add Error Handling
```javascript
const [error, setError] = useState(null);

useEffect(() => {
  fetch(API_URL)
    .then(r => r.json())
    .then(data => setData(data))
    .catch(e => setError(e.message));
}, []);

if (error) return <div className="error">Error: {error}</div>;
```

---

## ✅ Checklist

- [ ] Backend running (`python app.py`)
- [ ] Frontend running (`npm start`)
- [ ] Can access http://localhost:3000/
- [ ] Can access http://localhost:5001/api/agent8/recommendations
- [ ] Overview page shows KPIs
- [ ] Recommendations display
- [ ] Click tabs to navigate
- [ ] No console errors
- [ ] Call Quality tab links to QA portal

---

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 5001 already in use | `netstat -ano \| findstr :5001` then kill process |
| Port 3000 already in use | `netstat -ano \| findstr :3000` then kill process |
| CORS error | Ensure `CORS(app)` in app.py |
| API returns 404 | Check endpoint name matches exactly |
| Blank page in React | Check browser console (F12) for errors |
| npm install fails | Delete `node_modules`, run `npm install` again |

---

## 🚀 Deploy Next

### Backend (Render)
```bash
git add .
git commit -m "Agent 8 backend"
git push origin main
# Create Render app pointing to this repo
```

### Frontend (Netlify)
```bash
cd clinical-dashboard
npm run build
# Drag-drop build/ folder to Netlify
```

Or via CLI:
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=build
```

---

## 📚 Full Docs

- **Backend Setup**: `README.md`
- **Integration Guide**: `FRONTEND_INTEGRATION.md`
- **Architecture**: `INTEGRATION_PLAN.md`
- **Algorithm Details**: `AGENT_8_SPEC.md`
- **Complete Summary**: `PROJECT_SUMMARY.md`

---

## 💡 Remember

✅ **Backend is done** - Don't modify `app.py` unless adding features  
✅ **Frontend is provided** - Just wire up API calls  
✅ **No Dietician QA changes** - Integrate via proxy  
✅ **CORS enabled** - React can talk to Flask  
✅ **Design complete** - Follow Material Design 3  

---

**Status**: Ready to integrate  
**Time to get running**: 2 minutes  
**Time to complete integration**: 1-2 hours  

**Go build! 🚀**
