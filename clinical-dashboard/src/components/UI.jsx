import { T } from "../tokens";

export const Badge = ({ variant = "default", children }) => {
  const styles = {
    critical:    { background: T.redLight,     color: T.red,    border: `1px solid ${T.red}` },
    high:        { background: T.black,         color: T.white,  border: `1px solid ${T.black}` },
    optimal:     { background: "transparent",   color: T.gray700,border: `1px solid ${T.gray300}` },
    stable:      { background: "transparent",   color: T.gray700,border: `1px solid ${T.gray300}` },
    default:     { background: T.gray100,       color: T.gray700,border: `1px solid ${T.gray200}` },
    "ai-enabled":{ background: T.black,         color: T.white,  border: "none" },
    core:        { background: "transparent",   color: T.gray700,border: `1px solid ${T.gray300}` },
    support:     { background: "transparent",   color: T.gray700,border: `1px solid ${T.gray300}` },
    external:    { background: "transparent",   color: T.gray500,border: `1px solid ${T.gray300}` },
    verified:    { background: T.greenLight,    color: T.green,  border: `1px solid ${T.green}` },
    breach:      { background: T.redLight,      color: T.red,    border: `1px solid ${T.red}` },
    flagged:     { background: T.orangeLight,   color: T.orange, border: `1px solid ${T.orange}` },
  };
  const s = styles[variant] || styles.default;
  return (
    <span style={{
      ...s,
      padding: "2px 8px",
      fontSize: 10,
      fontWeight: 700,
      letterSpacing: "0.08em",
      textTransform: "uppercase",
      fontFamily: "monospace",
      display: "inline-block",
    }}>
      {children}
    </span>
  );
};

export const MetricCard = ({ label, value, sub, subColor, icon, highlight }) => (
  <div style={{
    border: `1px solid ${highlight ? T.black : T.gray200}`,
    padding: "20px 24px",
    background: T.white,
    flex: 1,
    minWidth: 0,
  }}>
    <div style={{
      fontSize: 10, letterSpacing: "0.1em", color: T.gray500,
      textTransform: "uppercase", fontFamily: "monospace",
      marginBottom: 12, display: "flex", justifyContent: "space-between",
    }}>
      {label}
      {icon && <span style={{ color: T.gray400 }}>{icon}</span>}
    </div>
    <div style={{ fontSize: 36, fontWeight: 700, fontFamily: "Georgia, serif", color: T.black, lineHeight: 1 }}>
      {value}
    </div>
    {sub && (
      <div style={{ fontSize: 11, marginTop: 8, color: subColor || T.gray500, fontFamily: "monospace" }}>
        {sub}
      </div>
    )}
  </div>
);

export const UtilBar = ({ pct, color }) => {
  const c = pct > 100 ? T.red : pct > 90 ? T.black : T.gray300;
  return (
    <div style={{ height: 3, background: T.gray100, marginTop: 8 }}>
      <div style={{ height: 3, width: `${Math.min(pct, 100)}%`, background: color || c }} />
    </div>
  );
};

export const Header = ({
  title,
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  onExport,
  lastSynced = "14:02 GMT"
}) => (
  <div style={{
    display: "flex", alignItems: "center", gap: 12,
    padding: "14px 28px",
    borderBottom: `1px solid ${T.gray200}`,
    background: T.white,
    position: "sticky", top: 0, zIndex: 10,
    flexWrap: "wrap",
  }}>
    <div style={{ fontSize: 22, fontWeight: 700, fontFamily: "Georgia, serif", flex: 1 }}>{title}</div>

    {/* Date Range Inputs */}
    {startDate && endDate && (
      <>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <label style={{ fontSize: 10, fontFamily: "monospace", fontWeight: 700, color: T.gray500, textTransform: "uppercase" }}>FROM</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => onStartDateChange(e.target.value)}
            style={{
              padding: "6px 10px",
              border: `1px solid ${T.gray200}`,
              fontSize: 11,
              fontFamily: "monospace",
              background: T.white,
              borderRadius: 3,
            }}
          />
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <label style={{ fontSize: 10, fontFamily: "monospace", fontWeight: 700, color: T.gray500, textTransform: "uppercase" }}>TO</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => onEndDateChange(e.target.value)}
            style={{
              padding: "6px 10px",
              border: `1px solid ${T.gray200}`,
              fontSize: 11,
              fontFamily: "monospace",
              background: T.white,
              borderRadius: 3,
            }}
          />
        </div>
      </>
    )}

    {/* Export Button */}
    {onExport && (
      <button
        onClick={onExport}
        style={{
          background: T.black,
          color: T.white,
          border: "none",
          padding: "7px 14px",
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: "0.05em",
          textTransform: "uppercase",
          cursor: "pointer",
          fontFamily: "monospace",
          borderRadius: 3,
        }}
      >
        📥 Export CSV
      </button>
    )}

    {/* Info Section */}
    <div style={{ display: "flex", gap: 12, alignItems: "center", marginLeft: "auto" }}>
      <div style={{ fontSize: 10, color: T.gray400, fontFamily: "monospace" }}>LAST SYNCED: {lastSynced}</div>
      <span style={{ fontSize: 18, color: T.gray400, cursor: "pointer" }}>🔔</span>
      <span style={{ fontSize: 18, color: T.gray400, cursor: "pointer" }}>👤</span>
    </div>
  </div>
);
