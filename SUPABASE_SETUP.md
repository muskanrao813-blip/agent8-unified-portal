# Supabase Setup Guide

## Production-Ready PostgreSQL Database for Agent 8

### Quick Setup (5 minutes)

**1. Create Supabase Project**
- Go to https://supabase.com and sign up
- Click "New Project"
- Project name: `agent8-clinical-portal`
- Database password: (save this!)
- Region: `us-east-1` or closest to you
- Wait 2-3 minutes for project to spin up

**2. Get Connection Details**
- In Supabase, go to **Settings → Database → Connection Info**
- Copy:
  - **Project URL** (starts with `https://`)
  - **Anon Public Key** (under "Project API keys")

**3. Create SQL Table**
- In Supabase, click **SQL Editor** (left sidebar)
- Click **New Query**
- Paste this SQL:

```sql
CREATE TABLE professional_metrics (
    id BIGSERIAL PRIMARY KEY,
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
```

- Click **Run**
- Confirm table created ✓

**4. Enable Row Level Security (RLS)**
- Still in SQL Editor, run:

```sql
ALTER TABLE professional_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read" ON professional_metrics
  FOR SELECT USING (true);

CREATE POLICY "Allow public insert" ON professional_metrics
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update" ON professional_metrics
  FOR UPDATE USING (true);

CREATE POLICY "Allow public delete" ON professional_metrics
  FOR DELETE USING (true);
```

**5. Configure Agent 8**
- Create `.env` file in project root:

```env
# Supabase PostgreSQL
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key

# Existing config
TRINO_HOST=trino-prod.healthrx.co.in
TRINO_PORT=443
TRINO_USER=vasu.verma
TRINO_PASSWORD=vvaass6543
```

- Replace `your-project-id` and `your-anon-public-key` with actual values

**6. Restart Backend**
```bash
# Kill Flask
pkill -f "python app.py"

# Start Flask fresh
python app.py
```

- Logs will show: `[SUPABASE] Connected to Supabase PostgreSQL` ✓

**7. Test Batch Calculation**
```bash
curl -X POST http://localhost:5001/api/agent8/batch-calculate \
  -H "Content-Type: application/json" \
  -d '{"start_date":"2026-07-01","end_date":"2026-07-23"}'
```

- Wait 15 seconds
- Check Supabase: **SQL Editor → new query:**

```sql
SELECT COUNT(*) as metric_count FROM professional_metrics;
```

- Should show `26` rows ✓

### What Supabase Solves

✅ **No more SQLite locking**
  - Managed PostgreSQL handles concurrent writes automatically
  - Built-in connection pooling

✅ **Real-time data sync**
  - Supabase Realtime updates dashboard automatically when data changes
  - Can add subscriptions later

✅ **Production-ready**
  - Automatic backups
  - Built-in auth (JWT)
  - REST API auto-generated

✅ **Scalable**
  - Handles millions of records
  - Automatic indexing

### Troubleshooting

**Connection Error: "Invalid API key"**
- Check SUPABASE_KEY is Anon Public Key (not service role key)
- Make sure no extra spaces in .env

**Table creation failed**
- Check that Supabase project Status = "Active" (green checkmark)
- SQL permissions might be limited - use service role key in private API calls

**RLS Policies Error**
- Supabase may have different syntax - check their docs
- Can temporarily disable RLS for testing: `ALTER TABLE professional_metrics DISABLE ROW LEVEL SECURITY;`

### Next: Update app.py to Use db_layer

The backend will automatically detect Supabase configuration and use it.
If SUPABASE_URL/SUPABASE_KEY are set, it uses Supabase.
Otherwise, it falls back to SQLite.

### Costs

**Free tier ($0):**
- Up to 500 MB database
- Sufficient for 50k+ metric records
- Auto-pause if inactive 7+ days

**Usage-based pricing (~$2-5/month):**
- If you exceed free tier
- Per GB beyond 500 MB
- No charge for API calls

Perfect for development and small production deployments!
