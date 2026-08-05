import { useState, useEffect } from "react";

export default function QADashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateFrom, setDateFrom] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().split('T')[0];
  });
  const [dateTo, setDateTo] = useState(new Date().toISOString().split('T')[0]);

  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      try {
        const response = await fetch(
          `/api/qa/dashboard/stats?start_date=${dateFrom}&end_date=${dateTo}`
        );
        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error("Failed to load QA dashboard:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [dateFrom, dateTo]);

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
        .qa-section-title i {
          font-size: 1.5rem;
          color: #3b82f6;
        }
        .qa-filter-group {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
        }
        .qa-filter-input {
          padding: 0.75rem;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          font-size: 0.95rem;
        }
        .qa-kpi-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1.5rem;
        }
        .qa-kpi-card {
          background: white;
          border-radius: 12px;
          padding: 1.8rem;
          text-align: center;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
          border: 1px solid #f0f4f8;
          transition: all 0.3s ease;
        }
        .qa-kpi-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        }
        .qa-kpi-value {
          font-size: 2.5rem;
          font-weight: 700;
          background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          margin: 0.5rem 0;
        }
        .qa-kpi-label {
          font-size: 0.9rem;
          color: #64748b;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
      `}</style>

      <div className="qa-container">
        {/* Header */}
        <div style={{ marginBottom: "2rem" }}>
          <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.5rem" }}>
            📊 Call Quality Dashboard
          </div>
          <div style={{ fontSize: "1rem", color: "#64748b" }}>
            Real-time QA metrics and performance analytics
          </div>
        </div>

        {/* Date Filters */}
        <div className="qa-section">
          <div className="qa-section-title">
            <i>📅</i> Filter by Date Range
          </div>
          <div className="qa-filter-group">
            <div>
              <label style={{ fontSize: "0.85rem", color: "#64748b", fontWeight: 600, display: "block", marginBottom: "0.5rem" }}>
                FROM DATE
              </label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="qa-filter-input"
              />
            </div>
            <div>
              <label style={{ fontSize: "0.85rem", color: "#64748b", fontWeight: 600, display: "block", marginBottom: "0.5rem" }}>
                TO DATE
              </label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="qa-filter-input"
              />
            </div>
          </div>
        </div>

        {/* KPI Cards */}
        {!loading && stats && (
          <div className="qa-kpi-grid">
            <div className="qa-kpi-card">
              <div style={{ fontSize: "1.2rem", marginBottom: "0.5rem" }}>📞</div>
              <div className="qa-kpi-label">Total Calls Analyzed</div>
              <div className="qa-kpi-value">{stats.total_calls || 0}</div>
            </div>

            <div className="qa-kpi-card">
              <div style={{ fontSize: "1.2rem", marginBottom: "0.5rem" }}>⭐</div>
              <div className="qa-kpi-label">Average QA Score</div>
              <div className="qa-kpi-value" style={{ color: stats.avg_qa_score >= 80 ? "#10b981" : stats.avg_qa_score >= 70 ? "#f59e0b" : "#ef4444" }}>
                {stats.avg_qa_score?.toFixed(1) || 0}%
              </div>
            </div>

            <div className="qa-kpi-card">
              <div style={{ fontSize: "1.2rem", marginBottom: "0.5rem" }}>✅</div>
              <div className="qa-kpi-label">SOP Compliance</div>
              <div className="qa-kpi-value" style={{ color: "#10b981" }}>
                {stats.sop_compliance?.toFixed(1) || 0}%
              </div>
            </div>

            <div className="qa-kpi-card">
              <div style={{ fontSize: "1.2rem", marginBottom: "0.5rem" }}>🚨</div>
              <div className="qa-kpi-label">Critical Alerts</div>
              <div className="qa-kpi-value" style={{ color: "#ef4444" }}>
                {stats.critical_alerts_count || 0}
              </div>
            </div>
          </div>
        )}

        {loading && (
          <div style={{ textAlign: "center", color: "#64748b", padding: "3rem", fontSize: "1.1rem" }}>
            Loading QA dashboard...
          </div>
        )}
      </div>
    </div>
  );
}
