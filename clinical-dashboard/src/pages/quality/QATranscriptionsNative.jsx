import { useState, useEffect } from "react";
import { T } from "../../tokens";

export default function QATranscriptions() {
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCall, setSelectedCall] = useState(null);
  const API_BASE = "http://localhost:8000/api";

  useEffect(() => {
    fetchCalls();
  }, []);

  const fetchCalls = async () => {
    try {
      const response = await fetch(`${API_BASE}/calls/`);
      const data = await response.json();
      const completed = (Array.isArray(data) ? data : []).filter(c => c.status === "completed");
      setCalls(completed);
    } catch (error) {
      console.error("Error fetching calls:", error);
      setCalls([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "2rem", background: T.offwhite, overflow: "auto", flex: 1 }}>
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "2rem", color: T.black }}>
          Transcriptions
        </h2>

        {loading ? (
          <p style={{ color: T.gray600 }}>Loading transcriptions...</p>
        ) : calls.length === 0 ? (
          <p style={{ color: T.gray600 }}>No completed calls available</p>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}>
            {/* Calls List */}
            <div style={{
              background: T.white,
              borderRadius: "8px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
              overflow: "hidden"
            }}>
              <div style={{ borderBottom: `1px solid ${T.gray200}`, padding: "1rem", fontWeight: 600 }}>
                Calls ({calls.length})
              </div>
              <div style={{ maxHeight: "500px", overflow: "auto" }}>
                {calls.map(call => (
                  <div
                    key={call.id}
                    onClick={() => setSelectedCall(call)}
                    style={{
                      padding: "1rem",
                      borderBottom: `1px solid ${T.gray200}`,
                      cursor: "pointer",
                      background: selectedCall?.id === call.id ? T.gray50 : "transparent",
                      transition: "background 0.2s"
                    }}
                    onMouseEnter={(e) => {
                      if (selectedCall?.id !== call.id) {
                        e.currentTarget.style.background = T.gray100;
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = selectedCall?.id === call.id ? T.gray50 : "transparent";
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: "0.95rem", color: T.black, marginBottom: "0.25rem" }}>
                      {call.dietician_name || "Unknown"}
                    </div>
                    <div style={{ fontSize: "0.875rem", color: T.gray600 }}>
                      {call.patient_name || "N/A"} • {new Date(call.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Transcript View */}
            {selectedCall ? (
              <div style={{
                background: T.white,
                borderRadius: "8px",
                padding: "1.5rem",
                boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
                display: "flex",
                flexDirection: "column"
              }}>
                <div style={{ marginBottom: "1rem", paddingBottom: "1rem", borderBottom: `1px solid ${T.gray200}` }}>
                  <h3 style={{ fontWeight: 600, color: T.black, marginBottom: "0.5rem" }}>
                    {selectedCall.dietician_name} • {selectedCall.patient_name}
                  </h3>
                  <p style={{ fontSize: "0.875rem", color: T.gray600 }}>
                    {new Date(selectedCall.created_at).toLocaleString()}
                  </p>
                </div>

                <div style={{ flex: 1, overflow: "auto" }}>
                  <div style={{
                    padding: "1rem",
                    background: T.offwhite,
                    borderRadius: "6px",
                    fontSize: "0.95rem",
                    lineHeight: "1.6",
                    color: T.black,
                    fontFamily: "monospace",
                    whiteSpace: "pre-wrap",
                    wordWrap: "break-word"
                  }}>
                    {selectedCall.raw_transcript || selectedCall.reconstructed_transcript || "No transcript available"}
                  </div>
                </div>

                {selectedCall.overall_weighted_score && (
                  <div style={{
                    marginTop: "1rem",
                    padding: "1rem",
                    background: T.gray50,
                    borderRadius: "6px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center"
                  }}>
                    <span style={{ fontWeight: 600, color: T.black }}>QA Score:</span>
                    <span style={{
                      fontSize: "1.5rem",
                      fontWeight: 700,
                      color: selectedCall.overall_weighted_score >= 80 ? "#15803d" :
                             selectedCall.overall_weighted_score >= 70 ? "#92400e" : "#991b1b"
                    }}>
                      {selectedCall.overall_weighted_score.toFixed(1)}/100
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <div style={{
                background: T.white,
                borderRadius: "8px",
                padding: "2rem",
                boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
                textAlign: "center",
                color: T.gray600
              }}>
                Select a call to view transcript
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
