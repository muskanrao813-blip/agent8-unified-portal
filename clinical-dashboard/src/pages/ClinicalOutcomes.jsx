import { useState, useEffect } from "react";
import { T } from "../tokens";
import { Badge, Header } from "../components/UI";

const COHORT_TABS = ["ALL COHORTS", "IN-HOUSE AI", "IN-HOUSE OTHERS", "IN-HOUSE MC", "CONTRACTUAL"];

const TOP_METRICS = [
  {
    label1: "TOTAL PATIENT",
    label2: "COUNT",
    value: "0",
    valueSuffix: null,
    sub: "Real Trino data",
    subColor: T.green,
    accentColor: T.green,
  },
  {
    label1: "AVG BIOMARKER",
    label2: "IMPROVEMENT",
    value: "+14.2%",
    valueSuffix: null,
    sub: "↗ Target: 12.0%",
    subColor: T.gray500,
    accentColor: T.black,
  },
  {
    label1: "PATIENT",
    label2: "WITH LAB DATA",
    value: "0%",
    valueSuffix: null,
    sub: "Data availability rate",
    subColor: T.green,
    accentColor: "#6B8FA8",
  },
  {
    label1: "MC DIETICIANS",
    label2: "ACTIVE",
    value: "0",
    valueSuffix: null,
    sub: "Providers in view",
    subColor: T.gray500,
    accentColor: T.gray700,
  },
];

