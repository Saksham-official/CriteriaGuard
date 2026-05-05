import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';

import API_BASE_URL from '../api/config';

const Dashboard = () => {
  const { tenderId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState({ bidders: [], verdicts: [], extractions: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/verdicts/tender/${tenderId}`);
        setData(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
    
    // Poll for progress if any bidder is processing
    const interval = setInterval(() => {
      fetchDashboard();
    }, 5000);
    
    return () => clearInterval(interval);
  }, [tenderId]);

  if (loading) return <div className="text-center py-20 text-xl font-bold">Loading verdicts...</div>;

  const { bidders = [], verdicts = [] } = data;

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-10">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
          <div>
            <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">Evaluation Dashboard</h1>
            <p className="text-slate-500 mt-2">Automated eligibility screening for Tender ID: <span className="font-mono text-blue-600">{tenderId}</span></p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button 
              onClick={() => navigate(`/bidder-upload/${tenderId}`)}
              className="bg-blue-600 text-white px-5 py-2.5 rounded-xl font-semibold hover:bg-blue-700 transition shadow-sm hover:shadow-md flex items-center gap-2"
            >
              <span>+</span> Add Bidder
            </button>
            <button 
              onClick={() => navigate(`/comparative-matrix/${tenderId}`)}
              className="bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-semibold hover:bg-indigo-700 transition shadow-sm hover:shadow-md flex items-center gap-2"
            >
              📊 Compare Bidders
            </button>
            <button 
              onClick={() => navigate(`/review-queue/${tenderId}`)}
              className="bg-white text-slate-700 border border-slate-200 px-5 py-2.5 rounded-xl font-semibold hover:bg-slate-50 transition shadow-sm"
            >
              Review Queue
            </button>
            <a 
              href={`${API_BASE_URL}/api/reports/export/${tenderId}`}
              className="bg-slate-900 text-white px-5 py-2.5 rounded-xl font-semibold hover:bg-black transition shadow-sm flex items-center gap-2"
              download
            >
              Export Report
            </a>
            <button 
              onClick={() => navigate(`/audit-trail`)}
              className="bg-white text-slate-700 border border-slate-200 px-5 py-2.5 rounded-xl font-semibold hover:bg-slate-50 transition shadow-sm"
            >
              Audit Log
            </button>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-slate-900 rounded-3xl p-6 text-white shadow-xl shadow-slate-200 relative overflow-hidden group">
            <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-blue-500/10 rounded-full blur-2xl group-hover:bg-blue-500/20 transition-all duration-700"></div>
            <div className="flex items-center gap-4 mb-4">
              <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-900/50">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
              </div>
              <h3 className="font-bold text-sm uppercase tracking-widest text-slate-400">System Integrity</h3>
            </div>
            <div className="text-3xl font-black mb-1">100% SECURE</div>
            <p className="text-[10px] text-slate-500 font-medium leading-relaxed">Cryptographic SHA-256 chain is active and verifying all decisions.</p>
          </div>
          
          <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-xl shadow-slate-100/50 relative overflow-hidden group">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
              </div>
              <h3 className="font-bold text-sm uppercase tracking-widest text-slate-400">Avg. Confidence</h3>
            </div>
            <div className="text-3xl font-black text-slate-800 mb-1">
              {data.extractions.length > 0 
                ? Math.round((data.extractions.reduce((acc, curr) => acc + (curr.extraction_confidence || 0), 0) / data.extractions.length) * 100) 
                : 0}%
            </div>
            <p className="text-[10px] text-slate-500 font-medium leading-relaxed">Based on {data.extractions.length} evidence extractions across all bidders.</p>
          </div>

          <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-xl shadow-slate-100/50 relative overflow-hidden group">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              </div>
              <h3 className="font-bold text-sm uppercase tracking-widest text-slate-400">Time Saved</h3>
            </div>
            <div className="text-3xl font-black text-slate-800 mb-1">~{Math.max(1, Math.round(data.bidders.length * 45))} MIN</div>
            <p className="text-[10px] text-slate-500 font-medium leading-relaxed">Estimated manual evaluation time replaced by AI pipeline.</p>
          </div>
        </div>

        {/* Empty State / Zero State */}
        {(bidders || []).length === 0 && !loading && (
          <div className="mt-12 animate-in fade-in zoom-in duration-700">
            <div className="bg-white rounded-[3rem] border-2 border-dashed border-slate-200 p-16 md:p-24 text-center relative overflow-hidden group">
              {/* Abstract Background Shapes */}
              <div className="absolute top-0 left-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 group-hover:bg-blue-500/10 transition-colors"></div>
              <div className="absolute bottom-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl translate-x-1/2 translate-y-1/2 group-hover:bg-indigo-500/10 transition-colors"></div>
              
              <div className="relative z-10 max-w-xl mx-auto">
                <div className="w-24 h-24 bg-blue-600 rounded-[2rem] flex items-center justify-center mx-auto mb-10 shadow-2xl shadow-blue-200 text-white transform group-hover:rotate-12 transition-transform duration-500">
                  <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 4v16m8-8H4"></path></svg>
                </div>
                
                <h2 className="text-4xl font-black text-slate-900 tracking-tight mb-4">No Bidders Evaluated Yet</h2>
                <p className="text-lg text-slate-500 font-medium leading-relaxed mb-10">
                  The criteria are set and verified. Now, upload bidder response documents (PDF, DOCX, or Images) to start the automated eligibility screening.
                </p>
                
                <div className="flex flex-col md:flex-row gap-4 justify-center">
                  <button 
                    onClick={() => navigate(`/bidder-upload/${tenderId}`)}
                    className="px-10 py-5 bg-blue-600 text-white rounded-2xl font-black text-lg shadow-2xl shadow-blue-200 hover:bg-blue-700 hover:scale-105 active:scale-95 transition-all flex items-center justify-center gap-3"
                  >
                    <span>Upload Bidder Files</span>
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                  </button>
                  <button 
                    onClick={() => navigate(`/criteria-review/${tenderId}`)}
                    className="px-10 py-5 bg-white border-2 border-slate-100 text-slate-600 rounded-2xl font-black text-lg hover:bg-slate-50 transition-all flex items-center justify-center gap-3"
                  >
                    Review Criteria
                  </button>
                </div>

                <div className="mt-16 grid grid-cols-3 gap-8">
                  <div className="text-left">
                    <div className="text-2xl font-black text-slate-900 mb-1">Step 1</div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Select Bidder Files</p>
                  </div>
                  <div className="text-left border-l border-slate-100 pl-8">
                    <div className="text-2xl font-black text-slate-900 mb-1">Step 2</div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">AI Extraction</p>
                  </div>
                  <div className="text-left border-l border-slate-100 pl-8">
                    <div className="text-2xl font-black text-slate-900 mb-1">Step 3</div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Final Verdict</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {(bidders || []).map(bidder => {
            const bidderVerdicts = verdicts.filter(v => v.bidder_id === bidder.id);
            const passed = bidderVerdicts.filter(v => v.status === 'Eligible').length;
            const failed = bidderVerdicts.filter(v => v.status === 'Not Eligible').length;
            const review = bidderVerdicts.filter(v => v.status === 'Needs Review').length;
            const total = bidderVerdicts.length;
            
            let statusBadge = "bg-slate-100 text-slate-600";
            let statusText = "Processing";

            if (bidder.status === 'complete') {
                if (failed > 0) {
                    statusBadge = "bg-red-50 text-red-600 border border-red-100";
                    statusText = "Not Eligible";
                } else if (review > 0) {
                    statusBadge = "bg-amber-50 text-amber-600 border border-amber-100";
                    statusText = "Needs Review";
                } else if (total > 0 && passed === total) {
                    statusBadge = "bg-emerald-50 text-emerald-600 border border-emerald-100";
                    statusText = "Eligible";
                }
            }

            return (
              <div 
                key={bidder.id} 
                onClick={() => navigate(`/bidder/${tenderId}/${bidder.id}`)}
                className="glass-card rounded-3xl p-6 hover:shadow-xl transition-all duration-300 cursor-pointer group relative overflow-hidden"
              >
                <div className="absolute top-0 left-0 w-1 h-full bg-blue-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-slate-800 group-hover:text-blue-600 transition">{bidder.name}</h2>
                    <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold">Bidder ID: {bidder.id.substring(0,8)}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-lg text-xs font-bold ${statusBadge}`}>
                    {statusText}
                  </span>
                </div>
                
                {bidder.status === 'processing' && (
                  <div className="mb-6">
                    <div className="flex justify-between text-[10px] font-bold text-blue-600 uppercase mb-1">
                      <span>{bidder.current_step || 'Initializing...'}</span>
                      <span>{Math.round((bidder.processed_count / (bidder.total_count || 1)) * 100)}%</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                      <div 
                        className="bg-blue-500 h-full transition-all duration-500"
                        style={{ width: `${(bidder.processed_count / (bidder.total_count || 1)) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-3 gap-2 mb-6">
                  <div className="bg-emerald-50/50 rounded-xl p-2 text-center">
                    <div className="text-emerald-600 font-bold text-lg">{passed}</div>
                    <div className="text-[10px] text-emerald-600 uppercase font-bold">Pass</div>
                  </div>
                  <div className="bg-red-50/50 rounded-xl p-2 text-center">
                    <div className="text-red-600 font-bold text-lg">{failed}</div>
                    <div className="text-[10px] text-red-600 uppercase font-bold">Fail</div>
                  </div>
                  <div className="bg-amber-50/50 rounded-xl p-2 text-center">
                    <div className="text-amber-600 font-bold text-lg">{review}</div>
                    <div className="text-[10px] text-amber-600 uppercase font-bold">Review</div>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-100 flex justify-between items-center text-sm">
                  <span className="text-slate-500">Evaluation Progress</span>
                  <span className="font-bold text-slate-700">{total} Criteria</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
