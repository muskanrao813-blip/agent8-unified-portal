// QA Portal View Components Only
// For embedding in Agent 8 - no sidebar/header, just content views

export { default as DashboardView } from './components/DashboardView.tsx';
export { default as CallUploadView } from './components/CallUploadView.tsx';
export { default as TranscriptionsView } from './components/TranscriptionsView.tsx';
export { default as AIInsightsView } from './components/AIInsightsView.tsx';
export { default as DieticianReportsView } from './components/DieticianReportsView.tsx';
export { default as QAAlertsView } from './components/QAAlertsView.tsx';

// Export types
export type { Recording, SystemSettings, QAAlert } from './types';
