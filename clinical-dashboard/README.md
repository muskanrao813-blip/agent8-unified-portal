# Clinical Provider Management Dashboard

React dashboard implementation of the Clinical Provider Management UI.

## Project Structure

```
src/
├── tokens.js                  # Design tokens (colors)
├── App.jsx                    # Root app shell + routing
├── index.js                   # Entry point
├── components/
│   ├── UI.jsx                 # Shared: Badge, MetricCard, UtilBar, Header
│   ├── Sidebar.jsx            # Left nav
│   └── ProfilePanel.jsx       # Slide-out provider profile
└── pages/
    ├── Overview.jsx           # Operations Overview
    ├── ClinicalOutcomes.jsx   # Clinical Outcomes
    ├── Utilization.jsx        # Utilization
    └── CallQuality.jsx        # Call Quality Dashboard
public/
└── index.html
package.json
```

## Setup & Run

```bash
npm install
npm start
```

Opens at http://localhost:3000

## Build for production

```bash
npm run build
```

## Pages

| Route (sidebar)   | Page                  |
|-------------------|-----------------------|
| Overview          | Operations Overview   |
| Clinical Outcomes | Clinical Outcomes     |
| Utilization       | Utilization           |
| Call Quality      | Executive Perf. View  |

## Notes for Claude Code

- No external UI libraries — pure React + inline styles
- Design tokens in `src/tokens.js` — edit colors there
- Each page is fully self-contained in its `pages/` file
- Shared components (Badge, Header, MetricCard) live in `components/UI.jsx`
- Provider profile panel opens when clicking a name in the Overview table
