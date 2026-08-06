import { useState, useRef, useEffect } from "react";
import { T } from "../tokens";

/**
 * Call Quality Analysis
 * Displays production QA Portal with sidebar hidden
 */

export default function CallQualityAnalysis({ view = "dashboard" }) {
  const [selectedView, setSelectedView] = useState(view);
  const [showDropdown, setShowDropdown] = useState(false);
  const containerRef = useRef(null);
  const iframeRef = useRef(null);

  const qaViews = [
    { id: "dashboard", label: "Dashboard" },
    { id: "upload", label: "Call Upload" },
    { id: "transcriptions", label: "Transcriptions" },
    { id: "insights", label: "AI Insights" },
    { id: "reports", label: "Dietician Reports" },
    { id: "alerts", label: "QA Alerts" },
  ];

  const currentView = qaViews.find(v => v.id === selectedView || v.id === view);

  // Update view when prop changes
  useEffect(() => {
    setSelectedView(view);
  }, [view]);

  // Load QA Portal iframe with correct view
  useEffect(() => {
    if (!containerRef.current) return;

    containerRef.current.innerHTML = "";

    const wrapper = document.createElement("div");
    wrapper.style.cssText = `
      position: relative;
      width: 100%;
      height: 100%;
      overflow: hidden;
    `;

    const iframe = document.createElement("iframe");
    // QA Portal frontend is on Netlify
    const qaUrl = process.env.REACT_APP_QA_URL || process.env.REACT_APP_QA_PORTAL_URL || 'https://consultation-call-quality-analysis.netlify.app';
    const viewParam = view || selectedView || 'dashboard';
    const iframeUrl = `${qaUrl}/?view=${viewParam}`;

    console.log('[CallQualityAnalysis] Loading iframe URL:', iframeUrl);
    iframe.src = iframeUrl;
    iframe.style.cssText = `
      position: absolute;
      top: 0;
      left: -256px;
      width: calc(100% + 256px);
      height: 100%;
      border: none;
      background: white;
    `;
    iframe.allow = "microphone; camera; clipboard-read; clipboard-write";
    iframe.title = "QA Portal";

    iframeRef.current = iframe;
    wrapper.appendChild(iframe);
    containerRef.current.appendChild(wrapper);

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = "";
      }
    };
  }, [view, selectedView]);

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      height: "100%",
      background: T.offwhite
    }}>
      {/* Header with Dropdown */}
      <div style={{
        padding: "1.5rem",
        background: T.white,
        borderBottom: `1px solid ${T.gray200}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        zIndex: 100
      }}>
        <h1 style={{
          fontSize: "1.5rem",
          fontWeight: 700,
          color: T.black
        }}>
          Call Quality Analysis
        </h1>

        {/* Dropdown Menu */}
        <div style={{ position: "relative" }}>
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            style={{
              padding: "0.5rem 1rem",
              background: T.white,
              border: `1px solid ${T.gray300}`,
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: 500,
              fontSize: "0.95rem",
              color: T.black,
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              transition: "all 0.2s"
            }}
          >
            {currentView?.label}
            <span>{showDropdown ? "▾" : "▸"}</span>
          </button>

          {showDropdown && (
            <div style={{
              position: "absolute",
              top: "100%",
              right: 0,
              marginTop: "0.5rem",
              background: T.white,
              border: `1px solid ${T.gray300}`,
              borderRadius: "6px",
              boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
              minWidth: "200px"
            }}>
              {qaViews.map((v) => (
                <button
                  key={v.id}
                  onClick={() => {
                    setSelectedView(v.id);
                    setShowDropdown(false);
                  }}
                  style={{
                    width: "100%",
                    padding: "0.75rem 1rem",
                    border: "none",
                    background: (view || selectedView) === v.id ? T.gray100 : "transparent",
                    cursor: "pointer",
                    textAlign: "left",
                    fontSize: "0.95rem",
                    color: T.black,
                    fontWeight: (view || selectedView) === v.id ? 600 : 400,
                    borderLeft: (view || selectedView) === v.id ? `3px solid ${T.black}` : "3px solid transparent"
                  }}
                >
                  {v.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* QA Portal Iframe (sidebar hidden via CSS) */}
      <div
        ref={containerRef}
        style={{
          flex: 1,
          position: "relative",
          overflow: "hidden"
        }}
      />
    </div>
  );
}
