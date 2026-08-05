import { useRef, useEffect } from "react";

/**
 * QA Portal View Wrapper
 * Displays QA Portal content WITHOUT sidebar
 * Creates fresh iframe for each view to ensure proper state
 */

export default function QAViewWrapper({ view }) {
  const containerRef = useRef(null);

  const qaView = view || "dashboard";

  useEffect(() => {
    if (!containerRef.current) return;

    // Create a unique key to force iframe recreation
    const iframeKey = `qa-iframe-${qaView}`;

    // Clear previous iframe
    containerRef.current.innerHTML = "";

    // Create new iframe
    const iframeContainer = document.createElement("div");
    iframeContainer.style.cssText = `
      position: relative;
      width: 100%;
      height: 100%;
      overflow: hidden;
    `;

    const iframe = document.createElement("iframe");
    iframe.key = iframeKey;
    iframe.src = `http://localhost:3001/?view=${qaView}`;
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
    iframe.title = `QA Portal - ${qaView}`;

    iframeContainer.appendChild(iframe);
    containerRef.current.appendChild(iframeContainer);

    // Hide sidebar and inject view changer after iframe loads
    const hideSidebar = () => {
      try {
        const doc = iframe.contentDocument;
        if (doc && doc.head) {
          // Hide sidebar via CSS
          const style = doc.createElement("style");
          style.textContent = `
            aside { display: none !important; }
            .w-64 { display: none !important; }
            [class*="sidebar"] { display: none !important; }
          `;
          doc.head.appendChild(style);

          // Inject JavaScript to change React state
          // The QA Portal's App.tsx has currentView state
          const script = doc.createElement("script");
          script.textContent = `
            // Try to find and click the menu item corresponding to the view
            const viewMap = {
              'dashboard': 'dashboard',
              'upload': 'upload',
              'transcriptions': 'transcriptions',
              'insights': 'insights',
              'reports': 'reports',
              'alerts': 'alerts'
            };
            const targetView = '${qaView}';
            const buttons = document.querySelectorAll('button');
            for (let btn of buttons) {
              const text = btn.textContent.toLowerCase();
              if (
                (targetView === 'dashboard' && text.includes('dashboard')) ||
                (targetView === 'upload' && (text.includes('upload') || text.includes('call'))) ||
                (targetView === 'transcriptions' && text.includes('transcription')) ||
                (targetView === 'insights' && text.includes('insight')) ||
                (targetView === 'reports' && text.includes('report')) ||
                (targetView === 'alerts' && text.includes('alert'))
              ) {
                btn.click();
                break;
              }
            }
          `;
          doc.body.appendChild(script);
        }
      } catch (e) {
        console.log("Cannot inject into iframe:", e.message);
      }
    };

    iframe.addEventListener("load", hideSidebar);

    // Try after a delay to ensure DOM is ready
    setTimeout(hideSidebar, 500);

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = "";
      }
    };
  }, [qaView]);

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        height: "100%",
        position: "relative",
        overflow: "hidden",
        flex: 1
      }}
    />
  );
}
