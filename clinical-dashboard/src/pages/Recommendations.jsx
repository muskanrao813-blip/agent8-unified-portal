import { T } from "../tokens";
import { Header } from "../components/UI";
import { useState, useEffect } from "react";

export default function RecommendationsPage({ startDate: initialStartDate, endDate: initialEndDate, setStartDate, setEndDate }) {
  const getDefaultDates = () => {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - 90);
    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0]
    };
  };

  const defaults = getDefaultDates();
  const [startDate, setLocalStartDate] = useState(initialStartDate || defaults.start);
  const [endDate, setLocalEndDate] = useState(initialEndDate || defaults.end);
  const [recommendations, setRecommendations] = useState([]);
  const [providerProfiles, setProviderProfiles] = useState(null);
  const [actionPlans, setActionPlans] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);

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

          const res = await fetch(`${baseUrl}/recommendations-proper?${params}`);
          if (!res.ok) throw new Error(`API error: ${res.status}`);

          const data = await res.json();
          setRecommendations(data.top_recommendations || []);
          setProviderProfiles(data.provider_profiles || {});
          setActionPlans(data.detailed_action_plans || []);
          setSummary(data.summary || {});
        } catch (err) {
          console.error("Error fetching recommendations:", err);
        } finally {
          setLoading(false);
        }
      };

      fetchData();
    }, 500);

    return () => clearTimeout(timer);
  }, [startDate, endDate]);

  const getPriorityColor = (priority) => {
    const colors = { CRITICAL: T.red, HIGH: T.orange, INFO: T.blue };
    return colors[priority] || T.gray500;
  };

  const getPriorityBg = (priority) => {
    const bgs = { CRITICAL: '#FFE5E5', HIGH: '#FFF3E0', INFO: '#E5F3FF' };
    return bgs[priority] || T.gray100;
  };

  const getTierColor = (tier) => {
    switch(tier) {
      case 'EXCELLENT': return T.green;
      case 'GOOD': return '#2E8B57';
      case 'MONITOR': return T.orange;
      case 'NEEDS_HELP': return T.red;
      default: return T.gray500;
    }
  };

  const getTierBg = (tier) => {
    switch(tier) {
      case 'EXCELLENT': return '#F0FFF0';
      case 'GOOD': return '#F5FFF5';
      case 'MONITOR': return '#FFF8F0';
      case 'NEEDS_HELP': return '#FFE5E5';
      default: return T.gray100;
    }
  };

  if (loading) {
    return <div style={{ padding: 40, textAlign: "center", color: T.gray500 }}>Loading analysis...</div>;
  }

  return (
    <div style={{ background: T.gray50, minHeight: "100vh", padding: 24 }}>
      <Header
        title="Recommendations & Analytics"
        subtitle="Capacity-based analysis with QA integration and seasonality trends"
        startDate={startDate}
        endDate={endDate}
        setStartDate={setLocalStartDate}
        setEndDate={setLocalEndDate}
      />

      {/* Key Metrics */}
      {summary && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, marginBottom: 24 }}>
          <div style={{ background: T.white, border: `1px solid ${T.gray200}`, padding: 16, borderRadius: 4 }}>
            <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace", marginBottom: 8 }}>YoY GROWTH</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: summary.overall_seasonality_pct > 10 ? T.green : summary.overall_seasonality_pct < -10 ? T.red : T.black }}>
              {summary.overall_seasonality_pct > 0 ? '+' : ''}{summary.overall_seasonality_pct}%
            </div>
            <div style={{ fontSize: 9, color: T.gray600, marginTop: 4 }}>vs same period last year</div>
          </div>

          <div style={{ background: T.white, border: `1px solid ${T.gray200}`, padding: 16, borderRadius: 4 }}>
            <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace", marginBottom: 8 }}>AVG UTILIZATION</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: T.black }}>
              {summary.current_avg_appts ? Math.round(summary.current_avg_appts) : 0}
            </div>
            <div style={{ fontSize: 9, color: T.gray600, marginTop: 4 }}>appts/provider</div>
          </div>

          <div style={{ background: T.white, border: `1px solid ${T.gray200}`, padding: 16, borderRadius: 4 }}>
            <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace", marginBottom: 8 }}>EXCELLENT</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: T.green }}>
              {summary.tier_counts?.excellent || 0}
            </div>
            <div style={{ fontSize: 9, color: T.gray600, marginTop: 4 }}>{summary.tier_counts?.excellent ? 'performing excellent' : 'none'}</div>
          </div>

          <div style={{ background: T.white, border: `1px solid ${T.gray200}`, padding: 16, borderRadius: 4 }}>
            <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace", marginBottom: 8 }}>NEEDS HELP</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: T.red }}>
              {summary.tier_counts?.needs_help || 0}
            </div>
            <div style={{ fontSize: 9, color: T.gray600, marginTop: 4 }}>below capacity threshold</div>
          </div>
        </div>
      )}

      {/* Top Strategic Recommendations */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "Georgia, serif", marginBottom: 16, color: T.black }}>
          Strategic Insights
        </div>

        {recommendations.length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {recommendations.map((rec, idx) => (
              <div key={idx} style={{ background: T.white, border: `1px solid ${T.gray200}`, padding: 20, borderRadius: 4, borderLeft: `5px solid ${getPriorityColor(rec.priority)}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: T.black, marginBottom: 4 }}>
                      {rec.title}
                    </div>
                    <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace" }}>
                      {rec.category}
                      {rec.affected_providers !== undefined && ` | ${rec.affected_providers} providers affected`}
                    </div>
                  </div>
                  <div style={{ background: getPriorityBg(rec.priority), color: getPriorityColor(rec.priority), padding: "6px 12px", borderRadius: 3, fontSize: 11, fontWeight: 700 }}>
                    {rec.priority}
                  </div>
                </div>

                <div style={{ fontSize: 12, color: T.gray700, marginBottom: 16, lineHeight: 1.6 }}>
                  {rec.description}
                </div>

                <div style={{ background: "#F5F5F5", padding: 12, borderRadius: 3, marginBottom: 12 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: T.black, marginBottom: 8 }}>Action Items:</div>
                  <ul style={{ margin: 0, paddingLeft: 20, fontSize: 11, color: T.gray700 }}>
                    {rec.action_items?.map((item, i) => (
                      <li key={i} style={{ marginBottom: 4 }}>{item}</li>
                    ))}
                  </ul>
                </div>

                {rec.worst_performers && rec.worst_performers.length > 0 && (
                  <div style={{ background: "#FFF8F8", padding: 12, borderRadius: 3, borderLeft: `2px solid ${T.orange}` }}>
                    <div style={{ fontSize: 10, fontWeight: 600, color: T.black, marginBottom: 8 }}>Affected Providers:</div>
                    {rec.worst_performers.slice(0, 3).map((p, i) => (
                      <div key={i} style={{ fontSize: 10, color: T.gray700, marginBottom: 4 }}>
                        • <strong>{p.provider}</strong>: {p.utilization_pct}% capacity {p.qa_score ? `| QA: ${p.qa_score}` : ''}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ background: T.white, border: `1px solid ${T.gray200}`, padding: 24, textAlign: "center", color: T.gray400 }}>
            No critical insights found
          </div>
        )}
      </div>

      {/* Performance Tiers */}
      {providerProfiles && (
        <div style={{ marginTop: 32 }}>
          <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "Georgia, serif", marginBottom: 16, color: T.black }}>
            Provider Performance Tiers
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(380px, 1fr))", gap: 16 }}>
            {/* EXCELLENT TIER */}
            <div style={{ background: T.white, border: `1px solid ${T.gray200}`, padding: 16, borderRadius: 4, borderTop: `4px solid ${T.green}` }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: T.green, marginBottom: 12 }}>
                EXCELLENT ({providerProfiles.excellent?.length || 0})
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {providerProfiles.excellent?.map((p, i) => (
                  <div key={i} style={{ fontSize: 10, color: T.black, padding: 8, background: "#F0FFF0", borderRadius: 2 }}>
                    <div style={{ fontWeight: 600, marginBottom: 4 }}>{p.provider}</div>
                    <div style={{ color: T.gray600, fontSize: 9, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                      <div>Capacity: <strong>{p.utilization_pct}%</strong></div>
                      <div>Appts/Day: <strong>{p.appts_per_day}</strong></div>
                      {p.qa_score && <div>QA: <strong>{p.qa_score}</strong></div>}
                      <div>Days: <strong>{p.working_days}</strong></div>
                    </div>
                  </div>
                ))}
                {(!providerProfiles.excellent || providerProfiles.excellent.length === 0) && (
                  <div style={{ fontSize: 10, color: T.gray400, padding: 8 }}>No providers at this tier</div>
                )}
              </div>
            </div>

            {/* GOOD TIER */}
            <div style={{ background: T.white, border: `1px solid ${T.gray200}`, padding: 16, borderRadius: 4, borderTop: `4px solid #2E8B57` }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#2E8B57', marginBottom: 12 }}>
                GOOD ({providerProfiles.good?.length || 0})
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {providerProfiles.good?.map((p, i) => (
                  <div key={i} style={{ fontSize: 10, color: T.black, padding: 8, background: "#F5FFF5", borderRadius: 2 }}>
                    <div style={{ fontWeight: 600, marginBottom: 4 }}>{p.provider}</div>
                    <div style={{ color: T.gray600, fontSize: 9, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                      <div>Capacity: <strong>{p.utilization_pct}%</strong></div>
                      <div>Appts/Day: <strong>{p.appts_per_day}</strong></div>
                      {p.qa_score && <div>QA: <strong>{p.qa_score}</strong></div>}
                      <div>Days: <strong>{p.working_days}</strong></div>
                    </div>
                  </div>
                ))}
                {(!providerProfiles.good || providerProfiles.good.length === 0) && (
                  <div style={{ fontSize: 10, color: T.gray400, padding: 8 }}>No providers at this tier</div>
                )}
              </div>
            </div>

            {/* MONITOR TIER */}
            <div style={{ background: T.white, border: `1px solid ${T.gray200}`, padding: 16, borderRadius: 4, borderTop: `4px solid ${T.orange}` }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: T.orange, marginBottom: 12 }}>
                MONITOR ({providerProfiles.monitor?.length || 0})
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {providerProfiles.monitor?.map((p, i) => (
                  <div key={i} style={{ fontSize: 10, color: T.black, padding: 8, background: "#FFF8F0", borderRadius: 2 }}>
                    <div style={{ fontWeight: 600, marginBottom: 4 }}>{p.provider}</div>
                    <div style={{ color: T.gray600, fontSize: 9, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                      <div>Capacity: <strong>{p.utilization_pct}%</strong></div>
                      <div>Appts/Day: <strong>{p.appts_per_day}</strong></div>
                      {p.qa_score && <div>QA: <strong>{p.qa_score}</strong></div>}
                      <div>Days: <strong>{p.working_days}</strong></div>
                    </div>
                  </div>
                ))}
                {(!providerProfiles.monitor || providerProfiles.monitor.length === 0) && (
                  <div style={{ fontSize: 10, color: T.gray400, padding: 8 }}>No providers at this tier</div>
                )}
              </div>
            </div>

            {/* NEEDS HELP TIER */}
            <div style={{ background: T.white, border: `1px solid ${T.gray200}`, padding: 16, borderRadius: 4, borderTop: `4px solid ${T.red}` }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: T.red, marginBottom: 12 }}>
                NEEDS HELP ({providerProfiles.needs_help?.length || 0}) ⚠️
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {providerProfiles.needs_help?.map((p, i) => (
                  <div key={i} style={{ fontSize: 10, color: T.black, padding: 8, background: "#FFE5E5", borderRadius: 2 }}>
                    <div style={{ fontWeight: 600, marginBottom: 4 }}>{p.provider}</div>
                    <div style={{ color: T.gray600, fontSize: 9, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                      <div>Capacity: <strong>{p.utilization_pct}%</strong></div>
                      <div>Appts/Day: <strong>{p.appts_per_day}</strong></div>
                      {p.qa_score && <div>QA: <strong>{p.qa_score}</strong></div>}
                      <div>Days: <strong>{p.working_days}</strong></div>
                    </div>
                  </div>
                ))}
                {(!providerProfiles.needs_help || providerProfiles.needs_help.length === 0) && (
                  <div style={{ fontSize: 10, color: T.gray400, padding: 8 }}>No providers at this tier</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detailed Action Plans for NEEDS_HELP Providers */}
      {actionPlans.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "Georgia, serif", marginBottom: 16, color: T.black }}>
            Detailed Action Plans - NEEDS_HELP Providers
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {actionPlans.map((plan, idx) => (
              <div key={idx} style={{ background: T.white, border: `2px solid ${T.red}`, padding: 20, borderRadius: 4 }}>
                {/* Provider Header */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
                  <div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: T.black, marginBottom: 4 }}>
                      {plan.provider}
                    </div>
                    <div style={{ fontSize: 11, color: T.gray500, fontFamily: "monospace" }}>
                      NEEDS_HELP Tier | Priority: {plan.priority}
                    </div>
                  </div>
                  <div style={{ background: '#FFE5E5', color: T.red, padding: "8px 16px", borderRadius: 4, fontWeight: 700, fontSize: 12 }}>
                    {plan.priority}
                  </div>
                </div>

                {/* Current Metrics */}
                <div style={{ background: T.gray50, padding: 12, borderRadius: 4, marginBottom: 16 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: T.black, marginBottom: 8 }}>Current Performance:</div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12, fontSize: 10, color: T.gray700 }}>
                    <div>
                      <strong>Utilization:</strong> {plan.current_metrics.utilization_pct.toFixed(1)}%
                      <div style={{ fontSize: 9, color: plan.current_metrics.utilization_pct < 40 ? T.red : T.orange }}>
                        {plan.current_metrics.utilization_pct < 40 ? 'CRITICAL' : 'BELOW TARGET'}
                      </div>
                    </div>
                    <div>
                      <strong>Appointments/Day:</strong> {plan.current_metrics.appts_per_day.toFixed(1)}
                      <div style={{ fontSize: 9, color: T.gray600 }}>
                        {plan.current_metrics.total_appointments} total
                      </div>
                    </div>
                    <div>
                      <strong>Working Days:</strong> {plan.current_metrics.working_days}
                      <div style={{ fontSize: 9, color: plan.current_metrics.working_days < 15 ? T.orange : T.gray600 }}>
                        {plan.current_metrics.working_days < 15 ? 'LOW ACTIVITY' : 'Acceptable'}
                      </div>
                    </div>
                    {plan.current_metrics.qa_score && (
                      <div>
                        <strong>QA Score:</strong> {plan.current_metrics.qa_score}
                        <div style={{ fontSize: 9, color: plan.current_metrics.qa_score < 70 ? T.red : plan.current_metrics.qa_score < 80 ? T.orange : T.green }}>
                          {plan.current_metrics.qa_score < 70 ? 'CRITICAL' : plan.current_metrics.qa_score < 80 ? 'WARNING' : 'GOOD'}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Issues Identified */}
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: T.black, marginBottom: 8 }}>Issues Identified:</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {plan.issues.map((issue, i) => (
                      <div key={i} style={{ fontSize: 10, color: T.red, paddingLeft: 16, borderLeft: `2px solid ${T.red}`, padding: "4px 0 4px 12px" }}>
                        ⚠️ {issue}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recommended Actions */}
                <div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: T.black, marginBottom: 12 }}>Recommended Actions:</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    {plan.recommended_actions.map((action, i) => (
                      <div key={i} style={{ background: "#FFF8F0", border: `1px solid ${T.orange}`, borderRadius: 4, padding: 12 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                          <div>
                            <div style={{ fontSize: 11, fontWeight: 700, color: T.black }}>
                              {action.type.replace(/_/g, ' ')}
                            </div>
                            <div style={{ fontSize: 10, fontWeight: 600, color: T.orange, marginTop: 2 }}>
                              {action.title}
                            </div>
                          </div>
                          <div style={{ fontSize: 9, background: '#FFE5CC', color: T.orange, padding: "4px 8px", borderRadius: 2, fontWeight: 600, whiteSpace: "nowrap" }}>
                            {action.timeline}
                          </div>
                        </div>

                        <div style={{ fontSize: 10, color: T.gray700, marginBottom: 8 }}>
                          {action.description}
                        </div>

                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontSize: 9, color: T.gray600 }}>
                          <div>
                            <strong style={{ color: T.black }}>Action:</strong><br/>
                            {action.action}
                          </div>
                          <div>
                            <strong style={{ color: T.black }}>Owner:</strong><br/>
                            {action.owner}
                          </div>
                          <div style={{ gridColumn: "1 / -1" }}>
                            <strong style={{ color: T.green }}>Success Metric:</strong><br/>
                            {action.success_metric}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Methodology Section */}
      {summary?.methodology && (
        <div style={{ marginTop: 32, background: T.gray100, border: `1px solid ${T.gray200}`, padding: 16, borderRadius: 4 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: T.gray700, marginBottom: 12 }}>Methodology</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: 16, fontSize: 10, color: T.gray600 }}>
            <div>
              <strong>Utilization %:</strong><br/>
              {summary.methodology?.utilization}
            </div>
            <div>
              <strong>Seasonality:</strong><br/>
              {summary.methodology?.seasonality}
            </div>
            <div>
              <strong>Performance Tiers:</strong><br/>
              {summary.methodology?.tiers}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
