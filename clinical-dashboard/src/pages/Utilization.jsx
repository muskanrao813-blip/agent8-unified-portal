import { T } from "../tokens";
import { Badge, Header } from "../components/UI";
import { useState, useEffect } from "react";

const FORECAST_DAYS  = ["MON","TUE","WED","THU","FRI","SAT","SUN"];

// Hourly heatmap intensity mapping
const getHeatmapColor = (utilization) => {
  if (utilization >= 75) return "#0A0A0A"; // Black
  if (utilization >= 50) return "#3A3935"; // Dark gray
  if (utilization >= 25) return "#9A9990"; // Medium gray
  if (utilization >= 10) return "#C8C7C0"; // Light gray
  return "#E2E1DC"; // Very light gray
};

function DonutChart({ segments }) {
  let offset = 0;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginTop: 16 }}>
      <div style={{ position: "relative", width: 100, height: 100 }}>
        <svg viewBox="0 0 36 36" style={{ width: 100, height: 100, transform: "rotate(-90deg)" }}>
          <circle cx="18" cy="18" r="15.9" fill="none" stroke={T.gray100} strokeWidth="3" />
          {segments.map((d, i) => {
            const dash = (d.pct / 100) * 100;
            const el = (
              <circle key={i} cx="18" cy="18" r="15.9" fill="none"
                stroke={d.color} strokeWidth="3"
                strokeDasharray={`${dash} ${100 - dash}`}
                strokeDashoffset={-offset}
              />
            );
            offset += dash;
            return el;
          })}
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
          <div style={{ fontSize: 13, fontWeight: 700 }}>100%</div>
          <div style={{ fontSize: 7, color: T.gray500, fontFamily: "monospace" }}>COHORT SPLIT</div>
        </div>
      </div>
      <div style={{ marginTop: 12, display: "flex", flexWrap: "wrap", gap: 8, fontSize: 10, justifyContent: "center" }}>
        {segments.map(d => (
          <span key={d.label} style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <span style={{ width: 8, height: 8, background: d.color, borderRadius: "50%", display: "inline-block" }} />
            {d.label}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function UtilizationPage({ startDate, endDate, setStartDate, setEndDate }) {
  const [providers, setProviders] = useState([]);
  const [donutSegments, setDonutSegments] = useState([]);
  const [kpis, setKpis] = useState({});
  const [loading, setLoading] = useState(true);
  const [forecast, setForecast] = useState([]);
  const [hourlyData, setHourlyData] = useState([]);
  const [peakHour, setPeakHour] = useState(null);
  const [offPeakHour, setOffPeakHour] = useState(null);
  const [qaScores, setQaScores] = useState([]);
  const [qaAnomalies, setQaAnomalies] = useState([]);
  const [historicalTrends, setHistoricalTrends] = useState({});

  // Calculate utilization status based on correct rubric:
  // CRITICAL: < 50%, HIGH: 50-95%, OPTIMAL: ≥95%
  const calculateStatus = (utilization) => {
    if (utilization < 50) return "critical";
    if (utilization < 95) return "high";
    return "optimal";
  };

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

          // Fetch all data in parallel
          const [capRes, forecastRes, peakRes, qaRes, histRes] = await Promise.all([
            fetch(`${baseUrl}/capacity-analysis?${params}`),
            fetch(`${baseUrl}/forecast-7day?${params}`),
            fetch(`${baseUrl}/peak-hours?${params}`),
            fetch(`${baseUrl}/qa-analytics?${params}`),
            fetch(`${baseUrl}/historical-trends?${params}`)
          ]);

          // Process capacity analysis
          const capData = await capRes.json();
          if (capData.kpis) {
            const kpiMap = {};
            capData.kpis.forEach(k => {
              kpiMap[k.label.toLowerCase().replace(/\s+/g, "_")] = k.value;
            });
            setKpis(kpiMap);
          }

          if (capData.providers) {
            setProviders(capData.providers.map(p => ({
              name: p.name,
              cohort: p.cohort,
              slots: p.slots || 0,
              cap: p.capacity || 0,
              booked: p.booked || 0,
              util: parseFloat(p.utilization) || 0,
              status: calculateStatus(parseFloat(p.utilization) || 0)
            })));
          }

          if (capData.cohort_distribution) {
            setDonutSegments(capData.cohort_distribution);
          }

          // Process forecast data
          if (forecastRes.ok) {
            const forecastData = await forecastRes.json();
            if (forecastData.forecast && Array.isArray(forecastData.forecast)) {
              const forecastVals = forecastData.forecast.map(d => d.projected || 0);
              setForecast(forecastVals);
            }
          }

          // Process peak hours data
          if (peakRes.ok) {
            const peakData = await peakRes.json();
            if (peakData.hourly_data && Array.isArray(peakData.hourly_data)) {
              setHourlyData(peakData.hourly_data);

              // Find peak and off-peak hours
              const maxHour = peakData.hourly_data.reduce((max, h) =>
                h.utilization_pct > max.utilization_pct ? h : max, peakData.hourly_data[0]);
              const minHour = peakData.hourly_data.reduce((min, h) =>
                h.utilization_pct < min.utilization_pct ? h : min, peakData.hourly_data[0]);

              setPeakHour(maxHour.hour);
              setOffPeakHour(minHour.hour);
            }
          }

          // Process QA analytics data
          if (qaRes.ok) {
            const qaData = await qaRes.json();
            if (qaData.qa_scorecard && Array.isArray(qaData.qa_scorecard)) {
              setQaScores(qaData.qa_scorecard);
            }
            if (qaData.anomalies && Array.isArray(qaData.anomalies)) {
              setQaAnomalies(qaData.anomalies);
            }
          }

          // Process historical trends data
          if (histRes.ok) {
            const histData = await histRes.json();
            if (histData.historical_trends) {
              setHistoricalTrends(histData.historical_trends);
            }
          }
        } catch (e) {
          console.error("Failed to fetch utilization data:", e);
        } finally {
          setLoading(false);
        }
      };
      fetchData();
    }, 500);

    return () => clearTimeout(timer);
  }, [startDate, endDate]);

  return (
    <div style={{ flex: 1, overflow: "auto", background: T.offwhite }}>
      <Header
        title="Capacity Analysis & Utilization"
        startDate={startDate}
        endDate={endDate}
        onStartDateChange={setStartDate}
        onEndDateChange={setEndDate}
      />
      <div style={{ padding: "28px" }}>

        {/* Dimension 02 */}
        <div style={{ fontSize: 10, color: T.gray500, letterSpacing: "0.1em", fontFamily: "monospace", marginBottom: 12 }}>
          DIMENSION 02 — CAPACITY ANALYSIS
        </div>
        <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
          <div style={{ flex: 1, background: T.white, border: `1px solid ${T.gray200}`, padding: "20px 24px" }}>
            <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace", marginBottom: 8 }}>TOTAL TEAM CAPACITY (30-DAY)</div>
            <div style={{ fontSize: 36, fontWeight: 700, fontFamily: "Georgia, serif" }}>
              {typeof kpis.total_capacity === 'number' ? kpis.total_capacity.toLocaleString() : kpis.total_capacity ? kpis.total_capacity : '—'}
            </div>
            <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace", marginTop: 4 }}>UNITS: SLOT-HOURS</div>
          </div>
          <div style={{ flex: 1, background: T.white, border: `1px solid ${T.gray200}`, padding: "20px 24px" }}>
            <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace", marginBottom: 8 }}>TOTAL BOOKED APPOINTMENTS</div>
            <div style={{ fontSize: 36, fontWeight: 700, fontFamily: "Georgia, serif" }}>
              {typeof kpis.total_booked === 'number' ? kpis.total_booked.toLocaleString() : kpis.total_booked ? kpis.total_booked : '—'}
            </div>
            <div style={{ fontSize: 11, color: T.green, fontFamily: "monospace", marginTop: 4 }}>↗ Real-time utilization data</div>
          </div>
          <div style={{ flex: 1, background: T.white, border: `2px solid ${T.orange}`, padding: "20px 24px" }}>
            <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace", marginBottom: 8 }}>AVG. TEAM UTILIZATION %</div>
            <div style={{ fontSize: 36, fontWeight: 700, fontFamily: "Georgia, serif", color: T.orange }}>
              {typeof kpis.avg_utilization === 'number' ? kpis.avg_utilization.toFixed(1) : kpis.avg_utilization ? kpis.avg_utilization : '—'}%
            </div>
            <div style={{ fontSize: 10, color: T.orange, fontFamily: "monospace", marginTop: 4 }}>CAPACITY: {typeof kpis.avg_utilization === 'number' && kpis.avg_utilization > 90 ? "HIGH UTILIZATION" : "NOMINAL"}</div>
          </div>
        </div>

        {/* Charts row */}
        <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
          {/* Utilization Peaks */}
          <div style={{ flex: 2, background: T.white, border: `1px solid ${T.gray200}`, padding: "20px 24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
              <div>
                <div style={{ fontSize: 18, fontWeight: 700, fontFamily: "Georgia, serif" }}>Utilization Trends</div>
                <div style={{ fontSize: 11, color: T.gray500, marginTop: 2 }}>Provider engagement metrics from capacity analysis.</div>
              </div>
            </div>
            {providers && providers.length > 0 ? (
              <div style={{ marginTop: 16, color: T.gray500, fontSize: 11, padding: "20px", textAlign: "center" }}>
                <div>Total Providers Analyzed: <strong>{providers.length}</strong></div>
                <div style={{ marginTop: 8 }}>Average Utilization: <strong>{providers.length > 0 ? (providers.reduce((sum, p) => sum + p.util, 0) / providers.length).toFixed(1) : 0}%</strong></div>
              </div>
            ) : (
              <div style={{ marginTop: 16, color: T.gray500, fontSize: 11, padding: "40px 20px", textAlign: "center" }}>
                No provider utilization data available for this period
              </div>
            )}
          </div>

          {/* Cohort Donut */}
          <div style={{ flex: 1, background: T.white, border: `1px solid ${T.gray200}`, padding: "20px 24px" }}>
            <div style={{ fontSize: 18, fontWeight: 700, fontFamily: "Georgia, serif", marginBottom: 4 }}>Utilization by Cohort</div>
            <div style={{ fontSize: 11, color: T.gray500 }}>Patient demographic distribution.</div>
            <DonutChart segments={donutSegments} />
          </div>
        </div>

        {/* Cohort Summary Table (Aggregated) */}
        <div style={{ background: T.white, border: `1px solid ${T.gray200}`, marginBottom: 24 }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${T.gray200}` }}>
                {["COHORT","PROVIDERS","AVG UTILIZATION","TOTAL CAPACITY","TOTAL BOOKED","% SPLIT","STATUS"].map(h => (
                  <th key={h} style={{ padding: "10px 14px", textAlign: "left", fontSize: 10, fontFamily: "monospace", color: T.gray500, fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {donutSegments && donutSegments.length > 0 ? donutSegments.map((cohort, i) => {
                const cohortProviders = providers.filter(p => p.cohort === cohort.label);
                const cohortUtilAvg = cohortProviders.length > 0
                  ? (cohortProviders.reduce((sum, p) => sum + p.util, 0) / cohortProviders.length).toFixed(1)
                  : 0;
                const cohortCapacity = cohortProviders.reduce((sum, p) => sum + p.cap, 0);
                const cohortBooked = cohortProviders.reduce((sum, p) => sum + p.booked, 0);
                const cohortStatus = cohortUtilAvg > 95 ? "optimal" : cohortUtilAvg > 50 ? "high" : "critical";

                return (
                  <tr key={cohort.label} style={{ borderBottom: `1px solid ${T.gray100}` }}>
                    <td style={{ padding: "12px 14px", fontWeight: 600 }}>{cohort.label}</td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>{cohortProviders.length}</td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace", fontWeight: 700, color: cohortStatus === "critical" ? T.red : cohortStatus === "high" ? T.orange : T.green }}>{cohortUtilAvg}%</td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>{cohortCapacity.toLocaleString()}</td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>{cohortBooked.toLocaleString()}</td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace", fontWeight: 700 }}>{cohort.pct}%</td>
                    <td style={{ padding: "12px 14px" }}><Badge variant={cohortStatus}>{cohortStatus.toUpperCase()}</Badge></td>
                  </tr>
                );
              }) : (
                <tr><td colSpan="7" style={{ padding: "20px", textAlign: "center", color: T.gray500 }}>Loading cohort data...</td></tr>
              )}
            </tbody>
          </table>
          <div style={{ padding: "12px 14px", fontSize: 10, color: T.gray500, fontFamily: "monospace", borderTop: `1px solid ${T.gray100}`, background: T.offwhite }}>
            📊 Cohort Utilization Summary (see Overview tab for individual provider details)
          </div>
        </div>

        {/* Bottom row labels */}
        <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
          <div style={{ fontSize: 10, color: T.gray500, letterSpacing: "0.1em", fontFamily: "monospace", flex: 1 }}>DIMENSION 04 — DEMAND FORECAST</div>
          <div style={{ fontSize: 10, color: T.gray500, letterSpacing: "0.1em", fontFamily: "monospace", flex: 1 }}>DIMENSION 05 — LOAD BALANCING</div>
        </div>

        <div style={{ display: "flex", gap: 12 }}>
          {/* Predictive Modeling */}
          <div style={{ flex: 1, background: T.white, border: `1px solid ${T.gray200}`, padding: "20px 24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
              <div>
                <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "Georgia, serif" }}>Predictive Modeling</div>
                <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace", marginTop: 2 }}>7-DAY APPOINTMENT PROJECTION</div>
              </div>
              <div style={{ display: "flex", gap: 10, fontSize: 10, fontFamily: "monospace" }}>
                <span style={{ display: "flex", alignItems: "center", gap: 4 }}><span style={{ width: 8, height: 8, background: T.black,  display: "inline-block" }} />ACTUAL</span>
                <span style={{ display: "flex", alignItems: "center", gap: 4 }}><span style={{ width: 8, height: 8, background: T.gray300,display: "inline-block" }} />FORECAST</span>
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "flex-end", gap: 6, height: 120, marginBottom: 8, border: "1px solid red" }}>
              {forecast.length > 0 ? forecast.map((v, i) => {
                const forecastPeak = Math.max(...forecast);
                const normalizedVal = (v / forecastPeak) * 100;
                const isPeak = v === forecastPeak;
                console.log(`Forecast ${i}: value=${v}, normalized=${normalizedVal}%, isPeak=${isPeak}`);
                return (
                  <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                    {isPeak && (
                      <div style={{ fontSize: 8, fontFamily: "monospace", background: T.black, color: T.white, padding: "2px 4px", marginBottom: 0 }}>PEAK</div>
                    )}
                    <div style={{ width: "100%", height: `${normalizedVal}px`, background: isPeak ? T.accent : i >= 5 ? T.gray300 : T.black, minHeight: "2px" }} />
                  </div>
                );
              }) : <div style={{color: T.red}}>NO FORECAST DATA</div>}
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              {FORECAST_DAYS.map(d => (
                <div key={d} style={{ flex: 1, textAlign: "center", fontSize: 9, fontFamily: "monospace", color: T.gray500 }}>{d}</div>
              ))}
            </div>
            <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
              {[
                { label: "FORECAST DAILY AVG.", val: (forecast.reduce((a, b) => a + b, 0) / forecast.length).toFixed(0) },
                { label: "PEAK PREDICTED DAY", val: FORECAST_DAYS[forecast.indexOf(Math.max(...forecast))] }
              ].map(s => (
                <div key={s.label} style={{ flex: 1, background: T.gray100, padding: "12px 16px" }}>
                  <div style={{ fontSize: 9, color: T.gray500, fontFamily: "monospace", marginBottom: 4 }}>{s.label}</div>
                  <div style={{ fontSize: s.label.includes("DAY") ? 16 : 22, fontWeight: 700, fontFamily: "Georgia, serif" }}>{s.val}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Load Distribution */}
          <div style={{ flex: 1, background: T.white, border: `1px solid ${T.gray200}`, padding: "20px 24px" }}>
            <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "Georgia, serif", marginBottom: 2 }}>Load Distribution</div>
            <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace", marginBottom: 16 }}>HOURLY FREQUENCY HEATMAP</div>

            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace", marginBottom: 8 }}>24-HOUR UTILIZATION</div>
              <div style={{ display: "flex", gap: 1, width: "100%", height: 40 }}>
                {hourlyData && hourlyData.length > 0 ? (
                  hourlyData.map((h, i) => {
                    const color = getHeatmapColor(h.utilization_pct);
                    return (
                      <div
                        key={i}
                        style={{
                          flex: 1,
                          height: "100%",
                          background: color,
                          cursor: "pointer",
                          opacity: 0.9
                        }}
                        title={`${h.hour}: ${h.utilization_pct}%`}
                      />
                    );
                  })
                ) : (
                  <div style={{ width: "100%", textAlign: "center", color: T.gray500, padding: "10px" }}>
                    Loading hourly data...
                  </div>
                )}
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 8, color: T.gray500, marginTop: 4, fontFamily: "monospace" }}>
                <span>00:00</span>
                <span>06:00</span>
                <span>12:00</span>
                <span>18:00</span>
                <span>23:00</span>
              </div>
            </div>
            <div style={{ display: "flex", gap: 0, marginBottom: 16, borderTop: `1px solid ${T.gray200}`, paddingTop: 12 }}>
              {[
                { label: "PEAK HOUR", val: peakHour },
                { label: "OFF-PEAK", val: offPeakHour },
                {
                  label: "PEAK RATIO",
                  val: hourlyData.length > 0 ? (() => {
                    const maxUtil = hourlyData.reduce((max, h) => Math.max(max, h.utilization_pct), 0);
                    const minUtil = hourlyData.reduce((min, h) => Math.min(min, h.utilization_pct), 100);
                    const ratio = minUtil > 0 ? (maxUtil / minUtil).toFixed(1) : (maxUtil > 0 ? "High" : "N/A");
                    return typeof ratio === 'string' ? ratio : ratio + "X";
                  })() : "N/A"
                }
              ].map((s, i) => (
                <div key={s.label} style={{ flex: 1, paddingRight: 12, borderRight: i < 2 ? `1px solid ${T.gray200}` : "none", marginRight: i < 2 ? 12 : 0 }}>
                  <div style={{ fontSize: 9, color: T.gray500, fontFamily: "monospace", marginBottom: 4 }}>{s.label}</div>
                  <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "Georgia, serif" }}>{s.val}</div>
                </div>
              ))}
            </div>
            {peakHour && peakHour !== "N/A" && (
              <div style={{ background: T.black, color: T.white, padding: "16px" }}>
                <div style={{ fontSize: 9, letterSpacing: "0.1em", fontFamily: "monospace", marginBottom: 8, color: T.gray300 }}>⚙ AI OPTIMIZATION INSIGHT</div>
                <div style={{ fontSize: 11, lineHeight: 1.5, marginBottom: 12, color: T.gray100 }}>
                  Peak load detected at {peakHour}. Recommend scheduling high-priority appointments during {offPeakHour} to {peakHour} window for optimal load distribution.
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Dimension 06 - QA Analytics */}
        <div style={{ marginTop: 24, marginBottom: 24 }}>
          <div style={{ fontSize: 10, color: T.gray500, letterSpacing: "0.1em", fontFamily: "monospace", marginBottom: 12 }}>
            DIMENSION 06 — QA ANALYTICS
          </div>

          <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
            {/* QA Scores Table */}
            <div style={{ flex: 1, background: T.white, border: `1px solid ${T.gray200}` }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: `1px solid ${T.gray200}` }}>
                    {["PROVIDER","QA SCORE","CALLS","BENCHMARK","STATUS"].map(h => (
                      <th key={h} style={{ padding: "10px 14px", textAlign: "left", fontSize: 10, fontFamily: "monospace", color: T.gray500, fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {qaScores && qaScores.length > 0 ? qaScores.map((qa, i) => {
                    const statusColor = qa.status === 'GOOD' ? T.green : qa.status === 'WARNING' ? T.orange : T.red;
                    return (
                      <tr key={i} style={{ borderBottom: `1px solid ${T.gray100}` }}>
                        <td style={{ padding: "12px 14px" }}>{qa.provider}</td>
                        <td style={{ padding: "12px 14px", fontFamily: "monospace", fontWeight: 700, color: statusColor }}>{qa.qa_score}</td>
                        <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>{qa.call_count}</td>
                        <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>{qa.benchmark}</td>
                        <td style={{ padding: "12px 14px", fontSize: 9, color: statusColor, fontWeight: 600 }}>{qa.status}</td>
                      </tr>
                    );
                  }) : (
                    <tr><td colSpan="5" style={{ padding: "20px", textAlign: "center", color: T.gray500 }}>Loading QA data...</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* QA Anomalies */}
            <div style={{ flex: 1, background: T.white, border: `1px solid ${T.gray200}`, padding: "20px 24px" }}>
              <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "Georgia, serif", marginBottom: 16 }}>Detected Anomalies</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {qaAnomalies && qaAnomalies.length > 0 ? qaAnomalies.slice(0, 5).map((anom, i) => {
                  const bgColor = anom.severity === 'CRITICAL' ? '#ffe6e6' : '#fff3cd';
                  const textColor = anom.severity === 'CRITICAL' ? T.red : T.orange;
                  return (
                    <div key={i} style={{ background: bgColor, padding: "12px 16px", borderRadius: 4, borderLeft: `3px solid ${textColor}` }}>
                      <div style={{ fontSize: 10, fontWeight: 700, color: textColor, marginBottom: 4 }}>{anom.provider}</div>
                      <div style={{ fontSize: 9, color: T.gray700, marginBottom: 4 }}>{anom.type} • {anom.value}</div>
                      <div style={{ fontSize: 8, color: T.gray600, fontStyle: "italic" }}>{anom.action}</div>
                    </div>
                  );
                }) : (
                  <div style={{ color: T.gray500, fontSize: 11, padding: "20px", textAlign: "center" }}>No anomalies detected</div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Dimension 08 - Historical Trends */}
        <div style={{ background: T.white, border: `1px solid ${T.gray200}`, padding: "20px 24px", marginBottom: 24 }}>
          <div style={{ fontSize: 10, color: T.gray500, letterSpacing: "0.1em", fontFamily: "monospace", marginBottom: 16 }}>
            DIMENSION 08 — HISTORICAL TRENDS
          </div>
          <div style={{ display: "flex", gap: 16 }}>
            {historicalTrends && Object.entries(historicalTrends).length > 0 ? Object.entries(historicalTrends).map(([year, data], i) => (
              <div key={year} style={{ flex: 1, background: T.gray50, padding: "16px", borderRadius: 4, border: `1px solid ${T.gray200}` }}>
                <div style={{ fontSize: 12, fontWeight: 700, fontFamily: "Georgia, serif", marginBottom: 12 }}>{year}</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {data.avg_util !== undefined && (
                    <div>
                      <div style={{ fontSize: 8, color: T.gray500, fontFamily: "monospace", marginBottom: 2 }}>AVG UTILIZATION</div>
                      <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "Georgia, serif" }}>{parseFloat(data.avg_util).toFixed(1)}%</div>
                    </div>
                  )}
                  {data.avg_qa !== undefined && (
                    <div>
                      <div style={{ fontSize: 8, color: T.gray500, fontFamily: "monospace", marginBottom: 2 }}>AVG QA SCORE</div>
                      <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "Georgia, serif" }}>{parseFloat(data.avg_qa).toFixed(1)}</div>
                    </div>
                  )}
                </div>
              </div>
            )) : (
              <div style={{ flex: 1, color: T.gray500, textAlign: "center", padding: "20px" }}>Loading historical data...</div>
            )}
          </div>
        </div>

        <div style={{ marginTop: 24, fontSize: 10, color: T.gray400, fontFamily: "monospace", display: "flex", gap: 16 }}>
          <span>CORE INTELLIGENCE V.4.2</span><span>|</span><span>SYSTEM HEALTHY</span>
          <span style={{ marginLeft: "auto" }}>PROPRIETARY CLINICAL DATA — INTERNAL USE ONLY</span>
        </div>
      </div>
    </div>
  );
}
