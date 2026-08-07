# Option B: Full System Integration Plan

## 🎯 Goal
Merge Dietician QA Portal into Agent 8 to create **ONE unified Clinical Operations Intelligence Platform**

```
BEFORE (2 Systems):
├── Agent 8 Portal (Clinical Operations)
└── Dietician QA Portal (Quality Management)

AFTER (1 System):
└── Clinical Operations Intelligence Portal
    ├── Clinical Operations (Agent 8 features)
    └── Quality Management (QA features - fully integrated)
```

---

## 📋 Integration Checklist

### Phase 1: Extract QA Portal React Components (Week 1, Days 1-2)

**Components to Extract from `dietician-qa/clinical-intelligence-system/src/components/`:**

1. **CallUploadView.tsx** → `clinical-dashboard/src/pages/quality/CallUpload.jsx`
   - Excel file upload interface
   - Batch processing UI
   - Status tracking

2. **TranscriptionsView.tsx** → `clinical-dashboard/src/pages/quality/Transcriptions.jsx`
   - Transcript display
   - Claude reconstruction visualization
   - Entity extraction view

3. **DashboardView.tsx** → `clinical-dashboard/src/pages/quality/QADashboard.jsx`
   - Call quality metrics
   - Provider performance overview
   - Key statistics

4. **DieticianReportsView.tsx** → `clinical-dashboard/src/pages/quality/DieticianAnalytics.jsx`
   - Individual provider QA scores
   - Performance ranking
   - Trend analysis
   - Coaching recommendations

5. **QAAlertsView.tsx** → `clinical-dashboard/src/pages/quality/QAAlerts.jsx`
   - SOP compliance violations
   - Critical/warning flags
   - Alert management

6. **AIInsightsView.tsx** → `clinical-dashboard/src/pages/quality/AIInsights.jsx`
   - AI-generated recommendations
   - Improvement suggestions
   - Pattern analysis

**Utilities to Extract:**

7. **useClinicalAPI.ts** → `clinical-dashboard/src/hooks/useClinicalAPI.ts`
   - API integration hook for QA endpoints
   - Data fetching and caching

8. **Types & Constants**
   - Copy TypeScript types
   - Copy API endpoint constants
   - Copy utility functions

