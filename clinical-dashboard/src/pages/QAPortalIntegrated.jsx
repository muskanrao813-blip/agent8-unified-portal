import React, { useState, useEffect } from 'react';

export default function QAPortalIntegrated({ view = "dashboard" }) {
  const [recordings, setRecordings] = useState([]);
  const [selectedCallId, setSelectedCallId] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const QA_BACKEND = 'https://consultation-call-quality-analysis-system.onrender.com';

  useEffect(() => {
    fetchRecordings();
  }, []);

  const fetchRecordings = async () => {
    try {
      const response = await fetch(`${QA_BACKEND}/api/calls`);
      if (response.ok) {
        const data = await response.json();
        setRecordings(Array.isArray(data) ? data : data.calls || []);
      }
    } catch (error) {
      console.error('Failed to fetch recordings:', error);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(false);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('dietician_name', 'Default'); // Optional: user can provide

    try {
      const response = await fetch(`${QA_BACKEND}/api/calls/audio-upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      setUploadSuccess(true);
      setUploadProgress(100);

      // Refresh recordings list
      setTimeout(() => {
        fetchRecordings();
        setUploadProgress(0);
      }, 2000);
    } catch (error) {
      setUploadError(error.message);
    } finally {
      setUploading(false);
    }
  };

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
                  <p className="text-3xl font-bold text-red-900">{recordings.filter(r => r.qa_alerts?.length > 0).length}</p>
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
                    <span>{rec.dietician_name || rec.call_id || 'Unknown'}</span>
                    <span className="text-sm text-gray-600">{rec.status || 'processing'}</span>
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

          {uploadSuccess && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded text-green-700">
              ✅ Upload successful! Processing started. Check the dashboard for progress.
            </div>
          )}

          {uploadError && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded text-red-700">
              ❌ Upload failed: {uploadError}
            </div>
          )}

          <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-gray-400 transition">
            <div className="text-5xl text-gray-400 mx-auto mb-4">🎙️</div>
            <h3 className="text-lg font-semibold mb-2">Drag & drop your audio file or click to browse</h3>
            <p className="text-gray-600 mb-6">Supported formats: MP3, WAV, FLAC, M4A, OGG</p>

            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".mp3,.wav,.flac,.m4a,.ogg"
              onChange={handleFileUpload}
              disabled={uploading}
            />

            <label
              htmlFor="file-upload"
              className={`inline-block px-6 py-2 rounded cursor-pointer font-semibold transition ${
                uploading
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              {uploading ? `Uploading... ${uploadProgress}%` : 'Choose File'}
            </label>

            {uploading && (
              <div className="mt-4">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>

          <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded">
            <h3 className="font-semibold text-blue-900 mb-2">What happens next:</h3>
            <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
              <li>Gemini API transcribes your audio to text</li>
              <li>Claude analyzes transcript for quality metrics</li>
              <li>QA scores are calculated automatically</li>
              <li>Results appear in the Dashboard within 2-5 minutes</li>
            </ol>
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
              recordings.filter(r => r.transcript).map(rec => (
                <div key={rec.id || rec.call_id} className="border border-gray-200 rounded p-4 hover:bg-gray-50 cursor-pointer">
                  <h3 className="font-semibold">{rec.dietician_name || rec.call_id || 'Unknown'}</h3>
                  <p className="text-sm text-gray-600 mt-2">{rec.transcript ? rec.transcript.substring(0, 200) + '...' : 'No transcript'}</p>
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
                <div key={rec.id || rec.call_id} onClick={() => setSelectedCallId(rec.id || rec.call_id)} className="border border-gray-200 rounded p-4 hover:bg-blue-50 cursor-pointer">
                  <h3 className="font-semibold">{rec.dietician_name || rec.call_id || 'Unknown'}</h3>
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
