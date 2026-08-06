import QAPortalIntegrated from './QAPortalIntegrated';

export default function CallQualityAnalysis({ view = "dashboard" }) {
  return <QAPortalIntegrated view={view} />;
}
