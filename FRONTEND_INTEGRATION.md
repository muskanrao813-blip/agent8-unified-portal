# Frontend Integration Guide
## Agent 8 Unified Portal - React Frontend

**Status**: React FE design provided in `clinical-dashboard/`  
**Task**: Integrate React FE with Flask backend API

---

## 📦 What's Included

Frontend React app located at:
```
agent8-unified-portal/clinical-dashboard/
├── package.json
├── public/
├── src/
│   ├── App.jsx                    # Main app component
│   ├── index.js                   # Entry point
│   ├── tokens.js                  # Design tokens (colors, spacing, etc)
│   ├── components/
│   │   ├── Sidebar.jsx           # Navigation sidebar
│   │   ├── ProfilePanel.jsx       # User profile section
│   │   └── UI.jsx                # Shared UI components
│   └── pages/
│       ├── Overview.jsx           # Overview with recommendations
│       ├── CallQuality.jsx        # QA portal integration
│       ├── ClinicalOutcomes.jsx   # Clinical outcomes
│       └── Utilization.jsx        # Utilization analysis
└── README.md
```

---

## 🔧 Integration Steps

### Step 1: Setup React Environment

```bash
cd C:\Users\muskan.rao\Documents\claude\agent8-unified-portal\clinical-dashboard

# Install dependencies
npm install

# Start development server
npm start
```

**React will run on**: `http://localhost:3000/`

### Step 2: Ensure Backend is Running

```bash
# In another terminal
cd C:\Users\muskan.rao\Documents\claude\agent8-unified-portal

# Activate venv
.\venv\Scripts\Activate.ps1

# Start Flask backend
python app.py
```

**Backend will run on**: `http://localhost:5001/`

### Step 3: Update React API Base URL

Edit `src/App.jsx` or create a config file:

```javascript
// src/config.js (Create if needed)
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// Usage in components
import { API_BASE_URL } from './config';

const fetchRecommendations = async () => {
  const res = await fetch(`${API_BASE_URL}/api/agent8/recommendations`);
  return res.json();
};
```

Or set environment variable:
```bash
# Create .env file in clinical-dashboard/
REACT_APP_API_URL=http://localhost:5001
```

### Step 4: Test Integration

1. **Start Backend** (Port 5001):
   ```bash
   python app.py
   ```

2. **Start Frontend** (Port 3000):
   ```bash
   npm start
   ```

3. **Test API Calls**:
   - Overview page should load KPIs from `/api/agent8/dashboard`
   - Recommendations should load from `/api/agent8/recommendations`
   - Call Quality tab should proxy to `/api/calls/*`

---

## 📝 Component Checklist

### Overview.jsx
- [x] Layout structure
- [ ] Connect to `/api/agent8/dashboard` endpoint
- [ ] Connect to `/api/agent8/recommendations` endpoint
- [ ] Render KPI cards
- [ ] Render recommendation cards (Training, Rebalancing, Quality Intervention, Mentoring)
- [ ] Add action buttons (Accept, Decline, Snooze)

### CallQuality.jsx
- [x] Layout structure
- [ ] Implement sub-tabs (Dashboard, Upload, Transcriptions, Scorecard, Coaching)
- [ ] Connect to `/api/calls/` endpoint
- [ ] Implement file upload to `/api/calls/bulk-upload`
- [ ] Display call list and details
- [ ] Show QA scores and feedback

### ClinicalOutcomes.jsx
- [x] Layout structure
- [ ] Connect to `/api/agent8/clinical-outcomes` endpoint
- [ ] Display programme performance cards
- [ ] Show outcome trends

### Utilization.jsx
- [x] Layout structure
- [ ] Connect to `/api/agent8/capacity-analysis` endpoint
- [ ] Display capacity metrics
- [ ] Show 7-day forecast if available

---

## 🎨 Design System

The React FE includes `tokens.js` which defines:
- **Colors**: Material Design 3 palette
- **Typography**: Playfair Display, Inter, JetBrains Mono
- **Spacing**: Standardized spacing scale
- **Components**: Reusable UI elements

**Ensure consistency** with:
- Sidebar navigation (240px width)
- Header styling (sticky, title + controls)
- KPI cards (white background, left border accent)
- Recommendation cards (with priority colors)
- Material Design 3 iconography

---

## 🔌 API Integration Points

### Overview Page
```javascript
// KPI Cards
fetch('/api/agent8/dashboard')
  .then(r => r.json())
  .then(data => {
    // data.kpis = [
    //   { label: 'Team Utilization', value: '94.2%', ... },
    //   ...
    // ]
  });

// Recommendations
fetch('/api/agent8/recommendations')
  .then(r => r.json())
  .then(data => {
    // data.training_required = [...]
    // data.capacity_rebalancing = [...]
    // data.quality_interventions = [...]
    // data.peer_mentoring = [...]
  });
```

### Call Quality Tab
```javascript
// List calls
fetch('/api/calls/')
  .then(r => r.json());

// Upload file
const formData = new FormData();
formData.append('file', excelFile);
fetch('/api/calls/bulk-upload', { method: 'POST', body: formData })
  .then(r => r.json());

// Get call details
fetch('/api/calls/{call_id}')
  .then(r => r.json());
```

