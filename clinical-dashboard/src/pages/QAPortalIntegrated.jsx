import React, { useState, useEffect } from 'react';

// Minimal QA Portal implementation - direct React component rendering
export default function QAPortalIntegrated({ view = "dashboard" }) {
  const [recordings, setRecordings] = useState([]);
  const [selectedCallId, setSelectedCallId] = useState(null);

  useEffect(() => {
    // Fetch real data from backend when component mounts
    const fetchData = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'https://consultation-call-quality-analysis-system.onrender.com'}/api/recordings`);
        if (response.ok) {
          const data = await response.json();
          setRecordings(data);
        }
      } catch (error) {
        console.log('Failed to fetch recordings, using empty state');
      }
    };
    fetchData();
  }, []);

  // Dashboard View
  if (view === 'dashboard') {
    return (
      <div className="w-full h-full bg-white p-8 overflow-auto">
        <div className="max-w-7xl">
          <h1 className="text-2xl font-bold mb-6">Call Quality Dashboard</h1>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded border border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Calls</p>
                  <p className="text-3xl font-bold text-blue-900">{recordings.length}</p>
                </div>
                <div className="w-8 h-8 text-blue-500 text-xl">📞</div>
              </div>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded border border-green-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Completed</p>
                  <p className="text-3xl font-bold text-green-900">{recordings.filter(r => r.status === 'completed').length}</p>
                </div>
                <div className="w-8 h-8 text-green-500 text-xl">✅</div>
              </div>
            </div>
            <div className="bg-gradient-to-br from-red-50 to-red-100 p-6 rounded border border-red-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Alerts</p>
                  <p className="text-3xl font-bold text-red-900">{recordings.filter(r => r.qaAlerts?.length > 0).length}</p>
                </div>
                <div className="w-8 h-8 text-red-500 text-xl">⚠️</div>
              </div>
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded p-6">
            <h2 className="text-lg font-semibold mb-4">Recent Calls</h2>
            {recordings.length === 0 ? (
              <p className="text-gray-500">No recordings available</p>
            ) : (
              <div className="space-y-2">
                {recordings.slice(0, 5).map(rec => (
                  <div key={rec.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <span>{rec.name || rec.id}</span>
                    <span className="text-sm text-gray-600">{rec.date}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Call Upload View
  if (view === 'upload') {
    return (
      <div className="w-full h-full bg-white p-8 overflow-auto">
        <div className="max-w-2xl">
          <h1 className="text-2xl font-bold mb-6">Upload Call Recording</h1>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-gray-400 transition">
            <div className="text-5xl text-gray-400 mx-auto mb-4">📄</div>
            <h3 className="text-lg font-semibold mb-2">Drag & drop your audio file</h3>
            <p className="text-gray-600 mb-4">Supported formats: MP3, WAV, FLAC</p>
            <input type="file" id="file-upload" className="hidden" accept=".mp3,.wav,.flac" />
            <label htmlFor="file-upload" className="bg-blue-500 text-white px-6 py-2 rounded cursor-pointer hover:bg-blue-600">
              Choose File
            </label>
          </div>
        </div>
      </div>
    );
  }

  // Transcriptions View
  if (view === 'transcriptions') {
    return (
      <div className="w-full h-full bg-white p-8 overflow-auto">
        <div className="max-w-4xl">
          <h1 className="text-2xl font-bold mb-6">Call Transcriptions</h1>
          <div className="space-y-4">
            {recordings.length === 0 ? (
              <p className="text-gray-500">No transcriptions available</p>
            ) : (
              recordings.map(rec => (
                <div key={rec.id} className="border border-gray-200 rounded p-4 hover:bg-gray-50 cursor-pointer">
                  <h3 className="font-semibold">{rec.name}</h3>
                  <p className="text-sm text-gray-600">{rec.transcript ? rec.transcript.substring(0, 100) + '...' : 'No transcript'}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    );
  }

  // AI Insights View
  if (view === 'insights') {
    return (
      <div className="w-full h-full bg-white p-8 overflow-auto">
        <div className="max-w-4xl">
          <h1 className="text-2xl font-bold mb-6">AI Insights</h1>
          {selectedCallId ? (
            <div>
              <button onClick={() => setSelectedCallId(null)} className="text-blue-500 mb-4">← Back</button>
              <div className="bg-blue-50 border border-blue-200 rounded p-6">
                <h2 className="font-semibold mb-4">Call Analysis: {selectedCallId}</h2>
                <p className="text-gray-700">Detailed AI-powered insights for this call would appear here.</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {recordings.filter(r => r.status === 'completed').slice(0, 5).map(rec => (
                <div key={rec.id} onClick={() => setSelectedCallId(rec.id)} className="border border-gray-200 rounded p-4 hover:bg-blue-50 cursor-pointer">
                  <h3 className="font-semibold">{rec.name}</h3>
                  <p className="text-sm text-gray-600">Click to view insights</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Reports View
  if (view === 'reports') {
    return (
      <div className="w-full h-full bg-white p-8 overflow-auto">
        <div className="max-w-4xl">
          <h1 className="text-2xl font-bold mb-6">Dietician Reports</h1>
          <div className="bg-gray-50 border border-gray-200 rounded p-6">
            <p className="text-gray-600">Performance reports and analytics would appear here.</p>
          </div>
        </div>
      </div>
    );
  }

  // Alerts View
  if (view === 'alerts') {
    const alerts = recordings.filter(r => r.qaAlerts?.length > 0).flatMap(r => r.qaAlerts) || [];
    return (
      <div className="w-full h-full bg-white p-8 overflow-auto">
        <div className="max-w-4xl">
          <h1 className="text-2xl font-bold mb-6">QA Alerts</h1>
          {alerts.length === 0 ? (
            <p className="text-gray-500">No alerts</p>
          ) : (
            <div className="space-y-4">
              {alerts.map((alert, idx) => (
                <div key={idx} className="border-l-4 border-red-500 bg-red-50 p-4 rounded">
                  <p className="font-semibold">{alert.title || 'Alert'}</p>
                  <p className="text-sm text-gray-600">{alert.message}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  return <div className="w-full h-full bg-white p-8">Unknown view</div>;
}
