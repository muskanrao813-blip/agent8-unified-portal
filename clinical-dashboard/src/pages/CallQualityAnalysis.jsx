import { useState, useEffect } from 'react';

export default function CallQualityAnalysis({ view = "dashboard" }) {
  const [currentView, setCurrentView] = useState(view);

  useEffect(() => {
    setCurrentView(view);
  }, [view]);

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'upload', label: 'Call Upload', icon: '📤' },
    { id: 'transcriptions', label: 'Transcriptions', icon: '📝' },
    { id: 'insights', label: 'AI Insights', icon: '💡' },
    { id: 'reports', label: 'Reports', icon: '📋' },
    { id: 'alerts', label: 'QA Alerts', icon: '⚠️' }
  ];

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return (
          <div className="p-8">
            <h1 className="text-3xl font-bold mb-4">Call Quality Dashboard</h1>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-blue-100 p-6 rounded">
                <p className="text-sm text-gray-600">Total Calls</p>
                <p className="text-2xl font-bold">0</p>
              </div>
              <div className="bg-green-100 p-6 rounded">
                <p className="text-sm text-gray-600">Completed</p>
                <p className="text-2xl font-bold">0</p>
              </div>
              <div className="bg-red-100 p-6 rounded">
                <p className="text-sm text-gray-600">Alerts</p>
                <p className="text-2xl font-bold">0</p>
              </div>
            </div>
          </div>
        );
      case 'upload':
        return (
          <div className="p-8">
            <h1 className="text-3xl font-bold mb-4">Call Upload</h1>
            <div className="border-2 border-dashed border-gray-300 rounded p-12 text-center">
              <p className="text-gray-600">Drag & drop audio files here</p>
              <p className="text-sm text-gray-400">Supported: MP3, WAV, FLAC</p>
            </div>
          </div>
        );
      case 'transcriptions':
        return (
          <div className="p-8">
            <h1 className="text-3xl font-bold mb-4">Transcriptions</h1>
            <p className="text-gray-600">No transcriptions available</p>
          </div>
        );
      case 'insights':
        return (
          <div className="p-8">
            <h1 className="text-3xl font-bold mb-4">AI Insights</h1>
            <p className="text-gray-600">Select a call to view insights</p>
          </div>
        );
      case 'reports':
        return (
          <div className="p-8">
            <h1 className="text-3xl font-bold mb-4">Reports</h1>
            <p className="text-gray-600">Performance reports would appear here</p>
          </div>
        );
      case 'alerts':
        return (
          <div className="p-8">
            <h1 className="text-3xl font-bold mb-4">QA Alerts</h1>
            <p className="text-gray-600">No active alerts</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-white">
      {/* Header with tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="flex gap-1 px-4 py-4 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setCurrentView(tab.id)}
              className={`px-4 py-2 rounded font-medium whitespace-nowrap transition ${
                currentView === tab.id
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-auto bg-gray-50">
        {renderView()}
      </div>
    </div>
  );
}
