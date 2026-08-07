# Agent 8 - Complete Setup Guide

## ZERO COST - PostgreSQL + SQLite

The system now supports **free** database options:
- **PostgreSQL** (Cloud or Local) - Recommended
- **SQLite** (Built-in) - No setup needed

---

## Quick Start (5 minutes)

### Option 1: PostgreSQL - Easiest (Neon.tech Cloud)

**Step 1: Create Database**
- Go to https://neon.tech
- Sign up (free, no credit card)
- Create project "agent8"
- Copy connection string

**Step 2: Configure .env**
```env
DATABASE_TYPE=postgresql
DATABASE_URL=<paste_neon_connection_string_here>
TRINO_HOST=trino-prod.healthrx.co.in
TRINO_PORT=443
TRINO_USER=vasu.verma
TRINO_PASSWORD=vvaass6543
```

**Step 3: Start System**
```bash
python app.py
# Logs: [DB-POSTGRES] Schema initialized
```

**Step 4: Run Batch Calculation**
```bash
curl -X POST http://localhost:5001/api/agent8/batch-calculate \
  -H "Content-Type: application/json" \
  -d '{"start_date":"2026-07-01","end_date":"2026-07-23"}'
```

**Step 5: Open Dashboard**
```
http://localhost:3000
```

✓ Done! All data persists in PostgreSQL, NO COST.

---

### Option 2: SQLite (No Setup)

If you prefer no cloud setup:

```bash
# Just set this in .env
DATABASE_TYPE=sqlite

# Or don't create .env at all - SQLite is the default
```

⚠️ Note: SQLite has locking issues with concurrent writes. PostgreSQL recommended.

---

## Detailed Setup by Database Type

### PostgreSQL: Local Installation

1. **Install PostgreSQL** (Windows)
   - Download: https://www.postgresql.org/download/windows/
   - Run installer
   - Set password for "postgres" user
   - Port: 5432 (default)

2. **Create Database**
   ```bash
   psql -U postgres
   
   # Inside psql:
   CREATE DATABASE agent8_db;
   \c agent8_db
   
   # Paste entire SQL from POSTGRES_SETUP.md
   # (includes CREATE TABLE and indexes)
   
   \q
   ```

3. **Configure .env**
   ```env
   DATABASE_TYPE=postgresql
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/agent8_db
   ```
   Replace YOUR_PASSWORD with your chosen password

4. **Test Connection**
   ```bash
   python -c "
   import os, psycopg2
   from dotenv import load_dotenv
   load_dotenv()
   conn = psycopg2.connect(os.getenv('DATABASE_URL'))
   print('✓ PostgreSQL Connected!')
   conn.close()
   "
   ```

---

### PostgreSQL: Cloud (Neon.tech - Recommended)

1. **Create Account**
   - Go to https://neon.tech
   - Sign up (free)
   - Create project "agent8"

2. **Get Connection String**
   - Dashboard → Connections
   - Copy PostgreSQL connection string

3. **Configure .env**
   ```env
   DATABASE_TYPE=postgresql
   DATABASE_URL=<paste_connection_string>
   ```

4. **Tables Created Automatically**
   - App initializes schema on first run
   - No manual SQL needed!

---

### PostgreSQL: Other Free Cloud Options

See **POSTGRES_SETUP.md** for:
- **Render.com** (256 MB free)
- **Railway.app** ($5 credit free)

All have same setup process:
1. Create account (free)
2. Create PostgreSQL database
3. Copy connection string
4. Paste into .env as DATABASE_URL
5. Done!

---

## System Architecture

```
┌─────────────────────────────────────────┐
│        Flask Backend (app.py)            │
├─────────────────────────────────────────┤
│                                          │
│  batch-calculate endpoint                │
│        ↓                                  │
│  store_professional_metric()             │
│        ↓                                  │
│  db_layer.py (Smart Router)              │
│  ├─ if DATABASE_TYPE=postgresql          │
│  │  └─ → psycopg2.connect()              │
│  └─ else                                 │
│     └─ → sqlite3.connect()               │
│        ↓                                  │
│  ┌──────────────────────────────┐        │
│  │   PostgreSQL or SQLite       │        │
│  │   professional_metrics table │        │
│  └──────────────────────────────┘        │
│                                          │
└─────────────────────────────────────────┘
        ↓
Frontend queries /api/agent8/professionals
        ↓
Data displays on dashboard
```

