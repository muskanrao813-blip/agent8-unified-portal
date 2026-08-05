import { useState, useEffect } from 'react';
import { Recording } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useClinicalAPI() {
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecordings = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`${API_BASE_URL}/api/calls`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        // Transform backend response to match frontend Recording type
        const transformed = (Array.isArray(data) ? data : [data]).map((call: any) => ({
          id: call.id,
          name: call.appointment_id || `Call ${call.id.substring(0, 8)}`,
          patientName: call.patient_name || 'Unknown Patient',
          agentName: call.dietician_name || 'Unknown Dietician',
          duration: call.call_duration_seconds
            ? `${Math.floor(call.call_duration_seconds / 60)}:${String(call.call_duration_seconds % 60).padStart(2, '0')}`
            : '0:00',
          date: call.call_datetime
            ? new Date(call.call_datetime).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
            : new Date().toLocaleDateString(),
          status: call.status || 'processing',
          progress: call.status === 'completed' ? 100 : 50,
          statusText: call.status === 'completed' ? 'Ready for review' : 'Processing',
          sopCompliant: (call.overall_weighted_score || 0) >= 60,
          sopComplianceScore: call.overall_weighted_score || 0,
          scores: call.scores || { greeting: 0, empathy: 0, compliance: 0, technical: 0 },
          qaAlerts: call.qaAlerts || [],
          transcript: [],
          insights: { whatWentWell: [], areasForImprovement: [], summary: '' }
        }));
        setRecordings(transformed);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        console.error('Failed to fetch recordings:', err);
        // Fallback to empty array instead of crashing
        setRecordings([]);
      } finally {
        setLoading(false);
      }
    };

    fetchRecordings();

    // Poll every 2 seconds for real-time processing updates
    const interval = setInterval(fetchRecordings, 2000);
    return () => clearInterval(interval);
  }, []);

  return { recordings, loading, error };
}

export async function fetchCallDetail(callId: string): Promise<Recording | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/calls/${callId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch call: ${response.status}`);
    }

    const data = await response.json();

    // Build transcript turns from diarized_lines (Gemini speaker-labelled output)
    const buildTranscriptTurns = (data: any) => {
      const diarizedLines: any[] = data.transcript?.diarized_lines || data.transcript?.segments || [];

      if (diarizedLines.length > 0) {
        return diarizedLines.map((seg: any, idx: number) => {
          const speakerRaw = seg.speaker || 'unknown';
          const isAgent = speakerRaw === 'dietician' || speakerRaw === 'agent';
          const speakerLabel: 'agent' | 'patient' = isAgent ? 'agent' : 'patient';
          const speakerName = isAgent
            ? (data.dietician_name || 'Dietician')
            : (data.patient_name || 'Customer');

          const text: string = seg.text || '';
          // Detect SOP issues in text
          const sopGap = /no health|koi problem nahi|sab theek/i.test(text) === false &&
                         /health assessment|medical history|allergy|condition/i.test(text);
          const isCritical = /guidelines|advice|recommendation|follow.?up/i.test(text);

          return {
            id: `t-${idx}`,
            speaker: speakerLabel,
            speakerName,
            timestamp: `${Math.floor((seg.start_s || idx * 5) / 60)}:${String(Math.floor((seg.start_s || idx * 5) % 60)).padStart(2, '0')}`,
            text,
            tags: speakerRaw === 'dietician' ? ['Dietician'] : ['Customer'],
            isCritical,
            sopGap: false,
          };
        });
      }

      // Fallback: full Gemini text as one block
      const fullText = data.transcript?.text || data.reconstructed_transcript || data.raw_transcript || '';
      if (fullText) {
        return [{
          id: 't-0',
          speaker: 'agent' as const,
          speakerName: 'Gemini Transcription',
          timestamp: '0:00',
          text: fullText,
          tags: ['Gemini'],
        }];
      }
      return [];
    };

    // Transform backend detailed response to Recording type
    return {
      id: data.id,
      name: data.appointment_id || `Call ${data.id.substring(0, 8)}`,
      patientName: data.patient_name || 'Unknown Patient',
      agentName: data.dietician_name || 'Unknown Dietician',
      duration: data.call_duration_seconds
        ? `${Math.floor(data.call_duration_seconds / 60)}:${String(data.call_duration_seconds % 60).padStart(2, '0')}`
        : '0:00',
      date: data.call_datetime
        ? new Date(data.call_datetime).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
        : new Date().toLocaleDateString(),
      status: data.status || 'completed',
      progress: 100,
      statusText: 'Ready for review',
      sopCompliant: (data.overall_weighted_score || 0) >= 70,
      sopComplianceScore: data.overall_weighted_score || 0,
      scores: data.scores || { greeting: 0, empathy: 0, compliance: 0, technical: 0 },
      qaAlerts: data.qaAlerts || data.qa_flags?.map((f: any) => ({
        id: f.flag_type,
        title: f.flag_type?.replace(/_/g, ' ') || '',
        description: f.detail || '',
        severity: f.triggered ? 'critical' : 'info',
        status: f.triggered ? 'active' : 'resolved',
        recordingId: data.id,
        recordingName: data.appointment_id || `Call ${data.id?.substring(0, 8)}`,
        dieticianName: data.dietician_name || 'Unknown',
      })) || [],
      transcript: buildTranscriptTurns(data),
      recording_url: data.recording_url,
      entities: data.entities || {},
      insights: {
        whatWentWell: data.insights?.whatWentWell || [],
        areasForImprovement: data.insights?.areasForImprovement || [],
        summary: data.insights?.summary || data.feedback_notes?.bullets?.[0] || '',
      },
    };
  } catch (err) {
    console.error('Failed to fetch call detail:', err);
    return null;
  }
}

export async function fetchDashboardStats() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/clinical/dashboard/stats`);
    if (!response.ok) throw new Error(`Failed to fetch stats: ${response.status}`);
    return await response.json();
  } catch (err) {
    console.error('Failed to fetch dashboard stats:', err);
    return null;
  }
}

export async function fetchDieticianReports(): Promise<{ dieticians: any[]; trainingGaps: any[] }> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/dieticians`);
    if (!response.ok) throw new Error(`Failed to fetch dieticians: ${response.status}`);
    const data: any[] = await response.json();

    // Attach qaAlerts to each dietician object so DieticianReportsView can use them
    const dieticians = data.map((d: any) => ({
      ...d.dietician,
      qaAlerts: d.qaAlerts || [],
    }));

    // Deduplicate training gaps by title
    const seen = new Set<string>();
    const trainingGaps: any[] = [];
    for (const d of data) {
      for (const gap of d.trainingGaps || []) {
        if (!seen.has(gap.title)) {
          seen.add(gap.title);
          trainingGaps.push({ ...gap, id: gap.title });
        }
      }
    }
    return { dieticians, trainingGaps };
  } catch (err) {
    console.error('Failed to fetch dietician reports:', err);
    return { dieticians: [], trainingGaps: [] };
  }
}
