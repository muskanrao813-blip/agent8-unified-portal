import { T } from "../tokens";

/**
 * Dietician QA Portal - Full Embedded
 * Runs the complete production QA Portal with all features:
 * - Dashboard: Call quality scores and metrics
 * - Upload: Excel file upload for batch processing
 * - Transcriptions: View call transcripts with Claude reconstruction
 * - AI Insights: Automated analysis and recommendations
 * - Dietician Reports: Provider performance analytics
 * - QA Alerts: Quality alerts and flags
 */

export default function CallQualityContainer() {
  // Embed the local QA Portal running on port 3001
  // This is the EXACT same UI/functionality as production
  return (
    <div style={{
      width: "100%",
      height: "100%",
      display: "flex",
      flexDirection: "column"
    }}>
      <iframe
        src="http://localhost:3001/"
        style={{
          width: "100%",
          height: "100%",
          border: "none",
          background: T.white,
          flex: 1
        }}
        title="Dietician Call Quality Analysis Portal"
        allow="microphone; camera; clipboard-read; clipboard-write"
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals allow-presentation"
      />
    </div>
  );
}
