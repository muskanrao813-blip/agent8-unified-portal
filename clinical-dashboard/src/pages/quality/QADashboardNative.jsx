import { useState, useEffect } from "react";
import { T } from "../../tokens";

export default function QADashboard() {
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const API_BASE = "http://localhost:8000/api";

  useEffect(() => {
    const fetchCalls = async () => {
      try {
        const response = await fetch(`${API_BASE}/calls/`);
        const data = await response.json();
        setCalls(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error("Error fetching calls:", error);
        setCalls([]);
      } finally {
        setLoading(false);
      }
    };

    fetchCalls();
    const interval = setInterval(fetchCalls, 5000);
    return () => clearInterval(interval);
  }, []);

  const getScoreColor = (score) => {
    if (score >= 80) return { bg: "#dcfce7", text: "#15803d", label: "Excellent" };
    if (score >= 70) return { bg: "#fef3c7", text: "#92400e", label: "Good" };
    if (score >= 60) return { bg: "#fed7aa", text: "#92400e", label: "Fair" };
    return { bg: "#fee2e2", text: "#991b1b", label: "Critical" };
  };

  return (
    <div style={{ padding: "2rem", background: T.offwhite, overflow: "auto", flex: 1 }}>
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "2rem", color: T.black }}>
          QA Dashboard
        </h2>

        {loading ? (
          <p style={{ color: T.gray600 }}>Loading calls...</p>
        ) : calls.length === 0 ? (
          <p style={{ color: T.gray600 }}>No calls available</p>
        ) : (
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
            gap: "1.5rem"
          }}>
            {calls.map(call => {
              const scoreInfo = getScoreColor(call.overall_weighted_score || 0);
              return (
                <div
                  key={call.id}
                  style={{
                    background: T.white,
                    borderRadius: "8px",
                    padding: "1.5rem",
                    boxShadow: "0 2px 8px rgba(0,0,0,0.06)"
                  }}
                >
                  <div style={{ marginBottom: "1rem" }}>
                    <div style={{ fontWeight: 600, color: T.black }}>
                      {call.dietician_name || "Unknown"}
                    </div>
                    <div style={{ fontSize: "0.875rem", color: T.gray600 }}>
                      {call.patient_name || "N/A"}
                    </div>
                  </div>

                  <div style={{
                    background: scoreInfo.bg,
                    padding: "1rem",
                    borderRadius: "6px",
                    textAlign: "center",
                    marginBottom: "1rem"
                  }}>
                    <div style={{
                      fontSize: "2rem",
                      fontWeight: 700,
                      color: scoreInfo.text,
                      marginBottom: "0.25rem"
                    }}>
                      {call.overall_weighted_score ? call.overall_weighted_score.toFixed(1) : "N/A"}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: scoreInfo.text, fontWeight: 600 }}>
                      {scoreInfo.label}
                    </div>
                  </div>

                  <div style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "0.75rem",
                    fontSize: "0.875rem"
                  }}>
                    <div>
                      <span style={{ color: T.gray600 }}>Date:</span>
                      <br />
                      <span style={{ fontWeight: 500 }}>
                        {new Date(call.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div>
                      <span style={{ color: T.gray600 }}>Status:</span>
                      <br />
                      <span style={{
                        background: "#dcfce7",
                        color: "#15803d",
                        padding: "0.25rem 0.5rem",
                        borderRadius: "4px",
                        fontWeight: 600
                      }}>
                        {call.status === "completed" ? "Completed" : "Processing"}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
