import { useState, useEffect } from "react";
import { T } from "../../tokens";

export default function QAInsights() {
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const API_BASE = "http://localhost:8000/api";

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    try {
      const response = await fetch(`${API_BASE}/calls/`);
      const data = await response.json();
      const completed = (Array.isArray(data) ? data : []).filter(c => c.status === "completed");
      setInsights(completed);
    } catch (error) {
      console.error("Error fetching insights:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "2rem", background: T.offwhite, overflow: "auto", flex: 1 }}>
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "2rem", color: T.black }}>
          AI Insights
        </h2>

        {loading ? (
          <p style={{ color: T.gray600 }}>Loading insights...</p>
        ) : insights.length === 0 ? (
          <p style={{ color: T.gray600 }}>No insights available</p>
        ) : (
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))",
            gap: "1.5rem"
          }}>
            {insights.map(call => (
              <div key={call.id} style={{
                background: T.white,
                borderRadius: "8px",
                padding: "1.5rem",
                boxShadow: "0 2px 8px rgba(0,0,0,0.06)"
              }}>
                <h3 style={{ fontWeight: 600, color: T.black, marginBottom: "0.5rem" }}>
                  {call.dietician_name}
                </h3>
                <p style={{ fontSize: "0.875rem", color: T.gray600, marginBottom: "1rem" }}>
                  Patient: {call.patient_name || "N/A"}
                </p>

                <div style={{
                  background: T.gray50,
                  padding: "1rem",
                  borderRadius: "6px",
                  marginBottom: "1rem"
                }}>
                  <div style={{ fontSize: "0.875rem", color: T.gray600, marginBottom: "0.5rem" }}>
                    QA Score
                  </div>
                  <div style={{
                    fontSize: "2rem",
                    fontWeight: 700,
                    color: call.overall_weighted_score >= 80 ? "#15803d" :
                           call.overall_weighted_score >= 70 ? "#92400e" : "#991b1b"
                  }}>
                    {call.overall_weighted_score ? call.overall_weighted_score.toFixed(1) : "N/A"}/100
                  </div>
                </div>

                <div style={{ fontSize: "0.875rem", color: T.gray600 }}>
                  📅 {new Date(call.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
