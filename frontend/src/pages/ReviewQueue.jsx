import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';

import API_BASE_URL from '../api/config';

const ReviewItem = ({ item, handleOverride }) => {
  const [reason, setReason] = useState('');
  
  return (
    <div className="bg-white rounded-2xl shadow-lg border-l-4 border-amber-500 overflow-hidden relative">
      <div className="p-6">
        <div className="flex flex-col md:flex-row justify-between mb-6 gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-black text-slate-400 uppercase tracking-widest">{item.bidder.name}</span>
              <span className="w-1 h-1 rounded-full bg-slate-300"></span>
              <span className="text-[10px] font-bold text-blue-500 uppercase tracking-tighter">AI Verification Flagged</span>
            </div>
            <h3 className="text-2xl font-extrabold text-slate-900">{item.extraction.criteria?.category || 'Criterion'} Check</h3>
            
            <div className="flex flex-wrap gap-2 mt-3">
              {item.verdict.review_sub_reason && (
                <span className="bg-amber-50 text-amber-700 text-[10px] font-black px-2 py-1 rounded border border-amber-100 uppercase tracking-tighter flex items-center gap-1.5">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                  {item.verdict.review_sub_reason.replace('_', ' ')}
                </span>
              )}
              {item.extraction.extraction_confidence < 0.7 && (
                <span className="bg-rose-50 text-rose-700 text-[10px] font-black px-2 py-1 rounded border border-rose-100 uppercase tracking-tighter flex items-center gap-1.5">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path></svg>
                  Low OCR Confidence
                </span>
              )}
              <span className="bg-slate-100 text-slate-600 text-[10px] font-black px-2 py-1 rounded border border-slate-200 uppercase tracking-tighter">
                Route: {item.extraction.source_document?.split('.').pop()?.toUpperCase() || 'N/A'}
              </span>
            </div>
          </div>
          <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 max-w-sm relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
              <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            </div>
            <span className="text-[10px] font-black text-blue-400 uppercase tracking-widest">AI Justification Engine</span>
            <p className="text-sm text-slate-300 font-medium mt-1 leading-snug">{item.verdict.reason}</p>
            <div className="mt-3 flex items-center gap-2">
              <div className="flex-1 bg-slate-800 h-1 rounded-full overflow-hidden">
                <div className="bg-blue-500 h-full" style={{ width: `${(item.extraction.extraction_confidence || 0.5) * 100}%` }}></div>
              </div>
              <span className="text-[9px] font-bold text-slate-500">{Math.round((item.extraction.extraction_confidence || 0.5) * 100)}% Match</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-slate-50 p-5 rounded-2xl border border-slate-100">
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">Requirement</span>
            <p className="text-slate-700 text-sm leading-relaxed">{item.extraction.criteria?.text}</p>
          </div>
          <div className="bg-slate-50 p-5 rounded-2xl border border-slate-100">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block">Evidence Snippet</span>
              {/* Routing Badge */}
              {(() => {
                const docName = item.extraction.source_document;
                if (!docName) return null;
                const ext = docName.split('.').pop().toLowerCase();
                let badge = { type: 'PDF', color: 'bg-rose-50 text-rose-700 border-rose-100' };
                if (ext === 'docx') badge = { type: 'DOCX', color: 'bg-indigo-50 text-indigo-700 border-indigo-100' };
                if (['jpg', 'jpeg', 'png'].includes(ext)) badge = { type: 'IMG', color: 'bg-violet-50 text-violet-700 border-violet-100' };
                
                return (
                  <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded-lg border text-[8px] font-black uppercase tracking-widest ${badge.color}`}>
                    {badge.type} ROUTE
                  </div>
                );
              })()}
            </div>
            {item.extraction.source_excerpt ? (
              <div className="relative">
                <p className="text-slate-600 text-sm italic border-l-2 border-slate-300 pl-3">"{item.extraction.source_excerpt}"</p>
                <div className="mt-2 text-[10px] font-bold text-blue-500 flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                  Source: {item.extraction.source_document} (P.{item.extraction.source_page || 1})
                </div>
              </div>
            ) : (
              <p className="text-slate-400 text-sm italic">No document evidence found by system.</p>
            )}
          </div>
        </div>

        <div className="border-t border-slate-100 pt-6">
          <div className="mb-4">
            <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Officer's Justification (Mandatory)</label>
            <textarea 
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="State the reason for your manual decision..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all outline-none"
              rows="2"
            ></textarea>
          </div>

          <div className="flex justify-end gap-3">
            <button 
              disabled={!reason.trim()}
              onClick={() => handleOverride(item.verdict.id, 'Not Eligible', reason)}
              className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all ${
                !reason.trim() ? 'bg-slate-100 text-slate-400 cursor-not-allowed' : 'bg-white border border-red-200 text-red-600 hover:bg-red-50'
              }`}
            >
              Reject Bidder
            </button>
            <button 
              disabled={!reason.trim()}
              onClick={() => handleOverride(item.verdict.id, 'Eligible', reason)}
              className={`px-6 py-2.5 rounded-xl font-bold text-sm shadow-md transition-all ${
                !reason.trim() ? 'bg-slate-100 text-slate-400 cursor-not-allowed shadow-none' : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              Approve Override
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const ReviewQueue = () => {
  const { tenderId } = useParams();
  const navigate = useNavigate();
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQueue();
  }, [tenderId]);

  const fetchQueue = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/verdicts/tender/${tenderId}`);
      
      const reviewItems = [];
      response.data.verdicts.forEach(v => {
        if (v.status === 'Needs Review') {
          const bidder = response.data.bidders.find(b => b.id === v.bidder_id);
          const ext = response.data.extractions.find(e => e.id === v.extraction_id);
          reviewItems.push({ verdict: v, bidder, extraction: ext });
        }
      });
      
      setQueue(reviewItems);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOverride = async (verdictId, newStatus, reason) => {
    try {
      const officerId = localStorage.getItem('officerId') || 'ANONYMOUS_OFFICER';
      await axios.post(`${API_BASE_URL}/api/verdicts/${verdictId}/override`, {
        officer_id: officerId,
        new_status: newStatus,
        reason: reason
      });
      fetchQueue(); // Refresh
    } catch (err) {
      alert("Failed to override: " + err.message);
    }
  };

  if (loading) return <div className="text-center py-20 text-xl">Loading Review Queue...</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-10">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-extrabold text-gray-800">Review Queue</h1>
          <button onClick={() => navigate(`/dashboard/${tenderId}`)} className="text-blue-600 font-medium hover:underline">
            Back to Dashboard
          </button>
        </div>

        {queue.length === 0 ? (
          <div className="bg-green-50 border border-green-200 rounded-xl p-10 text-center">
            <h2 className="text-2xl font-bold text-green-700 mb-2">Inbox Zero!</h2>
            <p className="text-green-600">There are no criteria requiring manual officer review.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {queue.map((item, index) => (
              <ReviewItem key={index} item={item} handleOverride={handleOverride} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReviewQueue;
