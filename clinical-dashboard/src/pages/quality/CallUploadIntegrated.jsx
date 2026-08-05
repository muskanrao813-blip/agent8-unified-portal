import { useState, useEffect } from "react";
import { T } from "../../tokens";

export default function CallUploadIntegrated() {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [processingCalls, setProcessingCalls] = useState([]);
  const [completedCalls, setCompletedCalls] = useState([]);
  const API_URL = "http://localhost:8000/api";

  useEffect(() => {
    fetchCalls();
    const interval = setInterval(fetchCalls, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchCalls = async () => {
    try {
      const response = await fetch(`${API_URL}/calls/`);
      const data = await response.json();
      const processing = data.filter(c => c.status === "processing" || c.status === "pending");
      const completed = data.filter(c => c.status === "completed").slice(0, 10);
      setProcessingCalls(processing);
      setCompletedCalls(completed);
    } catch (error) {
      console.error("Failed to fetch calls:", error);
    }
  };

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
    setUploadMessage("Uploading...");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_URL}/calls/bulk-upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      setUploadMessage(`Success: ${data.valid_rows} calls added, ${data.invalid_rows} invalid`);
      fetchCalls();
    } catch (error) {
      setUploadMessage(`Error: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files?.[0]) {
      uploadFile(e.target.files[0]);
    }
  };

  return (
    <div style={{
      flex: 1,
      overflow: "auto",
      padding: "2rem",
      background: T.offwhite,
    }}>
      <style>{`
        .upload-container {
          max-width: 1200px;
          margin: 0 auto;
        }
        .upload-section {
          background: ${T.white};
          border-radius: 12px;
          padding: 2rem;
          margin-bottom: 2rem;
          box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
        .upload-title {
          font-size: 1.2rem;
          font-weight: 700;
          color: ${T.black};
          margin-bottom: 1.5rem;
        }
        .drop-zone {
          border: 2px dashed ${dragOver ? "#3b82f6" : "#cbd5e1"};
          border-radius: 8px;
          padding: 2rem;
          text-align: center;
          cursor: pointer;
          background: ${dragOver ? "#eff6ff" : T.offwhite};
          transition: all 0.2s;
        }
        .drop-zone:hover {
          border-color: #3b82f6;
          background: #eff6ff;
        }
        .file-input {
          display: none;
        }
        .call-table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 1rem;
        }
        .call-table th, .call-table td {
          padding: 0.75rem;
          text-align: left;
          border-bottom: 1px solid #e2e8f0;
        }
        .call-table th {
          background: #f8fafc;
          font-weight: 600;
          color: #1e293b;
        }
        .status-badge {
          display: inline-block;
          padding: 0.25rem 0.75rem;
          border-radius: 4px;
          font-size: 0.875rem;
          font-weight: 600;
        }
        .status-pending {
          background: #fef3c7;
          color: #92400e;
        }
        .status-processing {
          background: #bfdbfe;
          color: #1e40af;
        }
        .status-completed {
          background: #dcfce7;
          color: #15803d;
        }
      `}</style>

      <div className="upload-container">
        {/* Upload Section */}
        <div className="upload-section">
          <div className="upload-title">📤 Upload Call Recordings</div>
          <div
            className="drop-zone"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById("fileInput").click()}
          >
            <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>📁</div>
            <div style={{ fontWeight: 600, color: T.black, marginBottom: "0.25rem" }}>
              Drag Excel file here or click to browse
            </div>
            <div style={{ fontSize: "0.875rem", color: T.gray600 }}>
              Supported: .xlsx, .xls (with columns: dietician_name, patient_id, patient_name, appointment_id, recording_url)
            </div>
            <input
              id="fileInput"
              type="file"
              className="file-input"
              accept=".xlsx,.xls"
              onChange={handleFileSelect}
            />
          </div>
          {uploadMessage && (
            <div style={{
              marginTop: "1rem",
              padding: "0.75rem",
              borderRadius: "4px",
              background: uploadMessage.includes("Error") ? "#fee2e2" : "#dcfce7",
              color: uploadMessage.includes("Error") ? "#991b1b" : "#15803d",
            }}>
              {uploadMessage}
            </div>
          )}
        </div>

        {/* Processing Calls */}
        {processingCalls.length > 0 && (
          <div className="upload-section">
            <div className="upload-title">⏳ Processing ({processingCalls.length})</div>
            <table className="call-table">
              <thead>
                <tr>
                  <th>Dietician</th>
                  <th>Patient</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {processingCalls.map(call => (
                  <tr key={call.id}>
                    <td>{call.dietician_name || "N/A"}</td>
                    <td>{call.patient_name || "N/A"}</td>
                    <td>
                      <span className={`status-badge status-${call.status}`}>
                        {call.status === "pending" ? "Pending" : "Processing"}
                      </span>
                    </td>
                    <td>{new Date(call.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Completed Calls */}
        {completedCalls.length > 0 && (
          <div className="upload-section">
            <div className="upload-title">✅ Completed Calls (Latest 10)</div>
            <table className="call-table">
              <thead>
                <tr>
                  <th>Dietician</th>
                  <th>Patient</th>
                  <th>QA Score</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {completedCalls.map(call => (
                  <tr key={call.id}>
                    <td>{call.dietician_name || "N/A"}</td>
                    <td>{call.patient_name || "N/A"}</td>
                    <td>
                      <span style={{
                        fontWeight: 600,
                        color: call.overall_weighted_score >= 80 ? "#15803d" :
                               call.overall_weighted_score >= 70 ? "#92400e" : "#991b1b"
                      }}>
                        {call.overall_weighted_score ? `${call.overall_weighted_score.toFixed(1)}/100` : "N/A"}
                      </span>
                    </td>
                    <td>{new Date(call.created_at).toLocaleDateString()}</td>
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
