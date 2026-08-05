import React, { useState } from 'react';
import {
  Save,
  RotateCcw,
  CheckCircle,
  Users,
  Settings,
  Scale,
  ShieldCheck,
  UserPlus,
  Trash2
} from 'lucide-react';
import { SystemSettings, TeamMember } from '../types';

interface SettingsViewProps {
  settings: SystemSettings;
  onSaveSettings: (updatedSettings: SystemSettings) => void;
  onResetSettings: () => void;
}

export default function SettingsView({
  settings,
  onSaveSettings,
  onResetSettings
}: SettingsViewProps) {
  const [profileName, setProfileName] = useState(settings.accountProfile.name);
  const [profileRole, setProfileRole] = useState(settings.accountProfile.role);
  const [profileEmail, setProfileEmail] = useState(settings.accountProfile.email);

  const [nutritionalWeight, setNutritionalWeight] = useState(settings.rubricWeights.nutritionalAccuracy);
  const [empathyWeight, setEmpathyWeight] = useState(settings.rubricWeights.patientEmpathy);
  const [sopWeight, setSopWeight] = useState(settings.rubricWeights.sopAdherence);
  const [clarityWeight, setClarityWeight] = useState(settings.rubricWeights.actionPlanClarity);

  const [retentionPolicy, setRetentionPolicy] = useState(settings.platformPreferences.dataRetentionPolicy);
  const [triggerThreshold, setTriggerThreshold] = useState(settings.platformPreferences.qaAlertTriggers);
  const [timezone, setTimezone] = useState(settings.platformPreferences.defaultTimezone);

  const [teamMembers, setTeamMembers] = useState<TeamMember[]>(settings.teamMembers);
  const [showNotification, setShowNotification] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const updated: SystemSettings = {
      accountProfile: {
        name: profileName,
        role: profileRole,
        email: profileEmail,
        avatar: settings.accountProfile.avatar
      },
      rubricWeights: {
        nutritionalAccuracy: nutritionalWeight,
        patientEmpathy: empathyWeight,
        sopAdherence: sopWeight,
        actionPlanClarity: clarityWeight
      },
      platformPreferences: {
        dataRetentionPolicy: retentionPolicy,
        qaAlertTriggers: triggerThreshold,
        defaultTimezone: timezone,
        primaryLanguage: settings.platformPreferences.primaryLanguage
      },
      teamMembers: teamMembers
    };
    onSaveSettings(updated);
    setShowNotification(true);
    setTimeout(() => {
      setShowNotification(false);
    }, 3000);
  };

  const handleReset = () => {
    onResetSettings();
    setProfileName(settings.accountProfile.name);
    setProfileRole(settings.accountProfile.role);
    setProfileEmail(settings.accountProfile.email);
    setNutritionalWeight(settings.rubricWeights.nutritionalAccuracy);
    setEmpathyWeight(settings.rubricWeights.patientEmpathy);
    setSopWeight(settings.rubricWeights.sopAdherence);
    setClarityWeight(settings.rubricWeights.actionPlanClarity);
    setRetentionPolicy(settings.platformPreferences.dataRetentionPolicy);
    setTriggerThreshold(settings.platformPreferences.qaAlertTriggers);
    setTimezone(settings.platformPreferences.defaultTimezone);
    setTeamMembers(settings.teamMembers);
  };

  const toggleTeamStatus = (memberId: string) => {
    const updated = teamMembers.map((m) => {
      if (m.id === memberId) {
        const nextStatus: 'Active' | 'Offline' | 'Suspended' = 
          m.status === 'Active' ? 'Offline' : m.status === 'Offline' ? 'Suspended' : 'Active';
        return { ...m, status: nextStatus };
      }
      return m;
    });
    setTeamMembers(updated);
  };

  const totalWeights = nutritionalWeight + empathyWeight + sopWeight + clarityWeight;

  return (
    <div className="flex-grow overflow-y-auto custom-scrollbar p-8 bg-[#F7F3F0] space-y-8 select-none">
      
      {/* Header and save status banner */}
      <section className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 border-b border-[#1A1A1A]/10 pb-6">
        <div>
          <span className="text-[10px] font-sans font-bold uppercase tracking-[0.3em] text-[#8B7E66]">System Control</span>
          <h2 className="text-3xl font-serif italic font-medium tracking-tight text-[#1A1A1A] mt-1">System Settings</h2>
          <p className="text-xs font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1">
            Configure QA scoring algorithms, auto-retention triggers, and review clinical team administrative accounts.
          </p>
        </div>
        
        {showNotification && (
          <div className="bg-emerald-50 border border-emerald-300 text-emerald-800 px-4 py-2.5 rounded-none text-xs font-sans uppercase tracking-wider flex items-center gap-2 shadow-sm animate-bounce">
            <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>Preferences Saved Successfully!</span>
          </div>
        )}
      </section>

      <form onSubmit={handleSave} className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left main forms columns */}
        <div className="lg:col-span-8 space-y-8">
          
          {/* Card 1: Account Profile */}
          <div className="bg-white border border-[#1A1A1A]/10 rounded-none p-6 space-y-6 shadow-sm">
            <div className="flex items-center gap-2 border-b border-[#1A1A1A]/10 pb-3">
              <Settings className="w-4.5 h-4.5 text-[#8B7E66]" />
              <h3 className="text-[10px] font-sans font-bold tracking-widest text-[#1A1A1A] uppercase">Account Profile</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="space-y-1.5 flex flex-col">
                <label className="text-[10px] font-sans font-bold text-[#1A1A1A]/50 uppercase tracking-wider">Full Name</label>
                <input
                  type="text"
                  value={profileName}
                  onChange={(e) => setProfileName(e.target.value)}
                  className="w-full bg-[#FAF8F6] border border-[#1A1A1A]/15 rounded-none px-4 py-2.5 text-sm text-[#1A1A1A] font-sans focus:outline-none focus:border-[#8B7E66] transition-colors"
                  required
                />
              </div>

              <div className="space-y-1.5 flex flex-col">
                <label className="text-[10px] font-sans font-bold text-[#1A1A1A]/50 uppercase tracking-wider">Clinical Role</label>
                <input
                  type="text"
                  value={profileRole}
                  onChange={(e) => setProfileRole(e.target.value)}
                  className="w-full bg-[#FAF8F6] border border-[#1A1A1A]/15 rounded-none px-4 py-2.5 text-sm text-[#1A1A1A] font-sans focus:outline-none focus:border-[#8B7E66] transition-colors"
                  required
                />
              </div>

              <div className="space-y-1.5 md:col-span-2 flex flex-col">
                <label className="text-[10px] font-sans font-bold text-[#1A1A1A]/50 uppercase tracking-wider">Primary Email</label>
                <input
                  type="email"
                  value={profileEmail}
                  onChange={(e) => setProfileEmail(e.target.value)}
                  className="w-full bg-[#FAF8F6] border border-[#1A1A1A]/15 rounded-none px-4 py-2.5 text-sm text-[#1A1A1A] font-sans focus:outline-none focus:border-[#8B7E66] transition-colors"
                  required
                />
              </div>
            </div>
          </div>

          {/* Card 2: Clinical Rubric Weights */}
          <div className="bg-white border border-[#1A1A1A]/10 rounded-none p-6 space-y-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-[#1A1A1A]/10 pb-3">
              <div className="flex items-center gap-2">
                <Scale className="w-4.5 h-4.5 text-[#8B7E66]" />
                <h3 className="text-[10px] font-sans font-bold tracking-widest text-[#1A1A1A] uppercase">Clinical Rubric Weights</h3>
              </div>
              <span className={`text-[10px] font-sans font-bold uppercase tracking-wider px-3 py-1 rounded-none border ${totalWeights === 100 ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-[#F9EAE6] text-[#A34E36] border-[#A34E36]/30 animate-pulse'}`}>
                Sum: {totalWeights}% (Required: 100%)
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Slider 1 */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-[10px] font-sans font-bold uppercase tracking-wider">
                  <span className="text-[#1A1A1A]/70">Nutritional Accuracy</span>
                  <span className="text-[#8B7E66] font-mono">{nutritionalWeight}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={nutritionalWeight}
                  onChange={(e) => setNutritionalWeight(parseInt(e.target.value))}
                  className="w-full h-1 bg-[#1A1A1A]/10 rounded-none appearance-none accent-[#1A1A1A] cursor-pointer"
                />
              </div>

              {/* Slider 2 */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-[10px] font-sans font-bold uppercase tracking-wider">
                  <span className="text-[#1A1A1A]/70">Patient Empathy</span>
                  <span className="text-[#8B7E66] font-mono">{empathyWeight}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={empathyWeight}
                  onChange={(e) => setEmpathyWeight(parseInt(e.target.value))}
                  className="w-full h-1 bg-[#1A1A1A]/10 rounded-none appearance-none accent-[#1A1A1A] cursor-pointer"
                />
              </div>

              {/* Slider 3 */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-[10px] font-sans font-bold uppercase tracking-wider">
                  <span className="text-[#1A1A1A]/70">SOP Adherence</span>
                  <span className="text-[#8B7E66] font-mono">{sopWeight}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={sopWeight}
                  onChange={(e) => setSopWeight(parseInt(e.target.value))}
                  className="w-full h-1 bg-[#1A1A1A]/10 rounded-none appearance-none accent-[#1A1A1A] cursor-pointer"
                />
              </div>

              {/* Slider 4 */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-[10px] font-sans font-bold uppercase tracking-wider">
                  <span className="text-[#1A1A1A]/70">Action Plan Clarity</span>
                  <span className="text-[#8B7E66] font-mono">{clarityWeight}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={clarityWeight}
                  onChange={(e) => setClarityWeight(parseInt(e.target.value))}
                  className="w-full h-1 bg-[#1A1A1A]/10 rounded-none appearance-none accent-[#1A1A1A] cursor-pointer"
                />
              </div>
            </div>
          </div>

          {/* Card 3: Platform Preferences */}
          <div className="bg-white border border-[#1A1A1A]/10 rounded-none p-6 space-y-6 shadow-sm">
            <div className="flex items-center gap-2 border-b border-[#1A1A1A]/10 pb-3">
              <ShieldCheck className="w-4.5 h-4.5 text-[#8B7E66]" />
              <h3 className="text-[10px] font-sans font-bold tracking-widest text-[#1A1A1A] uppercase">Platform Preferences</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div className="space-y-1.5 flex flex-col">
                <label className="text-[10px] font-sans font-bold text-[#1A1A1A]/50 uppercase tracking-wider">Data Retention Policy</label>
                <select
                  value={retentionPolicy}
                  onChange={(e) => setRetentionPolicy(e.target.value)}
                  className="w-full bg-[#FAF8F6] border border-[#1A1A1A]/15 rounded-none px-4 py-2.5 text-sm text-[#1A1A1A] font-sans font-medium focus:outline-none focus:border-[#8B7E66] cursor-pointer"
                >
                  <option value="6 Months">6 Months</option>
                  <option value="1 Year">1 Year</option>
                  <option value="3 Years">3 Years</option>
                  <option value="Indefinite">Indefinite</option>
                </select>
              </div>

              <div className="space-y-1.5 flex flex-col">
                <label className="text-[10px] font-sans font-bold text-[#1A1A1A]/50 uppercase tracking-wider">QA Trigger Threshold (%)</label>
                <input
                  type="number"
                  min="50"
                  max="100"
                  value={triggerThreshold}
                  onChange={(e) => setTriggerThreshold(parseInt(e.target.value))}
                  className="w-full bg-[#FAF8F6] border border-[#1A1A1A]/15 rounded-none px-4 py-2.5 text-sm text-[#1A1A1A] font-sans font-medium focus:outline-none focus:border-[#8B7E66]"
                />
              </div>

              <div className="space-y-1.5 flex flex-col">
                <label className="text-[10px] font-sans font-bold text-[#1A1A1A]/50 uppercase tracking-wider">Default Timezone</label>
                <select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-full bg-[#FAF8F6] border border-[#1A1A1A]/15 rounded-none px-4 py-2.5 text-sm text-[#1A1A1A] font-sans font-medium focus:outline-none focus:border-[#8B7E66] cursor-pointer"
                >
                  <option value="EST (Eastern Standard Time)">EST (Eastern Time)</option>
                  <option value="CST (Central Standard Time)">CST (Central Time)</option>
                  <option value="PST (Pacific Standard Time)">PST (Pacific Time)</option>
                  <option value="UTC">UTC (Coordinated Universal Time)</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Right Admin list sidebar - Team & Permissions */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-white border border-[#1A1A1A]/10 rounded-none p-6 space-y-6 shadow-sm h-full flex flex-col justify-between">
            <div className="space-y-5">
              <div className="flex items-center justify-between border-b border-[#1A1A1A]/10 pb-3">
                <div className="flex items-center gap-2">
                  <Users className="w-4.5 h-4.5 text-[#8B7E66]" />
                  <h3 className="text-[10px] font-sans font-bold tracking-widest text-[#1A1A1A] uppercase">Team & Access</h3>
                </div>
                <button 
                  type="button" 
                  className="p-1.5 text-[#1A1A1A]/50 hover:text-[#8B7E66] rounded-none hover:bg-[#FAF8F6] transition-colors"
                  title="Add team member"
                >
                  <UserPlus className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-3.5">
                {teamMembers.map((member) => (
                  <div key={member.id} className="flex items-center justify-between p-3 rounded-none bg-[#FAF8F6]/50 border border-[#1A1A1A]/5">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-8 h-8 rounded-none bg-white border border-[#1A1A1A]/10 text-[#1A1A1A] font-mono font-bold text-xs flex items-center justify-center shrink-0">
                        {member.initials}
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-serif italic font-medium text-[#1A1A1A] truncate">{member.name}</p>
                        <p className="text-[9px] text-[#1A1A1A]/50 font-sans uppercase tracking-wider truncate mt-0.5">{member.role}</p>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => toggleTeamStatus(member.id)}
                      className={`px-2 py-0.5 text-[9px] font-sans font-bold uppercase tracking-wider rounded-none border cursor-pointer transition-colors ${
                        member.status === 'Active'
                          ? 'bg-[#EAF3EA] border-emerald-300 text-emerald-800'
                          : member.status === 'Offline'
                          ? 'bg-white border-[#1A1A1A]/10 text-[#1A1A1A]/60'
                          : 'bg-[#F9EAE6] border-[#A34E36]/30 text-[#A34E36]'
                      }`}
                      title="Click to cycle status"
                    >
                      {member.status}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Bottom Actions inside Sidebar */}
            <div className="pt-8 border-t border-[#1A1A1A]/10 space-y-3">
              <button
                type="submit"
                className="w-full bg-[#1A1A1A] text-white hover:bg-[#8B7E66] py-3.5 rounded-none text-xs font-sans uppercase tracking-widest shadow-sm transition-colors cursor-pointer"
              >
                <Save className="w-4 h-4 inline mr-1.5 align-text-bottom" />
                <span>Save Preferences</span>
              </button>
              
              <button
                type="button"
                onClick={handleReset}
                className="w-full border border-[#1A1A1A]/25 text-[#1A1A1A] hover:bg-[#FAF8F6] py-3.5 rounded-none text-xs font-sans uppercase tracking-widest transition-colors cursor-pointer"
              >
                <RotateCcw className="w-4 h-4 inline mr-1.5 align-text-bottom" />
                <span>Reset Defaults</span>
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
