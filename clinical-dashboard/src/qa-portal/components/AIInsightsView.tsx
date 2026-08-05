import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  AlertTriangle,
  Info,
  Play,
  Pause,
  RotateCcw,
  Volume2,
  CheckCircle,
  TrendingUp,
  Lightbulb,
  FileText,
  Clock,
  ChevronRight,
  Share2,
  MessageSquare,
  ChevronDown
} from 'lucide-react';
import { Recording } from '../types';
import { fetchCallDetail } from '../hooks/useClinicalAPI';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface AIInsightsViewProps {
  completedRecordings: Recording[];
  selectedCallId: string | null;
  onSelectCallId: (id: string | null) => void;
}

export default function AIInsightsView({
  completedRecordings,
  selectedCallId,
  onSelectCallId
}: AIInsightsViewProps) {
  const callIdToLoad = selectedCallId || (completedRecordings.length > 0 ? completedRecordings[0].id : null);

  // Full detail (with transcript + insights) fetched from API
  const [detailCall, setDetailCall] = useState<Recording | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Audio playback
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioTime, setAudioTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(0);

  const [showSelector, setShowSelector] = useState<boolean>(false);

  // Fetch detail whenever selected call changes
  useEffect(() => {
    if (!callIdToLoad) return;
    setLoadingDetail(true);
    setIsPlaying(false);
    setAudioTime(0);
    fetchCallDetail(callIdToLoad).then(d => {
      setDetailCall(d);
      setLoadingDetail(false);
    });
  }, [callIdToLoad]);

  // Wire real audio element
  useEffect(() => {
    const url = detailCall?.recording_url;
    if (!url) return;
    if (!audioRef.current) audioRef.current = new Audio();
    const audio = audioRef.current;
    audio.src = url;
    const onTime = () => setAudioTime(Math.floor(audio.currentTime));
    const onDur = () => setAudioDuration(Math.floor(audio.duration) || 0);
    const onEnd = () => { setIsPlaying(false); setAudioTime(0); };
    audio.addEventListener('timeupdate', onTime);
    audio.addEventListener('loadedmetadata', onDur);
    audio.addEventListener('ended', onEnd);
    return () => {
      audio.pause();
      audio.removeEventListener('timeupdate', onTime);
      audio.removeEventListener('loadedmetadata', onDur);
      audio.removeEventListener('ended', onEnd);
    };
  }, [detailCall?.recording_url]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !detailCall?.recording_url) return;
    if (isPlaying) audio.play().catch(() => setIsPlaying(false));
    else audio.pause();
  }, [isPlaying, detailCall?.recording_url]);

  const activeCall = detailCall || completedRecordings.find(r => r.id === callIdToLoad);

  if (!activeCall) {
    return (
      <div className="flex-grow flex items-center justify-center text-center p-8 bg-surface">
        <div className="max-w-md">
          <AlertTriangle className="w-12 h-12 text-on-surface-variant/40 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-on-surface">No Call Selected for Analysis</h3>
          <p className="text-sm text-on-surface-variant mt-1">
            Analyze clinical recordings by visiting the Call Upload or Dashboard pages first.
          </p>
        </div>
      </div>
    );
  }

  const waveHeights = [30,50,80,60,100,40,70,50,90,30,50,80,40,60,50,70,40,20,50,30,60,50,80,40,70,50,90,40,60,45,80,30,70,55,95,30,40,60,20,10];
  const effectiveDuration = audioDuration || (activeCall ? parseInt(activeCall.duration?.split(':')[0] || '0') * 60 + parseInt(activeCall.duration?.split(':')[1] || '0') : 300);
  const fmtTime = (s: number) => `${Math.floor(s/60).toString().padStart(2,'0')}:${(s%60).toString().padStart(2,'0')}`;

  // Check if diabetes/specific conditions were actually mentioned in the call
  const transcriptText = (activeCall?.transcript || []).map(t => t.text).join(' ').toLowerCase();
  const diabetesMentioned = /diabet|sugar|insulin|glucose|hba1c/i.test(transcriptText);
  const conditionFilter = (text: string) => {
    if (!diabetesMentioned && /diabet/i.test(text)) return false;
    return true;
  };

  // Deduplicate and filter condition-specific inferences
  const uniqueWentWell = [...new Set(activeCall?.insights?.whatWentWell || [])].filter(conditionFilter);
  const uniqueImprovements = [...new Set(activeCall?.insights?.areasForImprovement || [])].filter(conditionFilter);
  const filteredAlerts = (activeCall?.qaAlerts || []).filter(a =>
    conditionFilter(a.title + ' ' + (a.description || ''))
  );

  return (
    <div className="flex-1 flex overflow-hidden h-full bg-[#F7F3F0] select-none">
      {/* Left side: Call Details & Timeline */}
      <div className="flex-1 flex flex-col border-r border-[#1A1A1A]/10 overflow-hidden h-full">
        
        {/* Audio Header */}
        <div className="p-6 bg-white border-b border-[#1A1A1A]/10 shrink-0">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-4">
            <div className="relative">
              {/* Call Selector Dropdown */}
              <button 
                onClick={() => setShowSelector(!showSelector)}
                className="flex items-center gap-2 text-left group cursor-pointer focus:outline-none"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] font-sans font-bold uppercase tracking-widest text-[#8B7E66] block">Active Analysis</span>
                    <ChevronDown className="w-4 h-4 text-[#8B7E66] group-hover:text-[#1A1A1A] transition-colors" />
                  </div>
                  <h2 className="text-xl font-serif italic font-medium text-[#1A1A1A] group-hover:text-[#8B7E66] transition-colors">
                    Consult ID: #{activeCall.id}
                  </h2>
                  <p className="text-xs font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1">
                    {activeCall.patientName}
                    {(activeCall as any).entities?.call_purpose
                      ? ` — ${(activeCall as any).entities.call_purpose}`
                      : ''} | Duration: {activeCall.duration}
                  </p>
                </div>
              </button>
 
              {showSelector && (
                <div className="absolute left-0 top-full mt-2 w-72 bg-white border border-[#1A1A1A]/10 rounded-none shadow-xl z-50 p-2 space-y-1">
                  <p className="text-[10px] font-sans font-bold text-[#1A1A1A]/40 uppercase tracking-[0.15em] px-3 py-2 border-b border-[#1A1A1A]/5 mb-1">
                    Switch Call Analysis
                  </p>
                  {completedRecordings.map((c) => (
                    <button
                      key={c.id}
                      onClick={() => {
                        onSelectCallId(c.id);
                        setShowSelector(false);
                        setIsPlaying(false);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-none text-xs font-sans uppercase tracking-wider flex items-center justify-between hover:bg-[#FAF8F6] transition-colors ${
                        c.id === activeCall.id ? 'bg-[#FAF8F6] text-[#8B7E66] font-bold' : 'text-[#1A1A1A]'
                      }`}
                    >
                      <span className="truncate max-w-[180px]">{c.patientName} Consult ({c.id})</span>
                      <span className={`font-mono text-[10px] font-bold ${c.sopCompliant ? 'text-emerald-700' : 'text-[#A34E36]'}`}>
                        {c.sopComplianceScore}%
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              {activeCall.sopCompliant ? (
                <span className="bg-emerald-50 border border-emerald-300 text-emerald-800 px-3 py-1 rounded-none text-[10px] font-sans font-bold uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                  SOP Compliant
                </span>
              ) : (
                <span className="bg-[#F9EAE6] text-[#A34E36] px-3 py-1 border border-[#A34E36]/30 rounded-none text-[10px] font-sans font-bold uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  SOP Alert
                </span>
              )}
              <span className="bg-[#FAF8F6] border border-[#1A1A1A]/10 text-[#1A1A1A]/60 px-3 py-1 rounded-none text-[10px] font-sans uppercase tracking-wider">
                {activeCall.date}
              </span>
            </div>
          </div>

          {/* Audio player */}
          <div className="bg-[#FAF8F6] rounded-none p-4 flex flex-col gap-3 border border-[#1A1A1A]/10">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setIsPlaying(p => !p)}
                className="w-10 h-10 bg-[#1A1A1A] text-white flex items-center justify-center hover:bg-[#8B7E66] active:scale-95 transition-all cursor-pointer shrink-0"
              >
                {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-0.5" />}
              </button>

              <div className="flex-1">
                {/* Waveform bars — highlight up to current play position */}
                <div className="flex items-end gap-[3px] h-10 mb-1 px-1">
                  {waveHeights.map((h, i) => {
                    const progress = effectiveDuration > 0 ? audioTime / effectiveDuration : 0;
                    const played = i / waveHeights.length < progress;
                    return (
                      <div key={i} className={`w-1 transition-all duration-150 ${played ? 'bg-[#8B7E66]' : 'bg-[#1A1A1A]/10'}`}
                        style={{ height: `${h}%` }} />
                    );
                  })}
                </div>
                {/* Seek bar */}
                <input type="range" min="0" max={effectiveDuration || 1} value={audioTime}
                  onChange={e => {
                    const t = parseInt(e.target.value);
                    setAudioTime(t);
                    if (audioRef.current) audioRef.current.currentTime = t;
                  }}
                  className="w-full h-1 bg-[#1A1A1A]/10 appearance-none cursor-pointer accent-[#8B7E66]"
                />
              </div>
              <span className="text-xs font-mono font-semibold text-[#1A1A1A]/60 shrink-0 select-none">
                {fmtTime(audioTime)} / {fmtTime(effectiveDuration)}
              </span>
            </div>
            {!detailCall?.recording_url && (
              <p className="text-[10px] text-[#1A1A1A]/40 font-sans uppercase tracking-wider">No audio URL available</p>
            )}
          </div>
        </div>

        {/* Transcript Panel Feed */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6 bg-[#FAF8F6]/20">
          {loadingDetail ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-8">
              <div className="w-8 h-8 border-2 border-[#8B7E66] border-t-transparent rounded-full animate-spin mb-3"></div>
              <p className="text-xs text-[#1A1A1A]/50 font-sans uppercase tracking-wider">Loading transcript...</p>
            </div>
          ) : activeCall.transcript.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-8">
              <FileText className="w-12 h-12 text-[#1A1A1A]/20 mb-3" />
              <h3 className="text-sm font-serif italic text-[#1A1A1A]">No Transcript Available</h3>
              <p className="text-xs text-[#1A1A1A]/50 mt-1 max-w-sm leading-relaxed font-sans uppercase tracking-wider">
                Transcription may still be processing. Refresh the page to check again.
              </p>
            </div>
          ) : (
            activeCall.transcript.map((turn) => {
              const isDietician = turn.speaker === 'agent' || turn.speaker === 'dietician';
              return (
                <div key={turn.id} className="flex gap-4">
                  {/* Speaker Badge */}
                  <div className="shrink-0 select-none">
                    <div className={`w-8 h-8 rounded-none font-mono font-bold text-[10px] flex items-center justify-center border ${
                      isDietician
                        ? 'bg-[#FAF8F6] text-[#1A1A1A] border-[#1A1A1A]/20'
                        : 'bg-[#1A1A1A] text-white border-[#1A1A1A]'
                    }`}>
                      {isDietician ? 'DT' : 'CU'}
                    </div>
                  </div>

                  <div className="flex-grow">
                    <div className="flex items-center gap-2 mb-1.5 text-[10px] font-sans font-bold uppercase tracking-wider">
                      <span className="text-[#1A1A1A]">{isDietician ? (activeCall.agentName || 'Dietician') : (activeCall.patientName || 'Customer')}</span>
                      <span className="text-[#1A1A1A]/40 font-mono text-[9px]">{turn.timestamp}</span>
                      {turn.sopGap && (
                        <span className="bg-[#F9EAE6] text-[#A34E36] px-2 py-0.5 border border-[#A34E36]/30 text-[9px] font-sans font-bold uppercase tracking-wider rounded-none">
                          SOP GAP
                        </span>
                      )}
                    </div>

                    {/* Speech block */}
                    {turn.sopGap ? (
                      <div className="p-4 bg-[#F9EAE6]/50 border border-[#A34E36]/30 rounded-none">
                        <p className="text-xs leading-relaxed text-[#1A1A1A] mb-3">{turn.text}</p>
                        {turn.aiCatch && (
                          <div className="bg-white p-3 rounded-none border border-[#A34E36]/30 flex items-start gap-2 text-[10px] font-sans font-bold uppercase tracking-wider text-[#A34E36]">
                            <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-[#A34E36]" />
                            <span>{turn.aiCatch}</span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className={`p-4 rounded-none border text-xs leading-relaxed ${
                        isDietician
                          ? 'bg-white border-[#1A1A1A]/10 text-[#1A1A1A]/80'
                          : 'bg-[#FAF8F6] border-[#1A1A1A]/10 text-[#1A1A1A]'
                      }`}>
                        <p>{turn.text}</p>
                        
                        {turn.warning && (
                          <div className="mt-2.5 p-2 bg-[#F9EAE6] border border-[#A34E36]/20 text-[#A34E36] rounded-none text-[10px] font-sans font-bold uppercase tracking-wider flex items-center gap-2">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            <span>{turn.warning}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right side: Insights Dashboard Panels */}
      <div className="w-[480px] bg-[#FAF8F6] border-l border-[#1A1A1A]/10 flex flex-col overflow-y-auto custom-scrollbar h-full">
        
        {/* Overall Score Card */}
        <section className="p-6 shrink-0 border-b border-[#1A1A1A]/10 bg-white">
          <div className="rounded-none p-2 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-6">
              <div>
                <span className="text-[9px] font-sans font-bold uppercase tracking-widest text-[#8B7E66] block">SOP Evaluation</span>
                <h3 className="text-xl font-serif italic font-medium text-[#1A1A1A] mt-0.5">Performance Score</h3>
                <p className="text-[10px] font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1">Overall weighted dietician score.</p>
              </div>
              
              {/* Score Circular gauge */}
              <div className="relative w-20 h-20 shrink-0">
                <svg className="w-20 h-20 -rotate-90">
                  <circle className="text-[#1A1A1A]/5" cx="40" cy="40" fill="transparent" r="34" stroke="currentColor" strokeWidth="4"></circle>
                  <circle 
                    className={activeCall.sopComplianceScore >= 90 ? 'text-emerald-700' : activeCall.sopComplianceScore >= 75 ? 'text-[#8B7E66]' : 'text-[#A34E36]'} 
                    cx="40" 
                    cy="40" 
                    fill="transparent" 
                    r="34" 
                    stroke="currentColor" 
                    strokeWidth="4"
                    strokeDasharray="213.6"
                    strokeDashoffset={213.6 - (213.6 * activeCall.sopComplianceScore) / 100}
                  ></circle>
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="font-mono font-bold text-lg text-[#1A1A1A]">{activeCall.sopComplianceScore}%</span>
                </div>
              </div>
            </div>

            {/* Score Sliders Breakdown */}
            <div className="space-y-4">
              {/* Stat 1 */}
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]">
                  <span>Greeting</span>
                  <span className="font-mono">{activeCall.scores.greeting}%</span>
                </div>
                <div className="h-1 bg-[#1A1A1A]/10 rounded-none overflow-hidden">
                  <div className="h-full bg-[#1A1A1A] rounded-none" style={{ width: `${activeCall.scores.greeting}%` }}></div>
                </div>
              </div>

              {/* Stat 2 */}
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]">
                  <span>Empathy & Listening</span>
                  <span className="font-mono">{activeCall.scores.empathy}%</span>
                </div>
                <div className="h-1 bg-[#1A1A1A]/10 rounded-none overflow-hidden">
                  <div className="h-full bg-[#8B7E66] rounded-none" style={{ width: `${activeCall.scores.empathy}%` }}></div>
                </div>
              </div>

              {/* Stat 3 */}
              <div className="space-y-1">
                <div className={`flex justify-between text-[10px] font-sans font-bold uppercase tracking-wider ${activeCall.scores.compliance < 70 ? 'text-[#A34E36]' : 'text-[#1A1A1A]'}`}>
                  <span>SOP Compliance</span>
                  <span className="font-mono">{activeCall.scores.compliance}%</span>
                </div>
                <div className="h-1 bg-[#1A1A1A]/10 rounded-none overflow-hidden">
                  <div className={`h-full rounded-none ${activeCall.scores.compliance < 70 ? 'bg-[#A34E36]' : 'bg-[#1A1A1A]'}`} style={{ width: `${activeCall.scores.compliance}%` }}></div>
                </div>
              </div>

              {/* Stat 4 */}
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]">
                  <span>Technical Accuracy</span>
                  <span className="font-mono">{activeCall.scores.technical}%</span>
                </div>
                <div className="h-1 bg-[#1A1A1A]/10 rounded-none overflow-hidden">
                  <div className="h-full bg-[#8B7E66] rounded-none" style={{ width: `${activeCall.scores.technical}%` }}></div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Critical QA Alerts — filtered, no diabetes inference without mention */}
        {filteredAlerts.filter(a => a.severity === 'critical').length > 0 && (
          <section className="p-6 shrink-0 bg-[#FAF8F6] border-b border-[#1A1A1A]/10">
            <div className="bg-[#F9EAE6] border border-[#A34E36]/30 rounded-none p-5">
              <div className="flex items-center gap-2 mb-4 text-[#A34E36]">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <h3 className="text-[10px] font-sans font-bold uppercase tracking-[0.15em]">
                  Critical QA Alerts ({filteredAlerts.filter(a => a.severity === 'critical').length})
                </h3>
              </div>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {filteredAlerts.filter(a => a.severity === 'critical').map((alert) => (
                  <div key={alert.id} className="bg-white p-4 rounded-none border border-[#A34E36]/20">
                    <p className="text-xs font-sans font-bold uppercase tracking-wider text-[#A34E36]">{alert.title}</p>
                    <p className="text-xs text-[#1A1A1A]/80 leading-relaxed mt-1.5 font-sans">{alert.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* AI Analytical Insights Panel */}
        <section className="p-6 space-y-6">
          {/* What went well */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-emerald-800">
              <CheckCircle className="w-4 h-4 shrink-0 text-emerald-600" />
              <h3 className="text-[10px] font-sans font-bold uppercase tracking-[0.15em]">What Went Well</h3>
            </div>
            {uniqueWentWell.length === 0 ? (
              <p className="text-xs text-[#1A1A1A]/40 italic font-sans">No positive observations recorded for this call.</p>
            ) : (
              <ul className="space-y-2">
                {uniqueWentWell.map((pt, idx) => (
                  <li key={idx} className="flex gap-2 text-xs text-[#1A1A1A]/70">
                    <span className="w-1.5 h-1.5 bg-emerald-600 mt-1.5 shrink-0"></span>
                    <p className="leading-relaxed text-sm text-[#1A1A1A]">{pt}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Areas for improvement */}
          <div className="space-y-3 pt-4 border-t border-[#1A1A1A]/5">
            <div className="flex items-center gap-2 text-[#8B7E66]">
              <Lightbulb className="w-4 h-4 shrink-0" />
              <h3 className="text-[10px] font-sans font-bold uppercase tracking-[0.15em]">Areas For Improvement</h3>
            </div>
            {uniqueImprovements.length === 0 ? (
              <p className="text-xs text-[#1A1A1A]/40 italic font-sans">No improvement areas identified.</p>
            ) : (
              <ul className="space-y-2">
                {uniqueImprovements.map((pt, idx) => (
                  <li key={idx} className="flex gap-2 text-xs text-[#1A1A1A]/70">
                    <span className="w-1.5 h-1.5 bg-[#8B7E66] mt-1.5 shrink-0"></span>
                    <p className="leading-relaxed text-sm text-[#1A1A1A]">{pt}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* AI Auto-Summary block */}
          {activeCall.insights.summary && (
            <div className="p-5 bg-white border border-[#1A1A1A]/10 rounded-none relative">
              <div className="absolute top-0 left-0 w-1 h-full bg-[#8B7E66]"></div>
              <div className="flex items-center gap-2 mb-2.5">
                <Sparkles className="w-4 h-4 text-[#8B7E66]" />
                <span className="text-[9px] font-sans font-bold uppercase tracking-[0.15em] text-[#8B7E66]">AI Summary</span>
              </div>
              <p className="text-xs font-serif leading-relaxed italic text-[#1A1A1A]/80">
                {/* Replace Diabetes-specific labels if diabetes not mentioned in the call */}
                {diabetesMentioned
                  ? activeCall.insights.summary
                  : activeCall.insights.summary
                      .replace(/diabetes management/gi, 'health consultation')
                      .replace(/diabetes/gi, 'health')
                      .replace(/diabetic/gi, 'patient')
                      .replace(/for \w+ management/gi, 'follow-up consultation')
                }
              </p>
            </div>
          )}
        </section>
      </div>

      {/* Floating Actions button list */}
      <div className="fixed bottom-6 right-6 flex flex-col gap-2.5 z-50">
        <button className="w-10 h-10 bg-[#1A1A1A] text-white flex items-center justify-center hover:bg-[#8B7E66] transition-colors shadow-lg cursor-pointer rounded-none">
          <MessageSquare className="w-4 h-4" />
        </button>
        <button className="w-10 h-10 bg-white border border-[#1A1A1A]/20 text-[#1A1A1A] flex items-center justify-center hover:bg-[#FAF8F6] transition-colors shadow-lg cursor-pointer rounded-none">
          <Share2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
