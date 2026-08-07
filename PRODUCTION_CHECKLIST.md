# 🚀 Production Deployment Checklist

## Pre-Deployment Verification

### ✅ Code Quality
- [ ] All mock data removed - **VERIFIED ✅**
  - Forecast uses real historical patterns
  - Peak hours uses real Trino bookings
  - QA Analytics returns real data or error
  - Historical Trends queries real data
  - Recommendations uses real analysis only

- [ ] All endpoints tested locally
  - [ ] `/api/agent8/capacity-analysis` → Real data ✅
  - [ ] `/api/agent8/forecast-7day` → Real historical patterns ✅
  - [ ] `/api/agent8/peak-hours` → Real booking times ✅
  - [ ] `/api/agent8/qa-analytics` → Real QA data
  - [ ] `/api/agent8/recommendations-gemini` → API key required ✅

- [ ] React component updated
  - [ ] No hardcoded defaults (BAR_DATA, DEFAULT_FORECAST_VALS removed) ✅
  - [ ] State initialized to empty arrays ✅
  - [ ] Data loading from real API endpoints ✅

### 🔐 Secrets & Configuration
- [ ] Gemini API Key
  - [ ] API Key: Set in .env (use real key)
  - [ ] Billing: Active on Google Cloud
  - [ ] Quota: Available

- [ ] Trino Connection
  - [ ] Host: `trino-prod.healthrx.co.in`
  - [ ] User: `vasu.verma`
  - [ ] Password: Secure
  - [ ] Network Access: Configured

### 📦 Dependencies
- [ ] requirements.txt updated with production packages
  - [ ] `gunicorn==21.2.0` ✅
  - [ ] `psycopg2-binary==2.9.9` ✅
  - [ ] `google-generativeai==0.3.0` ✅

- [ ] Procfile created for Railway ✅
- [ ] runtime.txt specifies Python 3.11.7 ✅

### 🗄️ Database
- [ ] Supabase project created
  - [ ] Project Name: `agent8-production`
  - [ ] Database: PostgreSQL
  - [ ] Connection String: Copied

- [ ] Database Schema Initialized
  - [ ] professional_metrics table created
  - [ ] Indexes created
  - [ ] Backup configured

---

## Deployment Steps

### Step 1: GitHub Setup
```bash
cd C:\Users\muskan.rao\Documents\claude\agent8-unified-portal
git init
git add .
git commit -m "Agent 8 Production Setup - Ready for Deployment"
git remote add origin https://github.com/YOUR_USERNAME/agent8-unified-portal.git
git push -u origin main
```

- [ ] Repository created
- [ ] Code pushed to GitHub

### Step 2: Railway Deployment
- [ ] Go to https://railway.app
- [ ] Login with GitHub
- [ ] Create new project → Deploy from GitHub
- [ ] Select `agent8-unified-portal` repository
- [ ] Wait for build to complete

**Railway Environment Variables** (in Railway Dashboard):
```
FLASK_ENV=production
FLASK_DEBUG=False
TRINO_HOST=trino-prod.healthrx.co.in
TRINO_PORT=443
TRINO_USER=vasu.verma
TRINO_PASSWORD=YOUR_TRINO_PASSWORD
TRINO_CATALOG=deltalake
DATABASE_URL=postgresql://user:password@db.supabase.co:5432/postgres
USE_POSTGRES=true
GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
DIETICIAN_QA_BACKEND=https://consultation-call-quality-analysis-system.onrender.com
```

- [ ] Environment variables set on Railway
- [ ] Build succeeds
- [ ] Railway URL obtained: `https://agent8-unified-portal-production.railway.app`

### Step 3: Test Backend
```bash
# Test capacity analysis endpoint
curl https://agent8-unified-portal-production.railway.app/api/agent8/capacity-analysis?start_date=2026-07-24&end_date=2026-08-03

# Test Gemini endpoint (if billing active)
curl https://agent8-unified-portal-production.railway.app/api/agent8/recommendations-gemini?start_date=2026-07-01&end_date=2026-07-28
```

- [ ] Capacity analysis returns data ✅
- [ ] Peak hours returns real booking data ✅
- [ ] Gemini endpoint responds (with AI or error handling) ✅

### Step 4: Vercel Frontend Deployment
- [ ] Update `clinical-dashboard/.env.production`:
  ```
  REACT_APP_API_URL=https://agent8-unified-portal-production.railway.app/api/agent8
  ```

- [ ] Go to https://vercel.com
- [ ] Import GitHub repository
- [ ] Set environment variable:
  ```
  REACT_APP_API_URL=https://agent8-unified-portal-production.railway.app/api/agent8
  ```
- [ ] Deploy
- [ ] Vercel URL obtained: `https://agent8-unified-portal.vercel.app`

- [ ] Frontend deployed
- [ ] Environment variables set on Vercel
- [ ] Build succeeds

### Step 5: Verify Production
- [ ] Open dashboard: https://agent8-unified-portal.vercel.app
- [ ] Utilization tab loads ✅
- [ ] Real data displays ✅
- [ ] All sections working:
  - [ ] Capacity Analysis
  - [ ] Demand Forecast
  - [ ] Peak Hours
  - [ ] QA Analytics
  - [ ] Historical Trends

---

## Post-Deployment

### 🔍 Monitoring
- [ ] Railway: Enable performance monitoring
- [ ] Vercel: Check build analytics
- [ ] Set up alerts for errors

### 📊 Data Validation
- [ ] Test with real date ranges
- [ ] Verify data matches Trino
- [ ] Check QA scores from production system

### 🔄 Backup & Recovery
- [ ] Supabase: Verify daily backups enabled
- [ ] GitHub: Ensure code is backed up
- [ ] Document rollback procedure

---

## Production URLs (After Deployment)

| Service | URL |
|---------|-----|
| Dashboard | https://agent8-unified-portal.vercel.app |
| Backend API | https://agent8-unified-portal-production.railway.app |
| Database | Supabase (PostgreSQL) |
| Monitoring | Railway Dashboard + Vercel Dashboard |

---

## Success Criteria ✅

- [ ] Dashboard loads without errors
- [ ] All endpoints return real data
- [ ] No mock/hardcoded data in production
- [ ] Gemini API working (if billing active)
- [ ] Database connected and storing metrics
- [ ] Performance acceptable (< 2s response time)
- [ ] No console errors
- [ ] Mobile responsive
- [ ] All tabs functional

---

## Ready to Deploy?

**You have:**
✅ Cleaned up all mock data
✅ Updated React component
✅ Configured production files
✅ Gemini API key ready
✅ Deployment guides created

**Next: Deploy to production! 🚀**
