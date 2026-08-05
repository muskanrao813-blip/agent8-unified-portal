import React, { useState } from 'react';
import {
  Sparkles,
  AlertTriangle,
  Award,
  TrendingUp,
  TrendingDown,
  Activity,
  CheckCircle,
  Clock,
  BookOpen,
  ArrowRight,
  Plus,
  Compass,
  Check,
  CheckSquare,
  ShieldAlert
} from 'lucide-react';
import { Dietician, TrainingGap, DieticianQAAlert } from '../types';

interface DieticianReportsViewProps {
  dieticians: Dietician[];
  trainingGaps: TrainingGap[];
  onAssignTraining: (id: string) => void;
  searchQuery: string;
}

export default function DieticianReportsView({
  dieticians,
  trainingGaps,
  onAssignTraining,
  searchQuery
}: DieticianReportsViewProps) {
  const [showAssignSuccess, setShowAssignSuccess] = useState<string | null>(null);

  const filteredDieticians = dieticians.filter((d) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return d.name.toLowerCase().includes(q) || d.role.toLowerCase().includes(q);
  });

  const handleAssign = (gapId: string) => {
    onAssignTraining(gapId);
    setShowAssignSuccess(gapId);
    setTimeout(() => {
      setShowAssignSuccess(null);
    }, 2000);
  };

  return (
    <div className="flex-grow flex overflow-hidden bg-[#F7F3F0] h-full select-none">
      {/* Main Table section - Left */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-8">
        <div>
          <span className="text-[10px] font-sans font-bold uppercase tracking-[0.3em] text-[#8B7E66]">Performance Audit</span>
          <h2 className="text-3xl font-serif italic font-medium tracking-tight text-[#1A1A1A] mt-1">Performance & Training Report</h2>
          <p className="text-xs font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1">
            Clinical quality score distributions and automated professional recommendation pathways.
          </p>
        </div>

        {/* Table layout container */}
        <div className="bg-white border border-[#1A1A1A]/10 rounded-none overflow-hidden shadow-sm">
          <div className="p-6 border-b border-[#1A1A1A]/10 bg-[#FAF8F6]">
            <h3 className="text-base font-serif italic font-medium text-[#1A1A1A]">Active Clinical Staff</h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#FAF8F6] border-b border-[#1A1A1A]/10">
                  <th className="px-6 py-4.5 text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]/50">Dietician</th>
                  <th className="px-6 py-4.5 text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]/50">Avg Quality Score</th>
                  <th className="px-6 py-4.5 text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]/50">SOP Compliance Trend</th>
                  <th className="px-6 py-4.5 text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]/50">SOP Breaches (Mo.)</th>
                  <th className="px-6 py-4.5 text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]/50">AI Recommendation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1A1A1A]/5">
                {filteredDieticians.map((d) => (
                  <tr key={d.id} className="hover:bg-[#FAF8F6]/40 transition-colors">
                    {/* User profile details */}
                    <td className="px-6 py-4.5">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-none bg-[#FAF8F6] text-[#1A1A1A] font-mono font-bold text-xs flex items-center justify-center border border-[#1A1A1A]/20 shadow-sm shrink-0">
                          {d.initials}
                        </div>
                        <div>
                          <p className="text-sm font-serif italic font-medium text-[#1A1A1A]">{d.name}</p>
                          <p className="text-[10px] font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-0.5">{d.role}</p>
                        </div>
                      </div>
                    </td>

                    {/* Avg Score with rating highlight */}
                    <td className="px-6 py-4.5">
                      <div className="flex items-baseline gap-2">
                        <span className="text-sm font-mono font-bold text-[#1A1A1A]">{d.avgScore}%</span>
                        <span className={`text-[10px] font-sans font-bold uppercase tracking-wider flex items-center gap-0.5 ${
                          d.trendDirection === 'up' 
                            ? 'text-emerald-700' 
                            : d.trendDirection === 'down' 
                            ? 'text-[#A34E36]' 
                            : 'text-[#1A1A1A]/50'
                        }`}>
                          {d.trendDirection === 'up' && <TrendingUp className="w-3 h-3" />}
                          {d.trendDirection === 'down' && <TrendingDown className="w-3 h-3" />}
                          {d.trend}
                        </span>
                      </div>
                    </td>

                    {/* SOP Compliance Trend Sparkline */}
                    <td className="px-6 py-4.5">
                      <div className="flex items-end gap-1 h-8 w-24">
                        {d.trendValues.map((val, vIdx) => (
                          <div
                            key={vIdx}
                            className={`w-2 rounded-none ${
                              d.trendDirection === 'up' 
                                ? 'bg-emerald-600/70' 
                                : d.trendDirection === 'down' 
                                  ? 'bg-[#A34E36]/70' 
                                  : 'bg-[#8B7E66]/50'
                            }`}
                            style={{ height: `${val * 16}%` }}
                          ></div>
                        ))}
                      </div>
                    </td>

                    {/* SOP Breaches Count */}
                    <td className="px-6 py-4.5">
                      <span className={`text-sm font-mono font-bold ${d.sopBreaches > 1 ? 'text-[#A34E36]' : 'text-[#1A1A1A]'}`}>
                        {d.sopBreaches}
                      </span>
                    </td>

                    {/* AI Status Badge */}
                    <td className="px-6 py-4.5">
                      {d.aiStatus === 'Exceeding Goals' && (
                        <span className="px-2.5 py-0.5 bg-[#FAF8F6] border border-[#1A1A1A]/10 text-[#8B7E66] text-[9px] font-sans font-bold uppercase tracking-wider rounded-none">
                          Exceeding Goals
                        </span>
                      )}
                      {d.aiStatus === 'Training Required' && (
                        <span className="px-2.5 py-0.5 bg-[#F9EAE6] border border-[#A34E36]/30 text-[#A34E36] text-[9px] font-sans font-bold uppercase tracking-wider rounded-none inline-flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" />
                          Training Required
                        </span>
                      )}
                      {d.aiStatus === 'Stability Alert' && (
                        <span className="px-2.5 py-0.5 bg-[#FAF8F6] border border-[#8B7E66]/30 text-[#8B7E66] text-[9px] font-sans font-bold uppercase tracking-wider rounded-none inline-flex items-center gap-1">
                          Stability Alert
                        </span>
                      )}
                      {d.aiStatus === 'Target Met' && (
                        <span className="px-2.5 py-0.5 bg-white border border-[#1A1A1A]/10 text-[#1A1A1A]/60 text-[9px] font-sans font-bold uppercase tracking-wider rounded-none">
                          Target Met
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Right Drawer section: Gaps & stats */}
      <div className="w-[480px] bg-[#FAF8F6] border-l border-[#1A1A1A]/10 flex flex-col p-6 overflow-y-auto custom-scrollbar h-full justify-between shrink-0">
        <div className="space-y-8">
          
          {/* radial overview card - Staff Score Distribution */}
          <div>
            <h3 className="text-[10px] font-sans font-bold uppercase tracking-[0.15em] text-[#1A1A1A]/50 mb-3 border-b border-[#1A1A1A]/10 pb-1.5">Staff Score Distribution</h3>
            <div className="bg-white border border-[#1A1A1A]/10 rounded-none p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 bg-emerald-600 rounded-none"></div>
                  <span className="text-xs font-sans text-[#1A1A1A]/70 uppercase tracking-wider text-[10px]">Top Performers (&gt;90% Score)</span>
                </div>
                <span className="text-xs font-mono font-bold text-[#1A1A1A]">64% of Staff</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 bg-[#8B7E66] rounded-none"></div>
                  <span className="text-xs font-sans text-[#1A1A1A]/70 uppercase tracking-wider text-[10px]">At Goal (80-90% Score)</span>
                </div>
                <span className="text-xs font-mono font-bold text-[#1A1A1A]">22% of Staff</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 bg-[#A34E36] rounded-none"></div>
                  <span className="text-xs font-sans text-[#1A1A1A]/70 uppercase tracking-wider text-[10px]">Needs Training (&lt;80% Score)</span>
                </div>
                <span className="text-xs font-mono font-bold text-[#1A1A1A]">14% of Staff</span>
              </div>
            </div>
          </div>

          {/* Recurring QA Alerts section — aggregated across all calls */}
          {dieticians.length > 0 && (dieticians[0].qaAlerts?.length ?? 0) > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b border-[#1A1A1A]/10 pb-2">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-[#A34E36]" />
                  <h3 className="text-[10px] font-sans font-bold uppercase tracking-[0.15em] text-[#1A1A1A]">Recurring SOP Breaches</h3>
                </div>
                <span className="text-[9px] bg-[#F9EAE6] border border-[#A34E36]/30 text-[#A34E36] font-sans font-bold px-2 py-0.5 rounded-none uppercase tracking-wider">
                  {dieticians[0].totalAlertTypes || dieticians[0].qaAlerts?.length} types
                </span>
              </div>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {dieticians[0].qaAlerts?.map((alert: DieticianQAAlert) => (
                  <div key={alert.id} className="bg-white border border-[#1A1A1A]/10 p-3 flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-[11px] font-sans font-bold text-[#1A1A1A] leading-tight truncate">{alert.title}</p>
                      {alert.description && (
                        <p className="text-[10px] text-[#1A1A1A]/50 mt-0.5 leading-relaxed line-clamp-2">{alert.description}</p>
                      )}
                    </div>
                    <span className={`shrink-0 text-[9px] font-mono font-bold px-2 py-0.5 border rounded-none whitespace-nowrap ${
                      alert.severity === 'critical'
                        ? 'bg-[#F9EAE6] border-[#A34E36]/30 text-[#A34E36]'
                        : alert.severity === 'warning'
                        ? 'bg-amber-50 border-amber-300 text-amber-700'
                        : 'bg-[#FAF8F6] border-[#1A1A1A]/10 text-[#8B7E66]'
                    }`}>
                      {alert.callFrequency}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Identified Training Gaps section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-[#1A1A1A]/10 pb-2">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#8B7E66]" />
                <h3 className="text-[10px] font-sans font-bold uppercase tracking-[0.15em] text-[#1A1A1A]">AI Identified Training Gaps</h3>
              </div>
              <span className="text-[9px] bg-[#FAF8F6] border border-[#8B7E66]/40 text-[#8B7E66] font-sans font-bold px-2 py-0.5 rounded-none uppercase tracking-wider">
                Active Audit
              </span>
            </div>

            {/* Gap cards */}
            <div className="space-y-4">
              {trainingGaps.map((gap) => (
                <div key={gap.id} className="border border-[#1A1A1A]/10 bg-white rounded-none p-5 space-y-3">
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <span className="bg-[#FAF8F6] border border-[#1A1A1A]/10 text-[#1A1A1A]/60 font-sans font-bold text-[8px] px-2 py-0.5 rounded-none uppercase tracking-wider">
                        {gap.category}
                      </span>
                      <h4 className="text-sm font-serif italic font-medium text-[#1A1A1A] mt-1.5 leading-tight">{gap.title}</h4>
                    </div>
                    <span className={`text-[9px] font-sans font-bold px-2 py-0.5 rounded-none uppercase tracking-wider ${
                      gap.urgency === 'Urgent' 
                        ? 'bg-[#F9EAE6] border border-[#A34E36]/30 text-[#A34E36]' 
                        : 'bg-[#FAF8F6] border border-[#8B7E66]/30 text-[#8B7E66]'
                    }`}>
                      {gap.urgency}
                    </span>
                  </div>

                  <p className="text-xs text-[#1A1A1A]/60 leading-relaxed font-sans">
                    {gap.description}
                  </p>

                  <div className="pt-2">
                    <button
                      onClick={() => handleAssign(gap.id)}
                      className={`w-full py-2.5 rounded-none text-xs font-sans uppercase tracking-widest cursor-pointer transition-colors flex items-center justify-center gap-1.5 border ${
                        gap.assigned
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                          : 'bg-[#1A1A1A] text-white border-transparent hover:bg-[#8B7E66]'
                      }`}
                    >
                      {gap.assigned ? (
                        <>
                          <Check className="w-3.5 h-3.5" />
                          <span>Remediation Assigned</span>
                        </>
                      ) : (
                        <>
                          <BookOpen className="w-3.5 h-3.5" />
                          <span>Assign Training Module</span>
                        </>
                      )}
                    </button>
                    {showAssignSuccess === gap.id && (
                      <p className="text-[9px] text-emerald-700 font-sans uppercase tracking-wider text-center mt-1.5 animate-pulse">
                        Course Assigned Successfully!
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Audit Meta Footer */}
        <div className="bg-white border border-[#1A1A1A]/10 rounded-none p-4 flex items-center gap-3 mt-6 select-none text-left">
          <Activity className="w-4 h-4 text-[#8B7E66] shrink-0" />
          <p className="text-[10px] text-[#1A1A1A]/50 font-sans uppercase tracking-wider leading-relaxed">
            Clinical audits run continuously on background audio transcripts. Data refreshed 5 minutes ago.
          </p>
        </div>
      </div>
    </div>
  );
}
