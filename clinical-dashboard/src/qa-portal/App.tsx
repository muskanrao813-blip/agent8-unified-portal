/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DashboardView from './components/DashboardView';
import CallUploadView from './components/CallUploadView';
import AIInsightsView from './components/AIInsightsView';
import DieticianReportsView from './components/DieticianReportsView';
import QAAlertsView from './components/QAAlertsView';
import TranscriptionsView from './components/TranscriptionsView';

import { Recording, SystemSettings, QAAlert } from './types';
import { useClinicalAPI, fetchDieticianReports } from './hooks/useClinicalAPI';

// Default settings (minimal, no mock data)
const DEFAULT_SETTINGS: SystemSettings = {
  accountProfile: {
    name: 'QA Manager',
    role: 'Clinical QA Lead',
    email: 'qa@dietician.local',
    avatar: ''
  },
  rubricWeights: {
    nutritionalAccuracy: 40,
    patientEmpathy: 25,
    sopAdherence: 20,
    actionPlanClarity: 15
  },
  platformPreferences: {
    dataRetentionPolicy: '1 Year',
    qaAlertTriggers: 70,
    defaultTimezone: 'EST',
    primaryLanguage: 'English (US)'
  },
  teamMembers: []
};

export default function App() {
  // Read view from query parameter (for Agent 8 integration)
  const urlParams = new URLSearchParams(window.location.search);
  const viewParam = urlParams.get('view') || 'dashboard';

  const [currentView, setCurrentView] = useState<string>(viewParam);

  // Listen for URL changes (iframe src updates)
  useEffect(() => {
    const handleURLChange = () => {
      const newParams = new URLSearchParams(window.location.search);
      const newView = newParams.get('view') || 'dashboard';
      console.log('[QA Portal] URL changed, updating view to:', newView);
      setCurrentView(newView);
    };

    // Listen for popstate events (browser back/forward)
    window.addEventListener('popstate', handleURLChange);
    // Also check URL periodically for iframe src changes
    const interval = setInterval(() => {
      const newParams = new URLSearchParams(window.location.search);
      const newView = newParams.get('view') || 'dashboard';
      setCurrentView(prev => {
        if (prev !== newView) {
          console.log('[QA Portal] URL polling detected view change to:', newView);
          return newView;
        }
        return prev;
      });
    }, 500);

    return () => {
      window.removeEventListener('popstate', handleURLChange);
      clearInterval(interval);
    };
  }, []);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Fetch ONLY real data from BE clinical API - NO FALLBACK
  const { recordings: apiRecordings, loading: apiLoading, error: apiError } = useClinicalAPI();

  // Use ONLY API data - empty by default, populated from API
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [activeQueue, setActiveQueue] = useState<Recording[]>([]);
  const [dieticians, setDieticians] = useState<any[]>([]);
  const [trainingGaps, setTrainingGaps] = useState<any[]>([]);
  const [settings, setSettings] = useState<SystemSettings>(DEFAULT_SETTINGS);
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null);

  // Update recordings ONLY from API data
  useEffect(() => {
    if (apiRecordings && apiRecordings.length > 0) {
      setRecordings(apiRecordings);
    }
  }, [apiRecordings]);

  // Fetch dietician reports whenever recordings update (completed calls drive the data)
  useEffect(() => {
    const completedCount = apiRecordings.filter(r => r.status === 'completed').length;
    if (completedCount > 0) {
      fetchDieticianReports().then(({ dieticians: d, trainingGaps: gaps }) => {
        if (d.length > 0) setDieticians(d);
        if (gaps.length > 0) setTrainingGaps(gaps);
      });
    }
  }, [apiRecordings]);

  // QA alerts derived ONLY from real API data
  const [allQAAlerts, setAllQAAlerts] = useState<QAAlert[]>([]);

  // Update QA alerts when recordings change (ONLY from real API data)
  useEffect(() => {
    if (recordings.length > 0) {
      const alerts = recordings.reduce((acc: QAAlert[], curr) => {
        if (curr.qaAlerts && curr.qaAlerts.length > 0) {
          return [...acc, ...curr.qaAlerts];
        }
        return acc;
      }, []);
      setAllQAAlerts(alerts);
    } else {
      setAllQAAlerts([]);
    }
  }, [recordings]);

  // Simulated transcription & upload processing progress update interval
  useEffect(() => {
    // Removed mock data timer - all data comes from real API only
    // The backend handles processing automatically
    return () => {};
  }, []);

  // Handle manual/drag file upload triggers
  const handleUploadFile = (fileName: string) => {
    const newId = `INGEST_${Math.floor(Math.random() * 9000) + 1000}`;
    const newQueueItem: Recording = {
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
    setCurrentView('upload'); // Switch view to Call Upload to show uploading item
  };

  // Switch to selected call details within AI Insights View
  const handleSelectCall = (id: string) => {
    setSelectedCallId(id);
    setCurrentView('insights');
  };

  // Assign dietician training remediation modules
  const handleAssignTraining = (gapId: string) => {
    setTrainingGaps((prevGaps) =>
      prevGaps.map((gap) => (gap.id === gapId ? { ...gap, assigned: !gap.assigned } : gap))
    );
  };

  // Toggle alert resolved status
  const handleToggleAlertStatus = (alertId: string) => {
    setAllQAAlerts((prevAlerts) =>
      prevAlerts.map((alert) =>
        alert.id === alertId
          ? { ...alert, status: alert.status === 'active' ? 'resolved' : 'active' }
          : alert
      )
    );
  };

  // Handle global preferences saves
  const handleSaveSettings = (updated: SystemSettings) => {
    setSettings(updated);
  };

  // Reset preferences
  const handleResetSettings = () => {
    setSettings(DEFAULT_SETTINGS);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden font-sans bg-background text-on-background">
      {/* Navigation Sidebar */}
      <Sidebar
        currentView={currentView}
        onViewChange={(view) => {
          setCurrentView(view);
          setSearchQuery(''); // reset search query on navigation
        }}
        onTriggerUpload={() => handleUploadFile('my_uploaded_clinical_audio.wav')}
        activeProcessingCount={activeQueue.length}
      />

      {/* Main Right Area: Header + Dynamic Viewports */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Dynamic header */}
        <Header
          currentView={currentView}
          settings={settings}
          searchQuery={searchQuery}
          onSearchQueryChange={setSearchQuery}
          criticalAlerts={allQAAlerts}
        />

        {/* Show API loading/error state */}
        {apiError && (
          <div className="bg-red-50 border-b border-red-200 px-4 py-3 text-sm text-red-700">
            <strong>API Error:</strong> {apiError} - Using fallback data
          </div>
        )}

        {/* View Switchboard */}
        <main className="flex-1 overflow-hidden relative">
          {currentView === 'dashboard' && (
            <DashboardView
              recordings={recordings}
              onSelectCall={handleSelectCall}
              dieticians={dieticians}
              searchQuery={searchQuery}
            />
          )}

          {currentView === 'upload' && (
            <CallUploadView
              activeQueue={activeQueue}
              completedRecordings={recordings}
              onSelectCall={handleSelectCall}
              onUploadFile={handleUploadFile}
            />
          )}

          {currentView === 'transcriptions' && (
            <TranscriptionsView
              recordings={recordings}
              onSelectCall={handleSelectCall}
              searchQuery={searchQuery}
            />
          )}

          {currentView === 'insights' && (
            <AIInsightsView
              completedRecordings={recordings}
              selectedCallId={selectedCallId}
              onSelectCallId={setSelectedCallId}
            />
          )}

          {currentView === 'reports' && (
            <DieticianReportsView
              dieticians={dieticians}
              trainingGaps={trainingGaps}
              onAssignTraining={handleAssignTraining}
              searchQuery={searchQuery}
            />
          )}

          {currentView === 'alerts' && (
            <QAAlertsView
              alerts={allQAAlerts}
              onSelectCall={handleSelectCall}
              onToggleAlertStatus={handleToggleAlertStatus}
              searchQuery={searchQuery}
            />
          )}
        </main>
      </div>
    </div>
  );
}
