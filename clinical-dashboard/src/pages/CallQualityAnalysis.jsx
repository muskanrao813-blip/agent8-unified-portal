import DashboardView from './quality/DashboardView';
import CallUploadView from './quality/CallUploadView';
import TranscriptionsView from './quality/TranscriptionsView';
import AIInsightsView from './quality/AIInsightsView';
import DieticianReportsView from './quality/DieticianReportsView';
import QAAlertsView from './quality/QAAlertsView';
import { useState, useEffect } from 'react';
import { useClinicalAPI } from '../hooks/useClinicalAPI';

export default function CallQualityAnalysis({ view = "dashboard" }) {
  const { recordings, loading, error } = useClinicalAPI();
  const [selectedCallId, setSelectedCallId] = useState(null);
  const [activeQueue, setActiveQueue] = useState([]);
  const [dieticians, setDieticians] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (recordings?.length > 0) {
      const completed = recordings.filter(r => r.status === 'completed');
      if (completed.length > 0) {
        // Extract dietician data from recordings
        const uniqueDieticians = [...new Set(recordings.map(r => r.agentName))];
        setDieticians(uniqueDieticians.map(name => ({ name, callsCompleted: recordings.filter(r => r.agentName === name && r.status === 'completed').length })));
      }
    }
  }, [recordings]);

  const renderContent = () => {
    switch (view) {
      case 'dashboard':
        return <DashboardView recordings={recordings} onSelectCall={(id) => setSelectedCallId(id)} dieticians={dieticians} searchQuery={searchQuery} />;
      case 'upload':
        return <CallUploadView activeQueue={activeQueue} completedRecordings={recordings} onSelectCall={(id) => setSelectedCallId(id)} />;
      case 'transcriptions':
        return <TranscriptionsView recordings={recordings} onSelectCall={(id) => setSelectedCallId(id)} searchQuery={searchQuery} />;
      case 'insights':
        return <AIInsightsView completedRecordings={recordings} selectedCallId={selectedCallId} onSelectCallId={setSelectedCallId} />;
      case 'reports':
        return <DieticianReportsView dieticians={dieticians} trainingGaps={[]} onAssignTraining={() => {}} searchQuery={searchQuery} />;
      case 'alerts':
        return <QAAlertsView alerts={recordings?.filter(r => r.qaAlerts?.length > 0).flatMap(r => r.qaAlerts) || []} onSelectCall={(id) => setSelectedCallId(id)} searchQuery={searchQuery} />;
      default:
        return <DashboardView recordings={recordings} onSelectCall={(id) => setSelectedCallId(id)} dieticians={dieticians} searchQuery={searchQuery} />;
    }
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden', background: 'white' }}>
      {error && (
        <div style={{ backgroundColor: '#fecaca', borderBottom: '1px solid #fca5a5', padding: '12px 16px', fontSize: '14px', color: '#991b1b' }}>
          <strong>API Error:</strong> {error}
        </div>
      )}
      {renderContent()}
    </div>
  );
}
