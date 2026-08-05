import { useState, useEffect } from "react";
import { T } from "../../tokens";

export default function QAScorecardsIntegrated() {
  const [scorecards, setScorecards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [sortBy, setSortBy] = useState("score_desc");
  const API_URL = "http://localhost:8000/api";

  useEffect(() => {
    fetchScorecards();
    const interval = setInterval(fetchScorecards, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchScorecards = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/calls/`);
      const data = await response.json();
      const completed = data.filter(c => c.status === "completed");
      setScorecards(completed);
    } catch (error) {
      console.error("Failed to fetch scorecards:", error);
    } finally {
      setLoading(false);
    }
  };

  const filtered = scorecards.filter(s => {
    const score = s.overall_weighted_score || 0;
    if (filter === "critical") return score < 70;
    if (filter === "warning") return score >= 70 && score < 80;
    if (filter === "good") return score >= 80;
    return true;
  });

  const sorted = [...filtered].sort((a, b) => {
    const scoreA = a.overall_weighted_score || 0;
    const scoreB = b.overall_weighted_score || 0;
    if (sortBy === "score_desc") return scoreB - scoreA;
    if (sortBy === "score_asc") return scoreA - scoreB;
    if (sortBy === "date_new") return new Date(b.created_at) - new Date(a.created_at);
    if (sortBy === "date_old") return new Date(a.created_at) - new Date(b.created_at);
    return 0;
  });

  const getScoreColor = (score) => {
    if (score >= 80) return { bg: "#dcfce7", text: "#15803d", label: "Excellent" };
    if (score >= 70) return { bg: "#fef3c7", text: "#92400e", label: "Good" };
    if (score >= 60) return { bg: "#fed7aa", text: "#92400e", label: "Fair" };
    return { bg: "#fee2e2", text: "#991b1b", label: "Critical" };
  };

  return (
    <div style={{
      flex: 1,
      overflow: "auto",
      padding: "2rem",
      background: T.offwhite,
    }}>
      <style>{`
        .scorecard-container {
          max-width: 1400px;
          margin: 0 auto;
        }
        .section-header {
          font-size: 1.2rem;
          font-weight: 700;
          color: ${T.black};
          margin-bottom: 1.5rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .filter-controls {
          display: flex;
          gap: 1rem;
          margin-bottom: 1.5rem;
          flex-wrap: wrap;
        }
        .filter-btn {
          padding: 0.5rem 1rem;
          border: 1px solid #cbd5e1;
          background: ${T.white};
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
        }
        .filter-btn:hover {
          border-color: #3b82f6;
          background: #eff6ff;
        }
        .filter-btn.active {
          background: #3b82f6;
          color: ${T.white};
          border-color: #3b82f6;
        }
        .sort-select {
          padding: 0.5rem;
          border: 1px solid #cbd5e1;
          border-radius: 6px;
          background: ${T.white};
          cursor: pointer;
        }
        .scorecard-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: 1.5rem;
        }
        .scorecard {
          background: ${T.white};
          border-radius: 8px;
          padding: 1.5rem;
          box-shadow: 0 2px 8px rgba(0,0,0,0.06);
          transition: all 0.2s;
        }
        .scorecard:hover {
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .score-header {
          display: flex;
          justify-content: space-between;
          align-items: start;
          margin-bottom: 1rem;
        }
        .dietician-info {
          flex: 1;
        }
        .dietician-name {
          font-weight: 600;
          color: ${T.black};
          margin-bottom: 0.25rem;
        }
        .patient-name {
          font-size: 0.875rem;
          color: ${T.gray600};
        }
        .score-badge {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.25rem;
        }
        .score-value {
          font-size: 1.5rem;
          font-weight: 700;
        }
        .score-label {
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .scorecard-meta {
          display: flex;
          gap: 1rem;
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid #e2e8f0;
          font-size: 0.875rem;
          color: ${T.gray600};
        }
        .meta-item {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }
        .meta-label {
          font-size: 0.75rem;
          color: ${T.gray500};
          text-transform: uppercase;
        }
        .empty-state {
          text-align: center;
          padding: 3rem;
          color: ${T.gray600};
        }
      `}</style>

      <div className="scorecard-container">
        <div className="section-header">
          <div>📊 QA Scorecards ({sorted.length})</div>
          {!loading && <span style={{ fontSize: "0.875rem", color: T.gray600 }}>Updated {new Date().toLocaleTimeString()}</span>}
        </div>

        <div className="filter-controls">
          <button
            className={`filter-btn ${filter === "all" ? "active" : ""}`}
            onClick={() => setFilter("all")}
          >
            All ({scorecards.length})
          </button>
          <button
            className={`filter-btn ${filter === "good" ? "active" : ""}`}
            onClick={() => setFilter("good")}
          >
            ✅ Excellent (≥80)
          </button>
          <button
            className={`filter-btn ${filter === "warning" ? "active" : ""}`}
            onClick={() => setFilter("warning")}
          >
            ⚠️ Good (70-80)
          </button>
          <button
            className={`filter-btn ${filter === "critical" ? "active" : ""}`}
            onClick={() => setFilter("critical")}
          >
            ❌ Critical (&lt;70)
          </button>
          <select className="sort-select" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="score_desc">Score: High to Low</option>
            <option value="score_asc">Score: Low to High</option>
            <option value="date_new">Date: Newest</option>
            <option value="date_old">Date: Oldest</option>
          </select>
        </div>

        {loading ? (
          <div className="empty-state">Loading scorecards...</div>
        ) : sorted.length === 0 ? (
          <div className="empty-state">
            {filter === "all" ? "No scorecards yet" : "No scorecards match this filter"}
          </div>
        ) : (
          <div className="scorecard-grid">
            {sorted.map(call => {
              const scoreInfo = getScoreColor(call.overall_weighted_score || 0);
              return (
                <div key={call.id} className="scorecard">
                  <div className="score-header">
                    <div className="dietician-info">
                      <div className="dietician-name">{call.dietician_name || "Unknown"}</div>
                      <div className="patient-name">{call.patient_name || "N/A"}</div>
                    </div>
                    <div
                      className="score-badge"
                      style={{ background: scoreInfo.bg, padding: "0.75rem", borderRadius: "6px" }}
                    >
                      <div className="score-value" style={{ color: scoreInfo.text }}>
                        {call.overall_weighted_score ? call.overall_weighted_score.toFixed(1) : "N/A"}
                      </div>
                      <div className="score-label" style={{ color: scoreInfo.text }}>
                        {scoreInfo.label}
                      </div>
                    </div>
                  </div>

                  <div className="scorecard-meta">
                    <div className="meta-item">
                      <span className="meta-label">Date</span>
                      <span>{new Date(call.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Appointment</span>
                      <span>{call.appointment_id || "N/A"}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Status</span>
                      <span style={{
                        background: "#dcfce7",
                        color: "#15803d",
                        padding: "0.25rem 0.5rem",
                        borderRadius: "4px",
                        fontSize: "0.75rem",
                        fontWeight: 600
                      }}>
                        Completed
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
