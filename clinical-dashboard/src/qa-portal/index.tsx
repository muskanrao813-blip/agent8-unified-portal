// Main export file for QA Portal components
// Fixes import paths so components can be used from outside qa-portal folder

export { default as Sidebar } from './components/Sidebar';
export { default as Header } from './components/Header';
export { default as DashboardView } from './components/DashboardView';
export { default as CallUploadView } from './components/CallUploadView';
export { default as TranscriptionsView } from './components/TranscriptionsView';
export { default as AIInsightsView } from './components/AIInsightsView';
export { default as DieticianReportsView } from './components/DieticianReportsView';
export { default as QAAlertsView } from './components/QAAlertsView';
export { default as SettingsView } from './components/SettingsView';

// Export types
export type { Recording, SystemSettings, QAAlert } from './types';
