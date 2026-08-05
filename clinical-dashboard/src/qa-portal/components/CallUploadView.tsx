import React, { useState, useEffect } from 'react';
import {
  UploadCloud,
  Loader2,
  Clock,
  CheckCircle2,
  FileCheck2,
  ShieldCheck,
  AlertCircle,
  FileText,
  Zap,
  Activity
} from 'lucide-react';
import { Recording } from '../types';

interface CallUploadViewProps {
  activeQueue: Recording[];
  completedRecordings: Recording[];
  onSelectCall: (id: string) => void;
  onUploadFile: (fileName: string) => void;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function CallUploadView({
  activeQueue,
  onUploadFile
}: CallUploadViewProps) {
  const [dragOver, setDragOver] = useState<boolean>(false);
  const [dragOverExcel, setDragOverExcel] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadMessage, setUploadMessage] = useState<string>('');
  const [selectedAudioFiles, setSelectedAudioFiles] = useState<File[]>([]);
  const [ingestionQueue, setIngestionQueue] = useState<Recording[]>([]);

  // Poll ingestion queue every 2 seconds
  useEffect(() => {
    const fetchIngestionQueue = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/calls`);
        if (response.ok) {
          const data = await response.json();
          const recordings = data.map((call: any) => {
            // Determine progress based on status and timing
            let progress = 0;
            let statusText = '';

            if (call.status === 'pending') {
              progress = 5;
              statusText = 'Queued - Waiting';
            } else if (call.status === 'processing') {
              // Estimate progress based on time elapsed
              const createdTime = new Date(call.created_at).getTime();
              const elapsedMs = Date.now() - createdTime;
              const elapsedSecs = Math.floor(elapsedMs / 1000);

              if (elapsedSecs < 3) {
                progress = 15;
                statusText = 'Downloading audio...';
              } else if (elapsedSecs < 10) {
                progress = 35;
                statusText = 'Transcribing (Whisper)...';
              } else if (elapsedSecs < 20) {
                progress = 65;
                statusText = 'Analyzing (Claude)...';
              } else {
                progress = 85;
                statusText = 'Finalizing...';
              }
            } else if (call.status === 'completed') {
              progress = 100;
              statusText = 'Completed';
            } else if (call.status === 'failed') {
              progress = 100;
              statusText = 'Failed';
            }

            return {
              id: call.id,
              name: call.appointment_id || `Call ${call.id.substring(0, 8)}`,
              patientName: call.patient_name || 'Unknown',
              agentName: call.dietician_name || 'Unknown',
              duration: call.call_duration_seconds ? `${Math.floor(call.call_duration_seconds / 60)}:${String(call.call_duration_seconds % 60).padStart(2, '0')}` : '0:00',
              date: call.call_datetime ? new Date(call.call_datetime).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleDateString(),
              status: call.status || 'pending',
              progress: progress,
              statusText: statusText,
              sopCompliant: (call.overall_weighted_score || 0) >= 70,
              sopComplianceScore: call.overall_weighted_score || 0,
              scores: { greeting: 0, empathy: 0, compliance: 0, technical: 0 },
              qaAlerts: [],
              transcript: [],
              insights: { whatWentWell: [], areasForImprovement: [], summary: '' }
            };
          });
          setIngestionQueue(recordings);
        }
      } catch (error) {
        console.error('Failed to fetch ingestion queue:', error);
      }
    };

    const interval = setInterval(fetchIngestionQueue, 2000);
    fetchIngestionQueue(); // Initial fetch
    return () => clearInterval(interval);
  }, []);

  // Handle Drag & Drop events
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      onUploadFile(file.name);
    }
  };

  // Handle manual file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUploadFile(e.target.files[0].name);
    }
  };

  // Handle Excel file upload with optional audio files
  const handleExcelUpload = async (file: File) => {
    setUploading(true);
    const hasAudioFiles = selectedAudioFiles.length > 0;
    setUploadMessage(hasAudioFiles ? 'Uploading Excel and audio files...' : 'Uploading Excel file...');

    try {
      const formData = new FormData();

      if (hasAudioFiles) {
        // For upload-with-audio endpoint: use excel_file and audio_files
        formData.append('excel_file', file);
        selectedAudioFiles.forEach((audioFile) => {
          formData.append('audio_files', audioFile);
        });
        const response = await fetch(`${API_BASE_URL}/api/calls/upload-with-audio`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.statusText}`);
        }