### Clinical Outcomes
```javascript
fetch('/api/agent8/clinical-outcomes')
  .then(r => r.json())
  .then(data => {
    // data.kpis = [...]
  });
```

### Utilization
```javascript
fetch('/api/agent8/capacity-analysis')
  .then(r => r.json())
  .then(data => {
    // data.kpis = [...]
  });
```

---

## 🚀 Build for Production

```bash
cd clinical-dashboard

# Build optimized version
npm run build

# Output: clinical-dashboard/build/
```

Deploy `build/` folder to:
- Netlify
- Vercel
- AWS S3 + CloudFront
- Your web server

---

## ⚙️ Backend CORS Configuration

Ensure Flask has CORS enabled for React frontend:

```python
# In app.py (already configured)
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allows requests from localhost:3000
```

**For production**, update CORS to specific origin:
```python
CORS(app, resources={r"/api/*": {"origins": ["https://yourdomain.com"]}})
```

---

## 🧪 Testing Checklist

### Local Development
- [ ] Backend running on http://localhost:5001
- [ ] Frontend running on http://localhost:3000
- [ ] Overview page loads without errors
- [ ] KPI cards display correctly
- [ ] Recommendations render properly
- [ ] Navigation between tabs works
- [ ] Call Quality tab shows placeholder/links to backend

### Integration Testing
- [ ] Click "Accept" on recommendation → Backend receives request
- [ ] Click "Decline" → Handled correctly
- [ ] Click "Snooze" → Modal appears
- [ ] Call Quality → Can upload Excel file
- [ ] Clinical Outcomes → Displays outcome data
- [ ] Utilization → Shows capacity metrics

### API Testing
```bash
# Test each endpoint
curl http://localhost:5001/api/agent8/recommendations
curl http://localhost:5001/api/agent8/dashboard
curl http://localhost:5001/api/agent8/clinical-outcomes
curl http://localhost:5001/api/agent8/capacity-analysis
curl http://localhost:5001/api/calls/
```

---

## 🐛 Common Issues

### React won't start
```bash
# Clear node_modules and reinstall
rm -r node_modules
npm install
npm start
```

### CORS errors in browser console
- Ensure backend has `CORS(app)` enabled
- Check that API_BASE_URL is correct
- Verify backend is running on port 5001

### API returns 404
- Check endpoint spelling matches backend routes
- Ensure Flask app.py is running
- Check proxy configuration

### Recommendations not loading
- Verify `/api/agent8/recommendations` endpoint works
- Check browser Network tab for response
- Look at Flask console for errors

---

## 📋 Development Workflow

1. **Start Backend**: `python app.py` (Port 5001)
2. **Start Frontend**: `npm start` (Port 3000)
3. **Edit React Components** → Auto-reload in browser
4. **Add API Calls** → Use fetch from API endpoints
5. **Test in Browser** → http://localhost:3000
6. **Check Console** → F12 for errors
7. **Build for Production**: `npm run build`

---

## 📦 Deployment Paths

### Option A: Separate Deployments
```
Frontend (React):     Netlify/Vercel
Backend (Flask):      Render/Heroku
Database:             PostgreSQL (Neon)
```

### Option B: Single Server
```
Backend (Flask):      Serve React build + API
  /build              → React static files
  /api/*              → API endpoints
```

For Option B, update Flask:
```python
from flask import send_from_directory

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join('build', path)):
        return send_from_directory('build', path)
    else:
        return send_from_directory('build', 'index.html')
```

---

## 🔐 Security Considerations

1. **Environment Variables**:
   ```bash
   # clinical-dashboard/.env
   REACT_APP_API_URL=http://localhost:5001  # Dev
   
   # Production
   REACT_APP_API_URL=https://api.yourdomain.com
   ```

2. **API Security**:
   - Use HTTPS in production
   - Validate all inputs on backend
   - Implement authentication if needed
   - Rate limiting on sensitive endpoints

3. **CORS Policy**:
   - Restrict to specific origins in production
   - Don't use `*` in production

---

## ✅ Deployment Checklist

- [ ] React build created: `npm run build`
- [ ] Frontend env variables set (.env)
- [ ] Backend API_BASE_URL configured
- [ ] All API endpoints tested
- [ ] CORS configured for production
- [ ] Authentication implemented (if needed)
- [ ] Logging configured
- [ ] Error handling tested
- [ ] Performance optimized
- [ ] Mobile responsive tested
- [ ] Accessibility checked
- [ ] Security audit passed

---

## 📞 Quick Reference

| Item | URL |
|------|-----|
| React Frontend (Dev) | http://localhost:3000 |
| Flask Backend (Dev) | http://localhost:5001 |
| Flask API Docs | http://localhost:5001/api |
| Dietician QA Portal | http://localhost:8000 |

---

**Next Steps**:
1. ✅ Setup React environment
2. ✅ Ensure Flask backend is running
3. ✅ Test API endpoints
4. ⏳ Build & deploy
5. ⏳ Monitor in production

---

*Version 1.0 - Integration Guide*  
*Created: 2026-07-21*
