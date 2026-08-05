/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export interface TranscriptTurn {
  id: string;
  speaker: 'agent' | 'patient';
  speakerName: string;
  timestamp: string;
  text: string;
  isCritical?: boolean;
  criticalBadge?: string;
  tags?: string[];
  warning?: string;
  aiCatch?: string;
  sopGap?: boolean;
}

export interface QAAlert {
  id: string;
  title: string;
  description: string;
  severity: 'critical' | 'warning' | 'info';
  status: 'active' | 'resolved';
  recordingId: string;
  recordingName: string;
  dieticianName: string;
  date?: string;
  patientName?: string;
}

export interface Recording {
  id: string;
  name: string;
  patientName: string;
  agentName: string;
  duration: string;
  date: string;
  status: 'completed' | 'processing' | 'waiting';
  progress: number;
  statusText: string;
  sopCompliant: boolean;
  sopComplianceScore: number;
  scores: {
    greeting: number;
    empathy: number;
    compliance: number;
    technical: number;
  };
  qaAlerts: QAAlert[];
  transcript: TranscriptTurn[];
  recording_url?: string;
  entities?: Record<string, string>;
  insights: {
    whatWentWell: string[];
    areasForImprovement: string[];
    summary: string;
  };
}

export interface DieticianQAAlert {
  id: string;
  title: string;
  description: string;
  callCount: number;
  totalCalls: number;
  callFrequency: string;   // e.g. "5/6 calls"
  severity: 'critical' | 'warning' | 'info';
}

export interface Dietician {
  id: string;
  initials: string;
  name: string;
  role: string;
  avgScore: number;
  avgComplianceScore?: number;
  trend: string;
  trendDirection: 'up' | 'down' | 'flat';
  trendValues: number[];
  sopBreaches: number;
  totalAlertTypes?: number;
  totalCalls?: number;
  aiStatus: 'Exceeding Goals' | 'Training Required' | 'Stability Alert' | 'Target Met';
  qaAlerts?: DieticianQAAlert[];
}

export interface TrainingGap {
  id: string;
  title: string;
  description: string;
  category: string;
  urgency: string;
  assigned: boolean;
  type: 'compliance' | 'soft_skills';
}

export interface TeamMember {
  id: string;
  name: string;
  role: string;
  status: 'Active' | 'Offline' | 'Suspended';
  initials: string;
}

export interface SystemSettings {
  accountProfile: {
    name: string;
    role: string;
    email: string;
    avatar: string;
  };
  rubricWeights: {
    nutritionalAccuracy: number;
    patientEmpathy: number;
    sopAdherence: number;
    actionPlanClarity: number;
  };
  platformPreferences: {
    dataRetentionPolicy: string;
    qaAlertTriggers: number;
    defaultTimezone: string;
    primaryLanguage: string;
  };
  teamMembers: TeamMember[];
}
