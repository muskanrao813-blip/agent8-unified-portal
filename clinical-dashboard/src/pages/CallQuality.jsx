import { T } from "../tokens";
import { Badge, Header } from "../components/UI";
import { useState, useEffect } from "react";

const DEFAULT_STAFF_BARS = [
  { name: "Dr. Aris",   ind: 85, peer: 70 },
  { name: "Dr. Chen",   ind: 60, peer: 70 },
  { name: "Nurse Bell", ind: 75, peer: 70 },
  { name: "Diet. Long", ind: 42, peer: 70 },
  { name: "Nurse Kim",  ind: 90, peer: 70 },
  { name: "Dr. Patel",  ind: 88, peer: 70 },
  { name: "Dr. Gomez",  ind: 78, peer: 70 },
];

const DEFAULT_BREACH_CATS = [
  { label: "Incomplete Clinical History",  pct: 42 },
  { label: "Missed Medication Protocol",   pct: 28 },
  { label: "Standard Greeting Lapse",      pct: 15 },
  { label: "Incorrect Referral Route",     pct: 9  },
];

const DEFAULT_CALL_ROWS = [
  { name: "Dr. Sarah Aris",   cohort: "Clinical Gen-B",    dur: "14m 22s", score: "94%", status: "verified", issue: "N/A",                 scoreColor: T.black  },
  { name: "Nurse Tom Bell",   cohort: "Remote Support",    dur: "08m 15s", score: "42%", status: "breach",   issue: "Medication Protocol", scoreColor: T.red    },
  { name: "Diet. Elena Long", cohort: "Nutritional Admin", dur: "22m 04s", score: "78%", status: "flagged",  issue: "History Depth",       scoreColor: T.orange },
  { name: "Dr. James Chen",   cohort: "Clinical Gen-B",    dur: "12m 58s", score: "89%", status: "verified", issue: "N/A",                 scoreColor: T.black  },
  { name: "Nurse Hana Kim",   cohort: "Remote Support",    dur: "10m 30s", score: "91%", status: "verified", issue: "N/A",                 scoreColor: T.black  },
];

