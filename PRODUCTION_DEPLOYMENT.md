# Production Deployment: Agent 8 Portal + Call Quality Analysis

## 🚀 Deployment Plan (Aug 5, 2026)

### Phase 1: GitHub Setup (5 minutes)

```bash
# 1. Initialize git in Agent 8 project
cd C:\Users\muskan.rao\Documents\claude\agent8-unified-portal
git init
git add .
git commit -m "Agent 8 Portal with integrated Call Quality Analysis"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/agent8-unified-portal.git
git push -u origin main
```

### Phase 2: Backend Deployment to Render (15 minutes)

**Backend Setup:**
1. Create `Procfile` in agent8-unified-portal root:
```
web: python app.py
```

2. Update `app.py` to use PORT env var:
```python
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
```

3. Deploy to Render:
   - Go to https://render.com
   - New → Web Service
   - Connect GitHub repo: `agent8-unified-portal`
   - Environment: Python
   - Build: `pip install -r requirements.txt`
   - Start: `python app.py`
   - Plan: Free ($0)
   - Add environment variables:
     ```
     FLASK_ENV=production
     FLASK_DEBUG=False
     PORT=8000
     TRINO_HOST=trino-prod.healthrx.co.in
     TRINO_PORT=443
     TRINO_USER=<your_user>
     TRINO_PASSWORD=<your_password>
     TRINO_CATALOG=deltalake
     USE_POSTGRES=true
     DATABASE_URL=postgresql://<user>:<pass>@<host>:<port>/db
     GEMINI_API_KEY=<your_key>
     DIETICIAN_QA_BACKEND=https://consultation-call-quality-analysis-system.onrender.com
     ```

4. Note the Render URL: `https://agent8-backend-xxx.onrender.com`

### Phase 3: Frontend Deployment to Vercel (10 minutes)

1. Update `clinical-dashboard/.env.production`:
```
REACT_APP_API_URL=https://agent8-backend-xxx.onrender.com/api/agent8
```

2. Deploy to Vercel:
   - Go to https://vercel.com
   - Import project: `agent8-unified-portal`
   - Root directory: `clinical-dashboard`
   - Environment variables:
     ```
     REACT_APP_API_URL=https://agent8-backend-xxx.onrender.com/api/agent8
     ```
   - Deploy

3. Note the Vercel URL: `https://agent8-portal.vercel.app`

### Phase 4: Database Setup (10 minutes)

**PostgreSQL (Free Options):**

**Option A: Neon (Recommended)**
1. Go to https://neon.tech
2. Sign up (free tier: 3 GB)
3. Create project: `agent8-prod`
4. Get connection string
5. Add to Render backend:
   ```
   DATABASE_URL=postgresql://user:password@ep-xxx.us-west-2.aws.neon.tech/neondb?sslmode=require
   ```

**Option B: Render PostgreSQL**
1. In Render dashboard: New → PostgreSQL
2. Free tier ($0)
3. Get internal connection string
4. Add to Render backend

### Phase 5: Verify Live (10 minutes)

**Test Backend API:**
```bash
curl https://agent8-backend-xxx.onrender.com/api/agent8/dashboard
```

**Test Frontend:**
1. Open https://agent8-portal.vercel.app
2. Click "Call Quality Analysis"
3. Test each sub-tab (Dashboard, Upload, Transcriptions, etc.)
4. Verify real data loads from API

### Phase 6: Configure Custom Domain (Optional)

**For Agent 8 Backend:**
- Render → Settings → Add custom domain: `api.yourdomain.com`
- Update DNS records

**For Agent 8 Frontend:**
- Vercel → Settings → Domains → Add: `app.yourdomain.com`
- Update DNS records

---

## 📋 Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] PostgreSQL database created (Neon or Render)
- [ ] Backend deployed to Render
  - [ ] Environment variables set
  - [ ] API endpoints responding
- [ ] Frontend deployed to Vercel
  - [ ] Environment variables set
  - [ ] Dashboard loads
- [ ] Call Quality Analysis tabs tested
  - [ ] Dashboard loads
  - [ ] Upload works
  - [ ] Transcriptions display
  - [ ] Reports show data
  - [ ] Alerts visible
- [ ] QA Backend API accessible
- [ ] Custom domains configured (optional)

---

## 🔗 Production URLs

| Service | URL |
|---------|-----|
| **Agent 8 Frontend** | https://agent8-portal.vercel.app |
| **Agent 8 Backend** | https://agent8-backend-xxx.onrender.com |
| **QA Portal Frontend** | https://consultation-call-quality-analysis-system.onrender.com |
| **QA Portal Backend** | https://consultation-call-quality-analysis-system.onrender.com/api |

---

## 🆘 Troubleshooting

**Backend not connecting to Trino:**
- Verify TRINO_* env vars on Render
- Check IP whitelist on Trino server

**QA Portal not loading in Agent 8:**
- Verify DIETICIAN_QA_BACKEND URL on Render
- Check browser console for CORS errors

**Database connection fails:**
- Test connection string locally
- Verify PostgreSQL is running
- Check firewall rules

---

## ⏱️ Total Deployment Time: ~50 minutes

Ready to deploy? Follow Phase 1-6 above! 🚀
