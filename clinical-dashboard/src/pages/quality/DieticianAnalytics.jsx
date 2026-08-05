import { useState, useEffect } from "react";

export default function DieticianAnalytics() {
  const [dieticians, setDieticians] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDieticians = async () => {
      setLoading(true);
      try {
        const response = await fetch("/api/qa/dietician-analytics");
        const data = await response.json();
        setDieticians(data || []);
      } catch (error) {
        console.error("Failed to fetch dietician analytics:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDieticians();
  }, []);

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
        .qa-badge {
          padding: 0.5rem 0.9rem;
          border-radius: 6px;
          font-size: 0.8rem;
          font-weight: 700;
          display: inline-block;
        }
        .qa-badge-good { background: #dcfce7; color: #166534; }
        .qa-badge-warning { background: #fef3c7; color: #92400e; }
        .qa-badge-critical { background: #fee2e2; color: #7f1d1d; }
        .qa-trend {
          font-size: 0.9rem;
          font-weight: 600;
        }
        .qa-trend-up { color: #10b981; }
        .qa-trend-down { color: #ef4444; }
        .qa-trend-stable { color: #64748b; }
      `}</style>

      <div className="qa-container">
        {/* Header */}
        <div style={{ marginBottom: "2rem" }}>
          <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.5rem" }}>
            👥 Dietician Analytics
          </div>
          <div style={{ fontSize: "1rem", color: "#64748b" }}>
            Individual provider QA performance and recommendations
          </div>
        </div>

        {/* Analytics Table */}
        {!loading && (
          <div className="qa-section">
            <div className="qa-section-title">
              <i>📊</i> Performance Overview
            </div>
            <table className="qa-table">
              <thead>
                <tr>
                  <th>Dietician</th>
                  <th style={{ textAlign: "center" }}>Total Calls</th>
                  <th style={{ textAlign: "center" }}>Avg QA Score</th>
                  <th style={{ textAlign: "center" }}>Trend</th>
                  <th style={{ textAlign: "center" }}>SOP Breaches</th>
                  <th style={{ textAlign: "center" }}>Status</th>
                  <th>Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {dieticians.length > 0 ? (
                  dieticians.map((d, i) => (
                    <tr key={i}>
                      <td style={{ fontWeight: 600 }}>{d.name || "Unknown"}</td>
                      <td style={{ textAlign: "center", fontWeight: 600 }}>{d.total_calls || 0}</td>
                      <td style={{
                        textAlign: "center",
                        fontWeight: 700,
                        color: d.avg_score >= 80 ? "#10b981" : d.avg_score >= 70 ? "#f59e0b" : "#ef4444"
                      }}>
                        {d.avg_score?.toFixed(1) || 0}%
                      </td>
                      <td style={{ textAlign: "center" }}>
                        <span className={`qa-trend ${
                          d.trend === "up" ? "qa-trend-up" :
                          d.trend === "down" ? "qa-trend-down" :
                          "qa-trend-stable"
                        }`}>
                          {d.trend === "up" ? "↗ Improving" : d.trend === "down" ? "↘ Declining" : "→ Stable"}
                        </span>
                      </td>
                      <td style={{ textAlign: "center", fontWeight: 600 }}>{d.sop_breaches || 0}</td>
                      <td style={{ textAlign: "center" }}>
                        <span className={`qa-badge ${
                          d.avg_score < 70 ? "qa-badge-critical" :
                          d.avg_score < 80 ? "qa-badge-warning" :
                          "qa-badge-good"
                        }`}>
                          {d.avg_score < 70 ? "CRITICAL" : d.avg_score < 80 ? "WARNING" : "GOOD"}
                        </span>
                      </td>
                      <td style={{ fontSize: "0.9rem", color: "#64748b" }}>
                        {d.recommendation || "Maintain current performance"}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7" style={{ padding: "2rem", textAlign: "center", color: "#94a3b8" }}>
                      No data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {loading && (
          <div style={{ textAlign: "center", color: "#64748b", padding: "3rem", fontSize: "1.1rem" }}>
            Loading dietician analytics...
          </div>
        )}
      </div>
    </div>
  );
}
