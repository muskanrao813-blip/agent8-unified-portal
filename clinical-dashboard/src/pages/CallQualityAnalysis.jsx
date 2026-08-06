import React, { useState, useEffect } from 'react';
import {
  Sidebar,
  Header,
  DashboardView,
  CallUploadView,
  TranscriptionsView,
  AIInsightsView,
  DieticianReportsView,
  QAAlertsView
} from '../qa-portal/index.tsx';

export default function CallQualityAnalysis({ view = "dashboard" }) {
  const [currentView, setCurrentView] = useState(view);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCallId, setSelectedCallId] = useState(null);
  const [activeQueue, setActiveQueue] = useState([]);
  const [recordings, setRecordings] = useState([]);
  const [dieticians, setDieticians] = useState([]);
  const [trainingGaps, setTrainingGaps] = useState([]);
  const [settings] = useState({
    accountProfile: { name: 'QA Manager', role: 'Clinical QA Lead', email: 'qa@dietician.local', avatar: '' },
    rubricWeights: { nutritionalAccuracy: 40, patientEmpathy: 25, sopAdherence: 20, actionPlanClarity: 15 },
    platformPreferences: { dataRetentionPolicy: '1 Year', qaAlertTriggers: 70, defaultTimezone: 'EST', primaryLanguage: 'English (US)' },
    teamMembers: []
  });

  useEffect(() => {
    setCurrentView(view);
  }, [view]);

  const handleUploadFile = (fileName) => {
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
    setCurrentView('upload');
  };

  const handleSelectCall = (id) => {
    setSelectedCallId(id);
    setCurrentView('insights');
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden font-sans bg-background text-on-background">
      <Sidebar
        currentView={currentView}
        onViewChange={(newView) => {
          setCurrentView(newView);
          setSearchQuery('');
        }}
        onTriggerUpload={() => handleUploadFile('my_uploaded_clinical_audio.wav')}
        activeProcessingCount={activeQueue.length}
      />

      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        <Header
          currentView={currentView}
          settings={settings}
          searchQuery={searchQuery}
          onSearchQueryChange={setSearchQuery}
          criticalAlerts={[]}
        />

        <main className="flex-1 overflow-hidden relative">
          {currentView === 'dashboard' && <DashboardView recordings={recordings} onSelectCall={handleSelectCall} dieticians={dieticians} searchQuery={searchQuery} />}
          {currentView === 'upload' && <CallUploadView activeQueue={activeQueue} completedRecordings={recordings} onSelectCall={handleSelectCall} onUploadFile={handleUploadFile} />}
          {currentView === 'transcriptions' && <TranscriptionsView recordings={recordings} onSelectCall={handleSelectCall} searchQuery={searchQuery} />}
          {currentView === 'insights' && <AIInsightsView completedRecordings={recordings} selectedCallId={selectedCallId} onSelectCallId={setSelectedCallId} />}
          {currentView === 'reports' && <DieticianReportsView dieticians={dieticians} trainingGaps={trainingGaps} onAssignTraining={() => {}} searchQuery={searchQuery} />}
          {currentView === 'alerts' && <QAAlertsView alerts={[]} onSelectCall={handleSelectCall} onToggleAlertStatus={() => {}} searchQuery={searchQuery} />}
        </main>
      </div>
    </div>
  );
}
