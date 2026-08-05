import { Recording, Dietician, TrainingGap, SystemSettings } from './types';

export const initialDieticians: Dietician[] = [
  {
    id: 'dr',
    initials: 'DR',
    name: 'David Richardson',
    role: 'Senior Clinical Dietician',
    avgScore: 96.8,
    trend: '+4.2%',
    trendDirection: 'up',
    trendValues: [2, 3, 5, 4, 6],
    sopBreaches: 0,
    aiStatus: 'Exceeding Goals'
  },
  {
    id: 'lm',
    initials: 'LM',
    name: 'Laura Martinez',
    role: 'General Staff',
    avgScore: 74.2,
    trend: '-8.1%',
    trendDirection: 'down',
    trendValues: [6, 4, 5, 3, 2],
    sopBreaches: 3,
    aiStatus: 'Training Required'
  },
  {
    id: 'sk',
    initials: 'SK',
    name: 'Simon Kalu',
    role: 'Clinical Associate',
    avgScore: 89.5,
    trend: 'Flat',
    trendDirection: 'flat',
    trendValues: [3, 4, 3, 4, 3],
    sopBreaches: 1,
    aiStatus: 'Stability Alert'
  },
  {
    id: 'eg',
    initials: 'EG',
    name: 'Elena Gomez',
    role: 'Lead Specialist',
    avgScore: 91.0,
    trend: '+1.5%',
    trendDirection: 'up',
    trendValues: [2, 3, 4, 5, 6],
    sopBreaches: 0,
    aiStatus: 'Target Met'
  }
];

export const initialTrainingGaps: TrainingGap[] = [
  {
    id: 'gap-1',
    title: 'High Incidence: Patient Privacy (HIPAA) Disclosures',
    description: '4 staff members showed inconsistent verification of patient IDs during start-of-call procedures. Recommend refresher on SOP Section 4.2.',
    category: 'Compliance',
    urgency: 'Urgent',
    assigned: false,
    type: 'compliance'
  },
  {
    id: 'gap-2',
    title: 'Empathy & Soft Skills Improvement',
    description: 'Sentiment analysis suggests tone variability in post-meal intake reviews. Opportunity for "Compassionate Feedback" training module.',
    category: 'Soft Skills',
    urgency: 'Mid-term',
    assigned: false,
    type: 'soft_skills'
  }
];

export const initialSettings: SystemSettings = {
  accountProfile: {
    name: 'Dr. Sarah Chen',
    role: 'Senior Clinical Lead',
    email: 's.chen@clinintel.ai',
    avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAzbFV1jqa2luGyK4qynF_N4sH8xcSlKXef5PZiUsXrykvs8PHhar56Rf_7CYisg9PFxaLF2wpDTOD-O5EgEWMYfTYm7mQA1jZVHSInRI3wQ_kkp3-KhXaMsXC1k4X9FcXmelW0p6jfKXNmbsZ6Ah_ARmwVnXy4zpGfytdtRfgBGdNwcSA_bZNKYsMV4CvV7sMPllUtPAkqMmXyCmSCSUwiJr10dzCHNNVwnQ9r2dmGfmgKET9uSB2b6w'
  },
  rubricWeights: {
    nutritionalAccuracy: 40,
    patientEmpathy: 25,
    sopAdherence: 20,
    actionPlanClarity: 15
  },
  platformPreferences: {
    dataRetentionPolicy: '1 Year',
    qaAlertTriggers: 70,
    defaultTimezone: 'EST (Eastern Standard Time)',
    primaryLanguage: 'English (US)'
  },
  teamMembers: [
    { id: 'tm-1', name: 'Mark K.', role: 'QA Manager', status: 'Active', initials: 'MK' },
    { id: 'tm-2', name: 'James T.', role: 'Analyst', status: 'Active', initials: 'JT' },
    { id: 'tm-3', name: 'Lisa S.', role: 'Dietician', status: 'Offline', initials: 'LS' },
    { id: 'tm-4', name: 'Rick D.', role: 'Admin', status: 'Suspended', initials: 'RD' }
  ]
};

