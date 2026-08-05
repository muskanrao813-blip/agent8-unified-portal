# 🚀 Unified Production Deployment: Agent 8 + Call Quality Analysis

**Status:** Ready to Deploy  
**Structure:** Single GitHub repo, single deployment  
**Components:** Agent 8 + QA Portal (merged)

---

## 📁 Merged Project Structure

```
agent8-unified-portal/
├── clinical-dashboard/              (Agent 8 Frontend - React)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Overview.jsx
│   │   │   ├── ClinicalOutcomes.jsx
│   │   │   ├── Utilization.jsx
│   │   │   ├── Recommendations.jsx
│   │   │   └── CallQualityAnalysis.jsx  ← Integrates QA Portal
│   │   ├── qa-portal/                   ← QA Portal frontend code
│   │   │   ├── App.tsx
│   │   │   ├── components/
│   │   │   └── pages/
│   │   └── ...
│   └── package.json
│
├── qa_backend/                      (QA Backend - FastAPI/Python)
│   ├── api/
│   │   ├── calls.py
│   │   ├── dieticians.py
│   │   └── clinical_calls.py
│   ├── services/
│   ├── schemas/
│   ├── db/
│   └── main.py
│
├── app.py                           (Agent 8 Backend - Flask/Python)
├── requirements.txt                 (Merged dependencies)
├── Procfile                         (Single deployment)
└── .env.production                  (Production config)
```

---

## 🛠️ Merge Steps (Already Done)

✅ QA Portal backend copied to `qa_backend/`  
✅ QA Portal frontend copied to `clinical-dashboard/src/qa-portal/`  
✅ Call Quality Analysis tab integrates both seamlessly

---

## 📋 Pre-Deployment Checklist

- [ ] Step 1: Update requirements.txt (merge QA deps)
- [ ] Step 2: Configure app.py to serve QA endpoints
- [ ] Step 3: Push to GitHub
- [ ] Step 4: Deploy backend to Render
- [ ] Step 5: Deploy frontend to Vercel
- [ ] Step 6: Test all features live

---

## ✨ Step 1: Update Requirements.txt

Add QA Portal dependencies to Agent 8's `requirements.txt`:

```
Flask==3.0.0
Flask-CORS==4.0.0
requests==2.31.0
python-dotenv==1.0.0
Werkzeug==3.0.0
trino==0.18.0
pyarrow==14.0.0
gunicorn==21.2.0
psycopg2-binary==2.9.9
google-generativeai==0.3.0
urllib3>=1.26.0

# QA Portal Backend Dependencies
fastapi==0.104.0
uvicorn==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.0
alembic==1.12.0
python-multipart==0.0.6
```

---

## 🔌 Step 2: Unified Backend Architecture

**Current:** Two separate backends (port 5001 + 8000)  
**Merged:** Single backend serving both

**Option A: Keep Separate (Simpler)**
- Agent 8 backend: `agent8-backend.onrender.com`
- QA backend: separate deployment
- Works now, minimal changes

**Option B: True Merge (Advanced)**
- Merge app.py + main.py into one backend
- Serve both at same domain
- Requires more refactoring

**Recommended:** Option A (Separate backends, merged frontend)

---

## 🚀 Step 3: Push to GitHub

```bash
cd C:\Users\muskan.rao\Documents\claude\agent8-unified-portal

# Initialize git if not already
git init
git add .
git commit -m "Merge QA Portal into Agent 8 - unified platform"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/agent8-unified-portal
git push -u origin main
```

---

## 🔧 Step 4: Deploy Backend to Render

### Backend 1: Agent 8 Backend (Existing)
- Already configured
- Keep as is
- URL: `https://agent8-backend-xxx.onrender.com`

### Backend 2: QA Backend (New)
1. In Render dashboard: **New → Web Service**
2. Connect GitHub: `agent8-unified-portal`
3. Settings:
   - **Root directory:** `qa_backend`
   - **Build:** `pip install -r ../requirements.txt`
   - **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free ($0)
4. Environment variables:
   ```
   DATABASE_URL=postgresql://<user>:<pass>@<host>/db
   GEMINI_API_KEY=<your_key>
   ```
5. Note URL: `https://qa-backend-xxx.onrender.com`

---

