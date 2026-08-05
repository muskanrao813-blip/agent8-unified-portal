import { useState, useEffect } from "react";
import { T } from "../../tokens";

export default function QAAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const API_BASE = "http://localhost:8000/api";

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE}/calls/`);
      const data = await response.json();

      // Generate alerts from calls
      const alertList = (Array.isArray(data) ? data : [])
        .filter(c => c.overall_weighted_score && c.overall_weighted_score < 70)
        .map(call => ({
          id: call.id,
          type: "Low QA Score",
          dietician: call.dietician_name,
          patient: call.patient_name,
          score: call.overall_weighted_score,
          date: call.created_at,
          severity: call.overall_weighted_score < 60 ? "critical" : "warning"
        }));

      setAlerts(alertList);
    } catch (error) {
      console.error("Error fetching alerts:", error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityStyle = (severity) => {
    if (severity === "critical") {
      return { bg: "#fee2e2", text: "#991b1b", label: "Critical" };
    }
    return { bg: "#fef3c7", text: "#92400e", label: "Warning" };
  };

  return (
    <div style={{ padding: "2rem", background: T.offwhite, overflow: "auto", flex: 1 }}>
      <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "2rem", color: T.black }}>
          QA Alerts ({alerts.length})
        </h2>

        {loading ? (
          <p style={{ color: T.gray600 }}>Loading alerts...</p>
        ) : alerts.length === 0 ? (
          <div style={{
            background: T.white,
            borderRadius: "8px",
            padding: "2rem",
            textAlign: "center",
            color: T.gray600,
            boxShadow: "0 2px 8px rgba(0,0,0,0.06)"
          }}>
            ✅ No alerts - all QA scores are good!
          </div>
        ) : (
          <div style={{ display: "grid", gap: "1rem" }}>
            {alerts.map(alert => {
              const style = getSeverityStyle(alert.severity);
              return (
                <div key={alert.id} style={{
                  background: T.white,
                  borderRadius: "8px",
                  padding: "1.5rem",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
                  borderLeft: `4px solid ${alert.severity === "critical" ? "#dc2626" : "#f59e0b"}`
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: "1rem" }}>
                    <div>
                      <h3 style={{ fontWeight: 600, color: T.black, marginBottom: "0.25rem" }}>
                        {alert.dietician}
                      </h3>
                      <p style={{ fontSize: "0.875rem", color: T.gray600 }}>
                        Patient: {alert.patient || "N/A"}
                      </p>
                    </div>
                    <span style={{
                      background: style.bg,
                      color: style.text,
                      padding: "0.5rem 1rem",
                      borderRadius: "4px",
                      fontWeight: 600,
                      fontSize: "0.875rem"
                    }}>
                      {style.label}
                    </span>
                  </div>

                  <div style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "1rem",
                    paddingTop: "1rem",
                    borderTop: `1px solid ${T.gray200}`
                  }}>
                    <div>
                      <div style={{ fontSize: "0.875rem", color: T.gray600, marginBottom: "0.25rem" }}>
                        QA Score
                      </div>
                      <div style={{
                        fontSize: "1.5rem",
                        fontWeight: 700,
                        color: alert.severity === "critical" ? "#dc2626" : "#f59e0b"
                      }}>
                        {alert.score.toFixed(1)}/100
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: "0.875rem", color: T.gray600, marginBottom: "0.25rem" }}>
                        Date
                      </div>
                      <div style={{ fontWeight: 500, color: T.black }}>
                        {new Date(alert.date).toLocaleDateString()}
                      </div>
                    </div>
                  </div>

                  <div style={{
                    marginTop: "1rem",
                    padding: "0.75rem",
                    background: T.gray50,
                    borderRadius: "4px",
                    fontSize: "0.875rem",
                    color: T.gray700
                  }}>
                    ⚠️ {alert.severity === "critical" ?
                      "Critical: Immediate training required" :
                      "Warning: Monitor performance"}
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
