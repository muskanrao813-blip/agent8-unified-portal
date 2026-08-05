import { useState, useEffect } from "react";
import { T } from "../../tokens";

export default function QAReports() {
  const [dieticians, setDieticians] = useState([]);
  const [loading, setLoading] = useState(true);
  const API_BASE = "http://localhost:8000/api";

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await fetch(`${API_BASE}/calls/`);
      const data = await response.json();

      // Group by dietician
      const grouped = {};
      (Array.isArray(data) ? data : []).forEach(call => {
        const name = call.dietician_name || "Unknown";
        if (!grouped[name]) {
          grouped[name] = { name, calls: [], totalScore: 0, count: 0 };
        }
        grouped[name].calls.push(call);
        if (call.overall_weighted_score) {
          grouped[name].totalScore += call.overall_weighted_score;
          grouped[name].count++;
        }
      });

      const list = Object.values(grouped).map(d => ({
        ...d,
        avgScore: d.count > 0 ? (d.totalScore / d.count) : 0
      })).sort((a, b) => b.avgScore - a.avgScore);

      setDieticians(list);
    } catch (error) {
      console.error("Error fetching reports:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "2rem", background: T.offwhite, overflow: "auto", flex: 1 }}>
      <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "2rem", color: T.black }}>
          Dietician Reports
        </h2>

        {loading ? (
          <p style={{ color: T.gray600 }}>Loading reports...</p>
        ) : dieticians.length === 0 ? (
          <p style={{ color: T.gray600 }}>No reports available</p>
        ) : (
          <div style={{
            background: T.white,
            borderRadius: "8px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
            overflow: "hidden"
          }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: T.gray50, borderBottom: `1px solid ${T.gray200}` }}>
                  <th style={{ textAlign: "left", padding: "1rem", fontWeight: 600, color: T.black }}>Dietician</th>
                  <th style={{ textAlign: "left", padding: "1rem", fontWeight: 600, color: T.black }}>Total Calls</th>
                  <th style={{ textAlign: "left", padding: "1rem", fontWeight: 600, color: T.black }}>Avg QA Score</th>
                  <th style={{ textAlign: "left", padding: "1rem", fontWeight: 600, color: T.black }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {dieticians.map((d, idx) => (
                  <tr key={idx} style={{ borderBottom: `1px solid ${T.gray200}` }}>
                    <td style={{ padding: "1rem" }}>
                      <div style={{ fontWeight: 600, color: T.black }}>{d.name}</div>
                    </td>
                    <td style={{ padding: "1rem", color: T.gray600 }}>
                      {d.calls.length}
                    </td>
                    <td style={{
                      padding: "1rem",
                      fontWeight: 600,
                      color: d.avgScore >= 80 ? "#15803d" :
                             d.avgScore >= 70 ? "#92400e" : "#991b1b"
                    }}>
                      {d.avgScore.toFixed(1)}/100
                    </td>
                    <td style={{ padding: "1rem" }}>
                      <span style={{
                        background: d.avgScore >= 80 ? "#dcfce7" :
                                   d.avgScore >= 70 ? "#fef3c7" : "#fee2e2",
                        color: d.avgScore >= 80 ? "#15803d" :
                               d.avgScore >= 70 ? "#92400e" : "#991b1b",
                        padding: "0.25rem 0.75rem",
                        borderRadius: "4px",
                        fontSize: "0.875rem",
                        fontWeight: 600
                      }}>
                        {d.avgScore >= 80 ? "Excellent" :
                         d.avgScore >= 70 ? "Good" : "Needs Improvement"}
                      </span>
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
