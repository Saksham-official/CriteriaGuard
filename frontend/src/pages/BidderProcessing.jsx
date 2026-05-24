import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import API_BASE_URL from '../api/config';

const BidderProcessing = () => {
  const { tenderId, bidderId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  // Bidder metadata from location state or fetched
  const [bidderName, setBidderName] = useState(location.state?.bidderName || 'Bidder Response');
  
  // Pipeline state
  const [status, setStatus] = useState('processing'); // processing, complete, failed
  const [currentStep, setCurrentStep] = useState('Initializing WebSocket connection...');
  const [documents, setDocuments] = useState([]); // Array of {label, text, filename}
  const [activeDocIndex, setActiveDocIndex] = useState(0);
  const [criteria, setCriteria] = useState([]);
  
  // Real-time LLM stream variables
  const [activeCriterionId, setActiveCriterionId] = useState(null);
  const [rawLogStream, setRawLogStream] = useState('');
  const [completedExtractions, setCompletedExtractions] = useState({}); // criterion_id -> { extraction, verdict }
  const [currentConfidence, setCurrentConfidence] = useState({ alignment: 0, authenticity: 0 });

  // Security Defense state
  const [scannedFiles, setScannedFiles] = useState([]); // Array of { filename, status, report }
  const [securityBreach, setSecurityBreach] = useState(null);

  // UI Refs
  const terminalEndRef = useRef(null);
  const wsRef = useRef(null);

  // Fetch approved criteria for the checklist on mount
  useEffect(() => {
    const fetchCriteria = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/tenders/${tenderId}/criteria`);
        // Filter approved criteria
        const approved = response.data.filter(c => c.approved_at !== null);
        setCriteria(approved);
      } catch (err) {
        console.error("Failed to fetch criteria:", err);
      }
    };
    fetchCriteria();
  }, [tenderId]);

  // WebSocket connection & lifecycle
  useEffect(() => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const cleanBaseUrl = API_BASE_URL.replace(/^http(s)?:\/\//, '');
    const wsUrl = `${wsProtocol}://${cleanBaseUrl}/ws/progress/${bidderId}`;

    console.log("Connecting to WebSocket:", wsUrl);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected.");
      setCurrentStep("Connected to pipeline. Listening for extraction streams...");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("WebSocket message received:", data.type);

      switch (data.type) {
        case 'status_update':
          setStatus(data.status);
          setCurrentStep(data.current_step);
          break;

        case 'security_scan':
          setScannedFiles(prev => {
            const index = prev.findIndex(item => item.filename === data.filename);
            if (index !== -1) {
              const updated = [...prev];
              updated[index] = { filename: data.filename, status: data.status, report: data.report };
              return updated;
            } else {
              return [...prev, { filename: data.filename, status: data.status, report: data.report }];
            }
          });
          if (data.status === 'failed') {
            setSecurityBreach(data.report);
            setStatus('failed');
            setCurrentStep("CRITICAL RISK SECURED: Adversarial Prompt Injection Blocked.");
          }
          break;

        case 'documents_extracted':
          setDocuments(data.documents || []);
          setActiveDocIndex(0);
          break;

        case 'criterion_start':
          setActiveCriterionId(data.criterion.id);
          setRawLogStream('');
          setCurrentConfidence({ alignment: 0, authenticity: 0 });
          break;

        case 'llm_token':
          setRawLogStream(prev => {
            const newStream = prev + data.token;
            
            // Try to extract metrics in real-time from the stream
            const alignmentMatch = newStream.match(/"alignment_score"\s*:\s*([0-9.]+)/);
            const authenticityMatch = newStream.match(/"authenticity_score"\s*:\s*([0-9.]+)/);
            
            setCurrentConfidence({
              alignment: alignmentMatch ? parseFloat(alignmentMatch[1]) : 0,
              authenticity: authenticityMatch ? parseFloat(authenticityMatch[1]) : 0
            });

            return newStream;
          });
          break;

        case 'extraction_result':
          setCompletedExtractions(prev => ({
            ...prev,
            [data.criterion_id]: {
              extraction: data.extraction,
              verdict: data.verdict
            }
          }));
          break;

        default:
          break;
      }
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed.");
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setCurrentStep("WebSocket connection encountered an error.");
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [bidderId]);

  // Scroll terminal to bottom as log streams
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [rawLogStream]);

  // Highlight Logic: Extract active excerpt from LLM stream in real-time
  const getActiveHighlightExcerpt = () => {
    // Regex matches text inside "source_excerpt" value as it streams
    const excerptMatch = rawLogStream.match(/"source_excerpt"\s*:\s*"([^"]*)/);
    return excerptMatch ? excerptMatch[1] : '';
  };

  const activeExcerpt = getActiveHighlightExcerpt();

  // Helper to render document text with live highlighting
  const renderDocumentText = (docText) => {
    if (!docText) return <p className="text-slate-400 italic">Empty page.</p>;

    // Split text into paragraphs
    const paragraphs = docText.split(/\n+/);
    const searchString = activeExcerpt.trim().toLowerCase();

    return paragraphs.map((paragraph, index) => {
      const isMatch = searchString.length > 10 && paragraph.toLowerCase().includes(searchString);

      return (
        <p 
          key={index} 
          className={`mb-4 text-sm leading-relaxed transition-all duration-700 rounded-lg p-2 ${
            isMatch 
              ? 'bg-amber-100/90 text-slate-900 font-bold border-l-4 border-amber-500 shadow-md scale-[1.01] animate-pulse' 
              : 'text-slate-600'
          }`}
        >
          {paragraph}
        </p>
      );
    });
  };

  const activeDoc = documents[activeDocIndex];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Header Workspace */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-8 py-5 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate(`/dashboard/${tenderId}`)}
            className="w-10 h-10 bg-slate-800 hover:bg-slate-700 active:scale-95 border border-slate-700 text-slate-300 hover:text-white rounded-xl flex items-center justify-center transition shadow-sm mr-1"
            title="Back to Dashboard"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M15 19l-7-7 7-7"></path></svg>
          </button>
          <div className="w-10 h-10 bg-blue-600/10 border border-blue-500/30 rounded-xl flex items-center justify-center shrink-0">
            <svg className="w-5 h-5 text-blue-400 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 4v4m0 8v4m4-12h4m-12 4H4m15.364-4.364l-2.828 2.828m-8.485 8.485L4.364 19.636M19.636 19.636l-2.828-2.828m-8.485-8.485L4.364 4.364"></path></svg>
          </div>
          <div>
            <h1 className="text-xl font-black text-white tracking-tight flex items-center gap-3">
              <span>{bidderName}</span>
              <span className="text-[10px] bg-blue-500/20 text-blue-400 border border-blue-500/30 font-mono px-2 py-0.5 rounded uppercase tracking-wider">
                Glass Box Auditor
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">{currentStep}</p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          {status === 'processing' ? (
            <div className="flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
              <span className="text-[10px] text-emerald-400 font-black tracking-widest font-mono uppercase">Pipeline Active</span>
            </div>
          ) : status === 'complete' ? (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full bg-blue-500"></span>
                <span className="text-[10px] text-blue-400 font-black tracking-widest font-mono uppercase">Analysis Completed</span>
              </div>
              <button
                onClick={() => navigate(`/bidder/${tenderId}/${bidderId}`)}
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 active:scale-95 text-white font-bold rounded-xl text-xs transition shadow-lg shadow-blue-500/20 flex items-center gap-2"
              >
                <span>View Full Verdict Report</span>
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full bg-red-500"></span>
                <span className="text-[10px] text-red-400 font-black tracking-widest font-mono uppercase">Analysis Failed</span>
              </div>
              <button
                onClick={() => navigate(`/dashboard/${tenderId}`)}
                className="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 active:scale-95 text-white font-bold rounded-xl text-xs transition border border-slate-700 shadow-lg flex items-center gap-2"
              >
                <span>Back to Dashboard</span>
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main Grid Workspace */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden h-[calc(100vh-81px)]">
        
        {/* Left Side: Extracted Evidence Document Viewer (cols 5) */}
        <section className="lg:col-span-5 border-r border-slate-900 bg-slate-950 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-900 bg-slate-900/30 flex items-center justify-between">
            <h2 className="text-xs font-black uppercase tracking-widest text-slate-400 flex items-center gap-2">
              <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"></path></svg>
              Extracted Document Text
            </h2>
            
            {documents.length > 0 && (
              <select 
                value={activeDocIndex}
                onChange={(e) => setActiveDocIndex(parseInt(e.target.value))}
                className="bg-slate-900 border border-slate-800 rounded-lg text-xs py-1.5 px-3 font-semibold text-slate-300 outline-none focus:border-blue-500 max-w-[200px]"
              >
                {documents.map((doc, idx) => (
                  <option key={idx} value={idx}>{doc.label}</option>
                ))}
              </select>
            )}
          </div>

          <div className="flex-1 p-6 overflow-y-auto bg-slate-900/10 space-y-6">
            {/* Critical Security Breach Alert Siren */}
            {securityBreach && (
              <div className="bg-rose-950/80 border-2 border-rose-500/40 p-6 rounded-3xl flex flex-col gap-4 animate-pulse shadow-2xl shadow-rose-900/20">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 bg-rose-600 border border-rose-500/30 text-white rounded-2xl flex items-center justify-center font-black animate-bounce shrink-0">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                  </div>
                  <div>
                    <h3 className="text-sm font-black text-rose-400 uppercase tracking-wider">CRITICAL BREACH NEUTRALIZED</h3>
                    <p className="text-[9px] font-mono text-rose-500 font-bold uppercase tracking-widest mt-0.5">Prompt Injection Intercepted</p>
                  </div>
                </div>
                <p className="text-xs text-rose-200 leading-relaxed font-bold">
                  Our SecurityShield middleware blocked an adversarial override payload designed to ignore system directives and force a positive verdict.
                </p>
                <div className="bg-slate-950/80 border border-rose-900/50 p-4 rounded-2xl font-mono text-[10px] text-rose-300 space-y-1.5 shadow-inner">
                  <div className="font-black text-[9px] uppercase tracking-wider text-rose-500 mb-1">Audit Details:</div>
                  {securityBreach.injection_details.map((d, i) => (
                    <div key={i} className="flex gap-2 items-start leading-normal">
                      <span className="text-rose-600 select-none shrink-0">&gt;</span>
                      <span>{d}</span>
                    </div>
                  ))}
                </div>
                <div className="text-[9px] text-rose-400 font-mono tracking-widest font-black uppercase text-center mt-1 border border-rose-500/10 py-1.5 rounded-lg bg-rose-500/5">
                  Pipeline Halted. Core Integrity Secure.
                </div>
              </div>
            )}

            {/* Adversarial & Forgery Shield Status Area */}
            <div className="bg-slate-900/40 border border-slate-900 rounded-3xl p-5 shadow-lg relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition-colors"></div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-[10px] font-black tracking-widest text-slate-400 uppercase flex items-center gap-2">
                  <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                  Adversarial & Forgery Shield
                </h3>
                <span className="text-[8px] font-mono font-black bg-blue-500/10 border border-blue-500/20 text-blue-400 px-2 py-0.5 rounded tracking-widest uppercase">
                  ACTIVE MIDDLEWARE
                </span>
              </div>
              
              {scannedFiles.length === 0 ? (
                <div className="text-[10px] text-slate-500 font-mono italic animate-pulse py-2 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500 animate-ping"></div>
                  Initializing real-time document security scanners...
                </div>
              ) : (
                <div className="space-y-2.5">
                  {scannedFiles.map((sf, idx) => {
                    let badge = "bg-slate-950 border-slate-900 text-slate-600";
                    let label = "Scanning...";
                    
                    if (sf.status === 'passed') {
                      badge = "bg-emerald-500/10 border-emerald-500/20 text-emerald-400 font-bold";
                      label = "Exif & Font Sanitized [SAFE]";
                    } else if (sf.status === 'warning') {
                      badge = "bg-amber-500/10 border-amber-500/20 text-amber-400 font-bold";
                      label = "Tampering Warning [SUSPICIOUS]";
                    } else if (sf.status === 'failed') {
                      badge = "bg-rose-500/10 border-rose-500/20 text-rose-400 font-bold animate-pulse";
                      label = "Prompt Injection Blocked [BLOCKED]";
                    }
                    
                    return (
                      <div key={idx} className="flex justify-between items-center text-[10px] bg-slate-950/40 border border-slate-900/60 p-3 rounded-2xl font-mono shadow-inner">
                        <span className="text-slate-300 font-bold max-w-[170px] truncate">{sf.filename}</span>
                        <span className={`px-2.5 py-0.5 border rounded-lg text-[8px] font-black tracking-wider uppercase ${badge}`}>{label}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {documents.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 pt-16">
                <div className="w-12 h-12 rounded-full border border-dashed border-slate-800 flex items-center justify-center text-slate-600 mb-4 animate-pulse">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 009 11V7a5 5 0 00-10 0v4c0 3.839 1.107 7.362 3 10c1.893-2.638 3-6.161 3-10z"></path></svg>
                </div>
                <h3 className="text-slate-500 font-bold text-sm">No Documents Extracted Yet</h3>
                <p className="text-slate-600 text-xs mt-1 max-w-[250px] leading-relaxed">Wait for the documents to finish text parsing/OCR extraction.</p>
              </div>
            ) : (
              <div className="bg-slate-950/40 p-6 rounded-2xl border border-slate-900 shadow-inner min-h-full">
                <div className="text-[10px] text-blue-500 font-mono uppercase tracking-widest border-b border-slate-900 pb-3 mb-4 flex justify-between items-center">
                  <span>Filename: {activeDoc?.filename}</span>
                  <span>{activeDoc?.label.split(',').pop()?.trim()}</span>
                </div>
                {renderDocumentText(activeDoc?.text)}
              </div>
            )}
          </div>
        </section>

        {/* Right Side: The Glass Box Auditing Dashboard (cols 7) */}
        <section className="lg:col-span-7 flex flex-col overflow-hidden bg-slate-900/10">
          <div className="flex-1 grid grid-cols-1 md:grid-cols-12 overflow-hidden">
            
            {/* Checklist & Results Tracker (cols 5) */}
            <div className="md:col-span-5 border-r border-slate-900 flex flex-col overflow-hidden bg-slate-950/20">
              <div className="p-4 border-b border-slate-900 bg-slate-900/30">
                <h2 className="text-xs font-black uppercase tracking-widest text-slate-400 flex items-center gap-2">
                  <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"></path></svg>
                  Pipeline Checklist
                </h2>
              </div>

              <div className="flex-1 p-4 overflow-y-auto space-y-3">
                {criteria.length === 0 ? (
                  <div className="text-center py-10 text-slate-600 font-mono text-xs">Loading checklist...</div>
                ) : (
                  criteria.map((c) => {
                    const isActive = activeCriterionId === c.id;
                    const extraction = completedExtractions[c.id];
                    const isCompleted = !!extraction;
                    const verdictStatus = extraction?.verdict?.status;

                    let bgClass = "bg-slate-900/40 border-slate-900/50 opacity-60";
                    let badgeClass = "bg-slate-800 text-slate-500";
                    let badgeLabel = "Pending";

                    if (isActive) {
                      bgClass = "bg-blue-950/30 border-blue-500/40 scale-[1.02] shadow-lg shadow-blue-500/5 opacity-100 border-l-4 border-l-blue-500";
                      badgeClass = "bg-blue-500/20 text-blue-400 border border-blue-500/30 animate-pulse";
                      badgeLabel = "Probing...";
                    } else if (isCompleted) {
                      bgClass = "bg-slate-900/60 border-slate-800 opacity-100";
                      if (verdictStatus === 'Eligible') {
                        badgeClass = "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold";
                        badgeLabel = "Eligible";
                      } else if (verdictStatus === 'Not Eligible') {
                        badgeClass = "bg-rose-500/20 text-rose-400 border border-rose-500/30 font-bold";
                        badgeLabel = "Failed";
                      } else {
                        badgeClass = "bg-amber-500/20 text-amber-400 border border-amber-500/30 font-bold";
                        badgeLabel = "Review";
                      }
                    }

                    return (
                      <div 
                        key={c.id}
                        className={`p-4 rounded-2xl border transition-all duration-300 ${bgClass}`}
                      >
                        <div className="flex justify-between items-start gap-4 mb-2">
                          <span className="text-[10px] font-mono text-blue-400 uppercase tracking-widest">{c.criterion_code}</span>
                          <span className={`text-[8px] px-2 py-0.5 rounded font-black tracking-widest font-mono uppercase ${badgeClass}`}>{badgeLabel}</span>
                        </div>
                        <p className="text-xs text-slate-300 font-bold line-clamp-2">{c.text}</p>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Monospace Parser Terminal & Confidence Panel (cols 7) */}
            <div className="md:col-span-7 flex flex-col overflow-hidden bg-slate-950/60">
              
              {/* Monospace Terminal Panel */}
              <div className="flex-1 flex flex-col overflow-hidden p-4">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden flex flex-col flex-1 shadow-2xl">
                  {/* Console Topbar */}
                  <div className="bg-slate-900 border-b border-slate-800 px-4 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 bg-rose-500 rounded-full"></span>
                      <span className="w-2.5 h-2.5 bg-amber-500 rounded-full"></span>
                      <span className="w-2.5 h-2.5 bg-emerald-500 rounded-full"></span>
                      <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider ml-2">DocProbe Parser Console</span>
                    </div>
                    {activeCriterionId && (
                      <span className="text-[9px] font-mono text-blue-400 animate-pulse bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded uppercase">
                        Streaming meta-llama-4...
                      </span>
                    )}
                  </div>
                  
                  {/* Console Body */}
                  <div className="flex-1 p-5 font-mono text-[11px] leading-relaxed text-emerald-400 overflow-y-auto selection:bg-emerald-900 selection:text-emerald-100 bg-slate-950 shadow-inner">
                    {rawLogStream ? (
                      <pre className="whitespace-pre-wrap">{rawLogStream}</pre>
                    ) : activeCriterionId ? (
                      <div className="h-full flex items-center justify-center text-slate-700 animate-pulse">
                        &gt; [INITIALIZING DOCPROBE GROQ ROUTE...]
                      </div>
                    ) : (
                      <div className="h-full flex flex-col items-center justify-center text-center text-slate-700">
                        <span className="text-3xl mb-3">⚡</span>
                        <span>WAITING FOR PIPELINE EVALUATION STAGE</span>
                      </div>
                    )}
                    <div ref={terminalEndRef} />
                  </div>
                </div>
              </div>

              {/* Confidence gauges */}
              <div className="border-t border-slate-900 p-5 bg-slate-950/40 flex flex-col gap-4">
                <h3 className="text-[10px] font-black uppercase tracking-wider text-slate-500">Live AI Score Metrics</h3>
                
                <div className="grid grid-cols-2 gap-4">
                  {/* Alignment Gauge */}
                  <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-4 flex flex-col gap-2 relative overflow-hidden group">
                    <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest font-mono">Alignment Score</div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-2xl font-black text-slate-100 font-mono">
                        {Math.round(currentConfidence.alignment * 100)}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1 overflow-hidden mt-1">
                      <div 
                        className="bg-blue-500 h-full rounded-full transition-all duration-300"
                        style={{ width: `${currentConfidence.alignment * 100}%` }}
                      ></div>
                    </div>
                    <p className="text-[8px] text-slate-500 leading-normal">Matches original criterion requirements.</p>
                  </div>

                  {/* Authenticity Gauge */}
                  <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-4 flex flex-col gap-2 relative overflow-hidden group">
                    <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest font-mono">Authenticity Score</div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-2xl font-black text-slate-100 font-mono">
                        {Math.round(currentConfidence.authenticity * 100)}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1 overflow-hidden mt-1">
                      <div 
                        className="bg-emerald-500 h-full rounded-full transition-all duration-300"
                        style={{ width: `${currentConfidence.authenticity * 100}%` }}
                      ></div>
                    </div>
                    <p className="text-[8px] text-slate-500 leading-normal">Evaluates seal, UDIN signatures, stamp integrity.</p>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </section>

      </main>
    </div>
  );
};

export default BidderProcessing;
