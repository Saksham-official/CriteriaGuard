import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

import API_BASE_URL from '../api/config';

const Upload = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const [dragging, setDragging] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => {
    setDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('officer_id', localStorage.getItem('officerId') || 'SYSTEM_OR_OFFICER');

    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API_BASE_URL}/api/tenders/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      navigate(`/criteria-review/${response.data.tender_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred during upload.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 md:p-12 relative overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute top-[-10%] right-[-10%] w-96 h-96 bg-blue-100 rounded-full blur-3xl opacity-50 animate-pulse"></div>
      <div className="absolute bottom-[-10%] left-[-10%] w-96 h-96 bg-indigo-100 rounded-full blur-3xl opacity-50"></div>

      <div className="flex flex-col lg:flex-row gap-12 max-w-6xl w-full relative z-10">
        {/* Guidance Panel */}
        <div className="lg:w-1/3 space-y-8 animate-in fade-in slide-in-from-left duration-700">
          <div>
            <h2 className="text-3xl font-black text-slate-900 tracking-tight mb-4">Start Evaluation</h2>
            <p className="text-slate-500 font-medium leading-relaxed">Prepare your procurement report in three simple steps using our governance-grade AI pipeline.</p>
          </div>

          <div className="space-y-6">
            <div className="flex gap-4 group">
              <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-black shrink-0 shadow-lg shadow-blue-200 group-hover:scale-110 transition-transform">1</div>
              <div>
                <h3 className="font-bold text-slate-800">Upload Tender Document</h3>
                <p className="text-xs text-slate-400 mt-1">Upload the master tender (PDF, Word, or Scanned Image). Our AI will extract all mandatory eligibility criteria and numeric thresholds using OCR if needed.</p>
              </div>
            </div>
            
            <div className="flex gap-4 group">
              <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 text-slate-400 flex items-center justify-center font-black shrink-0 group-hover:border-blue-400 group-hover:text-blue-600 transition-all">2</div>
              <div>
                <h3 className="font-bold text-slate-800 opacity-60">Review & Approve</h3>
                <p className="text-xs text-slate-400 mt-1">Verify the extracted criteria. Resolve any ambiguities flagged by the system before proceeding to bidder evaluation.</p>
              </div>
            </div>

            <div className="flex gap-4 group">
              <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 text-slate-400 flex items-center justify-center font-black shrink-0 group-hover:border-blue-400 group-hover:text-blue-600 transition-all">3</div>
              <div>
                <h3 className="font-bold text-slate-800 opacity-60">Bulk Bidder Upload</h3>
                <p className="text-xs text-slate-400 mt-1">Upload responses from all bidders. The system will cross-reference evidence and generate the comparative matrix.</p>
              </div>
            </div>
          </div>

          <div className="pt-8 border-t border-slate-200">
            <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Pipeline Capabilities</h4>
            <div className="flex flex-wrap gap-2">
              <span className="px-3 py-1.5 bg-white rounded-lg border border-slate-200 text-[10px] font-bold text-slate-600 shadow-sm">PDF (Native)</span>
              <span className="px-3 py-1.5 bg-white rounded-lg border border-slate-200 text-[10px] font-bold text-slate-600 shadow-sm">DOCX / MS Word</span>
              <span className="px-3 py-1.5 bg-white rounded-lg border border-slate-200 text-[10px] font-bold text-slate-600 shadow-sm">OCR (Scanned Images)</span>
            </div>
          </div>
        </div>

        {/* Upload Card */}
        <div className="lg:w-2/3">
          <div className="glass-card rounded-[2.5rem] shadow-2xl shadow-blue-900/5 p-10 md:p-16 border border-white/50 bg-white/80 backdrop-blur-xl animate-in fade-in slide-in-from-right duration-700">
            <div className="flex items-center justify-between mb-12">
              <div className="flex items-center gap-4">
                <div className="bg-blue-600 p-3.5 rounded-2xl shadow-xl shadow-blue-200 text-white">
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                </div>
                <div>
                  <h1 className="text-4xl font-black text-slate-900 tracking-tight">CriteriaGuard</h1>
                  <p className="text-slate-500 font-medium">Intelligent tender intelligence engine.</p>
                </div>
              </div>
              <div className="hidden md:block">
                <div className="px-4 py-2 bg-blue-50 text-blue-700 rounded-xl text-[10px] font-black uppercase tracking-widest border border-blue-100">Stage 01: Criteria Extraction</div>
              </div>
            </div>

            <div 
              onClick={() => document.getElementById('file-upload').click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-[2rem] p-16 flex flex-col items-center justify-center transition-all duration-500 cursor-pointer mb-12 group relative overflow-hidden ${
                dragging ? 'bg-blue-50 border-blue-500 shadow-2xl shadow-blue-500/10 scale-[1.02]' : 'border-slate-200 bg-slate-50/50 hover:bg-white hover:border-blue-400 hover:shadow-2xl hover:shadow-blue-900/5'
              }`}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-blue-50/0 to-blue-50/0 group-hover:to-blue-50/50 transition-all duration-500"></div>
              <input
                type="file"
                accept=".pdf,.docx,.jpg,.jpeg,.png,.tiff"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
              />
              <div className="bg-white p-6 rounded-[1.5rem] shadow-sm border border-slate-100 group-hover:scale-110 group-hover:shadow-lg transition-all duration-500 mb-6 relative z-10">
                <svg className="w-10 h-10 text-slate-400 group-hover:text-blue-500 transition-colors duration-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
              </div>
              <span className="text-slate-600 font-black text-xl text-center relative z-10">
                {file ? file.name : 'Drop Tender PDF, DOCX or Pic here'}
              </span>
              {!file && <span className="text-slate-400 text-xs mt-3 uppercase tracking-[0.2em] font-black relative z-10">Maximum file size 25MB</span>}
            </div>

            {error && (
              <div className="bg-rose-50 border border-rose-100 text-rose-600 text-sm p-5 rounded-2xl mb-8 flex items-start gap-4 animate-in shake duration-500">
                <div className="bg-rose-600 text-white w-5 h-5 rounded-full flex items-center justify-center font-black shrink-0">!</div>
                <div>
                  <p className="font-black uppercase text-[10px] tracking-widest mb-1">Upload Error</p>
                  <p className="font-medium">{error}</p>
                </div>
              </div>
            )}

            <button
              onClick={handleUpload}
              disabled={loading || !file}
              className={`w-full py-5 rounded-2xl font-black text-xl shadow-2xl transition-all duration-300 flex items-center justify-center gap-4 ${
                loading || !file 
                  ? 'bg-slate-100 text-slate-400 cursor-not-allowed shadow-none' 
                  : 'bg-blue-600 text-white hover:bg-blue-700 hover:scale-[1.02] active:scale-[0.98] shadow-blue-500/25'
              }`}
            >
              {loading ? (
                <>
                  <div className="w-6 h-6 border-3 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Deep Scanning Document...</span>
                </>
              ) : (
                <>
                  <span>Extract Criteria</span>
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 7l5 5m0 0l-5 5m5-5H6"></path></svg>
                </>
              )}
            </button>
            
            <p className="mt-10 text-center text-slate-400 text-[10px] font-black uppercase tracking-[0.3em]">
              Powered by Explainable AI 🛡️
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Upload;