## 🎨 Step 5: Deploy Frontend to Vercel

**Single frontend deployment** (serves both Agent 8 + QA Portal)

1. Update `clinical-dashboard/.env.production`:
```
REACT_APP_API_URL=https://agent8-backend-xxx.onrender.com/api/agent8
REACT_APP_QA_API_URL=https://qa-backend-xxx.onrender.com/api
```

2. Deploy to Vercel:
   - Root: `clinical-dashboard`
   - Build: `npm run build`
   - Output: `build`
   - Environment vars (above)

3. URL: `https://agent8-portal.vercel.app`

---

## ✅ Step 6: Verify Live

**Test Agent 8:**
```bash
curl https://agent8-backend-xxx.onrender.com/api/agent8/dashboard
```

**Test QA Backend:**
```bash
curl https://qa-backend-xxx.onrender.com/api/calls/
```

**Test Frontend:**
1. Open https://agent8-portal.vercel.app
2. Navigate: Overview → Call Quality Analysis
3. Click each sub-tab (Dashboard, Upload, Transcriptions, etc.)
4. Verify real data loads

---

## 🎯 Production URLs (Final)

| Service | URL |
|---------|-----|
| **Agent 8 + QA Portal** | https://agent8-portal.vercel.app |
| **Agent 8 Backend** | https://agent8-backend-xxx.onrender.com |
| **QA Backend** | https://qa-backend-xxx.onrender.com |
| **Database** | Neon PostgreSQL (free tier) |

---

## 📊 Architecture Summary

```
┌─────────────────────────────────────────────────────┐
│         VERCEL (Frontend)                           │
│  https://agent8-portal.vercel.app                   │
│                                                      │
│  Agent 8 Dashboard                                  │
│  ├── Overview                                       │
│  ├── Clinical Outcomes                              │
│  ├── Utilization                                    │
│  ├── Recommendations                                │
│  └── Call Quality Analysis  ← Embeds QA Portal      │
│      ├── Dashboard                                  │
│      ├── Call Upload                                │
│      ├── Transcriptions                             │
│      ├── AI Insights                                │
│      ├── Dietician Reports                          │
│      └── QA Alerts                                  │
└─────────────────────────────────────────────────────┘
         ↓                              ↓
   ┌─────────────────┐      ┌──────────────────────┐
   │ RENDER Backend 1│      │ RENDER Backend 2     │
   │ Agent 8 API     │      │ QA Portal API        │
   │ Port 8000       │      │ Port 8000            │
   └─────────────────┘      └──────────────────────┘
         ↓                              ↓
   ┌─────────────────────────────────────────────────┐
   │   Neon PostgreSQL (Free 3GB)                     │
   │   - agent8_db                                   │
   │   - qa_db                                       │
   └─────────────────────────────────────────────────┘
         ↓
   ┌─────────────────────────────────────────────────┐
   │   Trino (Healthcare Data)                        │
   │   - f_appointmentflattable                      │
   │   - health_vault                                │
   │   - benefit tables                              │
   └─────────────────────────────────────────────────┘
```

---

## 🎬 Deployment Timeline

1. **Push to GitHub** (5 min)
2. **Deploy backends to Render** (20 min)
   - Agent 8 backend (already done)
   - QA backend (new)
3. **Deploy frontend to Vercel** (10 min)
4. **Verify all endpoints** (10 min)
5. **Go live!** (2 min)

**Total: ~45 minutes**

---

## 🚨 Known Issues & Solutions

| Issue | Solution |
|-------|----------|
| QA Portal iframe showing sidebar | CSS already hides it (left: -256px) |
| CORS errors | Add frontend URL to CORS in backends |
| Query param not working | Ensure QA Portal App.tsx reads `?view=` param |
| Database connection fails | Verify PostgreSQL connection string |
| Slow cold starts | Normal for free tier, <2 min startup |

---

## 🎉 Success Metrics

✅ Agent 8 portal loads at vercel.app  
✅ All tabs render correctly  
✅ Call Quality Analysis sub-tabs work  
✅ Real data loads from QA API  
✅ No sidebar visible (hidden by CSS)  
✅ Transcriptions, reports, alerts display  
✅ Upload functionality works  

**Ready to deploy!** 🚀
