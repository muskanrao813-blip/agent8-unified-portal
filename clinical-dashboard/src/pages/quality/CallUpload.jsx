import { useState, useEffect } from "react";

export default function CallUpload() {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [processingCalls, setProcessingCalls] = useState([]);
  const [completedCalls, setCompletedCalls] = useState([]);

  useEffect(() => {
    const fetchCalls = async () => {
      try {
        const response = await fetch("/api/qa/calls");
        const data = await response.json();
        const processing = data.filter(c => c.status === "processing" || c.status === "pending");
        const completed = data.filter(c => c.status === "completed");
        setProcessingCalls(processing);
        setCompletedCalls(completed.slice(0, 10));
      } catch (error) {
        console.error("Failed to fetch calls:", error);
      }
    };

    fetchCalls();
    const interval = setInterval(fetchCalls, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files?.[0]) {
      uploadFile(e.dataTransfer.files[0]);
    }
  };

  const uploadFile = async (file) => {
    if (!file.name.endsWith(".xlsx") && !file.name.endsWith(".xls")) {
      setUploadMessage("Error: Please upload an Excel file");
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch("/api/qa/calls/bulk-upload", {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      setUploadMessage(`✓ Successfully uploaded! Processed ${data.valid_rows} rows.`);
      setTimeout(() => setUploadMessage(""), 3000);
    } catch (error) {
      setUploadMessage(`Error: ${error.message}`);
      setTimeout(() => setUploadMessage(""), 3000);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ flex: 1, overflow: "auto", background: "#f8fafc", padding: "2.5rem 1.5rem" }}>
      <style>{`
        .qa-container { max-width: 1400px; margin: 0 auto; }
        .qa-section {
          background: white;
          border-radius: 12px;
          padding: 2rem;
          margin-bottom: 2rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        }
        .qa-section-title {
          font-size: 1.2rem;
          font-weight: 700;
          color: #1e293b;
          margin-bottom: 1.5rem;
          padding-bottom: 1rem;
          border-bottom: 3px solid #3b82f6;
          display: flex;
          align-items: center;
          gap: 0.8rem;
        }
        .qa-dropzone {
          border: 2px dashed #3b82f6;
          border-radius: 12px;
          padding: 3rem;
          text-align: center;
          background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(30, 64, 175, 0.05) 100%);
          cursor: pointer;
          transition: all 0.3s ease;
        }
        .qa-dropzone:hover,
        .qa-dropzone.dragover {
          background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(30, 64, 175, 0.1) 100%);
          border-color: #1e40af;
          transform: scale(1.02);
        }
        .qa-dropzone-text {
          font-size: 1.1rem;
          font-weight: 600;
          color: #1e293b;
          margin-bottom: 0.5rem;
        }
        .qa-dropzone-subtext {
          font-size: 0.9rem;
          color: #64748b;
        }
        .qa-table {
          width: 100%;
          border-collapse: collapse;
        }
        .qa-table thead {
          background: #f0f4f8;
        }
        .qa-table th {
          padding: 1rem;
          text-align: left;
          font-weight: 700;
          color: #475569;
          font-size: 0.85rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          border-bottom: 2px solid #e2e8f0;
        }
        .qa-table td {
          padding: 1rem;
          border-bottom: 1px solid #e2e8f0;
          color: #475569;
        }
        .qa-table tbody tr:hover {
          background: #f8fafc;
        }
      `}</style>

      <div className="qa-container">
        {/* Header */}
        <div style={{ marginBottom: "2rem" }}>
          <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.5rem" }}>
            📤 Upload Call Recordings
          </div>
          <div style={{ fontSize: "1rem", color: "#64748b" }}>
            Upload Excel with recording URLs or drag audio files
          </div>
        </div>

        {/* Upload Zone */}
        <div className="qa-section">
          <div className="qa-section-title">
            <i>☁️</i> Upload Audio or Bulk Records
          </div>
          <div
            className={`qa-dropzone ${dragOver ? "dragover" : ""}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById("file-input")?.click()}
          >
            <div style={{ marginBottom: "1rem", fontSize: "3rem" }}>🎙️</div>
            <input
              id="file-input"
              type="file"
              accept=".xlsx,.xls,.mp3,.wav,.flac,.m4a,.ogg,.webm"
              onChange={(e) => e.target.files?.[0] && uploadFile(e.target.files[0])}
              style={{ display: "none" }}
            />
            <div className="qa-dropzone-text">Drag and drop your file here</div>
            <div className="qa-dropzone-subtext">MP3, WAV, FLAC, M4A, OGG, WEBM, or Excel (.xlsx, .xls)</div>
            {uploading && <div style={{ marginTop: "1rem", color: "#f59e0b", fontWeight: 600 }}>Uploading...</div>}
            {uploadMessage && (
              <div style={{
                marginTop: "1rem",
                color: uploadMessage.startsWith("Error") ? "#ef4444" : "#10b981",
                fontWeight: 600
              }}>
                {uploadMessage}
              </div>
            )}
          </div>
        </div>

        {/* Processing Queue */}
        {processingCalls.length > 0 && (
          <div className="qa-section">
            <div className="qa-section-title">
              <i>⏳</i> Processing Queue ({processingCalls.length})
            </div>
            <table className="qa-table">
              <thead>
                <tr>
                  <th>Appointment</th>
                  <th>Patient</th>
                  <th>Dietician</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {processingCalls.map((call, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 600 }}>{call.appointment_id}</td>
                    <td>{call.patient_name}</td>
                    <td>{call.dietician_name}</td>
                    <td>
                      <span style={{
                        padding: "0.4rem 0.8rem",
                        borderRadius: "6px",
                        fontSize: "0.8rem",
                        fontWeight: 600,
                        background: "#dbeafe",
                        color: "#0c4a6e"
                      }}>
                        {call.status === "processing" ? "🔄 Processing" : "⏸️ Queued"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Completed Calls */}
        {completedCalls.length > 0 && (
          <div className="qa-section">
            <div className="qa-section-title">
              <i>✅</i> Completed ({completedCalls.length})
            </div>
            <table className="qa-table">
              <thead>
                <tr>
                  <th>Appointment</th>
                  <th>Patient</th>
                  <th>QA Score</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {completedCalls.map((call, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 600 }}>{call.appointment_id}</td>
                    <td>{call.patient_name}</td>
                    <td>
                      <span style={{ fontWeight: 700, color: call.overall_weighted_score >= 80 ? "#10b981" : call.overall_weighted_score >= 70 ? "#f59e0b" : "#ef4444" }}>
                        {call.overall_weighted_score}%
                      </span>
                    </td>
                    <td>
                      <span style={{
                        padding: "0.4rem 0.8rem",
                        borderRadius: "6px",
                        fontSize: "0.8rem",
                        fontWeight: 600,
                        background: "#dcfce7",
                        color: "#166534"
                      }}>
                        ✓ Completed
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
