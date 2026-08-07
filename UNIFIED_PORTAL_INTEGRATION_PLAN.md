# Unified Clinical Portal - Integration Plan

## 📊 Current Situation

### Separate Systems Today:
```
SYSTEM 1: Agent 8 Portal (Building)
├── Frontend: Vercel (React)
├── Backend: Railway (Flask)
├── Database: Supabase PostgreSQL
└── Features: Outcomes, Utilization, Recommendations

SYSTEM 2: Dietician QA Portal (Live on Prod)
├── Frontend: Netlify (React)
├── Backend: Render (FastAPI)  
├── Database: Neon PostgreSQL
└── Features: Transcription, QA Scoring, Analytics
```

### Goal: Unified Portal
```
UNIFIED CLINICAL OPERATIONS PORTAL
├── Frontend: Vercel (Single React App)
├── Backend: Railway (Single Python App)
├── Database: Supabase PostgreSQL (Single Database)
└── Features: All combined
    ├── Clinical Outcomes (Agent 8)
    ├── Provider Utilization (Agent 8)
    ├── Call Quality Analysis (Dietician QA)
    ├── Transcription Management (Dietician QA)
    ├── AI Recommendations (Gemini)
    └── Unified Analytics Dashboard
```

---

## 🔄 Integration Architecture

### Backend Consolidation
```
Single Flask Backend (Railway)
    ├── Agent 8 Routes (/api/agent8/*)
    │   ├── capacity-analysis
    │   ├── utilization
    │   ├── recommendations
    │   └── historical-trends
    │
    ├── QA Routes (/api/qa/*)
    │   ├── calls (list/create/get)
    │   ├── transcription (upload/process)
    │   ├── scoring (QA analysis)
    │   ├── entities (extraction)
    │   └── bulk-upload (Excel)
    │
    └── Unified Routes (/api/*)
        ├── dashboard (combined metrics)
        ├── reports (cross-system analytics)
        └── settings
```

### Database Consolidation
```
Single Supabase PostgreSQL
    ├── Professional Metrics (Agent 8)
    │   └── utilization, capacity, appointments
    │
    ├── Call Records (QA System)
    │   ├── calls
    │   ├── transcripts
    │   ├── qa_scores
    │   └── qa_flags
    │
    ├── Recommendations (Agent 8)
    │   └── action_plans, strategies
    │
    └── Common Tables
        ├── users
        ├── providers/dieticians
        ├── settings
        └── audit_logs
```

### Frontend Consolidation
```
Single React App (Vercel)
    ├── Sidebar Navigation
    │   ├── Dashboard
    │   ├── Clinical Operations
    │   │   ├── Overview
    │   │   ├── Utilization
    │   │   ├── Outcomes
    │   │   └── Recommendations
    │   ├── Quality Management
    │   │   ├── Call Upload
    │   │   ├── Transcriptions
    │   │   ├── QA Scorecards
    │   │   └── Dietician Analytics
    │   ├── Analytics & Reports
    │   │   ├── Cross-system Dashboard
    │   │   ├── Provider Performance
    │   │   └── Quality Trends
    │   └── Settings
    │
    └── Responsive Tabs/Pages
```

---

## 📝 Migration Checklist

### Phase 1: Database Migration
- [ ] Create QA tables in Supabase (calls, transcripts, qa_scores, qa_flags)
- [ ] Migrate Neon PostgreSQL data to Supabase
  ```sql
  -- Create tables
  CREATE TABLE calls (
      id UUID PRIMARY KEY,
      dietician_name VARCHAR(255),
      patient_id VARCHAR(255),
      patient_name VARCHAR(255),
      appointment_id VARCHAR(255),
      recording_url TEXT,
      status VARCHAR(50), -- pending, processing, completed
      overall_weighted_score DECIMAL(5,2),
      language VARCHAR(20), -- en, hi
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  
  CREATE TABLE transcripts (
      id UUID PRIMARY KEY,
      call_id UUID REFERENCES calls(id),
      raw_transcript TEXT,
      reconstructed_transcript TEXT,
      provider VARCHAR(100), -- Whisper, Groq, Claude
      workflow_description TEXT,
      entities JSONB,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  
  CREATE TABLE qa_scores (
      id UUID PRIMARY KEY,
      call_id UUID REFERENCES calls(id),
      greeting_score DECIMAL(5,2),
      empathy_score DECIMAL(5,2),
      compliance_score DECIMAL(5,2),
      technical_score DECIMAL(5,2),
      overall_weighted_score DECIMAL(5,2),
      sop_violations JSONB,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  
  CREATE TABLE qa_flags (
      id UUID PRIMARY KEY,
      call_id UUID REFERENCES calls(id),
      flag_type VARCHAR(100),
      severity VARCHAR(20), -- CRITICAL, HIGH, MEDIUM, LOW
      description TEXT,
      timestamp TIMESTAMP,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```

