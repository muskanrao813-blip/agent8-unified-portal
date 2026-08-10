# Deployment Guide - Agent 8 Unified Portal

## Status
- ✅ Code committed and pushed to GitHub
- ✅ All 3 critical fixes implemented
- ✅ render.yaml configured for Render deployment
- ⏳ Awaiting Render auto-deployment

## Render Deployment (Backend)

### Auto-Deployment
If connected to GitHub repo, Render will auto-deploy when pushing to main branch.

**Service**: agent8-backend
**Region**: Oregon
**Database**: agent8-postgres (Neon PostgreSQL)

### Manual Deployment (if needed)
1. Go to Render Dashboard
2. Select "agent8-backend" service
3. Click "Manual Deploy" > "Deploy latest commit"

### Health Check
```bash
curl https://agent8-backend.onrender.com/api/agent8/health
```
Expected response: `{"status": "ok", "service": "agent8-backend"}`

## Vercel Deployment (Frontend)

### Option A: Serve from Render (Current Setup)
Flask serves the entire app including frontend. No separate Vercel deployment needed.

**URL**: https://agent8-backend.onrender.com/

### Option B: Separate Vercel Deployment
To deploy React frontend separately to Vercel:

1. Build React app:
```bash
cd clinical-dashboard
npm run build
```

2. Push build/ contents to Vercel:
```bash
vercel --prod
```

3. Update API_URL in React app:
```javascript
REACT_APP_API_URL=https://agent8-backend.onrender.com/api/agent8
```

## Fixed Issues

### 1. Improvement Scores (✅ FIXED)
- **Issue**: All improvement_score values = 0
- **Fix**: execute_improvement_mapping.py with month-level date aggregation
- **Result**: 65% average, 88.6% coverage

### 2. Capacity Calculation (✅ FIXED)
- **Issue**: Ambika Rode showed 1,680 capacity (was 1,555 appts, 92.6% util)
- **Fix**: Updated /api/agent8/professionals to use daily_metrics aggregation
- **Result**: 2,100 capacity (1,980 appts, 94.3% util)

### 3. QA Score Sync (✅ READY)
- **Issue**: QA Portal returns 0 scores (no call data)
- **Fix**: Created sync_qa_scores_live.py for live sync
- **Status**: Waiting for QA Portal data; script ready to run

## Production Deployment Checklist

- [x] Code changes committed
- [x] Database migrations applied (professional_daily_metrics table)
- [x] Environment variables set (.env)
- [x] Flask app tested locally
- [x] API endpoints verified working
- [x] render.yaml configured
- [ ] Render deployment triggered
- [ ] Health check passing on production
- [ ] Frontend accessible at production URL
- [ ] All tabs showing correct data

## Next Steps

1. **Monitor Render deployment** - Check if auto-deploy triggered
2. **Verify production data** - Test API endpoints on production
3. **Run daily syncs** - Set up cron jobs for:
   - sync_qa_scores_live.py (daily after QA updates)
   - execute_improvement_mapping.py (weekly refresh)

## Production URLs

- **Backend API**: https://agent8-backend.onrender.com
- **Health Check**: https://agent8-backend.onrender.com/api/agent8/health
- **Dashboard**: https://agent8-backend.onrender.com/

## Troubleshooting

If deployment fails:
1. Check Render build logs for errors
2. Verify DATABASE_URL is set in Render environment
3. Check GEMINI_API_KEY is configured
4. Verify Python dependencies in requirements.txt

If frontend doesn't load:
1. Check Flask templates/index.html exists
2. Verify REACT_APP_API_URL points to correct backend
3. Check browser console for API errors
