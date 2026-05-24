import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

import API_BASE_URL from '../api/config';

const AuditTrail = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [verifyResult, setVerifyResult] = useState(null);
  const [verifyError, setVerifyError] = useState('');
  const [draggingFile, setDraggingFile] = useState(false);

  const calculateSHA256 = async (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const buffer = e.target.result;
          const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
          const hashArray = Array.from(new Uint8Array(hashBuffer));
          const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
          resolve(hashHex);
        } catch (err) {
          reject(err);
        }
      };
      reader.onerror = (err) => reject(err);
      reader.readAsArrayBuffer(file);
    });
  };

  const handleVerifyFile = async (file) => {
    if (!file) return;
    setVerifyLoading(true);
    setVerifyError('');
    setVerifyResult(null);

    try {
      const hashHex = await calculateSHA256(file);
      const response = await axios.post(`${API_BASE_URL}/api/audit/verify-pdf`, { pdf_hash: hashHex });
      setVerifyResult(response.data);
    } catch (err) {
      console.error(err);
      setVerifyError('An error occurred during cryptographic verification.');
    } finally {
      setVerifyLoading(false);
    }
  };

  useEffect(() => {
    const fetchAudit = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/audit/`);
        setData(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchAudit();
  }, []);


  if (loading) return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50">
      <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
      <div className="text-xl font-black text-slate-900 tracking-tighter uppercase">Verifying Cryptographic Chain...</div>
      <p className="text-slate-400 text-sm mt-2 font-medium">SHA-256 Chaining in Progress</p>
    </div>
  );

  const { is_chain_valid, logs, verification } = data;

  return (
    <div className="min-h-screen bg-[#F8FAFC] p-6 md:p-12">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
          <div className="animate-in fade-in slide-in-from-left duration-700">
            <div className="flex items-center gap-3 mb-2">
              <div className="bg-slate-900 text-white text-[10px] font-black px-2 py-0.5 rounded tracking-widest uppercase">Governance Grade</div>
              <div className="bg-blue-100 text-blue-700 text-[10px] font-black px-2 py-0.5 rounded tracking-widest uppercase">Immutable</div>
            </div>
            <h1 className="text-5xl font-black text-slate-900 tracking-tight leading-none mb-3">System Audit Trail</h1>
            <p className="text-slate-500 font-medium max-w-xl">Every decision, extraction, and override is cryptographically hashed and chained to prevent tampering.</p>
          </div>
          <div className="flex flex-wrap gap-3 animate-in fade-in slide-in-from-right duration-700">
            {data && data.logs && (
              <button 
                onClick={() => {
                  const officerId = localStorage.getItem('officerId') || 'SYSTEM_OR_OFFICER';
                  window.open(`${API_BASE_URL}/api/audit/export-pdf?officer_id=${officerId}`, '_blank');
                }}
                className="bg-blue-600 text-white px-6 py-2.5 rounded-2xl font-bold text-sm hover:bg-blue-700 transition shadow-lg shadow-blue-200 flex items-center gap-2"
              >
                📥 Download Audit Log (.pdf)
              </button>
            )}
            <button 
              onClick={() => navigate(-1)} 
              className="bg-slate-900 text-white px-6 py-2.5 rounded-2xl font-bold text-sm hover:bg-black transition shadow-lg shadow-slate-200"
            >
              &larr; Back to Dashboard
            </button>
          </div>
        </div>

        {/* Integrity Header */}
        <div className={`relative overflow-hidden p-8 rounded-[2rem] mb-12 border-2 transition-all duration-500 animate-in zoom-in duration-500 ${is_chain_valid ? 'bg-emerald-50/50 border-emerald-100' : 'bg-rose-50 border-rose-200'}`}>
          <div className="absolute top-0 right-0 p-12 opacity-5">
            <svg className="w-64 h-64" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L3 7v10l9 5 9-5V7l-9-5z"/></svg>
          </div>
          
          <div className="relative z-10 flex flex-col md:flex-row items-center gap-8">
            <div className={`w-24 h-24 rounded-[2rem] flex items-center justify-center shrink-0 shadow-2xl ${is_chain_valid ? 'bg-emerald-500 shadow-emerald-200' : 'bg-rose-500 shadow-rose-200 animate-pulse'}`}>
              {is_chain_valid ? (
                <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
              ) : (
                <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
              )}
            </div>
            <div className="text-center md:text-left flex-1">
              <h2 className={`text-3xl font-black tracking-tight mb-2 ${is_chain_valid ? 'text-emerald-900' : 'text-rose-900'}`}>
                {is_chain_valid ? 'Cryptographic Integrity Verified' : 'Critical Integrity Alert'}
              </h2>
              <p className={`text-lg font-medium opacity-80 ${is_chain_valid ? 'text-emerald-700' : 'text-rose-700'}`}>
                {is_chain_valid 
                  ? 'The system has successfully validated the entire SHA-256 chain. No unauthorized changes detected.' 
                  : 'The validation sequence was broken at a specific block. Potential data tampering or unauthorized manual DB edit detected.'}
              </p>
              
              <div className="mt-6 flex flex-wrap gap-4 justify-center md:justify-start">
                <div className={`px-4 py-2 rounded-xl text-xs font-bold border uppercase tracking-widest ${is_chain_valid ? 'bg-emerald-100/50 border-emerald-200 text-emerald-700' : 'bg-rose-100 border-rose-200 text-rose-700'}`}>
                  Algorithm: SHA-256
                </div>
                <div className={`px-4 py-2 rounded-xl text-xs font-bold border uppercase tracking-widest ${is_chain_valid ? 'bg-emerald-100/50 border-emerald-200 text-emerald-700' : 'bg-rose-100 border-rose-200 text-rose-700'}`}>
                  Entries: {logs.length} Blocks
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Drag and Drop Cryptographic Verification Widget */}
        <div className="bg-white rounded-[2rem] p-8 mb-12 border border-slate-100 shadow-sm relative overflow-hidden animate-in fade-in zoom-in duration-600">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-2xl"></div>
          
          <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.2em] mb-6">Verify Report Authenticity (SHA-256 Ledger Audit)</h3>
          
          <div className="flex flex-col lg:flex-row gap-8 items-stretch">
            {/* File Dropzone */}
            <div 
              onDragOver={(e) => { e.preventDefault(); setDraggingFile(true); }}
              onDragLeave={() => setDraggingFile(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDraggingFile(false);
                if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                  handleVerifyFile(e.dataTransfer.files[0]);
                }
              }}
              onClick={() => document.getElementById('verify-pdf-upload').click()}
              className={`flex-1 border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center cursor-pointer transition-all duration-300 ${
                draggingFile 
                  ? 'bg-blue-50 border-blue-500 scale-[1.01]' 
                  : 'border-slate-200 bg-slate-50/50 hover:bg-white hover:border-blue-400'
              }`}
            >
              <input 
                type="file" 
                accept=".pdf"
                id="verify-pdf-upload"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleVerifyFile(e.target.files[0]);
                  }
                }}
                className="hidden"
              />
              <div className="w-12 h-12 rounded-xl bg-white border border-slate-100 flex items-center justify-center shadow-sm text-2xl mb-4">
                📁
              </div>
              <p className="text-slate-700 font-bold text-sm text-center">
                Drag & Drop Generated PDF Report
              </p>
              <p className="text-slate-400 text-[10px] uppercase font-bold tracking-wider mt-1.5 text-center">
                Or click to browse files
              </p>
            </div>

            {/* Results Output Viewport */}
            <div className="flex-1 min-h-[160px] bg-slate-900 border border-slate-800 rounded-2xl p-6 text-slate-300 flex flex-col justify-center relative overflow-hidden font-sans shadow-inner">
              <div className="absolute top-4 right-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                <span className="text-[8px] font-mono text-slate-500 font-bold tracking-wider uppercase">Verification Terminal</span>
              </div>

              {verifyLoading ? (
                <div className="flex flex-col items-center justify-center gap-3">
                  <div className="w-8 h-8 border-3 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
                  <p className="text-xs font-mono text-slate-400">Computing local SHA-256 hash...</p>
                </div>
              ) : verifyError ? (
                <div className="flex gap-4 items-start">
                  <div className="w-8 h-8 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center justify-center shrink-0 text-red-500 font-bold">!</div>
                  <div>
                    <h4 className="font-bold text-red-400 text-sm">System Verification Error</h4>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">{verifyError}</p>
                  </div>
                </div>
              ) : verifyResult ? (
                verifyResult.is_valid ? (
                  <div className="flex flex-col gap-4 animate-in fade-in duration-300">
                    <div className="flex gap-4 items-start">
                      <div className="w-10 h-10 rounded-xl bg-emerald-500 text-white flex items-center justify-center shrink-0 text-xl shadow-lg shadow-emerald-900/30">
                        ✓
                      </div>
                      <div>
                        <h4 className="font-black text-emerald-400 text-sm tracking-tight flex items-center gap-2">
                          <span>SIGNATURE VERIFIED</span>
                          <span className="text-[8px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded font-mono font-bold tracking-widest uppercase">Genuine</span>
                        </h4>
                        <p className="text-xs text-slate-300 mt-1 leading-relaxed font-bold">
                          Evaluation report matches exact seal logged on <span className="text-white">{new Date(verifyResult.audit_log.timestamp).toLocaleString()}</span>.
                        </p>
                      </div>
                    </div>
                    
                    <div className="mt-2 pt-4 border-t border-slate-800 font-mono text-[9px] text-slate-500 space-y-1 bg-slate-950/40 p-4 rounded-xl shadow-inner">
                      <div className="flex justify-between"><span>Audit Seq:</span> <span className="text-slate-400 font-bold">#{verifyResult.audit_log.sequence}</span></div>
                      <div className="flex justify-between"><span>Signed By:</span> <span className="text-slate-400 font-bold">{verifyResult.audit_log.actor}</span></div>
                      <div className="flex justify-between"><span>Chained Status:</span> <span className="text-emerald-400 font-bold">Ledger Integrity 100% Intact</span></div>
                      <div className="flex justify-between gap-4 mt-1 border-t border-white/5 pt-1">
                        <span>SHA-256:</span>
                        <span className="text-blue-400 truncate max-w-[190px] font-bold" title={verifyResult.audit_log.metadata?.pdf_hash}>
                          {verifyResult.audit_log.metadata?.pdf_hash}
                        </span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex gap-4 items-start animate-in shake duration-300">
                    <div className="w-10 h-10 rounded-xl bg-rose-650 text-white flex items-center justify-center shrink-0 text-xl font-bold shadow-lg shadow-rose-900/30">
                      ⚠️
                    </div>
                    <div>
                      <h4 className="font-black text-rose-400 text-sm tracking-tight flex items-center gap-2">
                        <span>VERIFICATION FAILED</span>
                        <span className="text-[8px] bg-rose-500/10 border border-rose-500/20 text-rose-400 px-1.5 py-0.5 rounded font-mono font-bold tracking-widest uppercase animate-pulse">Altered</span>
                      </h4>
                      <p className="text-xs text-slate-400 mt-1 leading-relaxed font-medium">
                        {verifyResult.message}
                      </p>
                    </div>
                  </div>
                )
              ) : (
                <div className="flex flex-col items-center justify-center text-center p-4 text-slate-500">
                  <span className="text-3xl mb-2">🛡️</span>
                  <p className="text-xs font-bold">Ledger Verification Node Ready</p>
                  <p className="text-[10px] text-slate-600 mt-1 max-w-[200px] leading-normal">Drag or select a compiled PDF compliance report to mathematically verify its authenticity.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* How it Works Section */}
        <div className="bg-white rounded-[2rem] p-8 mb-12 border border-slate-100 shadow-sm">
          <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.2em] mb-6">How the Immutable Ledger Works</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="flex gap-4">
              <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center shrink-0 text-blue-600 font-bold text-xs">1</div>
              <div>
                <p className="text-sm font-bold text-slate-800 mb-1">Hashing</p>
                <p className="text-xs text-slate-500 leading-relaxed">Every action is converted into a unique 64-character SHA-256 fingerprint.</p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center shrink-0 text-blue-600 font-bold text-xs">2</div>
              <div>
                <p className="text-sm font-bold text-slate-800 mb-1">Chaining</p>
                <p className="text-xs text-slate-500 leading-relaxed">Block N includes the fingerprint of Block N-1, creating a dependent chain.</p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center shrink-0 text-blue-600 font-bold text-xs">3</div>
              <div>
                <p className="text-sm font-bold text-slate-800 mb-1">Verification</p>
                <p className="text-xs text-slate-500 leading-relaxed">Changing any past entry invalidates all future fingerprints in the chain.</p>
              </div>
            </div>
          </div>
        </div>

        {/* The Chain */}
        <div className="space-y-4">
          {logs.map((log, index) => {
            const isIntact = verification.find(v => v.id === log.id)?.is_intact;
            
            return (
              <div key={log.id} className="relative animate-in slide-in-from-bottom duration-500" style={{ animationDelay: `${index * 100}ms` }}>
                {/* Visual Chain Link */}
                {index > 0 && (
                  <div className="flex justify-center -my-2 relative z-20">
                    <div className="bg-white border-2 border-slate-100 w-8 h-10 rounded-lg flex items-center justify-center shadow-sm">
                      <svg className={`w-4 h-4 ${isIntact ? 'text-blue-500' : 'text-rose-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.82a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
                    </div>
                  </div>
                )}

                <div className={`glass-card rounded-[2rem] p-8 border-2 transition-all duration-300 hover:shadow-2xl hover:-translate-y-1 relative overflow-hidden group bg-white ${isIntact ? 'border-transparent shadow-xl shadow-slate-100' : 'border-rose-200 bg-rose-50/20 shadow-none'}`}>
                  <div className="absolute top-0 right-0 p-8 text-[80px] font-black text-slate-50 opacity-[0.03] select-none group-hover:opacity-[0.06] transition-opacity">
                    #{logs.length - index}
                  </div>

                  <div className="flex flex-col md:flex-row justify-between mb-8 gap-4 relative z-10">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <span className={`px-4 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border ${isIntact ? 'bg-blue-50 text-blue-700 border-blue-100' : 'bg-rose-100 text-rose-700 border-rose-200'}`}>
                          {log.action_type.replace('_', ' ')}
                        </span>
                        {!isIntact && (
                          <span className="flex items-center gap-1 text-[10px] font-black text-rose-600 uppercase tracking-tighter">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                            Corrupted Block
                          </span>
                        )}
                      </div>
                      <h4 className="text-sm font-bold text-slate-400 uppercase tracking-widest">{new Date(log.timestamp).toLocaleString()}</h4>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest mb-1">Status</span>
                      <span className={`text-sm font-black uppercase tracking-tighter ${isIntact ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {isIntact ? 'Cryptographically Sealed' : 'Seal Compromised'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm mb-8 relative z-10">
                    <div className="bg-slate-50/50 p-5 rounded-2xl border border-slate-100 transition-colors group-hover:bg-white">
                      <span className="text-slate-400 font-bold uppercase text-[10px] block mb-3 tracking-[0.15em]">Registry Impact</span> 
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-white rounded-xl shadow-sm flex items-center justify-center text-xl border border-slate-50">
                          {log.target_type === 'verdict' ? '⚖️' : log.target_type === 'tender' ? '📋' : '👤'}
                        </div>
                        <div>
                          <p className="font-bold text-slate-800 text-base capitalize">{log.target_type}</p>
                          <p className="font-mono text-[10px] text-blue-500">{log.target_id}</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-slate-50/50 p-5 rounded-2xl border border-slate-100 transition-colors group-hover:bg-white">
                      <span className="text-slate-400 font-bold uppercase text-[10px] block mb-3 tracking-[0.15em]">Action Outcome</span> 
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-white rounded-xl shadow-sm flex items-center justify-center text-xl border border-slate-50">
                          {log.result === 'Eligible' ? '✅' : log.result === 'Not Eligible' ? '❌' : 'ℹ️'}
                        </div>
                        <div>
                          <p className="font-black text-slate-800 text-base uppercase tracking-tight">{log.result}</p>
                          <p className="text-xs text-slate-500 font-medium">Actor: {log.actor}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Hash Visualizer */}
                  <div className={`rounded-3xl p-6 font-mono text-[10px] overflow-x-auto relative border group/hash ${isIntact ? 'bg-slate-900 border-slate-800 text-slate-400' : 'bg-rose-900 border-rose-800 text-rose-300'}`}>
                    <div className="absolute top-4 right-6 flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${isIntact ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]' : 'bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)] animate-pulse'}`}></div>
                      <span className="font-black uppercase tracking-[0.2em] text-[8px] opacity-30">SHA-256 Ledger Node</span>
                    </div>
                    
                    <div className="mb-6 pb-6 border-b border-white/5">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-5 h-5 rounded-md bg-white/5 flex items-center justify-center text-[10px]">🔗</div>
                        <span className="opacity-40 font-bold uppercase tracking-widest text-[9px]">Previous Block Hash</span> 
                      </div>
                      <span className="break-all opacity-80 group-hover/hash:opacity-100 transition-opacity">{log.previous_hash}</span>
                    </div>
                    
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-5 h-5 rounded-md bg-white/5 flex items-center justify-center text-[10px]">📍</div>
                        <span className="text-blue-400 font-bold uppercase tracking-widest text-[9px]">Current Entry Hash</span> 
                      </div>
                      <span className={`break-all font-black tracking-tight ${isIntact ? 'text-blue-400' : 'text-rose-400'}`}>{log.entry_hash}</span>
                    </div>

                    {/* Verification Proof Section */}
                    <div className="mt-4 pt-4 border-t border-white/5 opacity-0 group-hover/hash:opacity-100 transition-opacity">
                      <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest block mb-2">Deterministic Verification Payload</span>
                      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[7px] text-slate-500 font-bold">
                        <div className="flex justify-between"><span>Actor:</span> <span className="text-slate-400">{log.actor}</span></div>
                        <div className="flex justify-between"><span>Action:</span> <span className="text-slate-400">{log.action_type}</span></div>
                        <div className="flex justify-between"><span>Result:</span> <span className="text-slate-400">{log.result}</span></div>
                        <div className="flex justify-between"><span>Timestamp:</span> <span className="text-slate-400">{log.timestamp.replace(' ', 'T').split('.')[0]}</span></div>
                      </div>
                    </div>

                    <div className="mt-6 flex justify-between items-center text-[8px] font-bold text-slate-600 uppercase tracking-widest">
                      <span>Verified: {isIntact ? 'True' : 'False'}</span>
                      <span>Sequence: {log.sequence}</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        
        {logs.length === 0 && (
          <div className="text-center py-32 bg-white rounded-[2rem] border-2 border-dashed border-slate-200">
            <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6 text-3xl">📭</div>
            <p className="text-slate-400 text-xl font-bold tracking-tight">Genesis block not yet initialized.</p>
            <p className="text-slate-300 text-sm mt-2">Upload a bidder or perform an action to start the chain.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditTrail;
