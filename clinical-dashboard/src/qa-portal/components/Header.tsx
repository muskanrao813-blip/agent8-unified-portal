import React, { useState } from 'react';
import { Search, Bell, HelpCircle, X } from 'lucide-react';
import { SystemSettings, QAAlert } from '../types';

interface HeaderProps {
  currentView: string;
  settings: SystemSettings;
  searchQuery: string;
  onSearchQueryChange: (query: string) => void;
  criticalAlerts?: QAAlert[];
}

export default function Header({
  currentView,
  settings,
  searchQuery,
  onSearchQueryChange,
  criticalAlerts = [],
}: HeaderProps) {
  const [showNotifs, setShowNotifs] = useState(false);
  // Get contextual header title or search placeholder
  const getSearchPlaceholder = () => {
    switch (currentView) {
      case 'dashboard':
        return 'Search analytics, dieticians, or QA tags...';
      case 'upload':
        return 'Search files, active uploads, or transcripts...';
      case 'transcriptions':
        return 'Search patient transcripts or recording IDs...';
      case 'insights':
        return 'Search call performance analyses...';
      case 'reports':
        return 'Search dieticians, active staff, or training reports...';
      case 'alerts':
        return 'Search compliance alerts, severity, or SOP rules...';
      case 'settings':
        return 'Search settings and preferences...';
      default:
        return 'Search analytics portal...';
    }
  };

  const getBreadcrumb = () => {
    switch (currentView) {
      case 'dashboard':
        return 'Executive Performance Overview';
      case 'upload':
        return 'Call Upload & Ingestion';
      case 'transcriptions':
        return 'Clinical Transcriptions';
      case 'insights':
        return 'Call Performance Analysis';
      case 'reports':
        return 'Performance & Training Report';
      case 'alerts':
        return 'QA Compliance Alerts';
      case 'settings':
        return 'System Settings';
      default:
        return 'Clinical Intelligence';
    }
  };

  return (
    <header className="h-16 border-b border-[#1A1A1A]/10 bg-white flex items-center justify-between px-8 sticky top-0 z-40 select-none">
      {/* Left side: Contextual search input */}
      <div className="flex items-center gap-6 flex-1 max-w-xl">
        <div className="relative w-full max-w-sm">
          <Search className="w-3.5 h-3.5 absolute left-1 top-1/2 -translate-y-1/2 text-[#1A1A1A]/50" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchQueryChange(e.target.value)}
            placeholder={getSearchPlaceholder()}
            className="w-full bg-transparent border-b border-[#1A1A1A]/10 pl-7 pr-7 py-1 text-xs text-[#1A1A1A] placeholder:text-[#1A1A1A]/40 focus:outline-none focus:border-[#8B7E66] transition-all"
          />
          {searchQuery && (
            <button onClick={() => onSearchQueryChange('')} className="absolute right-1 top-1/2 -translate-y-1/2 text-[#1A1A1A]/40 hover:text-[#A34E36]">
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
        <div className="h-6 w-[1px] bg-[#1A1A1A]/10 hidden sm:block"></div>
        <div className="hidden sm:flex items-center gap-2">
          <span className="text-sm font-serif italic text-[#1A1A1A]">{getBreadcrumb()}</span>
          <span className="bg-[#8B7E66] text-white text-[9px] font-sans font-bold px-1.5 py-0.5 tracking-widest uppercase">
            Internal
          </span>
        </div>
      </div>

      {/* Right side: Actions & User Info */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 relative">
          {/* Notification Bell */}
          <button
            onClick={() => setShowNotifs(v => !v)}
            className="text-[#1A1A1A]/60 hover:text-[#1A1A1A] p-2 rounded-none transition-all relative"
          >
            <Bell className="w-4 h-4" />
            {criticalAlerts.filter(a => a.status === 'active').length > 0 && (
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-[#A34E36] rounded-full"></span>
            )}
          </button>

          {/* Notification dropdown */}
          {showNotifs && (
            <div className="absolute top-10 right-0 w-80 bg-white border border-[#1A1A1A]/10 shadow-xl z-50">
              <div className="p-3 border-b border-[#1A1A1A]/10 flex justify-between items-center">
                <span className="text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]">
                  Active QA Alerts ({criticalAlerts.filter(a => a.status === 'active').length})
                </span>
                <button onClick={() => setShowNotifs(false)} className="text-[#1A1A1A]/40 hover:text-[#1A1A1A]">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
              <div className="max-h-72 overflow-y-auto">
                {criticalAlerts.filter(a => a.status === 'active').slice(0, 10).map((alert, idx) => (
                  <div key={`${alert.id}-${idx}`} className="p-3 border-b border-[#1A1A1A]/5 hover:bg-[#FAF8F6] cursor-pointer">
                    <div className="flex items-start gap-2">
                      <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${alert.severity === 'critical' ? 'bg-[#A34E36]' : 'bg-amber-500'}`}></span>
                      <div>
                        <p className="text-[11px] font-sans font-bold text-[#1A1A1A] leading-tight">{alert.title}</p>
                        <p className="text-[10px] text-[#1A1A1A]/50 mt-0.5">{alert.dieticianName} — {alert.patientName || alert.recordingName}</p>
                      </div>
                    </div>
                  </div>
                ))}
                {criticalAlerts.filter(a => a.status === 'active').length === 0 && (
                  <p className="p-4 text-xs text-[#1A1A1A]/40 text-center">No active alerts</p>
                )}
              </div>
            </div>
          )}

          <button className="text-[#1A1A1A]/60 hover:text-[#1A1A1A] p-2 rounded-none transition-all">
            <HelpCircle className="w-4 h-4" />
          </button>
        </div>

        <div className="h-8 w-[1px] bg-[#1A1A1A]/10"></div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden md:block">
            <p className="text-xs font-serif font-semibold text-[#1A1A1A] leading-tight">
              {settings.accountProfile.name}
            </p>
            <p className="text-[8px] font-sans font-bold text-[#8B7E66] uppercase tracking-widest">
              {settings.accountProfile.role}
            </p>
          </div>
          <div className="relative">
            {settings.accountProfile.avatar ? (
              <img
                src={settings.accountProfile.avatar}
                alt="User Portrait"
                className="w-9 h-9 rounded-none border border-[#1A1A1A]/20 p-[2px] bg-white object-cover shadow-none select-none"
                referrerPolicy="no-referrer"
              />
            ) : (
              <div className="w-9 h-9 rounded-none border border-[#1A1A1A]/20 bg-[#F7F3F0] flex items-center justify-center text-xs font-bold text-[#8B7E66]">
                {settings.accountProfile.name?.charAt(0) || 'U'}
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
