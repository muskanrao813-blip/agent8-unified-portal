# Production Deployment: Vercel + Render (FREE TIER)

## 🏗️ Architecture
- **Frontend**: Vercel (React Dashboard) — FREE
- **Backend**: Render (Flask API) — FREE  
- **Database**: Render PostgreSQL (FREE) or Neon (FREE with 3GB)
- **AI Agent**: Gemini API (FREE tier)

**Why this stack:**
- Vercel: Unlimited free deployments, serverless React
- Render: Free backend tier (auto-deploys from GitHub)
- Both have generous free limits for this workload
- No credit card required (or minimal charges only)

---

## Step 1: GitHub Setup

### 1.1 Create GitHub Repository
1. Go to https://github.com/new
2. Create repo: `agent8-unified-portal`
3. **Don't** initialize with README (we'll push existing code)

### 1.2 Push Code to GitHub
```powershell
cd C:\Users\muskan.rao\Documents\claude\agent8-unified-portal

git init
git add .
git commit -m "Initial commit: Agent 8 Unified Portal with React dashboard and Flask backend"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/agent8-unified-portal.git
git push -u origin main
```

---

## Step 2: Render Backend Deployment

### 2.1 Create Render Account
1. Go to https://render.com
2. Sign up (free account)
3. Connect GitHub account

### 2.2 Create PostgreSQL Database (FREE)
1. Go to Render Dashboard → **New +** → **PostgreSQL**
2. Fill in:
   - **Name**: `agent8-postgres`
   - **Database**: `agent8_db`
   - **User**: `agent8_user`
   - **Region**: Choose closest to you
   - **Plan**: **Free** ($0/month)
