import React, { useState } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';

import API_BASE_URL from '../api/config';

const BidderUpload = () => {
  const { tenderId } = useParams();
  const navigate = useNavigate();
  const [bidderName, setBidderName] = useState('');
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
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
    if (e.dataTransfer.files) {
      setFiles(prev => [...prev, ...Array.from(e.dataTransfer.files)]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files) {
      setFiles(prev => [...prev, ...Array.from(e.target.files)]);
    }
  };

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (!bidderName || files.length === 0) {
      setError('Please provide bidder name and at least one document.');
      return;
    }

    const formData = new FormData();
    formData.append('tender_id', tenderId);
    formData.append('bidder_name', bidderName);
    formData.append('officer_id', localStorage.getItem('officerId') || 'SYSTEM_OR_OFFICER');
    files.forEach(file => {
      formData.append('files', file);
    });

    setLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await axios.post(`${API_BASE_URL}/api/bidders/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      const bidderId = response.data.bidder_id;
      
      // Navigate to the live WebSocket streaming processing viewport
      navigate(`/bidder-processing/${tenderId}/${bidderId}`, {
        state: { bidderName: bidderName }
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred during upload.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8 md:p-12 relative overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute top-[-5%] right-[-5%] w-96 h-96 bg-blue-100 rounded-full blur-3xl opacity-30 animate-pulse"></div>
      <div className="absolute bottom-[-5%] left-[-5%] w-96 h-96 bg-emerald-100 rounded-full blur-3xl opacity-30"></div>

      <div className="max-w-4xl mx-auto relative z-10">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
          <div>
            <h1 className="text-4xl font-black text-slate-900 tracking-tighter">Add Bidder Submission</h1>
            <p className="text-slate-500 mt-2 font-medium italic">Stage 03: Document Evidence Probing (DocProbe)</p>
          </div>
          <button 
            onClick={() => navigate(`/dashboard/${tenderId}`)}
            className="px-6 py-3 bg-white border border-slate-200 text-slate-600 rounded-2xl font-bold hover:bg-slate-50 transition-all flex items-center gap-2 shadow-sm"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path></svg>
            Dashboard
          </button>
        </div>

        <div className="glass-card rounded-[2.5rem] p-10 md:p-14 shadow-2xl shadow-blue-900/5 border border-white bg-white/80 backdrop-blur-xl">
          <div className="space-y-10">
            <div className="relative">
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3 ml-1">Entity Information</label>
              <input 
                type="text" 
                value={bidderName}
                onChange={(e) => setBidderName(e.target.value)}
                className="w-full px-8 py-5 rounded-2xl bg-white border border-slate-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/5 outline-none transition-all text-xl font-bold text-slate-900 placeholder:text-slate-300 shadow-sm"
                placeholder="e.g. Sharma Constructions Private Ltd."
              />
            </div>

            <div 
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => document.getElementById('bidder-files').click()}
              className={`border-2 border-dashed rounded-[2rem] p-12 flex flex-col items-center justify-center transition-all duration-500 cursor-pointer group relative overflow-hidden ${
                dragging ? 'bg-blue-50 border-blue-500 scale-[1.01]' : 'border-slate-200 bg-slate-50/50 hover:bg-white hover:border-blue-400'
              }`}
            >
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.jpg,.jpeg,.png,.tiff"
                onChange={handleFileChange}
                className="hidden"
                id="bidder-files"
              />
              <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 group-hover:scale-110 transition-transform mb-6">
                <svg className="w-10 h-10 text-slate-400 group-hover:text-blue-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"></path></svg>
              </div>
              <p className="text-slate-600 font-black text-lg">
                {files.length > 0 ? `${files.length} documents staged` : 'Drag documents or click to browse'}
              </p>
              <p className="text-slate-400 text-xs mt-2 uppercase tracking-widest font-bold">PDF, Word, or Scanned Certificates</p>
            </div>

            {files.length > 0 && (
              <div className="space-y-3 animate-in fade-in slide-in-from-top-4 duration-500">
                <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Staged Evidence Documents</label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {files.map((file, idx) => (
                    <div key={idx} className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-100 group">
                      <div className="flex items-center gap-3 overflow-hidden">
                        <div className="w-8 h-8 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center shrink-0">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>
                        </div>
                        <span className="text-sm font-bold text-slate-700 truncate">{file.name}</span>
                      </div>
                      <button onClick={(e) => { e.stopPropagation(); removeFile(idx); }} className="p-2 text-slate-300 hover:text-rose-500 transition-colors">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {error && (
              <div className="p-5 bg-rose-50 border border-rose-100 rounded-2xl flex items-center gap-4 text-rose-600 animate-in shake duration-500">
                <div className="w-6 h-6 bg-rose-600 text-white rounded-full flex items-center justify-center font-black text-xs shrink-0">!</div>
                <p className="font-bold text-sm">{error}</p>
              </div>
            )}

            {message && (
              <div className="p-5 bg-emerald-50 border border-emerald-100 rounded-2xl flex items-center gap-4 text-emerald-600 animate-in fade-in duration-500">
                <div className="w-6 h-6 bg-emerald-500 text-white rounded-full flex items-center justify-center font-black text-xs shrink-0">✓</div>
                <p className="font-bold text-sm">{message}</p>
              </div>
            )}

            <button
              onClick={handleUpload}
              disabled={loading || !bidderName || files.length === 0}
              className={`w-full py-6 rounded-2xl font-black text-xl shadow-2xl transition-all duration-300 flex items-center justify-center gap-4 ${
                loading || !bidderName || files.length === 0 
                  ? 'bg-slate-100 text-slate-400 cursor-not-allowed shadow-none' 
                  : 'bg-blue-600 text-white hover:bg-blue-700 hover:scale-[1.02] active:scale-[0.98] shadow-blue-500/25'
              }`}
            >
              {loading ? (
                <>
                  <div className="w-6 h-6 border-3 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Scanning Evidence...</span>
                </>
              ) : (
                <>
                  <span>Commit to Evaluation</span>
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BidderUpload;