export default function CallQualityPage() {
  const [calls, setCalls] = useState([]);
  const [staffBars, setStaffBars] = useState(DEFAULT_STAFF_BARS);
  const [breachCats, setBreachCats] = useState(DEFAULT_BREACH_CATS);
  const [kpis, setKpis] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const baseUrl = process.env.REACT_APP_API_URL || "http://localhost:5001/api/agent8";
        const res = await fetch(`${baseUrl.replace('/api/agent8', '')}/api/calls/`);
        const data = await res.json();

        if (Array.isArray(data)) {
          setCalls(data.slice(0, 5).map(c => ({
            name: c.professional_name || "Unknown",
            cohort: c.cohort || "General",
            dur: c.duration || "N/A",
            score: c.qa_score ? `${c.qa_score}%` : "N/A",
            status: c.status || "verified",
            issue: c.primary_issue || "N/A",
            scoreColor: c.qa_score < 50 ? T.red : c.qa_score < 75 ? T.orange : T.black
          })));
        }
      } catch (e) {
        console.error("Failed to fetch calls:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);
  return (
    <div style={{ flex: 1, overflow: "auto", background: T.offwhite }}>
      <Header title="Call Quality" />
      <div style={{ padding: "28px" }}>

        <div style={{ fontSize: 10, color: T.gray500, letterSpacing: "0.1em", fontFamily: "monospace", marginBottom: 8 }}>
          CALL QUALITY ANALYSIS
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24 }}>
          <div>
            <div style={{ fontSize: 36, fontWeight: 700, fontFamily: "Georgia, serif", lineHeight: 1 }}>
              Executive Performance Overview
            </div>
            <div style={{ fontSize: 11, color: T.gray500, fontFamily: "monospace", marginTop: 6, letterSpacing: "0.06em" }}>
              REAL-TIME HEALTH OF CLINICAL CONSULTATIONS AND DIETICIAN PERFORMANCE.
            </div>
          </div>
          <button style={{
            background: T.black, color: T.white, border: "none",
            padding: "12px 20px", fontSize: 11, fontWeight: 700,
            letterSpacing: "0.06em", textTransform: "uppercase", cursor: "pointer",
          }}>↓ EXPORT PDF</button>
        </div>

        {/* Top KPI row */}
        <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
          {[
            { label: "TOTAL CALLS ANALYZED", value: "1,284", badge: "+12%",  badgeColor: T.green, icon: "📊" },
            { label: "AVG. QUALITY SCORE %",  value: "88.4%", badge: "+2.4%", badgeColor: T.green, icon: "✓" },
            { label: "SOP COMPLIANCE %",       value: "92.1%", badge: "-0.8%", badgeColor: T.red,   icon: "🛡" },
            { label: "CRITICAL QA ALERTS",     value: "12",    badge: "CRITICAL", badgeColor: T.red, icon: "!", highlight: true },
          ].map(m => (
            <div key={m.label} style={{
              flex: 1, background: T.white,
              border: m.highlight ? `1px solid ${T.red}` : `1px solid ${T.gray200}`,
              padding: "20px 24px",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <div style={{ fontSize: 10, color: T.gray500, letterSpacing: "0.1em", fontFamily: "monospace", marginBottom: 12 }}>{m.label}</div>
                <span style={{ fontSize: 16, color: m.highlight ? T.red : T.gray400 }}>{m.icon}</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ fontSize: 32, fontWeight: 700, fontFamily: "Georgia, serif", color: m.highlight ? T.red : T.black }}>
                  {m.value}
                </div>
                <Badge variant={m.highlight ? "critical" : m.badgeColor === T.red ? "critical" : "default"}>
                  {m.badge}
                </Badge>
              </div>
            </div>
          ))}
        </div>

        {/* Charts row */}
        <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
          {/* Staff Performance */}
          <div style={{ flex: 2, background: T.white, border: `1px solid ${T.gray200}`, padding: "20px 24px" }}>
            <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "Georgia, serif", marginBottom: 2 }}>Staff Performance Metrics</div>
            <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace", marginBottom: 12 }}>
              DISTRIBUTION OF QUALITY SCORES ACROSS CLINICAL STAFF MEMBERS.
            </div>
            <div style={{ display: "flex", gap: 10, marginBottom: 16, fontSize: 10, fontFamily: "monospace" }}>
              <span style={{ display: "flex", alignItems: "center", gap: 4 }}><span style={{ width: 8, height: 8, background: T.black,  display: "inline-block" }} />INDIVIDUAL</span>
              <span style={{ display: "flex", alignItems: "center", gap: 4 }}><span style={{ width: 8, height: 8, background: T.gray300,display: "inline-block" }} />PEER MEDIAN</span>
            </div>
            <div style={{ display: "flex", alignItems: "flex-end", gap: 10, height: 100, marginBottom: 28 }}>
              {staffBars.map((b, i) => (
                <div key={i} style={{ flex: 1, display: "flex", gap: 2, alignItems: "flex-end" }}>
                  <div style={{ flex: 1, height: `${b.ind}%`, background: b.ind < 50 ? T.red : T.black }} />
                  <div style={{ flex: 1, height: `${b.peer}%`, background: T.gray300 }} />
                </div>
              ))}
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              {staffBars.map((b, i) => (
                <div key={i} style={{ flex: 1, textAlign: "center", fontSize: 8, fontFamily: "monospace", color: T.gray500 }}>
                  {b.name}
                </div>
              ))}
            </div>
          </div>

          {/* SOP Breach */}
          <div style={{ flex: 1, background: T.white, border: `1px solid ${T.gray200}`, padding: "20px 24px" }}>
            <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "Georgia, serif", marginBottom: 2 }}>SOP Breach Categories</div>
            <div style={{ fontSize: 10, color: T.gray500, fontFamily: "monospace", marginBottom: 16 }}>
              MOST COMMON COMPLIANCE FAILURES IDENTIFIED BY AI.
            </div>
            {breachCats.map(b => (
              <div key={b.label} style={{ marginBottom: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
                  <span>{b.label}</span>
                  <span style={{ fontFamily: "monospace", fontWeight: 600 }}>{b.pct}%</span>
                </div>
                <div style={{ height: 3, background: T.gray100 }}>
                  <div style={{ height: 3, width: `${b.pct}%`, background: T.black }} />
                </div>
              </div>
            ))}
            <button style={{
              width: "100%", marginTop: 16,
              border: `1px solid ${T.black}`, background: T.white,
              padding: "10px", fontSize: 11, fontWeight: 700,
              letterSpacing: "0.06em", textTransform: "uppercase", cursor: "pointer",
            }}>
              VIEW ALL BREACH TYPES
            </button>
          </div>
        </div>

        {/* Recent Call Analysis */}
        <div style={{ background: T.white, border: `1px solid ${T.gray200}` }}>
          <div style={{ padding: "18px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: `1px solid ${T.gray200}` }}>
            <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "Georgia, serif" }}>Recent Call Analysis</div>
            <input
              placeholder="Search Calls..."
              style={{ padding: "7px 12px", border: "none", borderBottom: `1px solid ${T.gray300}`, fontSize: 12, width: 200, outline: "none", fontFamily: "monospace", background: "transparent" }}
            />
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${T.gray200}` }}>
                {["PROFESSIONAL NAME","COHORT","DURATION","QUALITY SCORE","COMPLIANCE STATUS","PRIMARY ISSUE",""].map(h => (
                  <th key={h} style={{ padding: "10px 14px", textAlign: "left", fontSize: 10, fontFamily: "monospace", color: T.gray500 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {calls.length > 0 ? calls.map(r => (
                <tr key={r.name} style={{ borderBottom: `1px solid ${T.gray100}` }}>
                  <td style={{ padding: "12px 14px", fontWeight: 600 }}>{r.name}</td>
                  <td style={{ padding: "12px 14px", color: T.gray500, fontSize: 11 }}>{r.cohort}</td>
                  <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>{r.dur}</td>
                  <td style={{ padding: "12px 14px", fontFamily: "monospace", fontWeight: 700, color: r.scoreColor }}>{r.score}</td>
                  <td style={{ padding: "12px 14px" }}><Badge variant={r.status}>{r.status.toUpperCase()}</Badge></td>
                  <td style={{ padding: "12px 14px", color: r.issue !== "N/A" ? T.red : T.gray400, fontWeight: r.issue !== "N/A" ? 600 : 400, fontSize: 11 }}>{r.issue}</td>
                  <td style={{ padding: "12px 14px", color: T.black, fontWeight: 600, cursor: "pointer", fontSize: 11, textDecoration: "underline" }}>Transcript</td>
                </tr>
              )) : (
                DEFAULT_CALL_ROWS.map(r => (
                  <tr key={r.name} style={{ borderBottom: `1px solid ${T.gray100}` }}>
                    <td style={{ padding: "12px 14px", fontWeight: 600 }}>{r.name}</td>
                    <td style={{ padding: "12px 14px", color: T.gray500, fontSize: 11 }}>{r.cohort}</td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>{r.dur}</td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace", fontWeight: 700, color: r.scoreColor }}>{r.score}</td>
                    <td style={{ padding: "12px 14px" }}><Badge variant={r.status}>{r.status.toUpperCase()}</Badge></td>
                    <td style={{ padding: "12px 14px", color: r.issue !== "N/A" ? T.red : T.gray400, fontWeight: r.issue !== "N/A" ? 600 : 400, fontSize: 11 }}>{r.issue}</td>
                    <td style={{ padding: "12px 14px", color: T.black, fontWeight: 600, cursor: "pointer", fontSize: 11, textDecoration: "underline" }}>Transcript</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <div style={{ padding: "12px 14px", fontSize: 11, color: T.gray500, fontFamily: "monospace", borderTop: `1px solid ${T.gray100}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            Showing 1-{calls.length || 5} of 1,284 sessions
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <button onClick={() => alert("Previous page")} style={{ border: `1px solid ${T.gray200}`, background: T.white, color: T.gray500, cursor: "pointer", fontSize: 10, padding: "6px 12px" }}>PREVIOUS</button>
              {["1","2","3"].map(p => (
                <button key={p} onClick={() => alert(`Page ${p}`)} style={{ width: 24, height: 24, border: `1px solid ${T.gray200}`, background: p === "1" ? T.black : T.white, color: p === "1" ? T.white : T.black, cursor: "pointer", fontSize: 11 }}>{p}</button>
              ))}
              <button onClick={() => alert("Next page")} style={{ border: `1px solid ${T.gray200}`, background: T.white, color: T.gray500, cursor: "pointer", fontSize: 10, padding: "6px 12px" }}>NEXT</button>
            </div>
          </div>
        </div>

        <div style={{ marginTop: 24, textAlign: "center", fontSize: 10, color: T.gray400, fontFamily: "monospace", letterSpacing: "0.1em" }}>
          OPERATIONS INTELLIGENCE LAYER ACTIVE
        </div>
      </div>
    </div>
  );
}