3. Click **Create Database**
4. Wait 2-3 minutes for creation
5. Copy the **Internal Database URL** (you'll need this)

**Database URL format:**
```
postgresql://agent8_user:PASSWORD@agent8-postgres.c.render.com/agent8_db
```

### 2.3 Create Backend Service on Render
1. Go to Render Dashboard → **New +** → **Web Service**
2. Select **Deploy from GitHub repository**
3. Choose your `agent8-unified-portal` repo
4. Fill in:
   - **Name**: `agent8-backend`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: **Free** ($0/month)
5. Click **Advanced** and add Environment Variables:

```
FLASK_ENV=production
FLASK_DEBUG=False
PORT=8000

# Database
DATABASE_URL=postgresql://agent8_user:PASSWORD@agent8-postgres.c.render.com/agent8_db
USE_POSTGRES=true

# Trino (Production)
TRINO_HOST=trino-prod.healthrx.co.in
TRINO_PORT=443
TRINO_USER=your_trino_user
TRINO_PASSWORD=your_trino_password
TRINO_CATALOG=deltalake

# Gemini API (FREE tier)
GEMINI_API_KEY=your_gemini_api_key

# Dietician QA Backend (Render instance)
DIETICIAN_QA_BACKEND=https://consultation-call-quality-analysis-system.onrender.com
```

6. Click **Create Web Service**
7. **Wait 5-10 minutes** for deployment
8. Once deployed, copy your URL: `https://agent8-backend-xxxx.onrender.com`

### 2.4 Test Backend is Running
```bash
curl https://agent8-backend-xxxx.onrender.com/api/agent8/dashboard
```

Expected: JSON response ✅

---

## Step 3: Vercel Frontend Deployment

### 3.1 Create Vercel Account
1. Go to https://vercel.com
2. Sign up (free account)
3. Click **Import** → Select your GitHub repo: `agent8-unified-portal`

### 3.2 Configure Build Settings
In Vercel import dialog:
- **Framework Preset**: React
- **Root Directory**: `clinical-dashboard`
- **Build Command**: `npm run build`
- **Output Directory**: `build`

### 3.3 Add Environment Variables
Click **Environment Variables** and add:
```
REACT_APP_API_URL=https://agent8-backend-xxxx.onrender.com/api/agent8
```

(Replace `agent8-backend-xxxx` with your actual Render URL)

### 3.4 Deploy
Click **Deploy** and wait 2-3 minutes.

Once done, you'll get a URL like: `https://agent8-unified-portal.vercel.app`

---

## Step 4: Verify Production Deployment

### Test Backend API
```bash
curl https://agent8-backend-xxxx.onrender.com/api/agent8/dashboard?start_date=2026-07-01&end_date=2026-08-05
```

Expected: `{"kpis": [...], "professionals": [...]}` ✅

### Test Frontend
Open: `https://agent8-unified-portal.vercel.app`

Expected: Dashboard loads with real data ✅

### Test Recommendations Endpoint
```bash
curl https://agent8-backend-xxxx.onrender.com/api/agent8/recommendations?start_date=2026-07-01&end_date=2026-08-05
```

Expected: AI-generated recommendations (if Gemini billing active) ✅

---

## Step 5: Add Custom Domain (Optional)

### Vercel Custom Domain
1. Go to Vercel → Project Settings → Domains
2. Add your domain: `app.yourdomain.com`
3. Update DNS records as instructed

### Render Custom Domain
1. Go to Render → Backend Service → Settings
2. Add custom domain: `api.yourdomain.com`
3. Update DNS records as instructed

---

## 📊 Deployment Checklist

- [ ] GitHub repository created and code pushed
- [ ] Render PostgreSQL database created
- [ ] Backend deployed to Render
- [ ] Environment variables set on Render
- [ ] Frontend deployed to Vercel
- [ ] Environment variables set on Vercel
- [ ] Backend API tested (returns JSON)
- [ ] Frontend loads (http://localhost:3000 or Vercel URL)
- [ ] Dashboard shows real data from Render backend
- [ ] Gemini recommendations working (if API key added)

---

## 🔗 Production URLs

| Service | URL |
|---------|-----|
| **Frontend** | `https://agent8-unified-portal.vercel.app` |
| **Backend API** | `https://agent8-backend-xxxx.onrender.com` |
| **Database** | Render PostgreSQL (private) |

---

## ⚡ Free Tier Limits & Warnings

### Vercel Free Tier
- ✅ Unlimited deployments
- ✅ Unlimited preview URLs
- ✅ 12 function invocations/sec
- ⚠️ Functions timeout after 10s

### Render Free Tier
- ✅ Unlimited services
- ✅ Auto-deploys from GitHub
- ⚠️ **Spins down after 15 min inactivity** (cold start ~30s next request)
- ⚠️ PostgreSQL database also spins down
- ⚠️ **Upgrade to Starter ($7/month) to keep always-on**

### Solution for Spun-Down Services
To prevent spin-down, upgrade to Starter plan ($7/month total):
1. Go to Render → Service → Settings
2. Change Plan from **Free** to **Starter**
3. This keeps the service always running

**Alternative**: Use a free uptime monitor to ping every 14 min (prevents spin-down):
```
https://uptimerobot.com (Free tier)
URL to ping: https://agent8-backend-xxxx.onrender.com/api/agent8/dashboard
```

---

## 🆘 Troubleshooting

### Backend Deployment Failed
**Check Logs:**
1. Go to Render → Deployments
2. Click latest deployment
3. Scroll down to see error messages

**Common Issues:**
- Missing `requirements.txt` → Add all Python packages
- `PORT` not set → Render requires PORT env var
- Trino credentials invalid → Update TRINO_* vars

### Frontend Shows "API Error"
1. Check browser console (F12 → Console)
2. Verify `REACT_APP_API_URL` is set correctly in Vercel
3. Test API directly: `curl https://agent8-backend-xxxx.onrender.com/api/agent8/dashboard`
4. Check CORS is enabled in `app.py` (it is)

### Render Service Keeps Spinning Down
- Upgrade to Starter plan ($7/month), or
- Set up UptimeRobot to ping every 14 min

### Database Connection Fails
- Verify `DATABASE_URL` on Render
- Check Render PostgreSQL is still active
- Test locally: Can you `psql DATABASE_URL`?

---

## 📝 Post-Deployment Monitoring

1. **Set Up Alerts**
   - Vercel: Enable analytics in project settings
   - Render: Set up email notifications for deployments

2. **Monitor Performance**
   - Vercel Dashboard → Analytics
   - Render Dashboard → Metrics

3. **Update Secrets Periodically**
   - Rotate Gemini API key every 90 days
   - Rotate Trino credentials if needed

4. **Keep Render Service Awake**
   - Either pay for Starter ($7/month)
   - Or set up free UptimeRobot ping

---

## 🚀 Deploy Now Steps Summary

### In 5 Minutes:
1. Push code to GitHub (4 min)
2. Create Render PostgreSQL (2 min)
3. Deploy backend to Render (5 min wait)
4. Deploy frontend to Vercel (3 min wait)
5. Update Vercel env var with Render URL (1 min)

**Total: ~15 minutes hands-on time**

---

## Next Steps

Once deployed, I can help with:
- ✅ Custom domain setup
- ✅ SSL certificates (auto-provisioned)
- ✅ Performance optimization
- ✅ Database backup strategy
- ✅ Uptime monitoring
- ✅ Auto-redeploy on git push

Ready to deploy? 🚀
