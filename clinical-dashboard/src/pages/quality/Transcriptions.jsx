import { useState, useEffect } from "react";

export default function Transcriptions() {
  const [transcripts, setTranscripts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    const fetchTranscripts = async () => {
      setLoading(true);
      try {
        const response = await fetch("/api/qa/calls");
        const data = await response.json();
        setTranscripts(data.filter(c => c.reconstructed_transcript) || []);
      } catch (error) {
        console.error("Failed to fetch transcripts:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchTranscripts();
  }, []);

  const selectedTranscript = transcripts.find(t => t.id === selectedId);

  return (
    <div style={{ flex: 1, overflow: "auto", background: "#f8fafc", padding: "2.5rem 1.5rem" }}>
      <style>{`
        .qa-container { max-width: 1400px; margin: 0 auto; }
        .qa-section {
          background: white;
          border-radius: 12px;
          padding: 2rem;
          margin-bottom: 2rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        }
        .qa-section-title {
          font-size: 1.2rem;
          font-weight: 700;
          color: #1e293b;
          margin-bottom: 1.5rem;
          padding-bottom: 1rem;
          border-bottom: 3px solid #3b82f6;
          display: flex;
          align-items: center;
          gap: 0.8rem;
        }
        .qa-list {
          background: white;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
          max-height: 600px;
          overflow-y: auto;
        }
        .qa-list-item {
          padding: 12px 16px;
          border-bottom: 1px solid #e2e8f0;
          cursor: pointer;
          transition: all 0.2s;
        }
        .qa-list-item:hover {
          background: #f8fafc;
        }
        .qa-list-item.active {
          background: #f0f4f8;
          border-left: 3px solid #3b82f6;
        }
        .qa-list-item-name {
          font-size: 11px;
          font-weight: 600;
          color: #1e293b;
        }
        .qa-list-item-meta {
          font-size: 9px;
          color: #94a3b8;
          margin-top: 2px;
        }
        .qa-transcript-box {
          background: #f8fafc;
          border-radius: 8px;
          padding: 1rem;
          max-height: 400px;
          overflow-y: auto;
          border: 1px solid #e2e8f0;
        }
      `}</style>

      <div className="qa-container">
        {/* Header */}
        <div style={{ marginBottom: "2rem" }}>
          <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.5rem" }}>
            💬 Transcriptions
          </div>
          <div style={{ fontSize: "1rem", color: "#64748b" }}>
            Call transcripts and intelligent reconstruction
          </div>
        </div>

        {/* Two Column Layout */}
        <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "2rem", maxHeight: "calc(100vh - 200px)" }}>
          {/* List */}
          <div>
            <div className="qa-section" style={{ padding: "0" }}>
              <div style={{ padding: "1rem", fontSize: "0.85rem", color: "#64748b", fontWeight: 600, background: "#f0f4f8", borderBottom: "1px solid #e2e8f0" }}>
                📋 TRANSCRIPTS ({transcripts.length})
              </div>
              <div className="qa-list">
                {transcripts.length > 0 ? (
                  transcripts.map(t => (
                    <div
                      key={t.id}
                      className={`qa-list-item ${selectedId === t.id ? "active" : ""}`}
                      onClick={() => setSelectedId(t.id)}
                    >
                      <div className="qa-list-item-name">{t.patient_name}</div>
                      <div className="qa-list-item-meta">{t.dietician_name}</div>
                    </div>
                  ))
                ) : (
                  <div style={{ padding: "1.5rem", color: "#94a3b8", textAlign: "center", fontSize: "0.9rem" }}>
                    No transcripts available
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Detail View */}
          <div>
            {selectedTranscript ? (
              <div>
                {/* Header */}
                <div className="qa-section">
                  <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.5rem" }}>
                    {selectedTranscript.patient_name}
                  </div>
                  <div style={{ fontSize: "0.9rem", color: "#64748b" }}>
                    Dietician: {selectedTranscript.dietician_name}
                  </div>
                </div>

                {/* Transcript */}
                <div className="qa-section">
                  <div className="qa-section-title">
                    <i>📝</i> Intelligent Reconstruction
                  </div>
                  <div className="qa-transcript-box" style={{ fontSize: "0.9rem", lineHeight: "1.6", color: "#475569", fontFamily: "monospace" }}>
                    {selectedTranscript.reconstructed_transcript || "No transcript available"}
                  </div>
                </div>

                {/* Entities */}
                {selectedTranscript.entities && (
                  <div className="qa-section">
                    <div className="qa-section-title">
                      <i>🏷️</i> Extracted Entities
                    </div>
                    <div className="qa-transcript-box" style={{ fontSize: "0.85rem" }}>
                      <pre style={{ margin: 0, overflow: "auto", color: "#475569" }}>
                        {JSON.stringify(selectedTranscript.entities, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="qa-section" style={{ textAlign: "center", padding: "4rem 2rem", color: "#94a3b8" }}>
                <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>👈</div>
                Select a transcript to view details
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
