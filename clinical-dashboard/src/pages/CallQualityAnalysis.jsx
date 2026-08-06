import { useRef, useEffect } from "react";

export default function CallQualityAnalysis({ view = "dashboard" }) {
  const containerRef = useRef(null);
  const iframeRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Clear previous content
    if (iframeRef.current) {
      iframeRef.current.remove();
    }
    containerRef.current.innerHTML = "";

    const wrapper = document.createElement("div");
    wrapper.style.cssText = `
      position: relative;
      width: 100%;
      height: 100%;
      overflow: hidden;
    `;

    const iframe = document.createElement("iframe");
    let qaUrl = process.env.REACT_APP_QA_URL || 'https://consultation-call-quality-analysis.netlify.app';
    qaUrl = qaUrl.replace(/\/$/, '');

    // Update URL with view parameter each time
    const iframeUrl = `${qaUrl}/?view=${view}`;

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
