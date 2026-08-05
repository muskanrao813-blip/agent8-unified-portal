import { T } from "../tokens";

const BARS = [65, 55, 60, 90, 45];
const BAR_COLORS = ["#C8C7C0", "#A8A79E", "#888780", "#3A3935", "#C8C7C0"];
const MAX_BAR = Math.max(...BARS);

const JOURNEY = [
  {
    when: "TODAY, 11:30 AM",
    title: "Complex Metabolic Review",
    sub: "Patient ID: 4920-X - Successful intervention",
  },
  {
    when: "YESTERDAY, 04:15 PM",
    title: "Routine Capacity Audit",
    sub: "Adjustment of patient scheduling flow",
  },
];

export default function ProfilePanel({ name, onClose }) {
  return (
    <div
      style={{
        position: "fixed", inset: 0,
        background: "rgba(0,0,0,0.3)", zIndex: 100,
        display: "flex", alignItems: "flex-start", justifyContent: "flex-end",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: 380, height: "100vh", background: T.white,
          display: "flex", flexDirection: "column", overflowY: "auto",
          boxShadow: "-4px 0 24px rgba(0,0,0,0.12)",
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ padding: "24px 24px 20px", borderBottom: `1px solid ${T.gray200}` }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <div style={{ fontSize: 10, color: T.gray500, letterSpacing: "0.1em", fontFamily: "monospace", marginBottom: 6 }}>
                PROFESSIONAL PROFILE
              </div>
              <div style={{ fontSize: 28, fontWeight: 700, fontFamily: "Georgia, serif" }}>{name}</div>
            </div>
            <button
              onClick={onClose}
              style={{ background: "none", border: "none", fontSize: 20, cursor: "pointer", color: T.gray400, marginTop: 4 }}
            >
              ✕
            </button>
          </div>
        </div>

        <div style={{ padding: "20px 24px", flex: 1 }}>
          {/* Mini metrics */}
          <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
            {[
              { label: "CURRENT LOAD", value: "98.2%" },
              { label: "CLINICAL SCORE", value: "98.5" },
            ].map(m => (
              <div key={m.label} style={{ flex: 1, border: `1px solid ${T.gray200}`, padding: "14px 16px" }}>
                <div style={{ fontSize: 9, color: T.gray500, letterSpacing: "0.1em", fontFamily: "monospace", marginBottom: 8 }}>{m.label}</div>
                <div style={{ fontSize: 28, fontWeight: 700, fontFamily: "Georgia, serif" }}>{m.value}</div>
              </div>
            ))}
          </div>

          {/* Clinical Journey */}
          <div style={{ marginBottom: 24 }}>
            <div style={{
              fontSize: 10, color: T.gray500, letterSpacing: "0.1em", fontFamily: "monospace",
              marginBottom: 14, borderBottom: `1px solid ${T.gray200}`, paddingBottom: 8,
            }}>
              CLINICAL JOURNEY
            </div>
            {JOURNEY.map(e => (
              <div key={e.when} style={{ borderLeft: `3px solid ${T.black}`, paddingLeft: 14, marginBottom: 18 }}>
                <div style={{ fontSize: 10, color: T.gray400, fontFamily: "monospace", marginBottom: 4 }}>{e.when}</div>
                <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 2 }}>{e.title}</div>
                <div style={{ fontSize: 12, color: T.gray500 }}>{e.sub}</div>
              </div>
            ))}
          </div>

          {/* Load Analysis */}
          <div>
            <div style={{
              fontSize: 10, color: T.gray500, letterSpacing: "0.1em", fontFamily: "monospace",
              marginBottom: 14, borderBottom: `1px solid ${T.gray200}`, paddingBottom: 8,
            }}>
              LOAD ANALYSIS
            </div>
            <div style={{ border: `1px solid ${T.gray200}`, padding: "16px", marginBottom: 8 }}>
              <div style={{ display: "flex", alignItems: "flex-end", gap: 6, height: 80 }}>
                {BARS.map((b, i) => (
                  <div key={i} style={{ flex: 1, height: `${(b / MAX_BAR) * 100}%`, background: BAR_COLORS[i] }} />
                ))}
              </div>
            </div>
            <div style={{ fontSize: 9, color: T.gray400, letterSpacing: "0.12em", fontFamily: "monospace", textAlign: "center" }}>
              30-DAY CAPACITY OSCILLATION
            </div>
          </div>
        </div>

        {/* Footer actions */}
        <div style={{ padding: "16px 24px", borderTop: `1px solid ${T.gray200}`, display: "flex", gap: 12 }}>
          <button style={{
            flex: 1, background: T.black, color: T.white, border: "none",
            padding: "12px", fontSize: 11, fontWeight: 700,
            letterSpacing: "0.08em", textTransform: "uppercase", cursor: "pointer",
          }}>
            REASSIGN PATIENTS
          </button>
          <button style={{
            flex: 1, background: T.white, color: T.black, border: `1px solid ${T.black}`,
            padding: "12px", fontSize: 11, fontWeight: 700,
            letterSpacing: "0.08em", textTransform: "uppercase", cursor: "pointer",
          }}>
            FULL RECORD
          </button>
        </div>
      </div>
    </div>
  );
}
