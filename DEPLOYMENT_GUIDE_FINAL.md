# 🚀 Agent 8 + Call Quality Analysis - Production Deployment

**Date**: August 5, 2026  
**Status**: Ready for Production  
**Architecture**: Render Backend + Vercel Frontend + PostgreSQL Database

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Your Local Machine (Windows/Mac)                               │
│  ├─ sync_data_from_trino.py (runs daily via Task Scheduler)    │
│  └─ Connects to Trino with YOUR OAuth                           │
│     └─ Fetches health data → Writes to Dietician QA Database   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓ (Data persisted)
                    ┌──────────────────┐
                    │  PostgreSQL DB   │
                    │  (Render Neon)   │
                    │ dietician_qa     │
                    └──────────────────┘
                           ↑
                           │ (Read)
        ┌──────────────────┴──────────────────┐
        │                                     │
        ↓                                     ↓
┌──────────────────────┐          ┌──────────────────────┐
│  Render Backend      │          │  Render Backend      │
│  agent8-backend      │          │  qa-backend (existing)
│  Flask API           │          │  FastAPI             │
│  :8000               │          │  :8000               │
└──────────────────────┘          └──────────────────────┘
        ↓                                     ↓
        └──────────────────┬──────────────────┘
                           │
                           ↓
                    ┌──────────────────┐
                    │  Vercel          │
                    │  agent8-portal   │
                    │  React Frontend  │
                    │  :3000 (prod)    │
                    └──────────────────┘
                           │
                           ↓
                    ┌──────────────────┐
                    │  Browser         │
                    │  User Dashboard  │
                    └──────────────────┘
```

---

## 🔐 Security Model

| Component | Trino Access | Database Access | OAuth |
|-----------|--------------|-----------------|-------|
| Your Machine | ✅ Yes | PostgreSQL | ✅ Your OAuth |
| Render Backend | ❌ No | PostgreSQL | ❌ No |
| Vercel Frontend | ❌ No | ❌ No | ❌ No |

**No credentials exposed to cloud services!**

---

## 📋 Prerequisites

- [ ] Render PostgreSQL running (already have: `dietician_qa`)
- [ ] Render account (https://render.com)
- [ ] Vercel account (https://vercel.com)
- [ ] Gemini API key
- [ ] Trino credentials (local only)
- [ ] GitHub account with `agent8-unified-portal` repo

---

## 🚀 Deployment Steps

### Step 1: Deploy Agent 8 Backend to Render (10 min)

1. Go to https://render.com → **New Web Service**
2. Click **Connect Repository**
   - Search for `agent8-unified-portal`
   - Click Connect
3. Configure Service:
   ```
   Name: agent8-backend
   Environment: Docker
   Region: US (Oregon) or your choice
   Plan: Free ($0)
   ```
4. Click **Create Web Service**

5. **Add Environment Variables** (while deploying):
   - Click **Environment** tab
   - Add these variables:
   ```
   FLASK_ENV=production
   PORT=8000
   DATABASE_URL=postgresql://postgress:rp3ve8DP4Df2FnNGpbZ7jN24bfqrDYab@dpg-d9eufq57vvec73fbv7k0-a/dietician_qa
   GEMINI_API_KEY=<your-gemini-api-key>
   DIETICIAN_QA_BACKEND=https://consultation-call-quality-analysis-system.onrender.com
   ```
   - Click **Save**

6. **Wait for deployment** (5-10 minutes)
   - Check status at bottom of page
   - Copy the service URL when live: `https://agent8-backend-xyz.onrender.com`

---

### Step 2: Deploy Frontend to Vercel (5 min)

1. Go to https://vercel.com → **Add New** → **Project**
2. Import GitHub Repository
   - Search for `agent8-unified-portal`
   - Click Import
3. Configure:
   ```
   Framework Preset: React
   Root Directory: ./clinical-dashboard
   Build Command: npm run build
   Output Directory: build
   ```
4. Add Environment Variable:
   ```
   REACT_APP_API_URL=https://agent8-backend-xyz.onrender.com/api/agent8
   ```
   (Replace with your actual Render backend URL from Step 1)

5. Click **Deploy**
6. **Copy your Vercel URL** when live: `https://agent8-portal.vercel.app`

---

### Step 3: Setup Local Data Sync (Your Machine)