export const initialRecordings: Recording[] = [
  {
    id: '88412',
    name: 'patient_visit_id_88412.wav',
    patientName: 'Mr. Henderson',
    agentName: 'David L.',
    duration: '08:42',
    date: '2023-11-24 14:30',
    status: 'completed',
    progress: 100,
    statusText: 'Ready for review',
    sopCompliant: false,
    sopComplianceScore: 42,
    scores: {
      greeting: 95,
      empathy: 88,
      compliance: 42,
      technical: 90
    },
    qaAlerts: [
      {
        id: 'alert-1',
        title: 'Mandatory HIPAA ID Verification Missed',
        description: 'The agent failed to request Date of Birth or Last 4 digits of SSN before proceeding with clinical device troubleshooting.',
        severity: 'critical',
        status: 'active',
        recordingId: '88412',
        recordingName: 'patient_visit_id_88412.wav',
        dieticianName: 'David L.',
        date: 'Nov 24, 2023'
      },
      {
        id: 'alert-2',
        title: 'Missing Closing Disclosure',
        description: 'Required \'Are there any other health concerns today?\' script was omitted during call wrap-up.',
        severity: 'critical',
        status: 'active',
        recordingId: '88412',
        recordingName: 'patient_visit_id_88412.wav',
        dieticianName: 'David L.',
        date: 'Nov 24, 2023'
      }
    ],
    transcript: [
      {
        id: 'turn-1',
        speaker: 'agent',
        speakerName: 'Agent (David L.)',
        timestamp: '00:00',
        text: 'Thank you for calling Clinical Care Network, my name is David. How can I assist you with your health management plan today?'
      },
      {
        id: 'turn-2',
        speaker: 'patient',
        speakerName: 'Patient (Mr. Henderson)',
        timestamp: '00:15',
        text: 'Hi David, I\'m calling because I received my new continuous glucose monitor yesterday, but I\'m having trouble syncing it with the mobile app on my phone.'
      },
      {
        id: 'turn-3',
        speaker: 'agent',
        speakerName: 'Agent (David L.)',
        timestamp: '00:32',
        text: 'Oh, I see. Let\'s look into that for you. What phone are you using?',
        sopGap: true,
        aiCatch: 'AI Catch: Agent failed to verify Patient DOB and Account ID before troubleshooting.'
      },
      {
        id: 'turn-4',
        speaker: 'patient',
        speakerName: 'Patient (Mr. Henderson)',
        timestamp: '00:45',
        text: 'I\'m using an iPhone 14 Pro. I\'ve turned Bluetooth off and on, but it just keeps searching and never finds the sensor.'
      },
      {
        id: 'turn-5',
        speaker: 'agent',
        speakerName: 'Agent (David L.)',
        timestamp: '01:10',
        text: 'Understood. Let\'s verify that the transmitter is fully clicked into the sensor guard. Sometimes it takes a little pressure to snap in.'
      },
      {
        id: 'turn-6',
        speaker: 'patient',
        speakerName: 'Patient (Mr. Henderson)',
        timestamp: '01:30',
        text: 'Ah, yes! I heard a click just now. Oh, wait, the phone screen just updated... It says "Transmitter Found"!'
      }
    ],
    insights: {
      whatWentWell: [
        'Exceptional use of active listening markers ("I understand", "Let me check that").',
        'Technical guidance regarding iPhone Bluetooth settings was accurate and easy for the patient to follow.'
      ],
      areasForImprovement: [
        'Speed up the identification phase; spent 2 minutes searching for patient profile without narrative explanation.',
        'Opportunity to cross-sell the new Diabetes Education Webinar given the patient\'s technical struggle.'
      ],
      summary: 'Patient called frustrated with hardware setup. Agent de-escalated well but skipped critical security protocols. Recommendation: Re-training on HIPAA Verification Module 2.'
    }
  },
  {
    id: '429',
    name: 'patient_visit_id_8829.wav',
    patientName: 'Jane Williams',
    agentName: 'Mark Roberts',
    duration: '14:22',
    date: '2023-10-24 10:15',
    status: 'completed',
    progress: 100,
    statusText: 'Ready for review',
    sopCompliant: true,
    sopComplianceScore: 92,
    scores: {
      greeting: 96,
      empathy: 94,
      compliance: 92,
      technical: 88
    },
    qaAlerts: [],
    transcript: [
      {
        id: 't-1',
        speaker: 'agent',
        speakerName: 'Mark Roberts',
        timestamp: '00:04',
        text: 'Hello, thank you for contacting the Clinical Support Line. My name is Mark. To ensure privacy, may I start by confirming your full name and date of birth?',
        tags: ['SOP: ID CONFIRMATION']
      },
      {
        id: 't-2',
        speaker: 'patient',
        speakerName: 'Jane Williams',
        timestamp: '00:15',
        text: 'Hi Mark, yes. It\'s Jane Williams, DOB January 14, 1978. I\'m calling regarding my recent lab results and some confusion about the insulin dosage.'
      },
      {
        id: 't-3',
        speaker: 'agent',
        speakerName: 'Mark Roberts',
        timestamp: '00:28',
        text: 'Understood, Ms. Williams. Let me pull that up. Based on the physician\'s notes from Tuesday, the units were adjusted from 10mg to 15mg. Are you currently feeling any dizziness or unusual fatigue after the last dose?',
        isCritical: true,
        criticalBadge: 'CRITICAL PROTOCOL',
        tags: ['SOP: SAFETY SCREENING', 'TIMESTAMP: 00:32']
      },
      {
        id: 't-4',
        speaker: 'patient',
        speakerName: 'Jane Williams',
        timestamp: '00:45',
        text: 'Actually, I have been feeling a bit shaky about an hour after the injection. Is that expected with the higher dose?',
        warning: 'Flagged: Potential Adverse Reaction'
      },
      {
        id: 't-5',
        speaker: 'agent',
        speakerName: 'Mark Roberts',
        timestamp: '01:05',
        text: 'Feeling shaky is a common symptom of low blood sugar, which can happen with a dosage increase. Have you been checking your levels?'
      },
      {
        id: 't-6',
        speaker: 'patient',
        speakerName: 'Jane Williams',
        timestamp: '01:22',
        text: 'Yes, it was around 72 mg/dL when I checked. I had some orange juice which helped.'
      }
    ],
    insights: {
      whatWentWell: [
        'Perfect execution of SOP identity confirmation protocols.',
        'Proper safety screening conducted immediately upon dosage discussion.'
      ],
      areasForImprovement: [
        'Provide clearer explanations of hypo-glycemic symptoms upfront.',
        'Slightly faster escalation path for adverse reactions.'
      ],
      summary: 'SOP compliant session. Patient called regarding confusion on adjusted insulin dosage. Identified potential adverse reaction (shakiness) and validated safety metrics. Corrective actions advised.'
    }
  },
  {
    id: '4922',
    name: 'CONS_4922_Sarah_K.mp3',
    patientName: 'Sarah K.',
    agentName: 'Dr. Eleanor Vance',
    duration: '11:15',
    date: '2023-10-24 14:15',
    status: 'completed',
    progress: 100,
    statusText: 'Ready for review',
    sopCompliant: true,
    sopComplianceScore: 98,
    scores: {
      greeting: 98,
      empathy: 100,
      compliance: 98,
      technical: 96
    },
    qaAlerts: [],
    transcript: [],
    insights: {
      whatWentWell: ['Excellent rapport building', 'Very high diagnostic confidence'],
      areasForImprovement: ['None identified'],
      summary: 'Perfect clinical consultation with clear action plan.'
    }
  },
  {
    id: '1102',
    name: 'INTK_1102_Mark_J.wav',
    patientName: 'Mark J.',
    agentName: 'Marcus Sterling',
    duration: '06:12',
    date: '2023-10-24 13:42',
    status: 'completed',
    progress: 100,
    statusText: 'Ready for review',
    sopCompliant: false,
    sopComplianceScore: 64,
    scores: {
      greeting: 70,
      empathy: 60,
      compliance: 64,
      technical: 80
    },
    qaAlerts: [
      {
        id: 'alert-3',
        title: 'Emergency Contact Verification Missed',
        description: 'Failed to verify secondary emergency contact during intake procedure.',
        severity: 'warning',
        status: 'active',
        recordingId: '1102',
        recordingName: 'INTK_1102_Mark_J.wav',
        dieticianName: 'Marcus Sterling',
        date: 'Oct 24, 2023'
      }
    ],
    transcript: [],
    insights: {
      whatWentWell: ['Good technical medical questioning'],
      areasForImprovement: ['Missed safety escalation triggers'],
      summary: 'SOP breach. Consultation completed without verifying secondary emergency contact details.'
    }
  },
  {
    id: '4919',
    name: 'CONS_4919_Liza_M.mp3',
    patientName: 'Liza M.',
    agentName: 'Dr. Julian Wu',
    duration: '09:30',
    date: '2023-10-24 11:30',
    status: 'completed',
    progress: 100,
    statusText: 'Ready for review',
    sopCompliant: true,
    sopComplianceScore: 91,
    scores: {
      greeting: 90,
      empathy: 92,
      compliance: 91,
      technical: 90
    },
    qaAlerts: [],
    transcript: [],
    insights: {
      whatWentWell: ['Accurate meal tracking review'],
      areasForImprovement: ['Spoke slightly too fast during guidelines discussion'],
      summary: 'Successful meal intake review, patient fully satisfied.'
    }
  }
];