        const data = await response.json();
        setUploadMessage(`Successfully uploaded! Processed ${data.valid_rows} rows. Batch ID: ${data.batch_id}`);
      } else {
        // For bulk-upload endpoint: use file parameter
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/calls/bulk-upload`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.statusText}`);
        }

        const data = await response.json();
        setUploadMessage(`Successfully uploaded! Processed ${data.valid_rows} rows. Batch ID: ${data.batch_id}`);
      }

      setSelectedAudioFiles([]);
      setTimeout(() => setUploadMessage(''), 5000);
    } catch (error) {
      setUploadMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setTimeout(() => setUploadMessage(''), 5000);
    } finally {
      setUploading(false);
    }
  };

  const handleExcelDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOverExcel(true);
  };

  const handleExcelDragLeave = () => {
    setDragOverExcel(false);
  };

  const handleExcelDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOverExcel(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        handleExcelUpload(file);
      } else {
        setUploadMessage('Please upload an Excel file (.xlsx or .xls)');
      }
    }
  };

  const handleExcelFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        handleExcelUpload(file);
      } else {
        setUploadMessage('Please upload an Excel file (.xlsx or .xls)');
      }
    }
  };

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar h-full bg-[#F7F3F0] p-8 select-none">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header Block */}
        <section className="border-b border-[#1A1A1A]/10 pb-6">
          <span className="text-[10px] font-sans font-bold uppercase tracking-[0.3em] text-[#8B7E66]">Ingestion Portal</span>
          <h2 className="text-3xl font-serif italic font-medium tracking-tight text-[#1A1A1A] mt-1">Upload Clinical Consultation</h2>
          <p className="text-xs font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1">
            Securely upload medical audio recordings for automated clinical transcription, compliance auditing, and performance scoring.
          </p>
        </section>

        {/* Dynamic Multi-Pane Layout */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
          
          {/* Left Block: Upload Zone */}
          <div className="md:col-span-7 bg-white border border-[#1A1A1A]/10 p-8 space-y-6">
            <div className="border-b border-[#1A1A1A]/5 pb-4">
              <h3 className="text-xs font-sans font-bold uppercase tracking-[0.15em] text-[#1A1A1A]">Audio Ingestion</h3>
              <p className="text-xs text-[#1A1A1A]/60 mt-1">Select or drag standard therapeutic conversation audio recordings.</p>
            </div>

            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`relative border border-dashed p-10 text-center transition-all duration-300 cursor-pointer ${
                dragOver 
                  ? 'border-[#8B7E66] bg-[#FAF8F6]' 
                  : 'border-[#1A1A1A]/20 hover:border-[#8B7E66] hover:bg-[#FAF8F6]/40'
              }`}
            >
              <input
                type="file"
                accept=".mp3,.wav,.flac"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              
              <div className="w-14 h-14 bg-[#FAF8F6] border border-[#1A1A1A]/10 flex items-center justify-center mx-auto mb-4 transition-transform duration-300">
                <UploadCloud className="w-6 h-6 text-[#8B7E66]" />
              </div>

              <h4 className="text-base font-serif italic font-medium text-[#1A1A1A]">Choose Audio File</h4>
              <p className="text-[10px] font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1.5">
                Drag & drop or browse your local system
              </p>
              <p className="text-[9px] text-[#1A1A1A]/40 font-mono mt-2">
                Supported formats: MP3, WAV, FLAC (Max 500MB)
              </p>
            </div>


            {/* Excel Bulk Upload Section */}
            <div className="border-t border-[#1A1A1A]/5 pt-6">
              <h3 className="text-xs font-sans font-bold uppercase tracking-[0.15em] text-[#1A1A1A] mb-4">Bulk Excel Upload with Audio</h3>

              <div className="space-y-3">
                {/* Excel File Input */}
                <div className="bg-white border border-[#1A1A1A]/10 p-4">
                  <label className="block text-xs font-sans font-bold uppercase tracking-wider text-[#1A1A1A] mb-2">
                    Step 1: Select Excel File
                  </label>
                  <input
                    id="excel-file-input"
                    type="file"
                    accept=".xlsx,.xls,.csv"
                    onChange={handleExcelFileChange}
                    className="block w-full text-sm text-gray-500
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-none file:border-0
                      file:text-sm file:font-semibold
                      file:bg-[#1A1A1A] file:text-white
                      hover:file:bg-[#8B7E66]
                      cursor-pointer"
                  />
                  <p className="text-xs text-[#1A1A1A]/60 mt-2">
                    Supported: XLSX, XLS, CSV files with call metadata
                  </p>
                </div>

                {/* Audio Files Input */}
                <div className="bg-white border border-[#1A1A1A]/10 p-4">
                  <label className="block text-xs font-sans font-bold uppercase tracking-wider text-[#1A1A1A] mb-2">
                    Step 2: Select Corresponding Audio Files (Optional)
                  </label>
                  <input
                    id="audio-files-input"
                    type="file"
                    multiple
                    accept=".mp3,.wav,.flac,.m4a,.ogg,.webm"
                    onChange={(e) => {
                      if (e.target.files) {
                        setSelectedAudioFiles(Array.from(e.target.files));
                      }
                    }}
                    className="block w-full text-sm text-gray-500
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-none file:border-0
                      file:text-sm file:font-semibold
                      file:bg-[#1A1A1A] file:text-white
                      hover:file:bg-[#8B7E66]
                      cursor-pointer"
                  />
                  <p className="text-xs text-[#1A1A1A]/60 mt-2">
                    Optional: Audio files will be matched by filename in Excel's recording_url column
                  </p>
                  {selectedAudioFiles.length > 0 && (
                    <div className="mt-3 bg-[#FAF8F6] p-3 rounded border border-[#8B7E66]/20">
                      <p className="text-xs font-semibold text-[#1A1A1A] mb-2">Selected Audio Files:</p>
                      <ul className="space-y-1 text-xs text-[#1A1A1A]/70">
                        {selectedAudioFiles.map((f, idx) => (
                          <li key={idx} className="flex items-center gap-2">
                            <span className="text-[#8B7E66]">•</span> {f.name}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Drag & Drop Area */}
                <div
                  onDragOver={handleExcelDragOver}
                  onDragLeave={handleExcelDragLeave}
                  onDrop={handleExcelDrop}
                  className={`border border-dashed p-6 text-center transition-all duration-300 ${
                    dragOverExcel
                      ? 'border-[#8B7E66] bg-[#FAF8F6]'
                      : 'border-[#1A1A1A]/20'
                  }`}
                >
                  <FileText className="w-8 h-8 text-[#8B7E66] mx-auto mb-2" />
                  <p className="text-sm text-[#1A1A1A] font-medium">Or drag Excel file here</p>
                </div>

                {/* Status Message */}
                {uploadMessage && (
                  <div className={`p-3 rounded text-sm font-mono ${
                    uploadMessage.includes('Error') || uploadMessage.includes('Please')
                      ? 'bg-red-50 text-red-700 border border-red-200'
                      : 'bg-green-50 text-green-700 border border-green-200'
                  }`}>
                    {uploadMessage}
                  </div>
                )}

                {uploading && (
                  <div className="bg-blue-50 border border-blue-200 text-blue-700 p-3 rounded text-sm">
                    Uploading... Please wait
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Block: Process Status Queue */}
          <div className="md:col-span-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[#1A1A1A]/10 pb-3">
              <h3 className="text-xs font-sans font-bold uppercase tracking-[0.15em] text-[#1A1A1A]">Ingestion Queue</h3>
              <span className="px-2.5 py-0.5 border border-[#8B7E66]/30 bg-white text-[#8B7E66] text-[10px] font-mono font-bold uppercase tracking-wider">
                {ingestionQueue.length} Total
              </span>
            </div>

            {ingestionQueue.length === 0 ? (
              <div className="bg-white border border-[#1A1A1A]/10 p-8 text-center flex flex-col items-center justify-center min-h-[220px]">
                <FileCheck2 className="w-10 h-10 text-[#1A1A1A]/20 mb-3" />
                <h4 className="text-sm font-serif italic font-medium text-[#1A1A1A]">Queue is empty</h4>
                <p className="text-[10px] font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1.5 max-w-[200px] leading-relaxed mx-auto">
                  No recordings in ingestion. Upload an Excel file with audio to begin processing.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {ingestionQueue.map((item) => {
                  const statusConfig: Record<string, { icon: React.ReactNode; color: string }> = {
                    pending: { icon: <Clock className="w-3 h-3" />, color: 'text-[#1A1A1A]/40' },
                    processing: { icon: <Zap className="w-3 h-3 animate-pulse" />, color: 'text-[#8B7E66]' },
                    completed: { icon: <CheckCircle2 className="w-3 h-3" />, color: 'text-green-600' },
                    failed: { icon: <AlertCircle className="w-3 h-3" />, color: 'text-red-600' }
                  };
                  const config = statusConfig[item.status] || statusConfig.pending;

                  return (
                    <div
                      key={item.id}
                      className="bg-white border border-[#1A1A1A]/10 p-4 space-y-3 shadow-sm hover:border-[#8B7E66] transition-colors"
                    >
                      {/* Header line */}
                      <div className="flex justify-between items-start gap-2">
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-serif font-semibold text-[#1A1A1A] truncate">{item.name}</p>
                          <p className="text-[9px] text-[#1A1A1A]/60 mt-0.5">Patient: {item.patientName} | Dietician: {item.agentName}</p>
                        </div>
                        <span className="text-[10px] font-mono font-bold text-[#8B7E66] shrink-0 whitespace-nowrap">
                          {item.progress}%
                        </span>
                      </div>

                      {/* Progress Bar */}
                      <div className="w-full bg-[#FAF8F6] border border-[#1A1A1A]/5 h-2 overflow-hidden">
                        <div
                          className={`h-full transition-all duration-500 ${
                            item.status === 'pending' ? 'bg-[#1A1A1A]/20' :
                            item.status === 'completed' ? 'bg-green-600' :
                            item.status === 'failed' ? 'bg-red-600' :
                            'bg-[#8B7E66]'
                          }`}
                          style={{ width: `${item.progress}%` }}
                        ></div>
                      </div>

                      {/* Status Text & Indicator */}
                      <div className="flex items-center justify-between text-[9px] font-sans font-bold uppercase tracking-wider">
                        <span className={`flex items-center gap-1.5 ${config.color}`}>
                          {config.icon}
                          <span className="truncate max-w-[200px]">{item.statusText}</span>
                        </span>
                        <span className="text-[#1A1A1A]/40">{item.date}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Ingestion Guidelines */}
            <div className="border border-[#1A1A1A]/10 p-4 space-y-2 bg-white">
              <div className="flex items-center gap-1.5 text-[#1A1A1A] mb-1">
                <AlertCircle className="w-3.5 h-3.5 text-[#8B7E66]" />
                <span className="text-[10px] font-sans font-bold uppercase tracking-wider">Troubleshooting Ingestion</span>
              </div>
              <ul className="space-y-1 text-[11px] text-[#1A1A1A]/60 leading-relaxed list-disc list-inside">
                <li>Processing times vary by audio length (~10s per minute).</li>
                <li>Ensure speaker clarity to maximize compliance score accuracy.</li>
                <li>Review finished consultations inside the Transcriptions tab.</li>
              </ul>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