### Phase 2: Backend Integration
- [ ] Copy QA FastAPI routes to Flask backend
  ```python
  # In app.py, add:
  
  # QA System Routes
  @app.route('/api/qa/calls', methods=['GET'])
  def get_calls():
      # List all calls with QA scores
  
  @app.route('/api/qa/calls', methods=['POST'])
  def create_call():
      # Create new call record
  
  @app.route('/api/qa/calls/<call_id>', methods=['GET'])
  def get_call(call_id):
      # Get call details with transcripts and scores
  
  @app.route('/api/qa/calls/bulk-upload', methods=['POST'])
  def bulk_upload():
      # Handle Excel file upload
  
  @app.route('/api/qa/transcribe/<call_id>', methods=['POST'])
  def transcribe_call(call_id):
      # Process audio and generate transcript
  
  @app.route('/api/qa/analyze/<call_id>', methods=['POST'])
  def analyze_call(call_id):
      # Run QA analysis on transcript
  ```

- [ ] Migrate transcription pipeline (Whisper → Claude reconstruction)
- [ ] Migrate QA scoring engine (Gemini 5-dimensions)
- [ ] Migrate entity extraction logic
- [ ] Set up PostgreSQL drivers (psycopg2)
- [ ] Update environment variables
  ```
  DATABASE_URL=postgresql://...supabase.co...
  WHISPER_MODEL=tiny
  GROQ_API_KEY=...
  GEMINI_API_KEY=...
  ```

### Phase 3: Frontend Integration
- [ ] Add "Quality Management" section to sidebar
- [ ] Create Call Upload component
- [ ] Create Transcriptions view
- [ ] Create QA Scorecard display
- [ ] Create Dietician Dashboard
- [ ] Add cross-system unified dashboard
- [ ] Update API URLs to point to unified backend

### Phase 4: Testing & Validation
- [ ] Test call upload flow
- [ ] Test transcription processing
- [ ] Test QA analysis
- [ ] Test unified dashboard queries
- [ ] Test cross-system reports
- [ ] Load testing (concurrent uploads)
- [ ] Database performance testing

### Phase 5: Deployment
- [ ] Deploy updated Flask backend to Railway
- [ ] Deploy updated React frontend to Vercel
- [ ] Migrate data from Neon to Supabase
- [ ] Decommission old Render QA backend
- [ ] Decommission old Netlify QA frontend
- [ ] Set up production monitoring
- [ ] Create data backup strategy

---

## 🎯 Key Integration Points

### 1. Unified Navigation
```javascript
// Common sidebar navigation
const navigation = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: 'LayoutDashboard'
  },
  {
    name: 'Clinical Operations',
    children: [
      { name: 'Overview', href: '/clinical/overview' },
      { name: 'Utilization', href: '/clinical/utilization' },
      { name: 'Outcomes', href: '/clinical/outcomes' },
      { name: 'Recommendations', href: '/clinical/recommendations' }
    ]
  },
  {
    name: 'Quality Management',
    children: [
      { name: 'Upload Calls', href: '/quality/upload' },
      { name: 'Transcriptions', href: '/quality/transcriptions' },
      { name: 'Scorecards', href: '/quality/scorecards' },
      { name: 'Analytics', href: '/quality/analytics' }
    ]
  },
  {
    name: 'Analytics & Reports',
    children: [
      { name: 'Combined Dashboard', href: '/analytics/combined' },
      { name: 'Provider Performance', href: '/analytics/providers' },
      { name: 'Quality Trends', href: '/analytics/trends' }
    ]
  }
];
```

### 2. Unified Dashboard
```
┌─────────────────────────────────────────────┐
│ Clinical Operations Intelligence Platform   │
├─────────────────────────────────────────────┤
│                                             │
│  Metrics Row:                              │
│  ├─ Team Utilization: 78.5%               │
│  ├─ Avg QA Score: 82.1/100                │
│  ├─ Calls Analyzed: 847                   │
│  └─ Performance Trend: ↗ +2.3%            │
│                                             │
│  Charts Row:                               │
│  ├─ Utilization Trends (7-day)            │
│  ├─ QA Score Distribution                 │
│  ├─ Call Processing Pipeline              │
│  └─ Quality Improvement Rate               │
│                                             │
│  Provider Analytics:                       │
│  ├─ Top Performers (Util + QA)            │
│  ├─ Improvement Needed (Qual or Util)     │
│  ├─ Recent Call Insights                  │
│  └─ Recommendations Pipeline               │
│                                             │
└─────────────────────────────────────────────┘
```

