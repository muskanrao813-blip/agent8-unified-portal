import React, { useState, useEffect, useRef } from 'react';
import {
  FileText,
  Search,
  Filter,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  Clock,
  ChevronRight,
  Sparkles,
  ArrowLeft,
  Play,
  Pause,
  RotateCcw,
  Volume2,
  Volume1,
  VolumeX,
  Download,
  Info,
  Lightbulb,
  CheckCircle2,
  ListFilter
} from 'lucide-react';
import { Recording } from '../types';
import { fetchCallDetail } from '../hooks/useClinicalAPI';

interface TranscriptionsViewProps {
  recordings: Recording[];
  onSelectCall: (id: string) => void;
  searchQuery: string;
}

export default function TranscriptionsView({
  recordings,
  onSelectCall,
  searchQuery
}: TranscriptionsViewProps) {
  const [complianceFilter, setComplianceFilter] = useState<string>('all');
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [volume, setVolume] = useState<number>(80);
  const [audioDuration, setAudioDuration] = useState<number>(0);

  // Real audio element ref
  const audioRef = useRef<HTMLAudioElement | null>(null);
  // Fallback timer reference (used only when no audio URL)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Find selected recording from list
  const listCall = recordings.find(r => r && r.id === selectedCallId);

  // Fetch detailed call data when a call is selected
  const [activeCall, setActiveCall] = useState<Recording | null>(null);

  useEffect(() => {
    if (selectedCallId) {
      fetchCallDetail(selectedCallId).then(detail => {
        if (detail) {
          setActiveCall(detail);
        }
      });
    } else {
      setActiveCall(null);
    }
  }, [selectedCallId]);

  // Guard against empty recordings
  if (!recordings || recordings.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#F7F3F0]">
        <div className="text-center">
          <FileText className="w-16 h-16 text-[#1A1A1A]/20 mx-auto mb-4" />
          <h3 className="text-xl font-serif italic text-[#1A1A1A] mb-2">No Transcriptions Yet</h3>
          <p className="text-sm text-[#1A1A1A]/60">Upload call recordings to see transcriptions here</p>
        </div>
      </div>
    );
  }

  const filtered = recordings.filter((r) => {
    if (!r) return false;
    // Search filter
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matches =
        (r.name || '').toLowerCase().includes(q) ||
        (r.patientName || '').toLowerCase().includes(q) ||
        (r.agentName || '').toLowerCase().includes(q) ||
        (r.id || '').includes(q);
      if (!matches) return false;
    }

    // Compliance filter
    if (complianceFilter === 'compliant' && !r.sopCompliant) return false;
    if (complianceFilter === 'gap' && r.sopCompliant) return false;

    return true;
  });

  // Calculate audio limits (duration parsing helper)
  const getDurationSeconds = (durationStr: string) => {
    const parts = durationStr.split(':');
    if (parts.length === 2) {
      return parseInt(parts[0]) * 60 + parseInt(parts[1]);
    }
    return 300; // default to 5 mins if invalid
  };

  const limitSeconds = activeCall ? getDurationSeconds(activeCall.duration) : 300;

  // Format time display helper
  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = Math.floor(secs % 60);
    return `${mins.toString().padStart(2, '0')}:${remainingSecs.toString().padStart(2, '0')}`;
  };

  // Wire real audio element when activeCall changes
  useEffect(() => {
    const url = activeCall?.recording_url;
    if (!url) return;

    // Create or reuse audio element
    if (!audioRef.current) {
      audioRef.current = new Audio();
    }
    const audio = audioRef.current;
    audio.src = url;
    audio.volume = volume / 100;
    audio.muted = isMuted;

    const onTimeUpdate = () => setCurrentTime(Math.floor(audio.currentTime));
    const onDurationChange = () => setAudioDuration(Math.floor(audio.duration) || 0);
    const onEnded = () => { setIsPlaying(false); setCurrentTime(0); };

    audio.addEventListener('timeupdate', onTimeUpdate);
    audio.addEventListener('durationchange', onDurationChange);
    audio.addEventListener('loadedmetadata', onDurationChange);
    audio.addEventListener('ended', onEnded);

    return () => {
      audio.pause();
      audio.removeEventListener('timeupdate', onTimeUpdate);
      audio.removeEventListener('durationchange', onDurationChange);
      audio.removeEventListener('loadedmetadata', onDurationChange);
      audio.removeEventListener('ended', onEnded);
    };
  }, [activeCall?.recording_url]);

  // Sync play/pause with real audio
  useEffect(() => {
    const audio = audioRef.current;
    const url = activeCall?.recording_url;
    if (!audio || !url) {
      // Fallback timer for calls without URL
      if (isPlaying) {
        timerRef.current = setInterval(() => {
          setCurrentTime((prev) => {
            if (prev >= limitSeconds) { setIsPlaying(false); return 0; }
            return prev + 1;
          });
        }, 1000);
      } else {
        if (timerRef.current) clearInterval(timerRef.current);
      }
      return () => { if (timerRef.current) clearInterval(timerRef.current); };
    }

    if (isPlaying) {
      audio.play().catch(() => setIsPlaying(false));
    } else {
      audio.pause();
    }
  }, [isPlaying, activeCall?.recording_url]);

  // Sync volume/mute
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume / 100;
      audioRef.current.muted = isMuted;
    }
  }, [volume, isMuted]);

  // Handle Seek
  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const t = parseInt(e.target.value);
    setCurrentTime(t);
    if (audioRef.current && activeCall?.recording_url) {
      audioRef.current.currentTime = t;
    }
  };

  // Effective duration: real audio duration or fallback from metadata
  const effectiveDuration = audioDuration > 0 ? audioDuration : limitSeconds;

  // View transcript detail
  if (activeCall) {
    return (
      <div className="flex flex-col h-full bg-[#FAF8F6] overflow-hidden select-none">
        
        {/* Navigation & Header strip */}
        <div className="flex-none p-6 bg-white border-b border-[#1A1A1A]/10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1.5">
            <button 
              onClick={() => {
                setSelectedCallId(null);
                setIsPlaying(false);
                setCurrentTime(0);
              }}
              className="flex items-center gap-1.5 text-xs font-sans font-bold uppercase tracking-wider text-[#8B7E66] hover:text-[#1A1A1A] transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to transcriptions list</span>
            </button>
            <div className="flex items-center gap-3 flex-wrap">
              <h2 className="text-2xl font-serif italic font-medium text-[#1A1A1A]">
                {activeCall.patientName} Consultation Transcript
              </h2>
              {activeCall.sopCompliant ? (
                <span className="bg-emerald-50 border border-emerald-300 text-emerald-800 px-2.5 py-0.5 text-[9px] font-sans font-bold uppercase tracking-wider">
                  SOP COMPLIANT
                </span>
              ) : (
                <span className="bg-[#F9EAE6] border border-[#A34E36]/30 text-[#A34E36] px-2.5 py-0.5 text-[9px] font-sans font-bold uppercase tracking-wider">
                  SOP GAP DETECTED
                </span>
              )}
            </div>
            <p className="text-xs text-[#1A1A1A]/50 font-sans uppercase tracking-wider flex items-center gap-2.5">
              <span>ID: #{activeCall.id}</span>
              <span>•</span>
              <span>Dietician: {activeCall.agentName}</span>
              <span>•</span>
              <span>Date: {activeCall.date}</span>
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <button className="flex items-center gap-1.5 px-4 py-2 border border-[#1A1A1A]/15 hover:bg-[#FAF8F6] text-xs font-sans uppercase tracking-wider bg-white cursor-pointer transition-colors">
              <Download className="w-4 h-4 text-[#8B7E66]" />
              <span>Export TXT</span>
            </button>
            <button 
              onClick={() => onSelectCall(activeCall.id)}
              className="flex items-center gap-1.5 px-4 py-2 bg-[#1A1A1A] text-white hover:bg-[#8B7E66] text-xs font-sans uppercase tracking-wider cursor-pointer transition-colors"
            >
              <Sparkles className="w-4 h-4" />
              <span>View Performance Metrics</span>
            </button>
          </div>
        </div>

        {/* Dynamic Split Content Pane */}
        <div className="flex-1 flex overflow-hidden min-h-0">
          
          {/* Left Column: Timeline speech bubble timeline */}
          <div className="flex-grow overflow-y-auto h-full custom-scrollbar p-6 space-y-6 bg-white min-h-0">
            {activeCall.transcript.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center p-8">
                <FileText className="w-12 h-12 text-[#1A1A1A]/20 mb-3" />
                <h3 className="text-sm font-serif italic text-[#1A1A1A]">No Transcript Available</h3>
                <p className="text-xs text-[#1A1A1A]/50 mt-1 max-w-sm leading-relaxed font-sans uppercase tracking-wider">
                  This recording contains no transcribed dialogue sequences.
                </p>
              </div>
            ) : (
              <>
                {/* Transcript Header - Explain this is Claude Reconstruction */}
                <div className="bg-[#FFF5E6] border border-[#D4A574]/30 p-3 rounded-none mb-2">
                  <p className="text-xs font-sans text-[#8B7E66] font-bold uppercase tracking-wider">
                    Claude Intelligent Reconstruction
                  </p>
                  <p className="text-xs text-[#8B7E66] mt-1 leading-relaxed">
                    Transcribed with Whisper Tiny (English) or Groq with Spectral Gating (Hindi), then intelligently reconstructed by Claude to fix phonetic errors and add medical context.
                  </p>
                </div>

                {/* Transcript Content */}
                {activeCall.transcript.map((turn) => {
                const isAgent = turn.speaker === 'agent';
                return (
                  <div 
                    key={turn.id} 
                    className={`flex gap-4 ${isAgent ? 'flex-row' : 'flex-row-reverse text-right'}`}
                  >
                    {/* Avatar Initials */}
                    <div className="shrink-0 select-none">
                      <div className={`w-9 h-9 border font-mono font-bold text-[11px] flex items-center justify-center ${
                        isAgent 
                          ? 'bg-[#FAF8F6] text-[#1A1A1A] border-[#1A1A1A]/25' 
                          : 'bg-[#1A1A1A] text-white border-[#1A1A1A]'
                      }`}>
                        {turn.speakerName.split(' ').map(n => n[0]).join('')}
                      </div>
                    </div>

                    {/* Chat Bubble Container */}
                    <div className="space-y-1.5 max-w-2xl">
                      <div className={`flex items-center gap-2.5 text-[10px] font-sans font-bold uppercase tracking-wider ${isAgent ? 'justify-start' : 'justify-end'}`}>
                        <span className="text-[#1A1A1A]">{turn.speakerName}</span>
                        <span className="text-[#1A1A1A]/40 font-mono text-[9px]">{turn.timestamp}</span>
                      </div>

                      {/* Bubble Text Card */}
                      <div className={`p-4 border text-xs leading-relaxed text-[#1A1A1A] ${
                        turn.sopGap
                          ? 'bg-[#F9EAE6] border-[#A34E36]/30'
                          : turn.isCritical
                          ? 'bg-[#FAF8F6] border-[#8B7E66]/30 relative'
                          : 'bg-white border-[#1A1A1A]/10'
                      }`}>
                        {turn.isCritical && turn.criticalBadge && (
                          <div className="absolute -top-2.5 right-4 bg-[#8B7E66] text-white text-[8px] font-sans font-bold uppercase tracking-widest px-2 py-0.5 border border-[#8B7E66]/40">
                            <Sparkles className="w-2.5 h-2.5 inline mr-1" />
                            {turn.criticalBadge}
                          </div>
                        )}

                        <p>{turn.text}</p>

                        {/* Metadata Tags / warnings inside bubble */}
                        {turn.tags && turn.tags.length > 0 && (
                          <div className={`mt-3 flex flex-wrap gap-1.5 ${isAgent ? 'justify-start' : 'justify-end'}`}>
                            {turn.tags.map((tag, tIdx) => (
                              <span key={tIdx} className="px-2 py-0.5 bg-[#FAF8F6] text-[#8B7E66] text-[9px] font-sans font-bold uppercase tracking-wider border border-[#1A1A1A]/5 rounded-none">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}

                        {turn.warning && (
                          <div className="mt-2.5 p-2 bg-[#F9EAE6] border border-[#A34E36]/20 text-[#A34E36] text-[10px] font-sans font-bold uppercase tracking-wider flex items-center gap-2">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            <span>{turn.warning}</span>
                          </div>
                        )}

                        {/* AI Gap Catch box */}
                        {turn.aiCatch && (
                          <div className="mt-3 bg-white p-2.5 border border-[#A34E36]/30 flex items-start gap-2 text-[10px] font-sans font-bold uppercase tracking-wider text-[#A34E36] text-left">
                            <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                            <span>{turn.aiCatch}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
              }
              </>
            )}
          </div>

          {/* Right Column: Mini Insights & Summaries Panel */}
          <div className="w-80 border-l border-[#1A1A1A]/10 bg-[#FAF8F6] p-6 space-y-6 overflow-y-auto custom-scrollbar flex-none">
            
            {/* Auto Summary */}
            <div className="bg-white border border-[#1A1A1A]/10 p-5 relative">
              <div className="absolute top-0 left-0 w-1 h-full bg-[#8B7E66]"></div>
              <div className="flex items-center gap-1.5 text-[#8B7E66] mb-2.5">
                <Sparkles className="w-4 h-4" />
                <span className="text-[9px] font-sans font-bold uppercase tracking-wider">AI Summary</span>
              </div>
              <p className="text-xs font-serif leading-relaxed italic text-[#1A1A1A]/80">
                {activeCall.insights.summary || "No automated summary compiled yet."}
              </p>
            </div>

            {/* What Went Well */}
            {activeCall.insights.whatWentWell.length > 0 && (
              <div className="space-y-2.5">
                <div className="flex items-center gap-1.5 text-emerald-800">
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span className="text-[9px] font-sans font-bold uppercase tracking-wider">What Went Well</span>
                </div>
                <ul className="space-y-1.5">
                  {activeCall.insights.whatWentWell.map((pt, idx) => (
                    <li key={idx} className="text-xs text-[#1A1A1A]/70 flex items-start gap-2 leading-relaxed">
                      <span className="w-1.5 h-1.5 bg-emerald-600 mt-1.5 shrink-0"></span>
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Areas for Improvement */}
            {activeCall.insights.areasForImprovement.length > 0 && (
              <div className="space-y-2.5 pt-4 border-t border-[#1A1A1A]/5">
                <div className="flex items-center gap-1.5 text-[#8B7E66]">
                  <Lightbulb className="w-3.5 h-3.5 shrink-0" />
                  <span className="text-[9px] font-sans font-bold uppercase tracking-wider">Areas For Improvement</span>
                </div>
                <ul className="space-y-1.5">
                  {activeCall.insights.areasForImprovement.map((pt, idx) => (
                    <li key={idx} className="text-xs text-[#1A1A1A]/70 flex items-start gap-2 leading-relaxed">
                      <span className="w-1.5 h-1.5 bg-[#8B7E66] mt-1.5 shrink-0"></span>
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Audio Playback Status */}
        <div className="flex-none px-4 py-2 bg-[#FFF5E6] border-t border-[#D4A574]/30">
          <p className="text-xs text-[#8B7E66] font-sans">
            {activeCall.recording_url?.startsWith('http')
              ? `Playing from: ${activeCall.recording_url.split('/').pop()}`
              : 'No audio URL available for this recording.'}
          </p>
        </div>

        {/* Interactive Playback Control Bar */}
        <div className="flex-none p-4 bg-[#FAF8F6] border-t border-[#1A1A1A]/10">
          <div className="max-w-5xl mx-auto flex flex-col gap-2">
            <div className="flex items-center gap-4">
              <span className="text-[10px] font-mono text-[#1A1A1A]/50 w-10 text-right">
                {formatTime(currentTime)}
              </span>

              {/* Seek Bar */}
              <div className="flex-1 relative flex items-center">
                <input
                  type="range"
                  min="0"
                  max={effectiveDuration || 1}
                  value={currentTime}
                  onChange={handleSeek}
                  className="w-full h-1 bg-[#1A1A1A]/10 appearance-none cursor-pointer accent-[#8B7E66]"
                />
                <div
                  className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-[#8B7E66] pointer-events-none"
                  style={{ width: `${effectiveDuration > 0 ? (currentTime / effectiveDuration) * 100 : 0}%` }}
                ></div>
              </div>

              <span className="text-[10px] font-mono text-[#1A1A1A]/50 w-10">
                {formatTime(effectiveDuration)}
              </span>
            </div>

            <div className="flex items-center justify-between mt-1 px-2">
              <div className="flex items-center gap-3">
                <button 
                  onClick={() => { const t = Math.max(0, currentTime - 10); setCurrentTime(t); if (audioRef.current) audioRef.current.currentTime = t; }}
                  className="p-1.5 text-[#1A1A1A]/60 hover:text-[#8B7E66] transition-colors cursor-pointer"
                  title="Rewind 10s"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="w-9 h-9 bg-[#1A1A1A] text-white flex items-center justify-center hover:bg-[#8B7E66] active:scale-95 transition-all cursor-pointer shrink-0"
                >
                  {isPlaying ? <Pause className="w-4.5 h-4.5 fill-current" /> : <Play className="w-4.5 h-4.5 fill-current ml-0.5" />}
                </button>
                <button 
                  onClick={() => { const t = Math.min(effectiveDuration, currentTime + 10); setCurrentTime(t); if (audioRef.current) audioRef.current.currentTime = t; }}
                  className="p-1.5 text-[#1A1A1A]/60 hover:text-[#8B7E66] transition-colors cursor-pointer"
                  title="Forward 10s"
                >
                  <RotateCcw className="w-3.5 h-3.5 transform scale-x-[-1]" />
                </button>
              </div>

              {/* Volume */}
              <div className="flex items-center gap-2">
                <button 
                  onClick={() => setIsMuted(!isMuted)}
                  className="p-1 text-[#1A1A1A]/60 hover:text-[#8B7E66] cursor-pointer"
                >
                  {isMuted || volume === 0 ? <VolumeX className="w-3.5 h-3.5" /> : volume < 50 ? <Volume1 className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                </button>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={isMuted ? 0 : volume}
                  onChange={(e) => {
                    setVolume(parseInt(e.target.value));
                    if (isMuted) setIsMuted(false);
                  }}
                  className="w-20 h-1 bg-[#1A1A1A]/10 appearance-none accent-[#8B7E66] cursor-pointer"
                />
              </div>
            </div>
          </div>
        </div>

      </div>
    );
  }

  // Browse List View
  return (
    <div className="h-full w-full flex flex-col overflow-hidden bg-[#F7F3F0] select-none p-8">
      {/* View Header */}
      <section className="flex-none flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 border-b border-[#1A1A1A]/10 pb-6">
        <div>
          <span className="text-[10px] font-sans font-bold uppercase tracking-[0.3em] text-[#8B7E66]">Clinical Vault</span>
          <h2 className="text-3xl font-serif italic font-medium tracking-tight text-[#1A1A1A] mt-1">Clinical Transcriptions</h2>
          <p className="text-xs font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1">
            Secure vault of automated audio transcriptions, patient consult transcripts, and dietician performance benchmarks.
          </p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 bg-white border border-[#1A1A1A]/15 px-4 py-2.5 rounded-none text-xs font-sans uppercase tracking-wider">
          <ListFilter className="w-3.5 h-3.5 text-[#8B7E66]" />
          <span className="text-[#1A1A1A]/60">SOP Audit:</span>
          <select
            value={complianceFilter}
            onChange={(e) => setComplianceFilter(e.target.value)}
            className="bg-transparent focus:outline-none text-[#1A1A1A] cursor-pointer font-bold font-sans uppercase tracking-wider border-none"
          >
            <option value="all">All Records</option>
            <option value="compliant">SOP Compliant Only</option>
            <option value="gap">SOP Breach Only</option>
          </select>
        </div>
      </section>

      {/* Scrollable Content Container */}
      <div className="flex-1 overflow-y-auto custom-scrollbar mt-6 min-h-0 pb-8">
        {/* Grid List */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((item) => {
            const isCompliant = item.sopCompliant;
            return (
              <div 
                key={item.id}
                className="bg-white border border-[#1A1A1A]/10 rounded-none p-6 flex flex-col justify-between hover:border-[#8B7E66] transition-all group relative"
              >
                <div>
                  <div className="flex items-center justify-between mb-5 border-b border-[#1A1A1A]/5 pb-3">
                    <div className="p-2 border border-[#1A1A1A]/10 bg-[#FAF8F6] text-[#8B7E66] rounded-none">
                      <FileText className="w-4 h-4" />
                    </div>
                    
                    {isCompliant ? (
                      <span className="px-2 py-0.5 bg-emerald-50 border border-emerald-300 text-emerald-800 text-[9px] font-sans font-bold uppercase tracking-wider rounded-none">
                        Compliant
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 bg-[#F9EAE6] border border-[#A34E36]/30 text-[#A34E36] text-[9px] font-sans font-bold uppercase tracking-wider rounded-none">
                        Breach Detected
                      </span>
                    )}
                  </div>

                  <h3 className="font-serif italic font-medium text-base text-[#1A1A1A] group-hover:text-[#8B7E66] transition-colors truncate">
                    {item.name || 'Untitled Call'}
                  </h3>

                  <div className="mt-4 space-y-2 text-xs font-sans text-[#1A1A1A]/60">
                    <div className="flex justify-between">
                      <span className="uppercase tracking-wider text-[10px]">Patient:</span>
                      <span className="text-[#1A1A1A] font-medium">{item.patientName || 'Unknown'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="uppercase tracking-wider text-[10px]">Dietician:</span>
                      <span className="text-[#1A1A1A] font-medium">{item.agentName || 'Unknown'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="uppercase tracking-wider text-[10px]">Duration:</span>
                      <span className="text-[#1A1A1A] font-medium flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-[#8B7E66]" />
                        {item.duration || '0:00'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center pt-3 border-t border-[#1A1A1A]/10 mt-3">
                      <span className="uppercase tracking-wider text-[10px] font-bold text-[#1A1A1A]">Clinical Score:</span>
                      <span className={`text-sm font-mono font-bold ${isCompliant ? 'text-emerald-700' : 'text-[#A34E36]'}`}>
                        {item.sopComplianceScore}%
                      </span>
                    </div>
                  </div>
                </div>

                <div className="mt-6">
                  <button
                    onClick={() => setSelectedCallId(item.id)}
                    className="w-full bg-[#1A1A1A] hover:bg-[#8B7E66] text-white py-3 rounded-none text-xs font-sans uppercase tracking-widest flex items-center justify-center gap-1.5 cursor-pointer transition-colors"
                  >
                    <span>Review Transcript</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
                <div className="absolute top-0 left-0 w-full h-[2px] bg-[#8B7E66] opacity-0 group-hover:opacity-100 transition-opacity"></div>
              </div>
            );
          })}
        </section>
      </div>
    </div>
  );
}