**What to Do:**
- [ ] Copy components from TypeScript to JavaScript (`.tsx` → `.jsx`)
- [ ] Update imports to match Agent 8 structure
- [ ] Replace QA backend URL with unified API URL
- [ ] Remove/adapt Sidebar (use Agent 8's unified sidebar)
- [ ] Test each component individually

### Phase 2: Migrate QA Backend to Flask (Week 1, Days 3-5)

**Python Files to Migrate from `dietician-qa/app/`:**

1. **Services Layer** → `agent8-backend/services/qa/`
   ```
   app/services/transcription/*.py → services/qa/transcription/
   app/services/llm/*.py → services/qa/llm/
   app/services/pipeline.py → services/qa/pipeline.py
   app/services/ingestion.py → services/qa/ingestion.py
   ```

2. **Models/Schemas** → `agent8-backend/models/`
   ```
   - Call schema
   - Transcript schema
   - QA Score schema
   - QA Flag schema
   - Entities schema
   ```

3. **Database Layer** → `agent8-backend/db/`
   ```
   - Database models for calls, transcripts, qa_scores, qa_flags
   - Migrations for Supabase
   - Query functions
   ```

4. **API Routes** → `app.py` (add `/api/qa/*` routes)
   ```python
   @app.route('/api/qa/calls', methods=['GET', 'POST'])
   @app.route('/api/qa/calls/<call_id>', methods=['GET'])
   @app.route('/api/qa/calls/bulk-upload', methods=['POST'])
   @app.route('/api/qa/transcribe/<call_id>', methods=['POST'])
   @app.route('/api/qa/analyze/<call_id>', methods=['POST'])
   @app.route('/api/qa/dashboard/stats', methods=['GET'])
   ```

**Dependencies to Add:**
```
# requirements.txt
uvicorn==0.23.0
fastapi-to-flask==1.0.0  # Adapter if needed
python-multipart==0.0.6
openpyxl==3.11.0
librosa==0.10.0
groq==0.4.0
google-generativeai==0.3.0
```

**What to Do:**
- [ ] Create `/services/qa/` directory structure
- [ ] Copy transcription pipeline (Whisper, Groq, Claude reconstruction)
- [ ] Copy QA analysis engine (Gemini 5-dimensions)
- [ ] Copy entity extraction logic
- [ ] Copy call ingestion (Excel parsing)
- [ ] Create Flask routes mirroring FastAPI endpoints
- [ ] Test each endpoint with sample data

### Phase 3: Database Consolidation (Week 2, Days 1-2)

**Supabase PostgreSQL Schema:**

```sql
-- Existing Agent 8 tables (keep as-is)
-- professional_metrics
-- recommendations
-- etc.

-- NEW: QA System Tables
CREATE TABLE IF NOT EXISTS calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dietician_name VARCHAR(255),
    patient_id VARCHAR(255),
    patient_name VARCHAR(255),
    appointment_id VARCHAR(255),
    recording_url TEXT,
    status VARCHAR(50), -- pending, processing, completed, error
    overall_weighted_score DECIMAL(5,2),
    language VARCHAR(20), -- en, hi
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(appointment_id)
);

CREATE TABLE IF NOT EXISTS transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID REFERENCES calls(id) ON DELETE CASCADE,
    raw_transcript TEXT,
    reconstructed_transcript TEXT,
    provider VARCHAR(100), -- Whisper, Groq, Claude
    workflow_description TEXT,
    entities JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qa_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID REFERENCES calls(id) ON DELETE CASCADE UNIQUE,
    greeting_score DECIMAL(5,2),
    empathy_score DECIMAL(5,2),
    compliance_score DECIMAL(5,2),
    technical_score DECIMAL(5,2),
    clinical_safety_score DECIMAL(5,2),
    overall_weighted_score DECIMAL(5,2),
    sop_violations JSONB,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qa_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID REFERENCES calls(id) ON DELETE CASCADE,
    flag_type VARCHAR(100),
    severity VARCHAR(20), -- CRITICAL, HIGH, MEDIUM, LOW
    description TEXT,
    flag_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_calls_dietician ON calls(dietician_name);
CREATE INDEX idx_calls_status ON calls(status);
CREATE INDEX idx_qa_call_id ON qa_scores(call_id);
CREATE INDEX idx_flags_severity ON qa_flags(severity);
```

**Data Migration:**
- [ ] Create Supabase project (if not exists)
- [ ] Create tables via SQL editor
- [ ] Migrate historical data from Neon PostgreSQL to Supabase
- [ ] Verify data integrity
- [ ] Update connection strings in Flask

**What to Do:**
- [ ] Update `db_layer.py` to handle QA tables
- [ ] Create migration scripts for historical data
- [ ] Test queries on Supabase
- [ ] Update environment variables

### Phase 4: Frontend Integration (Week 2, Days 3-5)

**Update Navigation:**

```javascript
// Update NAV_ITEMS in Sidebar.jsx
const NAV_ITEMS = [
  { id: "overview",          label: "Overview",          icon: "⊞" },
  { id: "clinical-outcomes", label: "Clinical Outcomes", icon: "📊" },
  { id: "utilization",       label: "Utilization",       icon: "📈" },
  { id: "recommendations",   label: "Recommendations",   icon: "💡" },
  { 
    id: "quality",           
    label: "Quality Management", 
    icon: "📞",
    children: [
      { id: "qa-dashboard",     label: "Dashboard" },
      { id: "call-upload",      label: "Upload Calls" },
      { id: "transcriptions",   label: "Transcriptions" },
      { id: "qa-scorecards",    label: "QA Scorecards" },
      { id: "dietician-analytics", label: "Dietician Analytics" },
      { id: "qa-alerts",        label: "QA Alerts" },
      { id: "ai-insights",      label: "AI Insights" }
    ]
  },
];
```

**Update App.jsx Routes:**

```javascript
case "qa-dashboard":      return <QADashboard ... />;
case "call-upload":       return <CallUpload ... />;
case "transcriptions":    return <Transcriptions ... />;
case "qa-scorecards":     return <QAScorecards ... />;
case "dietician-analytics": return <DieticianAnalytics ... />;
case "qa-alerts":         return <QAAlerts ... />;
case "ai-insights":       return <AIInsights ... />;
```

**What to Do:**
- [ ] Copy all QA components to `clinical-dashboard/src/pages/quality/`
- [ ] Update imports to use Agent 8 design tokens (T)
- [ ] Convert TypeScript to JavaScript
- [ ] Replace API URLs with unified backend
- [ ] Test all components render correctly
- [ ] Test API integration with Flask
- [ ] Verify styling matches Agent 8 design

### Phase 5: Testing & Integration (Week 3, Days 1-3)

**Local Testing:**
- [ ] Start Flask backend locally
- [ ] Start React frontend locally
- [ ] Test each QA component
- [ ] Test upload → transcription → analysis flow
- [ ] Test cross-system queries (e.g., utilization + QA scores)
- [ ] Test authentication and permissions

**Integration Testing:**
- [ ] Test navigation between Clinical Operations and Quality Management
- [ ] Test shared data (provider names, appointment IDs, etc.)
- [ ] Test unified dashboard with combined metrics
- [ ] Load testing (concurrent uploads, API calls)
- [ ] Performance testing (response times, data loading)

**What to Do:**
- [ ] Create test data set
- [ ] Write integration tests
- [ ] Performance benchmark
- [ ] User acceptance testing
- [ ] Documentation review

### Phase 6: Production Deployment (Week 3, Days 4-5)

**Pre-deployment:**
- [ ] Backup production data (Neon, current Supabase)
- [ ] Create Supabase recovery snapshot
- [ ] Prepare rollback plan

**Deployment Steps:**
1. Deploy updated Flask backend to Railway with QA endpoints
2. Deploy React frontend to Vercel with QA components
3. Run data migration (Neon → Supabase)
4. Verify all endpoints working
5. Monitor for errors
6. Gradually roll out to users

**Post-deployment:**
- [ ] Monitor Flask logs for errors
- [ ] Monitor Vercel errors
- [ ] Check database performance
- [ ] Test all critical flows
- [ ] Decommission old QA portal (after 1-2 weeks)

---

## 📂 New Project Structure

```
agent8-unified-portal/
├── clinical-dashboard/
│   └── src/
│       ├── pages/
│       │   ├── Overview.jsx
│       │   ├── ClinicalOutcomes.jsx
│       │   ├── Utilization.jsx
│       │   ├── Recommendations.jsx
│       │   └── quality/          [NEW QA COMPONENTS]
│       │       ├── QADashboard.jsx
│       │       ├── CallUpload.jsx
│       │       ├── Transcriptions.jsx
│       │       ├── QAScorecards.jsx
│       │       ├── DieticianAnalytics.jsx
│       │       ├── QAAlerts.jsx
│       │       └── AIInsights.jsx
│       ├── hooks/
│       │   ├── useAgentAPI.ts
│       │   └── useClinicalAPI.ts [FROM QA SYSTEM]
│       └── components/
│           ├── Sidebar.jsx [UPDATED WITH QA ROUTES]
│           └── ...existing
│
├── app.py [UPDATED WITH /api/qa/* ROUTES]
├── services/
│   ├── agent8/          [EXISTING]
│   └── qa/              [NEW FROM QA SYSTEM]
│       ├── transcription/
│       ├── llm/
│       ├── pipeline.py
│       └── ingestion.py
├── models/
│   ├── professional_metrics.py [EXISTING]
│   └── qa_models.py [NEW]
├── db/
│   ├── db_layer.py [UPDATED]
│   └── migrations/ [NEW]
└── requirements.txt [UPDATED]
```

---

## 🔌 API Endpoints (Unified)

### Agent 8 Clinical Operations
```
GET  /api/agent8/overview
GET  /api/agent8/capacity-analysis
GET  /api/agent8/clinical-outcomes
GET  /api/agent8/utilization
GET  /api/agent8/recommendations-gemini
GET  /api/agent8/recommendations-proper
GET  /api/agent8/forecast-7day
GET  /api/agent8/peak-hours
GET  /api/agent8/historical-trends
GET  /api/agent8/qa-analytics
```

### Quality Management (NEW - FROM QA SYSTEM)
```
GET    /api/qa/calls                    # List all calls
POST   /api/qa/calls                    # Create call
GET    /api/qa/calls/<call_id>          # Get call details
POST   /api/qa/calls/bulk-upload        # Upload Excel file
POST   /api/qa/transcribe/<call_id>     # Process transcription
POST   /api/qa/analyze/<call_id>        # Run QA analysis
GET    /api/qa/dashboard/stats          # Dashboard metrics
GET    /api/qa/scorecards               # Get QA scorecards
GET    /api/qa/alerts                   # Get QA alerts
GET    /api/qa/dietician/<name>         # Dietician analytics
```

### Unified Analytics (NEW)
```
GET  /api/dashboard/combined-metrics
GET  /api/dashboard/provider-matrix        # Utilization + QA score
GET  /api/analytics/cross-system-reports
GET  /api/analytics/correlation-analysis
```

---

## 📊 Timeline

| Week | Phase | Duration | Deliverable |
|------|-------|----------|------------|
| 1 | Extract & Migrate Components | 5 days | QA components in React, backend logic in Flask |
| 2 | Database Consolidation + Integration | 5 days | Unified Supabase schema, all APIs working |
| 3 | Testing + Production Deployment | 5 days | Live unified portal on Railway + Vercel |

**Total: 3 weeks to unified system**

---

## ✅ Success Criteria

- [ ] Single login for all features
- [ ] Single URL for entire platform
- [ ] All Clinical Operations features working
- [ ] All Quality Management features working
- [ ] Call upload → transcription → analysis flow working
- [ ] Cross-system queries working (e.g., provider utilization + QA scores)
- [ ] Unified dashboard showing combined metrics
- [ ] Performance < 2s response time
- [ ] Zero data loss during migration
- [ ] 99.9% uptime

---

## 🚀 Ready to Start?

**Next Step: Phase 1 - Extract QA Components**

I can immediately:
1. Copy all QA React components to Agent 8
2. Convert TypeScript to JavaScript
3. Update imports and styling
4. Test components render

Shall I start Phase 1? 🎯
