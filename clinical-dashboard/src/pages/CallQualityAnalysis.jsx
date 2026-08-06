import { useRef, useEffect } from "react";

export default function CallQualityAnalysis({ view = "dashboard" }) {
  const containerRef = useRef(null);
  const iframeRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

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
    iframe.src = qaUrl;

    iframeRef.current = iframe;
    wrapper.appendChild(iframe);
    containerRef.current.appendChild(wrapper);

    // Send postMessage to iframe when view changes
    const sendViewMessage = () => {
      if (iframeRef.current && iframeRef.current.contentWindow) {
        iframeRef.current.contentWindow.postMessage(
          { type: 'CHANGE_VIEW', view: view },
          '*'
        );
      }
    };

    // Wait for iframe to load, then send message
    iframe.onload = () => {
      setTimeout(sendViewMessage, 500);
    };

    // Also send message if iframe is already loaded
    setTimeout(sendViewMessage, 1000);

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