### 3. API Endpoint Unification
```
OLD (Separate APIs):
  Agent 8:       https://agent8-api.railway.app/api/agent8/*
  Dietician QA:  https://qa-api.onrender.com/api/qa/*

NEW (Unified API):
  All:           https://unified-api.railway.app/api/*
    ├── /api/agent8/*       (Clinical operations)
    ├── /api/qa/*           (Quality management)
    ├── /api/dashboard/*    (Unified metrics)
    └── /api/analytics/*    (Cross-system reports)
```

---

## 📦 What Needs to be Copied from QA System

### Backend Components (FastAPI → Flask):
1. **Transcription Pipeline**
   - `app/services/transcription/whisper_transcriber.py`
   - `app/services/transcription/groq_transcriber.py`
   - `app/services/transcription/claude_reconstruction.py`
   - `app/services/transcription/unified_integrated.py`

2. **QA Analysis Engine**
   - `app/services/llm/clinical_analyzer.py`
   - `app/services/llm/clinical_prompt.py`
   - QA scoring logic (5 dimensions)
   - Entity extraction

3. **Data Pipeline**
   - Call ingestion (Excel upload parsing)
   - Audio processing (download, format conversion)
   - Pipeline orchestration
   - Status tracking

4. **Database Models**
   - Call record schema
   - Transcript storage
   - QA scores and flags
   - Metrics and analytics

### Frontend Components (React):
1. **Call Management**
   - `CallUploadView.tsx` - Excel upload interface
   - `TranscriptionsView.tsx` - Transcript display
   - `QAScoreCardView.tsx` - QA results visualization
   - `DieticianAnalyticsView.tsx` - Provider analytics

2. **Utilities**
   - `useClinicalAPI.ts` - API integration hook
   - `useFileUpload.ts` - File upload handling
   - Constants and enums

### Configuration & Dependencies:
1. Add to requirements.txt:
   ```
   uvicorn==0.23.0  # For FastAPI compatibility layer
   python-multipart==0.0.6
   openpyxl==3.11.0  # Excel parsing
   librosa==0.10.0  # Audio processing
   groq==0.4.0  # Groq API
   ```

2. Add environment variables:
   ```
   GROQ_API_KEY=...
   GEMINI_FLASH_API_KEY=...
   ```

---

## 🚀 Phased Rollout Strategy

### Week 1: Backend Integration
- [ ] Set up Supabase tables
- [ ] Migrate QA logic to Flask
- [ ] Test API endpoints locally
- [ ] Deploy to Railway (behind feature flag)

### Week 2: Frontend Integration
- [ ] Add QA components to unified UI
- [ ] Connect to new backend endpoints
- [ ] Test upload → transcription → scoring flow
- [ ] Test cross-system queries

### Week 3: Data Migration & Testing
- [ ] Migrate historical data from Neon to Supabase
- [ ] Run full end-to-end tests
- [ ] Performance testing
- [ ] User acceptance testing

### Week 4: Launch & Decommission
- [ ] Cut over to unified portal
- [ ] Monitor for issues
- [ ] Decommission old systems
- [ ] Document unified system

---

## 📊 Expected Unified Portal Features

### Clinical Operations Dashboard
- Provider utilization vs capacity
- Clinical outcomes trending
- Performance recommendations
- Team analytics

### Quality Management Dashboard
- Call upload and processing status
- Transcript quality metrics
- QA score trends by provider
- Compliance alerts and flags
- Dietician performance rankings

### Combined Analytics
- Provider scores: (Utilization + QA) composite
- Quality impact on utilization
- Correlation analysis
- Predictive recommendations

### Unified Administration
- User management
- Role-based access
- Audit logs
- Settings and configuration

---

## ✅ Success Criteria

- [ ] Single URL for all features
- [ ] No need to switch between apps
- [ ] Unified authentication
- [ ] Shared provider/dietician data
- [ ] Combined reporting and analytics
- [ ] Seamless cross-system workflows
- [ ] Production performance (< 2s response time)
- [ ] 99.9% uptime
- [ ] Zero data loss

---

## 🎯 Next Steps

1. **Confirm Integration Scope** - User approval on plan
2. **Start Backend Migration** - Copy QA logic to Flask
3. **Prepare Supabase Schema** - Create QA tables
4. **Test Locally** - Integrated system on localhost
5. **Deploy to Production** - Railway + Vercel
6. **Migrate Data** - Neon → Supabase
7. **Decommission Old Systems** - Clean up

Ready to proceed with integration?
