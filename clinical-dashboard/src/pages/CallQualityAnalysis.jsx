import { useRef, useEffect } from "react";

export default function CallQualityAnalysis({ view = "dashboard" }) {
  const containerRef = useRef(null);
  const iframeRef = useRef(null);

  console.log('[CallQualityAnalysis] Component rendered with view:', view);

  // Load QA Portal iframe with correct view
  useEffect(() => {
    console.log('[CallQualityAnalysis] useEffect triggered with view:', view);
    if (!containerRef.current) return;

    // Clear previous iframe completely
    if (iframeRef.current) {
      iframeRef.current.remove();
      iframeRef.current = null;
    }
    containerRef.current.innerHTML = "";

    // Create new wrapper
    const wrapper = document.createElement("div");
    wrapper.style.cssText = `
      position: relative;
      width: 100%;
      height: 100%;
      overflow: hidden;
    `;

    // Create fresh iframe
    const iframe = document.createElement("iframe");
    let qaUrl = process.env.REACT_APP_QA_URL || process.env.REACT_APP_QA_PORTAL_URL || 'https://consultation-call-quality-analysis.netlify.app';
    qaUrl = qaUrl.replace(/\/$/, '');
    const viewParam = view || 'dashboard';
    const timestamp = Date.now();
    const iframeUrl = `${qaUrl}/?view=${viewParam}&t=${timestamp}`;

    console.log('[CallQualityAnalysis] Loading iframe with view=' + viewParam + ' URL:', iframeUrl);

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
    iframe.src = iframeUrl;

    iframeRef.current = iframe;
    wrapper.appendChild(iframe);
    containerRef.current.appendChild(wrapper);

    return () => {
      if (iframeRef.current) {
        iframeRef.current.remove();
      }
    };
  }, [view]);

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        height: "100%",
        position: "relative",
        overflow: "hidden",
        background: "white"
      }}
    />
  );
}
