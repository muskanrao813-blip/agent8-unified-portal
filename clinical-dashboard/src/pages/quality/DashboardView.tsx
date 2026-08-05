import React, { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  AlertOctagon,
  FileText,
  Activity,
  Award,
  BookOpen,
  ArrowRight,
  Sparkles,
  ChevronRight,
  ShieldCheck,
  CheckCircle,
  XCircle,
  HelpCircle,
  ExternalLink,
  Calendar,
  Download
} from 'lucide-react';
import { Recording, Dietician } from '../types';

interface DashboardViewProps {
  recordings: Recording[];
  onSelectCall: (id: string) => void;
  dieticians: Dietician[];
  searchQuery: string;
}

export default function DashboardView({
  recordings,
  onSelectCall,
  dieticians,
  searchQuery
}: DashboardViewProps) {
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const today = new Date().toISOString().split('T')[0];
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  const [dateFrom, setDateFrom] = useState(thirtyDaysAgo);
  const [dateTo, setDateTo] = useState(today);
  // Stats use dateFilteredRecordings (respects the calendar selection)
  // These are declared after dateFilteredRecordings below — hoisted by JS but defined after jsx starts
  // We'll compute after date filter is set up in render flow

  // Date-filtered recordings (for stats + charts)
  const dateFilteredRecordings = recordings.filter(r => {
    if (!r.date) return true;
    try {
      const callDate = new Date(r.date).toISOString().split('T')[0];
      return callDate >= dateFrom && callDate <= dateTo;
    } catch { return true; }
  });

  // Stats from date-filtered data
  const totalCalls = dateFilteredRecordings.length;
  const avgQualityScore = totalCalls > 0
    ? Math.round((dateFilteredRecordings.reduce((sum, r) => sum + (r.sopComplianceScore || 0), 0) / totalCalls) * 10) / 10
    : 0;
  const sopCompliance = totalCalls > 0
    ? Math.round(dateFilteredRecordings.reduce((sum, r) => sum + (r.scores?.compliance || 0), 0) / totalCalls)
    : 0;
  const criticalAlertsCount = dateFilteredRecordings.reduce((sum, r) =>
    sum + (r.qaAlerts?.filter(a => a.severity === 'critical').length || 0), 0);

  const filteredRecordings = dateFilteredRecordings.filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.name.toLowerCase().includes(q) ||
      r.patientName.toLowerCase().includes(q) ||
      r.agentName.toLowerCase().includes(q) ||
      r.id.includes(q)
    );
  });

  const exportPDF = () => {
    const byDietician: Record<string, Recording[]> = {};
    dateFilteredRecordings.forEach(r => {
      const d = r.agentName || 'Unknown';
      if (!byDietician[d]) byDietician[d] = [];
      byDietician[d].push(r);
    });

    const html = `<!DOCTYPE html><html><head>
<title>Dietician QA Report — ${dateFrom} to ${dateTo}</title>
<style>
  body { font-family: Arial, sans-serif; margin: 30px; color: #1A1A1A; font-size: 12px; }
  h1 { font-size: 22px; font-weight: bold; margin-bottom: 4px; }
  h2 { font-size: 16px; margin-top: 28px; margin-bottom: 8px; border-bottom: 2px solid #1A1A1A; padding-bottom: 4px; }
  h3 { font-size: 13px; margin: 14px 0 4px; }
  .meta { color: #555; font-size: 11px; margin-bottom: 20px; }
  .call-card { border: 1px solid #ddd; padding: 12px; margin-bottom: 12px; page-break-inside: avoid; }
  .scores { display: flex; gap: 20px; margin: 8px 0; }
  .score-item { text-align: center; }
  .score-val { font-size: 18px; font-weight: bold; }
  .score-lbl { font-size: 10px; color: #777; text-transform: uppercase; }
  .alert { background: #fff0ee; border-left: 3px solid #c0392b; padding: 6px 10px; margin: 4px 0; font-size: 11px; }
  .good { color: #27ae60; } .bad { color: #c0392b; }
  ul { margin: 4px 0; padding-left: 18px; }
  li { margin: 2px 0; }
  .transcript-line { margin: 3px 0; font-size: 11px; }
  .dietician-speaker { color: #2980b9; }
  .customer-speaker { color: #8e44ad; }
  @media print { .call-card { break-inside: avoid; } }
</style></head><body>
<h1>Dietician QA Analysis Report</h1>
<div class="meta">Period: ${dateFrom} to ${dateTo} | Generated: ${new Date().toLocaleString()} | Total Calls: ${dateFilteredRecordings.length}</div>
${Object.entries(byDietician).map(([dietician, calls]) => {
  const avgScore = Math.round(calls.reduce((s, c) => s + (c.sopComplianceScore || 0), 0) / calls.length);
  const critCount = calls.reduce((s, c) => s + (c.qaAlerts?.filter(a => a.severity === 'critical').length || 0), 0);
  return `<h2>Dietician: ${dietician}</h2>
<p><strong>Total Calls:</strong> ${calls.length} &nbsp;|&nbsp; <strong>Avg Score:</strong> ${avgScore}% &nbsp;|&nbsp; <strong>Critical Alerts:</strong> ${critCount}</p>
${calls.map(call => {
  const s = (call.scores || {}) as any;
  const ins = (call.insights || {}) as any;
  const alerts = (call.qaAlerts || []).filter(a => a.severity === 'critical').slice(0, 5);
  const transcript = (call.transcript || []).slice(0, 15);
  return `<div class="call-card">
  <h3>${call.patientName} — ${call.date} (${call.duration})</h3>
  <div class="scores">
    <div class="score-item"><div class="score-val ${(call.sopComplianceScore||0) >= 60 ? 'good' : 'bad'}">${call.sopComplianceScore || 0}%</div><div class="score-lbl">Overall</div></div>
    <div class="score-item"><div class="score-val">${s.greeting || 0}%</div><div class="score-lbl">Greeting</div></div>
    <div class="score-item"><div class="score-val">${s.empathy || 0}%</div><div class="score-lbl">Empathy</div></div>
    <div class="score-item"><div class="score-val ${(s.compliance||0) >= 50 ? '' : 'bad'}">${s.compliance || 0}%</div><div class="score-lbl">Compliance</div></div>
    <div class="score-item"><div class="score-val">${s.technical || 0}%</div><div class="score-lbl">Technical</div></div>
  </div>
  ${alerts.length > 0 ? `<p><strong>Critical Alerts:</strong></p>${alerts.map(a => `<div class="alert">${a.title}${a.description ? ` — ${a.description.substring(0, 120)}` : ''}</div>`).join('')}` : ''}
  ${ins.whatWentWell?.length ? `<p><strong>What Went Well:</strong></p><ul>${ins.whatWentWell.slice(0,3).map((p: string) => `<li class="good">${p}</li>`).join('')}</ul>` : ''}
  ${ins.areasForImprovement?.length ? `<p><strong>Areas for Improvement:</strong></p><ul>${ins.areasForImprovement.slice(0,3).map((p: string) => `<li class="bad">${p}</li>`).join('')}</ul>` : ''}
  ${transcript.length > 0 ? `<p><strong>Transcript (first 15 turns):</strong></p>${transcript.map(t => {
    const isDiet = (t.speaker as string) === 'agent' || (t.speaker as string) === 'dietician';
    return `<div class="transcript-line"><span class="${isDiet ? 'dietician-speaker' : 'customer-speaker'}">[${isDiet ? 'Dietician' : 'Customer'}]</span> ${t.text}</div>`;
  }).join('')}` : ''}
</div>`;
}).join('')}`;
}).join('')}
</body></html>`;

    const win = window.open('', '_blank');
    if (win) {
      win.document.write(html);
      win.document.close();
      setTimeout(() => win.print(), 500);
    }
  };

  // Performance data — one bar per DIETICIAN, date-filtered
  const performanceDist = (() => {
    const byDietician: Record<string, number[]> = {};
    dateFilteredRecordings.forEach(r => {
      const name = r.agentName || 'Unknown';
      if (!byDietician[name]) byDietician[name] = [];
      byDietician[name].push(r.sopComplianceScore || 0);
    });
    return Object.entries(byDietician).map(([name, scores]) => ({
      name: name.split(' ')[0],
      score: Math.round(scores.reduce((a, b) => a + b, 0) / scores.length),
      calls: scores.length,
      peerMedian: 60,
    }));
  })();

  return (
    <div className="flex-1 flex overflow-hidden bg-[#F7F3F0] h-full select-none">
      {/* Main Left Content Area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-8">
        {/* Header Section */}
        <section className="flex justify-between items-end border-b border-[#1A1A1A]/10 pb-6">
          <div>
            <span className="text-[10px] font-sans font-bold uppercase tracking-[0.3em] text-[#8B7E66]">Overview Report</span>
            <h2 className="text-3xl font-serif italic font-medium tracking-tight text-[#1A1A1A] mt-1">Executive Performance Overview</h2>
            <p className="text-xs font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1">
              Real-time health of clinical consultations and dietician performance.
            </p>
          </div>
          <div className="flex gap-3 items-center relative">
            {/* Date range picker */}
            <div className="relative">
              <button
                onClick={() => setShowDatePicker(v => !v)}
                className="px-4 py-2 text-xs font-sans uppercase tracking-wider border border-[#1A1A1A]/20 bg-white text-[#1A1A1A] hover:bg-[#F7F3F0] rounded-none flex items-center gap-2 cursor-pointer transition-colors"
              >
                <Calendar className="w-3.5 h-3.5" />
                <span>{dateFrom} — {dateTo}</span>
              </button>
              {showDatePicker && (
                <div className="absolute right-0 top-full mt-1 bg-white border border-[#1A1A1A]/15 shadow-xl z-50 p-4 space-y-3 w-64">
                  <div>
                    <label className="text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]/60 block mb-1">From</label>
                    <input type="date" value={dateFrom} max={dateTo} onChange={e => setDateFrom(e.target.value)}
                      className="w-full border border-[#1A1A1A]/15 px-3 py-1.5 text-xs focus:outline-none focus:border-[#8B7E66]" />
                  </div>
                  <div>
                    <label className="text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]/60 block mb-1">To</label>
                    <input type="date" value={dateTo} min={dateFrom} max={today} onChange={e => setDateTo(e.target.value)}
                      className="w-full border border-[#1A1A1A]/15 px-3 py-1.5 text-xs focus:outline-none focus:border-[#8B7E66]" />
                  </div>
                  <div className="flex gap-2">
                    {[['7d', 7], ['30d', 30], ['90d', 90]].map(([label, days]) => (
                      <button key={label} onClick={() => {
                        const f = new Date(Date.now() - (days as number) * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
                        setDateFrom(f); setDateTo(today);
                      }} className="flex-1 py-1.5 text-[10px] font-sans uppercase tracking-wider border border-[#1A1A1A]/15 hover:bg-[#FAF8F6] cursor-pointer">
                        {label}
                      </button>
                    ))}
                  </div>
                  <button onClick={() => setShowDatePicker(false)}
                    className="w-full py-2 bg-[#1A1A1A] text-white text-[10px] font-sans uppercase tracking-wider hover:bg-[#8B7E66] cursor-pointer">
                    Apply
                  </button>
                </div>
              )}
            </div>

            <button
              onClick={exportPDF}
              className="px-4 py-2 text-xs font-sans uppercase tracking-wider bg-[#1A1A1A] text-white hover:bg-[#8B7E66] rounded-none flex items-center gap-2 cursor-pointer transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export PDF</span>
            </button>
          </div>
        </section>

        {/* Quick Stats Bento */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Card 1: Total Calls */}
          <div className="bg-white border border-[#1A1A1A]/10 p-6 rounded-none hover:border-[#8B7E66] transition-all duration-200 relative group">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-sans font-bold text-[#1A1A1A]/50 uppercase tracking-[0.15em]">Total Calls Analyzed</span>
              <div className="text-[#8B7E66]">
                <Activity className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="text-4xl font-serif italic font-medium text-[#1A1A1A]">{totalCalls.toLocaleString()}</h3>
              <span className="text-emerald-700 text-xs font-mono font-bold flex items-center gap-1 bg-emerald-50 px-1.5 py-0.5 border border-emerald-200 shrink-0">
                <TrendingUp className="w-3 h-3" />
                +12%
              </span>
            </div>
            <div className="absolute top-0 left-0 w-full h-[2px] bg-[#8B7E66] opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </div>

          {/* Card 2: Avg Quality Score */}
          <div className="bg-white border border-[#1A1A1A]/10 p-6 rounded-none hover:border-[#8B7E66] transition-all duration-200 relative group">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-sans font-bold text-[#1A1A1A]/50 uppercase tracking-[0.15em]">Avg. Quality Score</span>
              <div className="text-[#8B7E66]">
                <Award className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="text-4xl font-serif italic font-medium text-[#1A1A1A]">{avgQualityScore}%</h3>
              <span className="text-emerald-700 text-xs font-mono font-bold flex items-center gap-1 bg-emerald-50 px-1.5 py-0.5 border border-emerald-200 shrink-0">
                <TrendingUp className="w-3 h-3" />
                +2.4%
              </span>
            </div>
            <div className="absolute top-0 left-0 w-full h-[2px] bg-[#8B7E66] opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </div>

          {/* Card 3: SOP Compliance */}
          <div className="bg-white border border-[#1A1A1A]/10 p-6 rounded-none hover:border-[#8B7E66] transition-all duration-200 relative group">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-sans font-bold text-[#1A1A1A]/50 uppercase tracking-[0.15em]">SOP Compliance %</span>
              <div className="text-[#8B7E66]">
                <ShieldCheck className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="text-4xl font-serif italic font-medium text-[#1A1A1A]">{sopCompliance}%</h3>
              <span className="text-[#A34E36] text-xs font-mono font-bold flex items-center gap-1 bg-[#F9EAE6] px-1.5 py-0.5 border border-[#A34E36]/20 shrink-0">
                <TrendingDown className="w-3 h-3" />
                -0.8%
              </span>
            </div>
            <div className="absolute top-0 left-0 w-full h-[2px] bg-[#8B7E66] opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </div>

          {/* Card 4: Critical Alerts */}
          <div className="bg-white border border-[#1A1A1A]/10 p-6 rounded-none hover:border-[#8B7E66] transition-all duration-200 relative group">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-sans font-bold text-[#1A1A1A]/50 uppercase tracking-[0.15em]">Critical QA Alerts</span>
              <div className="text-[#A34E36]">
                <AlertOctagon className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="text-4xl font-serif italic font-medium text-[#1A1A1A]">{criticalAlertsCount}</h3>
              <span className="bg-[#F9EAE6] border border-[#A34E36]/30 text-[#A34E36] text-[8px] font-sans font-bold px-2 py-0.5 rounded-none uppercase tracking-widest shrink-0">
                Critical
              </span>
            </div>
            <div className="absolute top-0 left-0 w-full h-[2px] bg-[#8B7E66] opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </div>
        </section>

        {/* Charts Section: Dietician Performance & SOP Breaches */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Dietician Performance Distribution SVG Chart */}
          <div className="lg:col-span-7 bg-white border border-[#1A1A1A]/10 rounded-none p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-[#1A1A1A]/5 pb-4">
                <div>
                  <h3 className="text-lg font-serif italic font-medium text-[#1A1A1A]">Staff Performance Metrics</h3>
                  <p className="text-[10px] font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-0.5">
                    Distribution of quality scores across clinical staff members.
                  </p>
                </div>
                {/* Legend */}
                <div className="flex gap-4 text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]/60">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 bg-[#8B7E66]"></span>
                    <span>Individual</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 bg-[#1A1A1A]/20"></span>
                    <span>Peer Median</span>
                  </div>
                </div>
              </div>

              {/* Chart Stage */}
              <div className="h-60 mt-8 flex items-end justify-between px-4 border-b border-[#1A1A1A]/10 pb-2 relative">
                {/* Y-Axis lines helper */}
                <div className="absolute left-0 right-0 top-0 h-[1px] bg-[#1A1A1A]/5"></div>
                <div className="absolute left-0 right-0 top-1/4 h-[1px] bg-[#1A1A1A]/5"></div>
                <div className="absolute left-0 right-0 top-2/4 h-[1px] bg-[#1A1A1A]/5"></div>
                <div className="absolute left-0 right-0 top-3/4 h-[1px] bg-[#1A1A1A]/5"></div>

                {performanceDist.map((item, idx) => (
                  <div key={idx} className="flex flex-col items-center gap-2 flex-1 group">
                    <div className="relative w-12 h-44 flex items-end justify-center">
                      {/* Peer Median Line Indicator */}
                      <div 
                        className="absolute w-full h-[2px] bg-[#1A1A1A]/30 z-10 transition-colors group-hover:bg-[#8B7E66]"
                        style={{ bottom: `${item.peerMedian}%` }}
                        title={`Peer Median: ${item.peerMedian}%`}
                      ></div>

                      {/* Score Bar */}
                      <div 
                        className={`w-3.5 rounded-none transition-all duration-300 group-hover:opacity-85 relative ${
                          item.score < 75 
                            ? 'bg-[#A34E36]' 
                            : item.score < 90 
                            ? 'bg-[#8B7E66]/60' 
                            : 'bg-[#8B7E66]'
                        }`}
                        style={{ height: `${item.score}%` }}
                      >
                        {/* Tooltip on hover */}
                        <div className="absolute -top-14 left-1/2 -translate-x-1/2 bg-[#1A1A1A] text-white text-[9px] font-mono font-bold px-2 py-1 rounded-none whitespace-nowrap z-30 shadow-md opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none text-center">
                          <div>Score: {item.score}%</div>
                          <div className="text-[#8B7E66]">{(item as any).calls} calls</div>
                        </div>
                      </div>
                    </div>
                    <span className="text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]/60">{item.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* SOP Breach Categories — from real QA alert data */}
          <div className="lg:col-span-5 bg-white border border-[#1A1A1A]/10 rounded-none p-6 flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-serif italic font-medium text-[#1A1A1A] border-b border-[#1A1A1A]/5 pb-4">SOP Breach Categories</h3>
              <p className="text-[10px] font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1.5">Most common compliance failures identified by AI, ranked by frequency.</p>

              <div className="mt-6 space-y-4">
                {(() => {
                  const allAlerts = recordings.flatMap(r => r.qaAlerts || []);
                  const counts: Record<string, number> = {};
                  for (const a of allAlerts) { const t = a?.title; if (t) counts[t] = (counts[t] || 0) + 1; }
                  const total = recordings.length || 1;
                  return Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([title, count]) => {
                    const pct = Math.round((count / total) * 100);
                    const color = pct >= 80 ? 'bg-[#A34E36]' : pct >= 50 ? 'bg-[#8B7E66]' : 'bg-[#8B7E66]/50';
                    const textColor = pct >= 80 ? 'text-[#A34E36]' : 'text-[#8B7E66]';
                    return (
                      <div key={title} className="space-y-1.5">
                        <div className="flex justify-between text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]">
                          <span className="truncate max-w-[200px]" title={title}>{title}</span>
                          <span className={`font-mono ml-2 shrink-0 ${textColor}`}>{count}/{total} calls</span>
                        </div>
                        <div className="w-full bg-[#FAF8F6] border border-[#1A1A1A]/5 h-2 rounded-none overflow-hidden">
                          <div className={`${color} h-full transition-all`} style={{ width: `${pct}%` }}></div>
                        </div>
                      </div>
                    );
                  });
                })()}
                {recordings.flatMap(r => r.qaAlerts || []).length === 0 && (
                  <p className="text-xs text-[#1A1A1A]/40 italic">No breach data yet. Upload and process calls to see patterns.</p>
                )}
              </div>
            </div>

            <button
              onClick={() => setShowHeatmap(true)}
              className="mt-6 w-full py-3 border border-[#1A1A1A]/30 text-[#1A1A1A] text-xs font-sans uppercase tracking-widest hover:bg-[#1A1A1A] hover:text-white transition-all rounded-none cursor-pointer">
              View All Breach Types
            </button>
          </div>

          {/* Heatmap Modal */}
          {showHeatmap && (
            <div className="fixed inset-0 bg-[#1A1A1A]/60 z-50 flex items-center justify-center p-6" onClick={() => setShowHeatmap(false)}>
              <div className="bg-white w-full max-w-xl max-h-[80vh] overflow-y-auto rounded-none p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
                <div className="flex justify-between items-center mb-4 border-b border-[#1A1A1A]/10 pb-3">
                  <h3 className="text-lg font-serif italic font-medium text-[#1A1A1A]">All SOP Breach Types</h3>
                  <button onClick={() => setShowHeatmap(false)} className="text-[#1A1A1A]/40 hover:text-[#1A1A1A] text-xs font-sans uppercase tracking-wider">Close</button>
                </div>
                <div className="space-y-3">
                  {(() => {
                    const allAlerts = recordings.flatMap(r => r.qaAlerts || []);
                    const counts: Record<string, number> = {};
                    for (const a of allAlerts) { const t = a?.title; if (t) counts[t] = (counts[t] || 0) + 1; }
                    const total = recordings.length || 1;
                    return Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([title, count]) => {
                      const pct = Math.round((count / total) * 100);
                      return (
                        <div key={title}>
                          <div className="flex justify-between text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A] mb-1">
                            <span className="max-w-[340px] leading-tight">{title}</span>
                            <span className={`ml-2 shrink-0 font-mono ${pct >= 80 ? 'text-[#A34E36]' : 'text-[#8B7E66]'}`}>{count}/{total}</span>
                          </div>
                          <div className="w-full bg-[#FAF8F6] h-1.5">
                            <div className={`h-full ${pct >= 80 ? 'bg-[#A34E36]' : 'bg-[#8B7E66]'}`} style={{ width: `${pct}%` }}></div>
                          </div>
                        </div>
                      );
                    });
                  })()}
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Lower Table: Recent Call Analysis */}
        <section className="bg-white border border-[#1A1A1A]/10 rounded-none overflow-hidden shadow-none">
          <div className="p-6 border-b border-[#1A1A1A]/10 flex items-center justify-between bg-[#FAF8F6]">
            <h3 className="text-lg font-serif italic font-medium text-[#1A1A1A]">Recent Ingested Audios</h3>
            <span className="text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]/40">Showing {filteredRecordings.length} calls</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#FAF8F6] border-b border-[#1A1A1A]/10">
                  <th className="px-6 py-3.5 text-[10px] font-sans font-bold uppercase tracking-widest text-[#1A1A1A]/60">Recording Name</th>
                  <th className="px-6 py-3.5 text-[10px] font-sans font-bold uppercase tracking-widest text-[#1A1A1A]/60">Dietician</th>
                  <th className="px-6 py-3.5 text-[10px] font-sans font-bold uppercase tracking-widest text-[#1A1A1A]/60">AI Score</th>
                  <th className="px-6 py-3.5 text-[10px] font-sans font-bold uppercase tracking-widest text-[#1A1A1A]/60">Compliance Status</th>
                  <th className="px-6 py-3.5 text-[10px] font-sans font-bold uppercase tracking-widest text-[#1A1A1A]/60">Date</th>
                  <th className="px-6 py-3.5 text-[10px] font-sans font-bold uppercase tracking-widest text-[#1A1A1A]/60 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1A1A1A]/10">
                {filteredRecordings.map((call) => {
                  const isCompliant = call.sopCompliant;
                  return (
                    <tr 
                      key={call.id} 
                      onClick={() => onSelectCall(call.id)}
                      className="hover:bg-[#FAF8F6] cursor-pointer transition-colors group"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <FileText className="w-4 h-4 text-[#8B7E66]" />
                          <span className="text-xs font-serif font-medium text-[#1A1A1A] truncate max-w-xs">{call.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-none border border-[#1A1A1A]/20 bg-[#F7F3F0] text-[#1A1A1A] font-mono font-bold text-[10px] flex items-center justify-center">
                            {call.agentName.split(' ').map(n => n[0]).join('')}
                          </span>
                          <span className="text-xs font-sans uppercase tracking-wide text-[#1A1A1A]">{call.agentName}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`text-xs font-mono font-bold ${
                          call.sopComplianceScore >= 90 
                            ? 'text-emerald-700' 
                            : call.sopComplianceScore >= 75 
                            ? 'text-[#8B7E66]' 
                            : 'text-[#A34E36]'
                        }`}>
                          {call.sopComplianceScore}%
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-0.5 text-[9px] font-sans font-bold border rounded-none uppercase tracking-widest ${
                          isCompliant 
                            ? 'bg-emerald-50 border-emerald-300 text-emerald-800' 
                            : 'bg-[#F9EAE6] border-[#A34E36]/30 text-[#A34E36]'
                        }`}>
                          {isCompliant ? 'Compliant' : 'Breach Detected'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-xs font-mono text-[#1A1A1A]/60">{call.date}</span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button className="p-1 text-[#1A1A1A]/40 hover:text-[#1A1A1A] rounded-none transition-colors group-hover:translate-x-0.5 transform transition-transform">
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="p-4 bg-[#FAF8F6] border-t border-[#1A1A1A]/10 text-center">
            <span className="text-[10px] text-[#8B7E66] hover:text-[#1A1A1A] cursor-pointer font-sans uppercase tracking-widest flex items-center justify-center gap-1">
              <span>Showing All {totalCalls} Analysed Calls</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </span>
          </div>
        </section>
      </div>
    </div>
  );
}
