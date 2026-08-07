# PostgreSQL Setup - FREE Options

## No Cost - Choose Your Option

### Option A: Local PostgreSQL (Completely Free + Fastest)

**Windows Installation (5 min)**

1. Download PostgreSQL 15+ from: https://www.postgresql.org/download/windows/
2. Run installer
3. Set password for "postgres" user (remember this!)
4. Default port: 5432
5. Installation complete!

**Create Database & Table**

```bash
# Open command prompt or PowerShell
psql -U postgres

# Inside psql prompt:
CREATE DATABASE agent8_db;
\c agent8_db

CREATE TABLE professional_metrics (
    id SERIAL PRIMARY KEY,
    provider_name TEXT NOT NULL,
    cohort TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    appts_count INTEGER DEFAULT 0,
    capacity INTEGER DEFAULT 0,
    utilization_pct FLOAT DEFAULT 0,
    qa_score FLOAT DEFAULT 0,
    improvement_score FLOAT DEFAULT 0,
    improvement_total INTEGER DEFAULT 0,
    status TEXT DEFAULT 'NA',
    forecast_7d INTEGER DEFAULT 0,
    patient_count INTEGER DEFAULT 0,
    with_lab_data INTEGER DEFAULT 0,
    without_lab_data INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(provider_name, start_date, end_date)
);

CREATE INDEX idx_date_range ON professional_metrics(start_date, end_date);
CREATE INDEX idx_provider ON professional_metrics(provider_name);

# Verify table created:
\dt

# Exit:
\q
```

**Configure .env**

```env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/agent8_db
```

Replace `YOUR_PASSWORD` with the password you set during installation.

---

### Option B: Render.com (Free Tier - Cloud)

**Free tier includes:**
- PostgreSQL database
- 256 MB storage (fits 50k+ metric records)
- No credit card needed

**Setup (5 min)**

1. Go to https://render.com
2. Sign up (free account)
3. Click "New +" → "PostgreSQL"
4. Database name: `agent8_db`
5. Region: US East (closest to your location)
6. Pricing Plan: **Free**
7. Click "Create Database"
8. Wait 1-2 minutes for creation
9. Copy connection string from "Connections" section

**Configure .env**

```env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://username:password@host:5432/agent8_db
```

The DATABASE_URL will be provided by Render. Just paste it!

**Create Table**

- Go to Render dashboard
- Click your database
- Click "Query"
- Paste SQL from "Local PostgreSQL" section above
- Execute

---

### Option C: Neon.tech (Free Tier - Cloud)

**Free tier includes:**
- PostgreSQL database
- 3 GB storage (excellent!)
- No credit card needed
- Auto-pause after 7 days inactivity

**Setup (5 min)**

1. Go to https://neon.tech
2. Sign up (free account)
3. Create project "agent8"
4. Region: US East 1
5. Click "Create project"
6. Copy connection string from "Connection strings" section

**Configure .env**

```env
DATABASE_TYPE=postgresql
DATABASE_URL=postgres://user:password@host/database
```

Just paste the connection string!

**Create Table**

- In Neon dashboard, click "SQL Editor"
- Paste SQL from "Local PostgreSQL" section
- Execute

---

### Option D: Railway.app (Free Tier - Cloud)

**Free tier includes:**
- PostgreSQL database
- $5/month credit (actually free for small usage)
- No credit card required

**Setup (5 min)**

1. Go to https://railway.app
2. Sign up with GitHub
3. Create new project
4. Add → Provision PostgreSQL
5. Wait 30 seconds
6. Go to "Connect" tab
7. Copy connection string

**Configure .env**

```env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@host:port/database
```

Just paste!

---

## Testing Connection

After setting up, test that it works:

```bash
# With your DATABASE_URL configured in .env
python -c "
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(url)
print('✓ PostgreSQL Connected!')
conn.close()
"
```

Should print: `✓ PostgreSQL Connected!`

---

## Comparison

| Feature | Local | Render | Neon | Railway |
|---------|-------|--------|------|---------|
| Cost | FREE | FREE | FREE | FREE |
| Setup Time | 10 min | 5 min | 5 min | 5 min |
| Storage | Unlimited | 256 MB | 3 GB | 3 GB |
| Backup | Manual | Automatic | Automatic | Automatic |
| Access | Local only | Cloud | Cloud | Cloud |
| Best For | Development | Testing | Production | Production |

**Recommendation:** Start with **Neon.tech** (3 GB, easiest setup, auto-backups)

---

## Troubleshooting

**"Connection refused" error**
- Local: Check PostgreSQL service is running (Windows Services → postgresql)
- Cloud: Copy-paste connection string exactly (no extra spaces)

**"Database does not exist"**
- Connection string points to wrong database
- Verify database name matches what you created

**"Authentication failed"**
- Wrong password in LOCAL setup
- Wrong credentials in connection string (CLOUD)
- Copy-paste the exact connection string!

**"Table does not exist"**
- SQL from setup wasn't executed
- Re-run the CREATE TABLE SQL in your database tool

---

## Start Using It

1. Set DATABASE_TYPE and DATABASE_URL in .env
2. Restart Flask: `python app.py`
3. Logs will show: `[DB] Connected to PostgreSQL`
4. Run batch: `curl -X POST http://localhost:5001/api/agent8/batch-calculate ...`
5. Check dashboard: `http://localhost:3000`

That's it! PostgreSQL is now handling all data storage with ZERO cost.

---

## Scaling Later

If you outgrow free tier:
- **Neon:** $0.16/GB/month after 3 GB
- **Render:** Pay as you go (~$10/month typical)
- **Railway:** $5 credit covers ~$50 usage
- **Local:** Upgrade to dedicated server (~$20/month on DigitalOcean/Linode)

All options are significantly cheaper than managed services!
