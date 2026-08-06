import React, { useState, useEffect } from 'react';

export default function CallQualityAnalysis({ view = "dashboard" }) {
  const [currentView, setCurrentView] = useState(view);

  useEffect(() => {
    setCurrentView(view);
  }, [view]);

  const tabsList = [
    { id: 'dashboard', name: 'Dashboard' },
    { id: 'upload', name: 'Call Upload' },
    { id: 'transcriptions', name: 'Transcriptions' },
    { id: 'insights', name: 'AI Insights' },
    { id: 'reports', name: 'Reports' },
    { id: 'alerts', name: 'QA Alerts' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'dashboard':
        return <div style={{ padding: '20px' }}><h2>Dashboard</h2><p>Welcome to Call Quality Dashboard</p></div>;
      case 'upload':
        return <div style={{ padding: '20px' }}><h2>Call Upload</h2><p>Upload call recordings here</p></div>;
      case 'transcriptions':
        return <div style={{ padding: '20px' }}><h2>Transcriptions</h2><p>View call transcriptions</p></div>;
      case 'insights':
        return <div style={{ padding: '20px' }}><h2>AI Insights</h2><p>AI-powered call analysis</p></div>;
      case 'reports':
        return <div style={{ padding: '20px' }}><h2>Reports</h2><p>Performance reports</p></div>;
      case 'alerts':
        return <div style={{ padding: '20px' }}><h2>QA Alerts</h2><p>Quality assurance alerts</p></div>;
      default:
        return null;
    }
  };

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', backgroundColor: '#f5f5f5' }}>
      {/* Tab Navigation */}
      <div style={{ display: 'flex', gap: '0px', backgroundColor: 'white', borderBottom: '1px solid #ddd', padding: '0px' }}>
        {tabsList.map(tab => (
          <button
            key={tab.id}
            onClick={() => setCurrentView(tab.id)}
            style={{
              padding: '12px 20px',
              border: 'none',
              backgroundColor: currentView === tab.id ? '#0066cc' : 'white',
              color: currentView === tab.id ? 'white' : '#333',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: currentView === tab.id ? 'bold' : 'normal',
              borderBottom: currentView === tab.id ? '3px solid #0066cc' : 'none'
            }}
          >
            {tab.name}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div style={{ flex: 1, overflow: 'auto', backgroundColor: 'white' }}>
        {renderContent()}
      </div>
    </div>
  );
}
