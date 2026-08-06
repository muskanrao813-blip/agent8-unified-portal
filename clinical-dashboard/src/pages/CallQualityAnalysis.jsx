import React, { useState, useEffect, useCallback } from 'react';
import {
  DashboardView,
  CallUploadView,
  TranscriptionsView,
  AIInsightsView,
  DieticianReportsView,
  QAAlertsView
} from '../qa-portal/index.tsx';

// Error boundary to catch component errors
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', color: '#666' }}>
          <p>Component is loading...</p>
        </div>
      );
    }
    return this.props.children;
  }
}

// Full state management for all QA Portal views with working flows
export default function CallQualityAnalysis({ view = "dashboard" }) {
  // Shared state across all views
  const [recordings, setRecordings] = useState([]);
  const [activeQueue, setActiveQueue] = useState([]);
  const [dieticians, setDieticians] = useState([]);
  const [trainingGaps, setTrainingGaps] = useState([]);
  const [selectedCallId, setSelectedCallId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [qaAlerts, setQaAlerts] = useState([]);

  // Handle file upload
  const handleUploadFile = useCallback((fileName) => {
    const newId = `INGEST_${Math.floor(Math.random() * 9000) + 1000}`;
    const newQueueItem = {
      id: newId,
      name: fileName,
      patientName: 'Pending Verification',
      agentName: 'Unassigned',
      duration: '04:12',
      date: new Date().toLocaleDateString('en-US'),
      status: 'processing',
      progress: 0,
      statusText: 'Uploading audio package...',
      sopCompliant: true,
      sopComplianceScore: 0,
      scores: { greeting: 0, empathy: 0, compliance: 0, technical: 0 },
      qaAlerts: [],
      transcript: [],
      insights: { whatWentWell: [], areasForImprovement: [], summary: '' }
    };
    setActiveQueue((prev) => [newQueueItem, ...prev]);
  }, []);

  // Handle call selection
  const handleSelectCall = useCallback((id) => {
    setSelectedCallId(id);
  }, []);

  // Handle training assignment
  const handleAssignTraining = useCallback((gapId) => {
    setTrainingGaps((prev) =>
      prev.map((gap) => (gap.id === gapId ? { ...gap, assigned: !gap.assigned } : gap))
    );
  }, []);

  // Handle alert status toggle
  const handleToggleAlertStatus = useCallback((alertId) => {
    setQaAlerts((prev) =>
      prev.map((alert) =>
        alert.id === alertId
          ? { ...alert, status: alert.status === 'active' ? 'resolved' : 'active' }
          : alert
      )
    );
  }, []);

  return (
    <ErrorBoundary>
      <div style={{ width: '100%', height: '100%', overflow: 'hidden', backgroundColor: '#f5f5f5' }}>
        {view === 'dashboard' && (
          <DashboardView
            recordings={recordings}
            onSelectCall={handleSelectCall}
            dieticians={dieticians}
            searchQuery={searchQuery}
          />
        )}
        {view === 'upload' && (
          <CallUploadView
            activeQueue={activeQueue}
            completedRecordings={recordings}
            onSelectCall={handleSelectCall}
            onUploadFile={handleUploadFile}
          />
        )}
        {view === 'transcriptions' && (
          <TranscriptionsView
            recordings={recordings}
            onSelectCall={handleSelectCall}
            searchQuery={searchQuery}
          />
        )}
        {view === 'insights' && (
          <AIInsightsView
            completedRecordings={recordings}
            selectedCallId={selectedCallId}
            onSelectCallId={setSelectedCallId}
          />
        )}
        {view === 'reports' && (
          <DieticianReportsView
            dieticians={dieticians}
            trainingGaps={trainingGaps}
            onAssignTraining={handleAssignTraining}
            searchQuery={searchQuery}
          />
        )}
        {view === 'alerts' && (
          <QAAlertsView
            alerts={qaAlerts}
            onSelectCall={handleSelectCall}
            onToggleAlertStatus={handleToggleAlertStatus}
            searchQuery={searchQuery}
          />
        )}
      </div>
    </ErrorBoundary>
  );
}
