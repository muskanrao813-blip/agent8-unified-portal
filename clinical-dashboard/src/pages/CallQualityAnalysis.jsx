import { useEffect } from 'react';

export default function CallQualityAnalysis({ view = "dashboard" }) {
  useEffect(() => {
    // When view prop changes, update iframe URL with hash
    const iframe = document.querySelector('iframe');
    if (iframe) {
      // The Netlify app uses hash-based routing, so update the hash
      iframe.src = `https://consultation-call-quality-analysis.netlify.app/#/${view}`;
    }
  }, [view]);

  return (
    <iframe
      src="https://consultation-call-quality-analysis.netlify.app"
      style={{
        width: '100%',
        height: '100%',
        border: 'none',
        borderRadius: '0'
      }}
      title="QA Portal"
      allow="microphone; camera; clipboard-read; clipboard-write"
    />
  );
}