export default function ClinicalOutcomesPage({ startDate, endDate, setStartDate, setEndDate }) {
  // ⚠️ Clinical Outcomes uses same date range as Overview/Utilization (July full month)
  // Matches the professional_metrics cache date range (2026-07-01 to 2026-07-28)
  const [tabStartDate, setTabStartDate] = useState("2026-07-01");
  const [tabEndDate, setTabEndDate] = useState("2026-07-28");

  const [tab, setTab] = useState("ALL COHORTS");
  const [metrics, setMetrics] = useState(TOP_METRICS);
  const [programmes, setProgrammes] = useState([]);
  const [directors, setDirectors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState("");
  const [sortConfig, setSortConfig] = useState({ key: null, direction: "asc" });

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Validate dates (use tab-specific dates, not global)
        if (!tabStartDate || !tabEndDate) {
          console.warn("Invalid dates:", { tabStartDate, tabEndDate });
          setLoading(false);
          return;
        }

        const params = new URLSearchParams({ start_date: tabStartDate, end_date: tabEndDate });
        const baseUrl = process.env.REACT_APP_API_URL || "http://localhost:5001/api/agent8";
        const timeout = 30000; // 30 second timeout

        const fetchWithTimeout = (url) => Promise.race([
          fetch(url),
          new Promise((_, reject) => setTimeout(() => reject(new Error("Fetch timeout")), timeout))
        ]);

        console.log(`[ClinicalOutcomes] Fetching data for ${tabStartDate} to ${tabEndDate}...`);

        // Fetch provider data and improvement data in parallel
        const [res, improvRes] = await Promise.all([
          fetchWithTimeout(`${baseUrl}/health-outcomes?${params}`),
          fetchWithTimeout(`${baseUrl}/dietician-improvement?${params}`)
        ]);

        if (!res.ok || !improvRes.ok) {
          throw new Error(`API error: health=${res.status}, improvement=${improvRes.status}`);
        }

        const data = await res.json();
        const improvData = await improvRes.json();

        console.log("[ClinicalOutcomes] API responses received");
        console.log("[ClinicalOutcomes] Data structure:", Object.keys(data));
        console.log("[ClinicalOutcomes] data.professionals type:", typeof data.professionals, "isArray:", Array.isArray(data.professionals));
        if (data.professionals) console.log("[ClinicalOutcomes] professionals count:", data.professionals.length);

        // Create improvement map with normalized scores
        const improvMap = {};
        if (improvData.data && Array.isArray(improvData.data)) {
          improvData.data.forEach(item => {
            improvMap[item.dietician] = {
              score: item.improvement_score !== null ? item.improvement_score : 0,
              pct: item.improvement_pct !== null ? item.improvement_pct.toFixed(1) : "N/A",
              improved: item.patients_improved !== null ? item.patients_improved : 0,
              total: item.patients_total !== null ? item.patients_total : 0
            };
          });
        }

        // Set providers with real cohort info and normalized improvement scores
        if (data.professionals && Array.isArray(data.professionals)) {
          const directorsData = data.professionals.map((p) => {
            // API returns 'provider_name' from clinical-outcomes endpoint
            const providerName = p.provider_name || p.dietician || p.doctorname || 'Unknown';
            const improvInfo = improvMap[providerName] || { score: 0, pct: "N/A", improved: 0, total: 0 };
            return {
              initials: providerName.split(" ").map(w => w[0]).join(""),
              name: providerName,
              cohort: p.cohort || 'UNKNOWN',
              count: p.patient_count?.toLocaleString?.() || p.patient_count || "0",
              improvementScore: improvInfo.score,
              improvementPct: improvInfo.pct,
              patientsTotal: improvInfo.total,
            };
          });

          console.log(`[ClinicalOutcomes] Loaded ${directorsData.length} providers`);
          setDirectors(directorsData);

          // Calculate metrics based on all data
          const totalPatients = data.professionals.reduce((sum, d) => sum + (d.patient_count || 0), 0);
          const totalWithLab = data.professionals.reduce((sum, d) => sum + (d.with_lab_data || 0), 0);
          const labPct = totalPatients > 0 ? ((totalWithLab / totalPatients) * 100).toFixed(1) : 0;

          // Calculate Avg Biomarker Improvement from improvement data
          let avgImprovement = 0;
          if (improvData.data && Array.isArray(improvData.data)) {
            const improvements = improvData.data.filter(d => d.improvement_pct !== null && d.improvement_pct !== undefined);
            if (improvements.length > 0) {
              avgImprovement = improvements.reduce((sum, d) => sum + d.improvement_pct, 0) / improvements.length;
            }
          }

          setMetrics([
            { ...TOP_METRICS[0], value: totalPatients.toLocaleString() },
            { ...TOP_METRICS[1], value: `+${avgImprovement.toFixed(1)}%` },
            { ...TOP_METRICS[2], value: `${labPct}%` },
            { ...TOP_METRICS[3], value: data.professionals.length.toString() }
          ]);
        }

        // Fetch programmes - ONLY for IN-HOUSE MC tab
        try {
          const progRes = await fetchWithTimeout(`${baseUrl}/mc-programmes?${params}`);
          if (progRes.ok) {
            const progData = await progRes.json();
            if (progData.programmes) {
              setProgrammes(progData.programmes);
            }
          }
        } catch (e) {
          console.warn("[ClinicalOutcomes] Could not fetch programmes:", e);
        }
      } catch (e) {
        console.error("[ClinicalOutcomes] Failed to fetch data:", e);
        alert(`Error loading data: ${e.message}`);
        setDirectors([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [tabStartDate, tabEndDate]);

  // Sort table data
  const handleSort = (key) => {
    let direction = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    }
    setSortConfig({ key, direction });
  };

  // Get sorted and filtered directors
  const filteredDirectors = directors
    .filter(d => {
      const matchTab = tab === "ALL COHORTS" || d.cohort === tab;
      const matchSearch = searchText === "" || d.name.toLowerCase().includes(searchText.toLowerCase());
      return matchTab && matchSearch;
    })
    .sort((a, b) => {
      // Default sort by improvement score (descending)
      if (!sortConfig.key) {
        return b.improvementScore - a.improvementScore;
      }

      let aVal = a[sortConfig.key];
      let bVal = b[sortConfig.key];

      if (sortConfig.key === "improvementScore") {
        aVal = a.improvementScore || 0;
        bVal = b.improvementScore || 0;
      } else if (typeof aVal === "string" && aVal !== "-" && !aVal.includes("%")) {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }

      if (aVal < bVal) return sortConfig.direction === "asc" ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === "asc" ? 1 : -1;
      return 0;
    })
    .map((d, idx) => ({ ...d, rank: idx + 1 }));

  // Export to CSV
  const handleExport = () => {
    const headers = ["RANK", "PROFESSIONAL NAME", "COHORT", "PATIENT COUNT", "IMPROVEMENT SCORE", "IMPROVEMENT %", "SAMPLE SIZE"];
    const rows = filteredDirectors.map(d => [
      d.rank,
      d.name,
      d.cohort,
      d.count,
      d.improvementScore,
      d.improvementPct,
      d.patientsTotal
    ]);

    const csvContent = [
      headers.join(","),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(","))
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Provider_Outcomes_${startDate}_${endDate}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div style={{ flex: 1, overflow: "auto", background: T.offwhite }}>
      <Header
        title="Clinical Outcomes"
        startDate={tabStartDate}
        endDate={tabEndDate}
        onStartDateChange={setTabStartDate}
        onEndDateChange={setTabEndDate}
        onExport={handleExport}
      />
      <div style={{ padding: "28px" }}>

        {/* ── COHORT SEGMENTATION label ── */}
        <div style={{
          fontSize: 10, color: T.gray500,
          letterSpacing: "0.12em", fontFamily: "monospace",
          textTransform: "uppercase", marginBottom: 14,
        }}>
          COHORT SEGMENTATION
        </div>

        {/* ── Tab strip ── */}
        <div style={{
          display: "inline-flex",
          border: `1px solid ${T.gray200}`,
          background: T.white,
          marginBottom: 20,
        }}>
          {COHORT_TABS.map((t, i) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              style={{
                padding: "9px 22px",
                fontSize: 11,
                fontFamily: "monospace",
                fontWeight: tab === t ? 700 : 400,
                border: "none",
                borderRight: i < COHORT_TABS.length - 1 ? `1px solid ${T.gray200}` : "none",
                cursor: "pointer",
                background: tab === t ? T.black : T.white,
                color: tab === t ? T.white : T.gray500,
                letterSpacing: "0.05em",
                textTransform: "uppercase",
                whiteSpace: "nowrap",
              }}
            >
              {t}
            </button>
          ))}
        </div>

        {/* ── 4 metric cards with thick colored left border ── */}
        <div style={{ display: "flex", gap: 12, marginBottom: 36 }}>
          {metrics.map((m, i) => {
            let displayValue = m.value;
            if (tab !== "ALL COHORTS" && directors.length > 0) {
              const filtered = directors.filter(d => d.cohort === tab);
              if (i === 0) displayValue = filtered.reduce((sum, d) => sum + parseInt(d.count.toString().replace(/,/g, '')) || 0, 0).toLocaleString();
              if (i === 3) displayValue = filtered.length.toString();
            }
            return (
              <div
                key={i}
                style={{
                  flex: 1,
                  background: T.white,
                  border: `1px solid ${T.gray200}`,
                  borderLeft: `4px solid ${m.accentColor}`,
                  padding: "20px 22px 20px 20px",
                  minHeight: 160,
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                }}
              >
                <div>
                  <div style={{
                    fontSize: 9, color: T.gray500,
                    letterSpacing: "0.12em", fontFamily: "monospace",
                    textTransform: "uppercase", lineHeight: 1.5, marginBottom: 12,
                  }}>
                    {m.label1}
                    {m.label2 && <><br />{m.label2}</>}
                  </div>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 1, marginBottom: 10 }}>
                    <span style={{
                      fontSize: 40, fontWeight: 700,
                      fontFamily: "Georgia, serif", lineHeight: 1,
                      color: T.black,
                    }}>
                      {displayValue}
                    </span>
                    {m.valueSuffix && (
                      <span style={{
                        fontSize: 20, fontWeight: 400,
                        fontFamily: "Georgia, serif",
                        color: T.gray400,
                      }}>
                        {m.valueSuffix}
                      </span>
                    )}
                  </div>
                </div>
                <div style={{
                  fontSize: 11, color: m.subColor,
                  fontFamily: "monospace", lineHeight: 1.4,
                }}>
                  {m.sub}
                </div>
              </div>
            );
          })}
        </div>

        {/* ── Programme Performance Breakdown (hidden if no data) ── */}
        {programmes && programmes.length > 0 && (
          <>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
              <div style={{ fontSize: 22, fontWeight: 700, fontFamily: "Georgia, serif" }}>
                Managed Care Programmes
              </div>
              <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace", letterSpacing: "0.08em" }}>
                ACTIVE PROGRAMMES: {programmes.length}
              </div>
            </div>

            <div style={{ display: "flex", gap: 12, marginBottom: 40 }}>
              {programmes.map((p) => (
                <div key={p.name} style={{
                  flex: 1,
                  background: T.white,
                  border: `1px solid ${T.gray200}`,
                  padding: "16px",
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
                    <span style={{
                      fontSize: 10, fontWeight: 700,
                      fontFamily: "monospace", letterSpacing: "0.06em",
                      border: `1px solid ${T.gray300}`,
                      padding: "3px 8px",
                      background: T.white, color: T.gray700,
                    }}>
                      {p.name}
                    </span>
                    <span style={{ fontSize: 14, color: T.gray300 }}>⊞</span>
                  </div>
                  <div style={{
                    fontSize: 12, color: T.gray500,
                    fontFamily: "monospace", marginBottom: 16,
                  }}>
                    {p.patients} Patients
                  </div>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 6, marginBottom: 4 }}>
                    <span style={{
                      fontSize: 24, fontWeight: 700,
                      fontFamily: "Georgia, serif",
                    }}>
                      {p.improvement}
                    </span>
                    <span style={{
                      fontSize: 9, color: T.gray500,
                      letterSpacing: "0.1em", fontFamily: "monospace",
                    }}>
                      BIOMARKER
                    </span>
                  </div>
                  <div style={{ height: 2, background: T.black, marginBottom: 8 }} />
                  <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace" }}>
                    {p.success_rate}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {/* ── Provider Outcomes Directory ── */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div style={{ fontSize: 22, fontWeight: 700, fontFamily: "Georgia, serif" }}>
            Provider Outcomes Directory
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <div style={{
              display: "flex", alignItems: "center",
              border: `1px solid ${T.gray300}`, background: T.white,
              padding: "0 12px",
            }}>
              <span style={{ fontSize: 13, color: T.gray400, marginRight: 8 }}>🔍</span>
              <input
                placeholder="Search professionals..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                style={{
                  border: "none", outline: "none",
                  fontSize: 12, fontFamily: "monospace",
                  padding: "9px 0", width: 210,
                  background: "transparent", color: T.black,
                }}
              />
            </div>
          </div>
        </div>

        {/* Table */}
        <div style={{ background: T.white, border: `1px solid ${T.gray200}` }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${T.gray200}`, background: T.white }}>
                {[
                  { label: "RANK", key: "rank" },
                  { label: "PROFESSIONAL NAME", key: "name" },
                  { label: "COHORT", key: "cohort" },
                  { label: "PATIENT COUNT", key: "count" },
                  { label: "IMPROVEMENT SCORE", key: "improvementScore" },
                  { label: "IMPROVEMENT %", key: "improvementPct" },
                  { label: "SAMPLE SIZE", key: "patientsTotal" },
                ].map(h => (
                  <th
                    key={h.label}
                    onClick={() => handleSort(h.key)}
                    style={{
                      padding: "11px 16px", textAlign: "left",
                      fontSize: 10, fontFamily: "monospace",
                      color: T.gray500, fontWeight: 600,
                      letterSpacing: "0.06em",
                      cursor: "pointer",
                      background: sortConfig.key === h.key ? T.gray100 : T.white,
                    }}
                  >
                    {h.label} {sortConfig.key === h.key ? (sortConfig.direction === "asc" ? "↑" : "↓") : ""}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredDirectors.length > 0 ? filteredDirectors.map((r, idx) => {
                const getRankBadge = (rank) => {
                  if (rank === 1) return "🥇";
                  if (rank === 2) return "🥈";
                  if (rank === 3) return "🥉";
                  return rank;
                };

                return (
                  <tr key={r.name} style={{ borderBottom: `1px solid ${T.gray100}` }}>
                    <td style={{ padding: "15px 16px", textAlign: "center", fontSize: 14, fontWeight: 700 }}>
                      {getRankBadge(r.rank)}
                    </td>
                    <td style={{ padding: "15px 16px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <div style={{
                          width: 30, height: 30,
                          background: T.gray200, borderRadius: "50%",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: 9, fontWeight: 700, fontFamily: "monospace",
                          flexShrink: 0, color: T.gray700,
                        }}>
                          {r.initials}
                        </div>
                        <span style={{ fontWeight: 600, fontFamily: "monospace", fontSize: 12 }}>
                          {r.name}
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: "15px 16px" }}>
                      <span style={{
                        fontSize: 10, fontWeight: 700,
                        fontFamily: "monospace", letterSpacing: "0.05em",
                        border: `1px solid ${T.gray300}`,
                        padding: "3px 8px", background: T.white, color: T.gray700,
                      }}>
                        {r.cohort}
                      </span>
                    </td>
                    <td style={{ padding: "15px 16px", fontFamily: "monospace" }}>{r.count}</td>
                    <td style={{ padding: "15px 16px", fontFamily: "monospace", fontWeight: 700, color: T.black }}>
                      {r.improvementScore}
                    </td>
                    <td style={{ padding: "15px 16px", fontFamily: "monospace", fontWeight: 700, color: r.improvementPct === "N/A" ? T.gray400 : T.black }}>
                      {r.improvementPct}{r.improvementPct !== "N/A" ? "%" : ""}
                    </td>
                    <td style={{ padding: "15px 16px", fontFamily: "monospace" }}>{r.patientsTotal}</td>
                  </tr>
                );
              }) : <tr><td colSpan="7" style={{ padding: "20px", textAlign: "center", color: T.gray500 }}>No providers found</td></tr>}
            </tbody>
          </table>

          {/* Footer with count */}
          <div style={{
            padding: "13px 16px",
            display: "flex", justifyContent: "space-between", alignItems: "center",
            borderTop: `1px solid ${T.gray100}`,
          }}>
            <div style={{ fontSize: 11, color: T.gray500, fontFamily: "monospace" }}>
              Showing {filteredDirectors.length} of {directors.length} Professionals
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
