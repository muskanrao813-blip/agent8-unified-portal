import { useState } from "react";
import { T } from "../tokens";

const NAV_ITEMS = [
  { id: "overview",          label: "Overview",          icon: "⊞" },
  { id: "clinical-outcomes", label: "Clinical Outcomes", icon: "📊" },
  { id: "utilization",       label: "Utilization",       icon: "📈" },
  { id: "recommendations",   label: "Recommendations",   icon: "💡" },
  {
    id: "call-quality",
    label: "Call Quality Analysis",
    icon: "📞",
    children: [
      { id: "qa-dashboard", label: "Dashboard" },
      { id: "qa-upload", label: "Call Upload" },
      { id: "qa-transcriptions", label: "Transcriptions" },
      { id: "qa-insights", label: "AI Insights" },
      { id: "qa-reports", label: "Dietician Reports" },
      { id: "qa-alerts", label: "QA Alerts" }
    ]
  },
];

export default function Sidebar({ active, setActive }) {
  const [expandedId, setExpandedId] = useState(null);

  const handleItemClick = (item) => {
    if (item.children) {
      setExpandedId(expandedId === item.id ? null : item.id);
    }
    setActive(item.children ? item.children[0].id : item.id);
  };

  return (
    <div style={{
      width: 210,
      minWidth: 210,
      background: T.white,
      borderRight: `1px solid ${T.gray200}`,
      display: "flex",
      flexDirection: "column",
      height: "100vh",
      position: "sticky",
      top: 0,
    }}>
      {/* Brand */}
      <div style={{ padding: "24px 20px 16px" }}>
        <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "Georgia, serif", color: T.black, lineHeight: 1.2 }}>
          Clinical Provider<br />Management
        </div>
        <div style={{ fontSize: 10, color: T.gray400, marginTop: 4, letterSpacing: "0.08em", textTransform: "uppercase", fontFamily: "monospace" }}>
          Clinical Command
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: "8px 0", overflow: "auto" }}>
        {NAV_ITEMS.map(item => (
          <div key={item.id}>
            <div
              onClick={() => handleItemClick(item)}
              style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "9px 20px", cursor: "pointer",
                background: active === item.id || (item.children && expandedId === item.id) ? T.gray100 : "transparent",
                borderLeft: active === item.id || (item.children && expandedId === item.id) ? `3px solid ${T.black}` : "3px solid transparent",
                fontSize: 13,
                fontWeight: active === item.id || (item.children && expandedId === item.id) ? 600 : 400,
                color: active === item.id || (item.children && expandedId === item.id) ? T.black : T.gray500,
                userSelect: "none",
              }}
            >
              <span style={{ fontSize: 14 }}>{item.icon}</span>
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.children && <span style={{ fontSize: 10 }}>{expandedId === item.id ? "▾" : "▸"}</span>}
            </div>

            {item.children && expandedId === item.id && (
              item.children.map(child => (
                <div
                  key={child.id}
                  onClick={() => setActive(child.id)}
                  style={{
                    padding: "7px 20px 7px 44px",
                    fontSize: 12,
                    color: active === child.id ? T.black : T.gray500,
                    background: active === child.id ? T.gray50 : "transparent",
                    cursor: "pointer",
                    fontFamily: "monospace",
                    fontWeight: active === child.id ? 600 : 400,
                    borderLeft: active === child.id ? `2px solid ${T.black}` : "2px solid transparent",
                  }}
                >
                  {child.label}
                </div>
              ))
            )}
          </div>
        ))}
      </nav>

      {/* User */}
      <div style={{ padding: "16px 20px", borderTop: `1px solid ${T.gray200}`, display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{
          width: 32, height: 32, borderRadius: "50%",
          background: T.black, color: T.white,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 11, fontWeight: 700,
        }}>OL</div>
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, color: T.black }}>Operations Lead</div>
          <div style={{ fontSize: 10, color: T.gray400, fontFamily: "monospace" }}>ID: 808-XRAY</div>
        </div>
      </div>
    </div>
  );
}