---

## Database Comparison

| Feature | SQLite | PostgreSQL Local | PostgreSQL Cloud |
|---------|--------|------------------|-----------------|
| Cost | $0 | $0 | $0 (free tier) |
| Setup Time | 0 min | 10 min | 5 min |
| Performance | Good | Excellent | Excellent |
| Concurrent Writes | Issues ⚠️ | Perfect ✓ | Perfect ✓ |
| Storage Limit | ~50k records | Unlimited | 256 MB - 3 GB |
| Backups | Manual | Manual | Automatic ✓ |
| Scaling | Hard | Easy | Easy |
| **Recommended** | Development | Development | **Production** |

---

## What Changed

**Old System (SQLite):**
- ❌ Database locking on batch writes
- ❌ NameError about 'providers_data'
- ❌ Data not persisting
- ❌ No production-ready option

**New System (PostgreSQL + SQLite):**
- ✅ Concurrent writes work automatically
- ✅ Robust error handling in db_layer
- ✅ Data persists reliably
- ✅ Free cloud option available
- ✅ Optional local setup
- ✅ Auto-schema initialization

---

## Files Updated

1. **db_layer.py** — Updated to support PostgreSQL + SQLite
2. **app.py** — Uses db_layer, initializes schema
3. **.env.example** — PostgreSQL configuration template
4. **POSTGRES_SETUP.md** — Complete PostgreSQL setup guide

---

## Testing Steps

1. **Setup Database** (5 min - pick one):
   - Local PostgreSQL, OR
   - Neon.tech free tier, OR
   - Use SQLite (default)

2. **Configure .env** (1 min)
   - Copy .env.example → .env
   - Add DATABASE_URL if using PostgreSQL

3. **Start Backend** (1 min)
   ```bash
   python app.py
   # Should show: [DB] Connected to PostgreSQL
   # Or: Using SQLite (if not configured)
   ```

4. **Run Batch** (30 sec)
   ```bash
   curl -X POST http://localhost:5001/api/agent8/batch-calculate \
     -H "Content-Type: application/json" \
     -d '{"start_date":"2026-07-01","end_date":"2026-07-23"}'
   ```

5. **Check Dashboard** (immediate)
   - Open http://localhost:3000
   - Should see data on Overview tab
   - Clinical Outcomes shows 1-year date range

6. **Verify Data Persistence** (1 min)
   - PostgreSQL: Check via Neon/psql
   - SQLite: `python -c "import sqlite3; c = sqlite3.connect('metrics_cache.db'); print(c.execute('SELECT COUNT(*) FROM professional_metrics').fetchone())"`
   - Should show: 26 rows (one per dietician)

---

## Troubleshooting

**"Connection refused" (PostgreSQL)**
- Local: PostgreSQL service not running
  - Windows: Services → postgresql → Start
- Cloud: Wrong connection string
  - Copy-paste exactly, no extra spaces

**"Table does not exist"**
- App should auto-create table on startup
- If not, manually run SQL from POSTGRES_SETUP.md

**"Database is locked" (SQLite)**
- Use PostgreSQL instead (solves this)
- Or restart Flask and retry batch

**App still shows "[DB] Using SQLite"**
- Check .env file exists and is in project root
- Verify DATABASE_TYPE=postgresql is set
- Restart Flask: `pkill -f "python app.py"` then `python app.py`

---

## Next Steps

1. ✅ Choose PostgreSQL (cloud) or SQLite (quick test)
2. ✅ Configure .env (if PostgreSQL)
3. ✅ Run batch calculation
4. ✅ View data on dashboard
5. ✅ Celebrate - system is working!

**Everything is FREE and production-ready!**

Questions? See POSTGRES_SETUP.md for detailed options.
