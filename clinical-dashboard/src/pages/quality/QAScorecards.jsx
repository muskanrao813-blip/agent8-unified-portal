import { useState, useEffect } from "react";

export default function QAScorecards() {
  const [scorecards, setScorecards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    const fetchScorecards = async () => {
      setLoading(true);
      try {
        const response = await fetch("/api/qa/scorecards");
        const data = await response.json();
        setScorecards(data || []);
      } catch (error) {
        console.error("Failed to fetch scorecards:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchScorecards();
  }, []);

  const filtered = scorecards.filter(s => {
    if (filter === "critical") return s.overall_weighted_score < 70;
    if (filter === "warning") return s.overall_weighted_score >= 70 && s.overall_weighted_score < 80;
    if (filter === "good") return s.overall_weighted_score >= 80;
    return true;
  });

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
        .qa-filter-btn {
          padding: 0.75rem 1.5rem;
          background: transparent;
          border: 1px solid #e2e8f0;
          color: #64748b;
          font-weight: 600;
          cursor: pointer;
          border-radius: 8px;
          transition: all 0.3s ease;
          font-size: 0.95rem;
        }
        .qa-filter-btn:hover {
          color: #3b82f6;
          background: rgba(59, 130, 246, 0.05);
        }
        .qa-filter-btn.active {
          background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
          color: white;
          border-color: transparent;
          box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
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
      `}</style>

      <div className="qa-container">
        {/* Header */}
        <div style={{ marginBottom: "2rem" }}>
          <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.5rem" }}>
            📋 QA Scorecards
          </div>
          <div style={{ fontSize: "1rem", color: "#64748b" }}>
            Call quality analysis and compliance scores
          </div>
        </div>

        {/* Filters */}
        <div className="qa-section" style={{ marginBottom: "1.5rem" }}>
          <div className="qa-section-title">
            <i>🔍</i> Filter Calls
          </div>
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
            {[
              { value: "all", label: "All Calls", icon: "📞" },
              { value: "critical", label: "Critical (<70)", icon: "🔴" },
              { value: "warning", label: "Warning (70-80)", icon: "🟡" },
              { value: "good", label: "Good (80+)", icon: "🟢" }
            ].map(f => (
              <button
                key={f.value}
                onClick={() => setFilter(f.value)}
                className={`qa-filter-btn ${filter === f.value ? "active" : ""}`}
              >
                {f.icon} {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Scorecards Table */}
        {!loading && (
          <div className="qa-section">
            <div className="qa-section-title">
              <i>⭐</i> Call Scorecards
            </div>
            <table className="qa-table">
              <thead>
                <tr>
                  <th>Call ID</th>
                  <th>Dietician</th>
                  <th style={{ textAlign: "center" }}>Greeting</th>
                  <th style={{ textAlign: "center" }}>Empathy</th>
                  <th style={{ textAlign: "center" }}>Compliance</th>
                  <th style={{ textAlign: "center" }}>Technical</th>
                  <th style={{ textAlign: "center" }}>Overall Score</th>
                  <th style={{ textAlign: "center" }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length > 0 ? (
                  filtered.map((score, i) => (
                    <tr key={i}>
                      <td style={{ fontFamily: "monospace", fontSize: "0.85rem" }}>{score.call_id?.substring(0, 8) || "—"}</td>
                      <td>{score.dietician_name || "Unknown"}</td>
                      <td style={{ textAlign: "center", fontWeight: 600 }}>{score.greeting_score || 0}%</td>
                      <td style={{ textAlign: "center", fontWeight: 600 }}>{score.empathy_score || 0}%</td>
                      <td style={{ textAlign: "center", fontWeight: 600 }}>{score.compliance_score || 0}%</td>
                      <td style={{ textAlign: "center", fontWeight: 600 }}>{score.technical_score || 0}%</td>
                      <td style={{
                        textAlign: "center",
                        fontWeight: 700,
                        color: score.overall_weighted_score >= 80 ? "#10b981" : score.overall_weighted_score >= 70 ? "#f59e0b" : "#ef4444"
                      }}>
                        {score.overall_weighted_score}%
                      </td>
                      <td style={{ textAlign: "center" }}>
                        <span className={`qa-badge ${
                          score.overall_weighted_score < 70 ? "qa-badge-critical" :
                          score.overall_weighted_score < 80 ? "qa-badge-warning" : "qa-badge-good"
                        }`}>
                          {score.overall_weighted_score < 70 ? "CRITICAL" :
                           score.overall_weighted_score < 80 ? "WARNING" : "GOOD"}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="8" style={{ padding: "2rem", textAlign: "center", color: "#64748b" }}>
                      No scorecards found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {loading && (
          <div style={{ textAlign: "center", color: "#64748b", padding: "3rem", fontSize: "1.1rem" }}>
            Loading QA scorecards...
          </div>
        )}
      </div>
    </div>
  );
}
