import { useState } from "react";
import { T } from "./tokens";
import Sidebar from "./components/Sidebar";
import ProfilePanel from "./components/ProfilePanel";
import OverviewPage from "./pages/Overview";
import ClinicalOutcomesPage from "./pages/ClinicalOutcomes";
import UtilizationPage from "./pages/Utilization";
import RecommendationsPage from "./pages/Recommendations";
import CallQualityAnalysis from "./pages/CallQualityAnalysis";

export default function App() {
  const [active, setActive] = useState("overview");
  const [profileOpen, setProfileOpen] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState(null);
  // ⚠️ SHARED STATE: All pages use these dates
  // Overview/Utilization: July full month (2026-07-01 to 2026-07-28)
  // Clinical Outcomes: 1-year range (2025-07-27 to 2026-07-27) - will be overridden in that tab
  const [startDate, setStartDate] = useState("2026-07-01");
  const [endDate, setEndDate] = useState("2026-07-28");

  const openProfile = (name) => {
    setSelectedProvider(name);
    setProfileOpen(true);
  };

  const renderPage = () => {
    switch (active) {
      case "overview":          return <OverviewPage setPage={openProfile} setSelectedProvider={openProfile} startDate={startDate} endDate={endDate} setStartDate={setStartDate} setEndDate={setEndDate} />;
      case "clinical-outcomes": return <ClinicalOutcomesPage startDate={startDate} endDate={endDate} setStartDate={setStartDate} setEndDate={setEndDate} />;
      case "utilization":       return <UtilizationPage startDate={startDate} endDate={endDate} setStartDate={setStartDate} setEndDate={setEndDate} />;
      case "recommendations":   return <RecommendationsPage startDate={null} endDate={null} setStartDate={setStartDate} setEndDate={setEndDate} />;
      case "call-quality":      return <CallQualityAnalysis view="dashboard" />;
      case "qa-dashboard":      return <CallQualityAnalysis view="dashboard" />;
      case "qa-upload":         return <CallQualityAnalysis view="upload" />;
      case "qa-transcriptions": return <CallQualityAnalysis view="transcriptions" />;
      case "qa-insights":       return <CallQualityAnalysis view="insights" />;
      case "qa-reports":        return <CallQualityAnalysis view="reports" />;
      case "qa-alerts":         return <CallQualityAnalysis view="alerts" />;
      default:                  return <OverviewPage setPage={openProfile} setSelectedProvider={openProfile} startDate={startDate} endDate={endDate} setStartDate={setStartDate} setEndDate={setEndDate} />;
    }
  };

  return (
    <div style={{
      display: "flex",
      height: "100vh",
      fontFamily: "system-ui, -apple-system, sans-serif",
      background: T.offwhite,
      color: T.black,
      overflow: "hidden",
    }}>
      <Sidebar
        active={active}
        setActive={setActive}
      />

      <div style={{ flex: 1, overflow: "auto", display: "flex", flexDirection: "column" }}>
        {renderPage()}
      </div>

      {profileOpen && selectedProvider && (
        <ProfilePanel
          name={selectedProvider}
          onClose={() => { setProfileOpen(false); setSelectedProvider(null); }}
        />
      )}
    </div>
  );
}
