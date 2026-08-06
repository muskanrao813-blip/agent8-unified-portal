import { useRef, useEffect } from "react";

export default function CallQualityAnalysis({ view = "dashboard" }) {
  const containerRef = useRef(null);
  const iframeRef = useRef(null);

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
    const viewParam = view || 'dashboard';
    const timestamp = Date.now();
    const iframeUrl = `${qaUrl}/?view=${viewParam}&t=${timestamp}`;

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
