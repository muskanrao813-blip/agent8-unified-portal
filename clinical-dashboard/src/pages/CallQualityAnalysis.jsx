import React from 'react';
import {
  DashboardView,
  CallUploadView,
  TranscriptionsView,
  AIInsightsView,
  DieticianReportsView,
  QAAlertsView
} from '../qa-portal/index.tsx';

// Only render the view component based on prop - no sidebar/header
export default function CallQualityAnalysis({ view = "dashboard" }) {
  return (
    <div style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      {view === 'dashboard' && <DashboardView recordings={[]} onSelectCall={() => {}} dieticians={[]} searchQuery="" />}
      {view === 'upload' && <CallUploadView activeQueue={[]} completedRecordings={[]} onSelectCall={() => {}} onUploadFile={() => {}} />}
      {view === 'transcriptions' && <TranscriptionsView recordings={[]} onSelectCall={() => {}} searchQuery="" />}
      {view === 'insights' && <AIInsightsView completedRecordings={[]} selectedCallId={null} onSelectCallId={() => {}} />}
      {view === 'reports' && <DieticianReportsView dieticians={[]} trainingGaps={[]} onAssignTraining={() => {}} searchQuery="" />}
      {view === 'alerts' && <QAAlertsView alerts={[]} onSelectCall={() => {}} onToggleAlertStatus={() => {}} searchQuery="" />}
    </div>
  );
}