export const initialActiveQueue: Recording[] = [
  {
    id: 'q-1',
    name: 'patient_visit_id_8829.wav',
    patientName: 'Jane Williams',
    agentName: 'Mark Roberts',
    duration: '14:22',
    date: 'Oct 24, 2023',
    status: 'processing',
    progress: 82,
    statusText: 'Identifying speakers...',
    sopCompliant: true,
    sopComplianceScore: 82,
    scores: { greeting: 0, empathy: 0, compliance: 0, technical: 0 },
    qaAlerts: [],
    transcript: [],
    insights: { whatWentWell: [], areasForImprovement: [], summary: '' }
  },
  {
    id: 'q-2',
    name: 'consultation_v4.mp3',
    patientName: 'Unassigned',
    agentName: 'Unassigned',
    duration: '05:10',
    date: 'Oct 24, 2023',
    status: 'waiting',
    progress: 0,
    statusText: 'Queued for AI summarization',
    sopCompliant: false,
    sopComplianceScore: 0,
    scores: { greeting: 0, empathy: 0, compliance: 0, technical: 0 },
    qaAlerts: [],
    transcript: [],
    insights: { whatWentWell: [], areasForImprovement: [], summary: '' }
  },
  {
    id: 'q-3',
    name: 'emergency_triage_992.wav',
    patientName: 'Unassigned',
    agentName: 'Unassigned',
    duration: '07:45',
    date: 'Oct 24, 2023',
    status: 'processing',
    progress: 14,
    statusText: 'Initial transcription phase',
    sopCompliant: false,
    sopComplianceScore: 0,
    scores: { greeting: 0, empathy: 0, compliance: 0, technical: 0 },
    qaAlerts: [],
    transcript: [],
    insights: { whatWentWell: [], areasForImprovement: [], summary: '' }
  }
];
