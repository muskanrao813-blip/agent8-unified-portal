import React from 'react';
import {
  LayoutDashboard,
  UploadCloud,
  FileText,
  Brain,
  FileBarChart2,
  AlertTriangle,
  Plus
} from 'lucide-react';

interface SidebarProps {
  currentView: string;
  onViewChange: (view: string) => void;
  onTriggerUpload: () => void;
  activeProcessingCount: number;
}

export default function Sidebar({
  currentView,
  onViewChange,
  onTriggerUpload,
  activeProcessingCount
}: SidebarProps) {
  const menuItems = [
    { id: 'dashboard', name: 'Dashboard', icon: LayoutDashboard },
    { id: 'upload', name: 'Call Upload', icon: UploadCloud, badge: activeProcessingCount > 0 ? activeProcessingCount : undefined },
    { id: 'transcriptions', name: 'Transcriptions', icon: FileText },
    { id: 'insights', name: 'AI Insights', icon: Brain },
    { id: 'reports', name: 'Dietician Reports', icon: FileBarChart2 },
    { id: 'alerts', name: 'QA Alerts', icon: AlertTriangle },
  ];

  return (
    <aside className="w-64 border-r border-[#1A1A1A]/10 bg-[#FAF8F6] flex flex-col h-full shrink-0 select-none">
      <div className="px-6 py-8 border-b border-[#1A1A1A]/10">
        <span className="text-[9px] font-sans font-bold uppercase tracking-[0.4em] text-[#8B7E66] block mb-1">Clinical Journal</span>
        <h1 className="text-2xl font-serif italic tracking-tight font-medium text-[#1A1A1A]">CallAnalytics AI</h1>
        <p className="text-[10px] font-sans uppercase tracking-[0.2em] text-[#1A1A1A]/60 mt-1">Clinical Precision</p>
      </div>

      <nav className="flex-1 py-4 space-y-[2px] overflow-y-auto custom-scrollbar">
        {menuItems.map((item) => {
          const IconComponent = item.icon;
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`w-full flex items-center justify-between px-6 py-3.5 transition-all duration-200 group text-left border-l-[3px] ${
                isActive
                  ? 'border-[#8B7E66] bg-white text-[#1A1A1A] font-semibold'
                  : 'border-transparent text-[#1A1A1A]/70 hover:bg-white hover:text-[#1A1A1A]'
              }`}
            >
              <div className="flex items-center gap-3">
                <IconComponent
                  className={`w-4 h-4 transition-transform duration-200 group-hover:scale-105 ${
                    isActive ? 'text-[#8B7E66]' : 'text-[#1A1A1A]/50 group-hover:text-[#1A1A1A]'
                  }`}
                />
                <span className="text-xs font-sans uppercase tracking-wider">{item.name}</span>
              </div>
              {item.badge !== undefined && (
                <span className="px-1.5 py-0.5 text-[9px] font-mono font-bold bg-[#8B7E66] text-white">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-[#1A1A1A]/10 bg-[#FAF8F6]">
        <button
          onClick={onTriggerUpload}
          className="w-full bg-[#1A1A1A] text-white py-3 rounded-none font-sans uppercase tracking-[0.15em] text-xs font-bold flex items-center justify-center gap-2 hover:bg-[#8B7E66] active:scale-[0.98] transition-all duration-200 cursor-pointer shadow-sm"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Upload Audio</span>
        </button>
      </div>
    </aside>
  );
}
