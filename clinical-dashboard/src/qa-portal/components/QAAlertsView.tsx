import React, { useState } from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  Info,
  CheckCircle,
  FileText,
  User,
  Calendar,
  Filter,
  CheckSquare,
  ArrowRight,
  ShieldCheck,
  RotateCcw
} from 'lucide-react';
import { QAAlert } from '../types';

interface QAAlertsViewProps {
  alerts: QAAlert[];
  onSelectCall: (id: string) => void;
  onToggleAlertStatus: (id: string) => void;
  searchQuery: string;
}

export default function QAAlertsView({
  alerts,
  onSelectCall,
  onToggleAlertStatus,
  searchQuery
}: QAAlertsViewProps) {
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const filteredAlerts = alerts.filter((alert) => {
    // Search query matches dietician, title or description
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matches = 
        alert.title.toLowerCase().includes(q) ||
        alert.description.toLowerCase().includes(q) ||
        alert.dieticianName.toLowerCase().includes(q) ||
        alert.recordingName.toLowerCase().includes(q);
      if (!matches) return false;
    }

    // Severity filter
    if (severityFilter !== 'all' && alert.severity !== severityFilter) {
      return false;
    }

    // Status filter
    if (statusFilter !== 'all' && alert.status !== statusFilter) {
      return false;
    }

    return true;
  });

  return (
    <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar p-8 space-y-8 bg-[#F7F3F0] select-none h-full">
      {/* Header section */}
      <section className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1A1A1A]/10 pb-6">
        <div>
          <span className="text-[10px] font-sans font-bold uppercase tracking-[0.3em] text-[#8B7E66]">Compliance Audit</span>
          <h2 className="text-3xl font-serif italic font-medium tracking-tight text-[#1A1A1A] mt-1">Clinical QA Compliance Alerts</h2>
          <p className="text-xs font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1">
            Real-time tracking of standard operating procedure (SOP) gaps and medical safety protocols.
          </p>
        </div>

        {/* Action controls */}
        <div className="flex gap-3">
          {/* Severity filter */}
          <div className="flex items-center gap-2 bg-white border border-[#1A1A1A]/15 px-3.5 py-2 rounded-none text-[10px] font-sans uppercase tracking-wider shadow-sm">
            <Filter className="w-3.5 h-3.5 text-[#1A1A1A]/60" />
            <span className="text-[#1A1A1A]/60">Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-transparent focus:outline-none text-[#1A1A1A] cursor-pointer font-bold uppercase tracking-wider"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
          </div>

          {/* Status filter */}
          <div className="flex items-center gap-2 bg-white border border-[#1A1A1A]/15 px-3.5 py-2 rounded-none text-[10px] font-sans uppercase tracking-wider shadow-sm">
            <CheckSquare className="w-3.5 h-3.5 text-[#1A1A1A]/60" />
            <span className="text-[#1A1A1A]/60">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent focus:outline-none text-[#1A1A1A] cursor-pointer font-bold uppercase tracking-wider"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active Breach</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>
      </section>

      {/* Grid containing alerts */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAlerts.length === 0 ? (
          <div className="col-span-full bg-white border border-[#1A1A1A]/10 rounded-none p-12 text-center flex flex-col justify-center items-center">
            <ShieldCheck className="w-12 h-12 text-emerald-600 mb-4" />
            <h3 className="text-base font-serif italic font-medium text-[#1A1A1A]">Compliance Clear!</h3>
            <p className="text-xs text-[#1A1A1A]/60 mt-1.5 max-w-sm font-sans leading-relaxed">
              No active QA breaches match the selected filters. Great job upholding clinical standard operating procedures!
            </p>
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            const isResolved = alert.status === 'resolved';
            const isCritical = alert.severity === 'critical';
            return (
              <div
                key={alert.id}
                className={`bg-white border rounded-none p-5 flex flex-col justify-between shadow-sm hover:shadow-md transition-shadow duration-200 relative overflow-hidden ${
                  isResolved 
                    ? 'border-[#1A1A1A]/10 opacity-70' 
                    : isCritical 
                    ? 'border-[#A34E36]/30 ring-1 ring-[#A34E36]/5' 
                    : 'border-[#1A1A1A]/15'
                }`}
              >
                {/* Severity header accent strip */}
                <div className={`absolute top-0 left-0 right-0 h-1 ${
                  isResolved 
                    ? 'bg-[#1A1A1A]/20' 
                    : isCritical 
                    ? 'bg-[#A34E36]' 
                    : alert.severity === 'warning' 
                    ? 'bg-amber-500' 
                    : 'bg-[#8B7E66]'
                }`}></div>

                <div>
                  <div className="flex justify-between items-center mb-3.5 pt-1.5">
                    <span className={`px-2 py-0.5 text-[9px] font-sans font-bold uppercase tracking-wider rounded-none border ${
                      isResolved
                        ? 'bg-[#FAF8F6] text-[#1A1A1A]/60 border-[#1A1A1A]/10'
                        : isCritical
                        ? 'bg-[#F9EAE6] text-[#A34E36] border-[#A34E36]/20'
                        : alert.severity === 'warning'
                        ? 'bg-amber-50 text-amber-800 border-amber-200'
                        : 'bg-[#FAF8F6] text-[#8B7E66] border-[#8B7E66]/20'
                    }`}>
                      {isResolved ? 'Resolved' : alert.severity}
                    </span>
                    <span className="text-[10px] font-mono text-[#1A1A1A]/50">{alert.date}</span>
                  </div>

                  <h3 className={`font-serif italic font-medium text-base text-[#1A1A1A] leading-tight ${isResolved ? 'line-through text-[#1A1A1A]/40' : ''}`}>
                    {alert.title}
                  </h3>
                  <p className="text-xs text-[#1A1A1A]/60 font-sans leading-relaxed mt-2.5">
                    {alert.description}
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-[#1A1A1A]/10 space-y-4">
                  {/* Linked dietician and file meta */}
                  <div className="flex justify-between items-center text-[10px] font-sans uppercase tracking-wider text-[#1A1A1A]/60">
                    <div className="flex items-center gap-1">
                      <User className="w-3.5 h-3.5 text-[#1A1A1A]/40" />
                      <span className="truncate max-w-[100px]">{alert.dieticianName}</span>
                    </div>
                    <div className="flex items-center gap-1 cursor-pointer hover:text-[#8B7E66] truncate max-w-[140px]" onClick={() => onSelectCall(alert.recordingId)}>
                      <FileText className="w-3.5 h-3.5 shrink-0 text-[#1A1A1A]/40" />
                      <span className="truncate">{alert.recordingName}</span>
                    </div>
                  </div>

                  {/* Actions row */}
                  <div className="grid grid-cols-2 gap-2 pt-1">
                    <button
                      onClick={() => onToggleAlertStatus(alert.id)}
                      className={`py-2 rounded-none text-[10px] font-sans uppercase tracking-widest cursor-pointer transition-colors flex items-center justify-center gap-1.5 border ${
                        isResolved
                          ? 'bg-[#FAF8F6] hover:bg-white border-[#1A1A1A]/10 text-[#1A1A1A]'
                          : 'bg-[#F9EAE6] hover:bg-white border-[#A34E36]/20 text-[#A34E36]'
                      }`}
                    >
                      {isResolved ? (
                        <>
                          <RotateCcw className="w-3 h-3" />
                          <span>Re-open</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-3 h-3" />
                          <span>Resolve</span>
                        </>
                      )}
                    </button>

                    <button
                      onClick={() => onSelectCall(alert.recordingId)}
                      className="py-2 rounded-none bg-[#1A1A1A] text-white hover:bg-[#8B7E66] border border-transparent text-[10px] font-sans uppercase tracking-widest flex items-center justify-center gap-1 cursor-pointer shadow-sm transition-colors"
                    >
                      <span>Audit</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </section>
    </div>
  );
}