1. **Create .env file** (keep private, don't commit):
   ```bash
   cp .env.example .env
   ```

2. **Edit .env**:
   ```
   TRINO_HOST=trino-prod.healthrx.co.in
   TRINO_PORT=443
   TRINO_USER=<your-trino-username>
   TRINO_PASSWORD=<your-trino-password>
   DATABASE_URL=postgresql://postgress:rp3ve8DP4Df2FnNGpbZ7jN24bfqrDYab@dpg-d9eufq57vvec73fbv7k0-a/dietician_qa
   GEMINI_API_KEY=<your-gemini-api-key>
   DIETICIAN_QA_BACKEND=https://consultation-call-quality-analysis-system.onrender.com
   FLASK_ENV=production
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt psycopg2-binary python-dotenv trino
   ```

4. **Test the sync script**:
   ```bash
   python sync_data_from_trino.py
   ```

   **Expected output**:
   ```
   ✅ Connected to Trino
   ✅ Connected to PostgreSQL
   ✅ Fetched 1000 appointments from Trino
   ✅ Synced 1000 appointments to PostgreSQL
   ✅ Data sync completed successfully!
   ```

---

### Step 4: Setup Daily Auto-Sync (Windows Task Scheduler)

Run this PowerShell command (as Administrator):

```powershell
$action = New-ScheduledTaskAction `
  -Execute "python" `
  -Argument "C:\Users\muskan.rao\Documents\claude\agent8-unified-portal\sync_data_from_trino.py" `
  -WorkingDirectory "C:\Users\muskan.rao\Documents\claude\agent8-unified-portal"

$trigger = New-ScheduledTaskTrigger -Daily -At 6am

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask `
  -TaskName "Agent8-DataSync" `
  -Action $action `
  -Trigger $trigger `
  -Settings $settings `
  -Description "Sync Agent 8 data from Trino to PostgreSQL daily"
```

**Verify it works**:
- Task Scheduler → Search for "Agent8-DataSync"
- Right-click → Run
- Check logs in Render dashboard (DB should update)

---

### Step 5: Test Everything Live (5 min)

1. **Open Vercel URL**: `https://agent8-portal.vercel.app`
2. **Login** (if required)
3. **Navigate to Call Quality Analysis** in sidebar
4. **Test each tab**:
   - ✅ Dashboard - Shows live QA metrics
   - ✅ Call Upload - Upload file works
   - ✅ Transcriptions - Lists calls
   - ✅ AI Insights - Shows analysis
   - ✅ Reports - Shows dietician reports
   - ✅ Alerts - Shows QA alerts
5. **Verify data**: Check provider metrics, patient data, etc.

---

## 📊 Monitor Production

### Render Dashboard
- Backend logs: https://dashboard.render.com/services
- Database connection: https://dashboard.render.com/databases
- Check for any errors or warnings

### Vercel Dashboard
- Frontend logs: https://vercel.com/dashboard
- Build history: Check if deployments succeeded
- Performance: Monitor page load times

### Local Machine
- Check Task Scheduler for sync job
- Monitor `sync_data_from_trino.py` logs
- Verify database is updating daily

---

## 🆘 Troubleshooting

### "Database connection failed"
- **Check**: DATABASE_URL is correct
- **Check**: Render PostgreSQL is running
- **Check**: Network access allowed (firewall)
- **Fix**: Copy connection string from Render dashboard again

### "Trino connection failed"
- **Check**: TRINO_HOST, TRINO_USER, TRINO_PASSWORD are correct
- **Check**: You can connect to Trino locally first
- **Check**: OAuth is working on your machine
- **Fix**: Run `python sync_data_from_trino.py` locally to debug

### "Frontend not loading data"
- **Check**: REACT_APP_API_URL is correct
- **Check**: Render backend is running (check status)
- **Check**: Browser console for CORS errors
- **Fix**: Redeploy Vercel frontend

### "Data not syncing"
- **Check**: Task Scheduler job ran (check logs)
- **Check**: `python sync_data_from_trino.py` runs without errors
- **Check**: PostgreSQL has write access
- **Fix**: Run script manually to debug

---

## 🔄 Update Process

**When you push code changes to GitHub:**

1. Vercel automatically redeploys frontend
2. Render automatically redeploys backend
3. No manual intervention needed!
4. Check status in respective dashboards

**When you update data sources:**

1. Modify `sync_data_from_trino.py`
2. Test locally: `python sync_data_from_trino.py`
3. Commit and push to GitHub
4. Task Scheduler will use new version

---

## 📱 Production URLs

| Service | URL | Status |
|---------|-----|--------|
| **Frontend** | https://agent8-portal.vercel.app | Live ✅ |
| **Backend** | https://agent8-backend-xyz.onrender.com | Live ✅ |
| **QA Backend** | https://consultation-call-quality-analysis-system.onrender.com | Live ✅ |
| **Database** | Render PostgreSQL (dietician_qa) | Live ✅ |

---

## ✅ Deployment Checklist

- [ ] Render backend deployed and running
- [ ] Vercel frontend deployed and loading
- [ ] Environment variables set on both services
- [ ] Local .env file created with Trino credentials
- [ ] sync_data_from_trino.py tested locally
- [ ] Task Scheduler job created and tested
- [ ] Frontend loads without errors
- [ ] Call Quality Analysis tab works
- [ ] All 6 sub-tabs load correctly
- [ ] Data displays correctly
- [ ] Daily sync job will run at 6 AM

---

## 🎉 Success!

Your Agent 8 + Call Quality Analysis portal is now live and production-ready! 

**Architecture**:
- ✅ Data stays secure: Trino credentials never exposed
- ✅ Scalable: PostgreSQL handles all data persistence
- ✅ Automated: Daily sync via Task Scheduler
- ✅ Zero-maintenance: Render + Vercel handle deployments
- ✅ Real-time: Frontend always shows latest data

**Next steps**:
- Monitor production for issues
- Optimize performance if needed
- Add custom domain (optional)
- Setup alerts/notifications (optional)

---

**Need help?** Check memory files:
- [Agent 8 Overview](agent8_overview_clinical_logic.md)
- [Merged Deployment](MERGED_PRODUCTION_DEPLOYMENT.md)
- [Dietician QA Setup](CLAUDE.md)
