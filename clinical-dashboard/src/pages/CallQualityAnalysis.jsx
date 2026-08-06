import React, { useState, useEffect } from 'react';
import QAPortalApp from '../qa-portal/App.tsx';

export default function CallQualityAnalysis({ view = "dashboard" }) {
  const [viewProp, setViewProp] = useState(view);

  useEffect(() => {
    setViewProp(view);
  }, [view]);

  // Pass view as a prop by simulating window.location.search
  // This makes the QA Portal App read the view parameter correctly
  useEffect(() => {
    const originalSearch = window.location.search;
    Object.defineProperty(window.location, 'search', {
      value: `?view=${viewProp}`,
      writable: true,
      configurable: true
    });

    return () => {
      Object.defineProperty(window.location, 'search', {
        value: originalSearch,
        writable: true,
        configurable: true
      });
    };
  }, [viewProp]);

  return <QAPortalApp />;
}
