import { T } from "../tokens";
import { Badge, MetricCard, UtilBar, Header } from "../components/UI";
import { useState, useEffect } from "react";

export default function OverviewPage({ setPage, setSelectedProvider, startDate, endDate, setStartDate, setEndDate }) {
  const [kpis, setKpis] = useState([]);
  const [professionals, setProfessionals] = useState([]);
  const [recommendations, setRecommendations] = useState({});
  const [cohortMetrics, setCohortMetrics] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedProgramme, setSelectedProgramme] = useState("All Systems");

  useEffect(() => {
    const timer = setTimeout(() => {
      const fetchData = async () => {
        setLoading(true);
        try {
          if (!startDate || !endDate) {
            setLoading(false);
            return;
          }

          const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
          const baseUrl = process.env.REACT_APP_API_URL || "http://localhost:5001/api/agent8";

          // Fetch KPIs, professionals, QA scores, and cohort performance in parallel
          const [dashRes, profsRes, qaRes, cohortRes] = await Promise.all([
            fetch(`${baseUrl}/dashboard?${params}`),
            fetch(`${baseUrl}/professionals?${params}`),
            fetch(`${baseUrl}/qa-scores?${params}`),
            fetch(`${baseUrl}/cohort-performance?${params}`)
          ]);

        if (!dashRes.ok || !profsRes.ok) {
          throw new Error(`API error: dashboard=${dashRes.status}, professionals=${profsRes.status}`);
        }

        const dashData = await dashRes.json();
        const profsData = await profsRes.json();
        const qaData = qaRes.ok ? await qaRes.json() : { data: {} };
        const cohortData = cohortRes.ok ? await cohortRes.json() : { data: {} };

        // Build QA score map
        const qaMap = {};
        if (qaData.data && typeof qaData.data === 'object') {
          Object.entries(qaData.data).forEach(([dietician, qaInfo]) => {
            qaMap[dietician] = qaInfo.avg_qa_score || "N/A";
          });
        }

        setKpis(dashData.kpis || []);

        // Map cached metrics to professional table format
        const profs = [];
        if (profsData.data && Array.isArray(profsData.data)) {
          profsData.data.forEach((prof, idx) => {
            profs.push({
              rank: idx + 1,
              name: prof.provider_name,
              cohort: prof.cohort || 'UNKNOWN',
              appt: prof.appts_count,
              cap: prof.capacity,
              util: prof.utilization_pct,
              outcome: prof.improvement_score ? prof.improvement_score.toFixed(1) + "/" + prof.improvement_total : "0/0",
              call: qaMap[prof.provider_name] || "N/A",
              status: prof.status ? prof.status.toLowerCase() : "optimal",
              forecast: prof.forecast_7d || 0
            });
          });
        }

        setProfessionals(profs);

        // Store cohort metrics from backend
        setCohortMetrics(cohortData.data || {});
        } catch (e) {
          console.error("Error fetching professional data:", e);
          // Don't clear data on error - use last successful fetch
          // setProfessionals([]);
          // setCohortMetrics({});
        } finally {
          setLoading(false);
        }
      };
      fetchData();
    }, 500); // 500ms debounce - waits 500ms after date change before fetching

    return () => clearTimeout(timer);
  }, [startDate, endDate]);

  // Build COHORTS from backend cohort metrics (NO HARDCODING)
  const buildCohortsFromMetrics = () => {
    const cohortConfig = {
      'IN-HOUSE AI': { name: "In-house AI", badge: "ai-enabled", staff: "6 Dieticians" },
      'IN-HOUSE OTHERS': { name: "In-house Others", badge: "support", staff: "2 Staff" },
      'IN-HOUSE MC': { name: "Managed Care", badge: "core", staff: "3 Diet + 1 Doc" },
      'CONTRACTUAL': { name: "Contractual", badge: "external", staff: "14 External" }
    };

    return Object.entries(cohortMetrics).map(([key, metrics]) => {
      const config = cohortConfig[key];
      return {
        name: config?.name || key,
        badge: config?.badge || "external",
        staff: config?.staff || "N/A",
        util: metrics.utilization_pct || 0,
        vol: metrics.vol_metric || 0
      };
    }).sort((a, b) => a.name.localeCompare(b.name));
  };

  const COHORTS = Object.keys(cohortMetrics).length > 0 ? buildCohortsFromMetrics() : [];

  // Filter professionals and cohorts based on selectedProgramme
  const filterProfessionals = () => {
    if (selectedProgramme === 'All Systems') return professionals;
    return professionals.filter(p => {
      if (selectedProgramme === 'In-house AI') return p.cohort === 'IN-HOUSE AI';
      if (selectedProgramme === 'Managed Care') return p.cohort === 'IN-HOUSE MC';
      if (selectedProgramme === 'Contractual') return p.cohort === 'CONTRACTUAL';
      return true;
    });
  };

  const filteredProfessionals = filterProfessionals();
  const filteredCohorts = selectedProgramme === 'All Systems'
    ? COHORTS
    : COHORTS.filter(c => {
        if (selectedProgramme === 'In-house AI') return c.name === 'In-house AI';
        if (selectedProgramme === 'Managed Care') return c.name === 'Managed Care';
        if (selectedProgramme === 'Contractual') return c.name === 'Contractual';
        return true;
      });

  if (loading) return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: T.offwhite }}>
      <div style={{ fontSize: 14, color: T.gray700, marginBottom: 16 }}>Fetching latest data...</div>
      <div style={{ width: 40, height: 40, border: `3px solid ${T.gray200}`, borderTop: `3px solid ${T.black}`, borderRadius: "50%", animation: "spin 1s linear infinite" }} />
      <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
    </div>
  );

  return (
    <div style={{ flex: 1, overflow: "auto", background: T.offwhite }}>
      <Header
        title="Operations Overview"
        startDate={startDate}
        endDate={endDate}
        onStartDateChange={setStartDate}
        onEndDateChange={setEndDate}
      />

      <div style={{ padding: "28px" }}>
        {/* Section heading + programme filter */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 10, color: T.gray500, letterSpacing: "0.1em", textTransform: "uppercase", fontFamily: "monospace" }}>
              OPERATIONAL OVERVIEW
            </div>
            <div style={{ fontSize: 26, fontWeight: 700, fontFamily: "Georgia, serif" }}>Performance Matrix</div>
          </div>
          <div style={{ border: `1px solid ${T.gray300}`, padding: "6px 14px", fontSize: 11, fontFamily: "monospace", cursor: "pointer", background: T.white }}>
            <select value={selectedProgramme} onChange={(e) => setSelectedProgramme(e.target.value)} style={{ border: "none", background: "transparent", cursor: "pointer", fontFamily: "monospace" }}>
              <option>All Systems</option>
              <option>In-house AI</option>
              <option>Managed Care</option>
              <option>Contractual</option>
            </select>
          </div>
        </div>

        {/* KPI cards */}
        <div style={{ display: "flex", gap: 12, marginBottom: 28 }}>
          {kpis.length > 0 ? (
            kpis.map(k => (
              <MetricCard key={k.label} label={k.label} value={k.value} sub={k.trend || k.comparison || ""} />
            ))
          ) : (
            <>
              <MetricCard label="Team Utilization"  value="94.2%" sub="+2.4% vs prev. period" icon={<Badge variant="critical">HIGH</Badge>} />
              <MetricCard label="Booked Appts"      value="12,482" sub="Target: 11,500 (+8.5%)" />
              <MetricCard label="Total Capacity"    value="13,248" sub="766 remaining slots" />
              <MetricCard label="Avg Improvement"   value="7.4%"   sub="Composite clinical gain" icon="↗" />
            </>
          )}
        </div>

        {/* AI Recommendations Section */}
        {recommendations.training_required && recommendations.training_required.length > 0 && (
          <div style={{ marginBottom: 28 }}>
            <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 16, color: T.black }}>🤖 AI Recommendations</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              {recommendations.training_required.slice(0, 2).map(rec => (
                <div key={rec.id} style={{ border: `1px solid ${T.gray200}`, background: T.white, padding: 16, borderLeft: `4px solid ${T.red}` }}>
                  <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 8, color: T.red }}>⚠ TRAINING REQUIRED</div>
                  <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>{rec.provider_name}</div>
                  <div style={{ fontSize: 11, color: T.gray500, marginBottom: 8 }}>QA Score: {rec.current_score}/{rec.benchmark_score} | Mentor: {rec.mentor_name}</div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button onClick={() => alert(`Training scheduled for ${rec.provider_name}`)} style={{ flex: 1, padding: "6px 12px", background: "#4CAF50", color: "white", border: "none", cursor: "pointer", fontSize: 11, fontWeight: 600 }}>✓ Accept</button>
                    <button onClick={() => alert(`Declined for ${rec.provider_name}`)} style={{ flex: 1, padding: "6px 12px", background: T.gray300, color: T.black, border: "none", cursor: "pointer", fontSize: 11, fontWeight: 600 }}>✕ Decline</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Cohort cards */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 600 }}>Clinical Cohort Performance</div>
        </div>

        <div style={{ display: "flex", gap: 12, marginBottom: 28 }}>
          {filteredCohorts.map(c => (
            <div key={c.name} style={{ flex: 1, border: `1px solid ${T.gray200}`, background: T.white, padding: "16px 18px", cursor: "pointer", transition: "all 0.2s" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{c.name}</div>
                <Badge variant={c.badge}>{c.badge.replace("-", " ").toUpperCase()}</Badge>
              </div>
              <div style={{ fontSize: 11, color: T.gray500, fontFamily: "monospace", marginBottom: 4 }}>
                Staff Count <span style={{ color: T.black, fontWeight: 700 }}>{c.staff}</span>
              </div>
              <div style={{ fontSize: 11, color: T.gray500, fontFamily: "monospace", display: "flex", justifyContent: "space-between" }}>
                Utilization <span style={{ color: c.util > 100 ? T.red : T.black, fontWeight: 700 }}>{c.util}%</span>
              </div>
              <UtilBar pct={c.util} />
              <div style={{ fontSize: 11, color: T.gray500, fontFamily: "monospace", marginTop: 10 }}>
                Vol. Metric <span style={{ color: T.black, fontWeight: 700 }}>{c.vol}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Provider table */}
        <div style={{ background: T.white, border: `1px solid ${T.gray200}` }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${T.gray200}` }}>
                {["RANK","PROFESSIONAL NAME","COHORT","APPT","CAPACITY","UTIL %","OUTCOME IMPR.","CALL SCORE","STATUS","7D FORECAST"].map(h => (
                  <th key={h} style={{ padding: "10px 14px", textAlign: "left", fontSize: 10, fontFamily: "monospace", color: T.gray500, fontWeight: 600, letterSpacing: "0.06em" }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredProfessionals.length > 0 ? (
                filteredProfessionals.map(r => (
                  <tr key={r.rank} style={{ borderBottom: `1px solid ${T.gray100}` }}>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace", color: T.gray400, fontSize: 11 }}>{r.rank}</td>
                    <td
                      style={{ padding: "12px 14px", fontWeight: 600, color: T.black, cursor: "pointer", textDecoration: "underline" }}
                      onClick={() => { setSelectedProvider(r.name); setPage(r.name); }}
                    >
                      {r.name}
                    </td>
                    <td style={{ padding: "12px 14px", color: T.gray500, fontFamily: "monospace", fontSize: 11 }}>{r.cohort}</td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>{r.appt}</td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>{r.cap}</td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace", fontWeight: 700, color: r.util > 95 ? T.red : T.black }}>{r.util}%</td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>{r.outcome}</td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>{r.call}</td>
                    <td style={{ padding: "12px 14px" }}><Badge variant={r.status}>{r.status.toUpperCase()}</Badge></td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>{r.forecast}</td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan="10" style={{ padding: "20px", textAlign: "center", color: T.gray500 }}>Loading professionals data...</td></tr>
              )}
            </tbody>
          </table>
          <div style={{
            padding: "12px 14px", fontSize: 11, color: T.gray500, fontFamily: "monospace",
            display: "flex", justifyContent: "space-between", alignItems: "center",
            borderTop: `1px solid ${T.gray100}`,
          }}>
            Showing {filteredProfessionals.length} of {professionals.length} MC Professionals (Dieticians + Doctor)
            {selectedProgramme !== 'All Systems' && <span style={{ marginLeft: 16, color: T.blue }}>Filter: {selectedProgramme}</span>}
            <div style={{ display: "flex", gap: 4 }}>
              {["‹", "›"].map(b => (
                <button key={b} onClick={() => alert("Pagination coming soon")} style={{ width: 28, height: 28, border: `1px solid ${T.gray200}`, background: T.white, cursor: "pointer", fontSize: 14 }}>
                  {b}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
