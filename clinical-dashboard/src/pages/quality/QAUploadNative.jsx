import { useState, useEffect } from "react";
import { T } from "../../tokens";

export default function QAUpload() {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [calls, setCalls] = useState([]);
  const API_BASE = "http://localhost:8000/api";

  useEffect(() => {
    fetchCalls();
    const interval = setInterval(fetchCalls, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchCalls = async () => {
    try {
      const response = await fetch(`${API_BASE}/calls/`);
      const data = await response.json();
      setCalls(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Error fetching calls:", error);
    }
  };

  const handleUpload = async (file) => {
    if (!file.name.endsWith(".xlsx") && !file.name.endsWith(".xls")) {
      setMessage("❌ Please upload an Excel file (.xlsx or .xls)");
      return;
    }

    setUploading(true);
    setMessage("📤 Uploading...");

    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(`${API_BASE}/calls/bulk-upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      setMessage(`✅ Success! ${data.valid_rows || 0} calls added`);
      fetchCalls();
    } catch (error) {
      setMessage(`❌ Error: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const processing = calls.filter(c => c.status === "processing" || c.status === "pending");
  const completed = calls.filter(c => c.status === "completed");

  return (
    <div style={{ padding: "2rem", background: T.offwhite, overflow: "auto", flex: 1 }}>
      <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "2rem", color: T.black }}>
          Call Upload
        </h2>

        {/* Upload Zone */}
        <div style={{
          background: T.white,
          borderRadius: "8px",
          padding: "2rem",
          marginBottom: "2rem",
          boxShadow: "0 2px 8px rgba(0,0,0,0.06)"
        }}>
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              if (e.dataTransfer.files[0]) handleUpload(e.dataTransfer.files[0]);
            }}
            onClick={() => document.getElementById("fileInput").click()}
            style={{
              border: `2px dashed ${dragOver ? "#3b82f6" : "#cbd5e1"}`,
              borderRadius: "8px",
              padding: "2rem",
              textAlign: "center",
              cursor: "pointer",
              background: dragOver ? "#eff6ff" : T.offwhite,
              transition: "all 0.2s"
            }}
          >
            <div style={{ fontSize: "2rem", marginBottom: "1rem" }}>📁</div>
            <div style={{ fontWeight: 600, color: T.black, marginBottom: "0.5rem" }}>
              Drag Excel file here or click to browse
            </div>
            <div style={{ fontSize: "0.875rem", color: T.gray600 }}>
              Supported: .xlsx, .xls with columns: dietician_name, patient_id, patient_name, appointment_id, recording_url
            </div>
            <input
              id="fileInput"
              type="file"
              accept=".xlsx,.xls"
              onChange={(e) => e.target.files[0] && handleUpload(e.target.files[0])}
              style={{ display: "none" }}
            />
          </div>

          {message && (
            <div style={{
              marginTop: "1rem",
              padding: "0.75rem",
              borderRadius: "4px",
              background: message.includes("❌") ? "#fee2e2" : "#dcfce7",
              color: message.includes("❌") ? "#991b1b" : "#15803d"
            }}>
              {message}
            </div>
          )}
        </div>

        {/* Processing */}
        {processing.length > 0 && (
          <div style={{
            background: T.white,
            borderRadius: "8px",
            padding: "1.5rem",
            marginBottom: "2rem",
            boxShadow: "0 2px 8px rgba(0,0,0,0.06)"
          }}>
            <h3 style={{ fontWeight: 600, marginBottom: "1rem", color: T.black }}>
              ⏳ Processing ({processing.length})
            </h3>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${T.gray200}` }}>
                  <th style={{ textAlign: "left", padding: "0.75rem", fontWeight: 600 }}>Dietician</th>
                  <th style={{ textAlign: "left", padding: "0.75rem", fontWeight: 600 }}>Patient</th>
                  <th style={{ textAlign: "left", padding: "0.75rem", fontWeight: 600 }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {processing.map(call => (
                  <tr key={call.id} style={{ borderBottom: `1px solid ${T.gray200}` }}>
                    <td style={{ padding: "0.75rem" }}>{call.dietician_name || "N/A"}</td>
                    <td style={{ padding: "0.75rem" }}>{call.patient_name || "N/A"}</td>
                    <td style={{ padding: "0.75rem" }}>
                      <span style={{
                        background: "#bfdbfe",
                        color: "#1e40af",
                        padding: "0.25rem 0.5rem",
                        borderRadius: "4px",
                        fontSize: "0.875rem",
                        fontWeight: 600
                      }}>
                        Processing
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Completed */}
        {completed.length > 0 && (
          <div style={{
            background: T.white,
            borderRadius: "8px",
            padding: "1.5rem",
            boxShadow: "0 2px 8px rgba(0,0,0,0.06)"
          }}>
            <h3 style={{ fontWeight: 600, marginBottom: "1rem", color: T.black }}>
              ✅ Completed ({completed.length})
            </h3>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${T.gray200}` }}>
                  <th style={{ textAlign: "left", padding: "0.75rem", fontWeight: 600 }}>Dietician</th>
                  <th style={{ textAlign: "left", padding: "0.75rem", fontWeight: 600 }}>Patient</th>
                  <th style={{ textAlign: "left", padding: "0.75rem", fontWeight: 600 }}>QA Score</th>
                </tr>
              </thead>
              <tbody>
                {completed.slice(0, 10).map(call => (
                  <tr key={call.id} style={{ borderBottom: `1px solid ${T.gray200}` }}>
                    <td style={{ padding: "0.75rem" }}>{call.dietician_name || "N/A"}</td>
                    <td style={{ padding: "0.75rem" }}>{call.patient_name || "N/A"}</td>
                    <td style={{
                      padding: "0.75rem",
                      fontWeight: 600,
                      color: call.overall_weighted_score >= 80 ? "#15803d" :
                             call.overall_weighted_score >= 70 ? "#92400e" : "#991b1b"
                    }}>
                      {call.overall_weighted_score ? `${call.overall_weighted_score.toFixed(1)}/100` : "N/A"}
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
