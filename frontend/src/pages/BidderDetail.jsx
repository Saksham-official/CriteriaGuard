import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';

import API_BASE_URL from '../api/config';

const BidderDetail = () => {
  const { tenderId, bidderId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedRow, setExpandedRow] = useState(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/verdicts/tender/${tenderId}`);
        const bidder = response.data.bidders.find(b => b.id === bidderId);
        const extractions = response.data.extractions.filter(e => e.bidder_id === bidderId);
        const verdicts = response.data.verdicts.filter(v => v.bidder_id === bidderId);
        setData({ bidder, extractions, verdicts });
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, [tenderId, bidderId]);

  if (loading) return <div className="text-center py-20 text-xl font-bold">Loading bidder details...</div>;
  if (!data?.bidder) return <div className="text-center py-20 text-red-500">Bidder not found.</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-10">
      <div className="max-w-6xl mx-auto">
        <button onClick={() => navigate(`/dashboard/${tenderId}`)} className="text-blue-600 mb-6 font-medium hover:underline">
          &larr; Back to Dashboard
        </button>
        
        <h1 className="text-4xl font-extrabold text-gray-800 mb-2">{data.bidder.name}</h1>
        <p className="text-gray-500 mb-8">Detailed Criteria Evaluation Report</p>

        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-100 text-gray-600 text-[10px] font-black uppercase tracking-[0.15em]">
                <th className="p-4 pl-6">Criterion</th>
                <th className="p-4 text-center">Pipeline Routing</th>
                <th className="p-4">Extracted Value</th>
                <th className="p-4">Status & Confidence</th>
                <th className="p-4">System Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data.extractions.map(ext => {
                const verdict = data.verdicts.find(v => v.criterion_id === ext.criterion_id);
                const isExpanded = expandedRow === ext.id;
                
                let badgeClass = "bg-gray-200 text-gray-800";
                if (verdict?.status === 'Eligible') badgeClass = "bg-green-100 text-green-800 border border-green-200";
                if (verdict?.status === 'Not Eligible') badgeClass = "bg-red-100 text-red-800 border border-red-200";
                if (verdict?.status === 'Needs Review') badgeClass = "bg-amber-100 text-amber-800 border border-amber-200";

                // Routing Logic
                const getRoutingInfo = (docName) => {
                  if (!docName) return { type: 'N/A', method: 'N/A', color: 'bg-gray-100 text-gray-400' };
                  const ext = docName.split('.').pop().toLowerCase();
                  if (ext === 'pdf') return { type: 'PDF', method: 'Hybrid OCR/Vector', color: 'bg-rose-50 text-rose-700 border-rose-100' };
                  if (ext === 'docx') return { type: 'DOCX', method: 'Native XML', color: 'bg-indigo-50 text-indigo-700 border-indigo-100' };
                  if (['jpg', 'jpeg', 'png'].includes(ext)) return { type: 'IMG', method: 'Tesseract OCR', color: 'bg-violet-50 text-violet-700 border-violet-100' };
                  return { type: ext.toUpperCase(), method: 'Binary Stream', color: 'bg-slate-50 text-slate-700 border-slate-100' };
                };
                const routing = getRoutingInfo(ext.source_document);

                return (
                  <React.Fragment key={ext.id}>
                    <tr className="hover:bg-gray-50 cursor-pointer transition" onClick={() => setExpandedRow(isExpanded ? null : ext.id)}>
                      <td className="p-4 pl-6 font-medium text-gray-800 max-w-xs truncate" title={ext.criteria?.text}>
                        {ext.criteria?.criterion_code || ext.criteria?.category}
                      </td>
                      <td className="p-4">
                        <div className="flex flex-col items-center gap-1">
                          <div className={`px-2 py-0.5 rounded border text-[9px] font-black tracking-widest uppercase ${routing.color}`}>
                            {routing.type}
                          </div>
                          <div className="text-[8px] text-gray-400 font-bold uppercase tracking-tighter">
                            {routing.method}
                          </div>
                        </div>
                      </td>
                      <td className="p-4 text-gray-600 font-mono text-sm">
                        {ext.extracted_value || 'Not Found'}
                      </td>
                      <td className="p-4">
                        <div className="flex flex-col gap-1">
                          <div className="flex items-center gap-2">
                            <span className={`px-3 py-1 rounded-full text-xs font-bold w-fit ${badgeClass}`}>
                              {verdict?.status || 'Pending'}
                            </span>
                            {verdict?.overridden_by && (
                              <span className="bg-slate-900 text-white text-[8px] font-black px-1.5 py-0.5 rounded tracking-tighter uppercase">
                                Manual
                              </span>
                            )}
                          </div>
                          {ext.extraction_confidence && (
                            <div className="flex items-center gap-2 mt-1">
                              <div className="w-24 bg-gray-200 rounded-full h-1.5 overflow-hidden">
                                <div 
                                  className={`h-full rounded-full ${
                                    ext.extraction_confidence >= 0.85 ? 'bg-emerald-500' : 
                                    ext.extraction_confidence >= 0.7 ? 'bg-amber-500' : 'bg-red-500'
                                  }`}
                                  style={{ width: `${ext.extraction_confidence * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-[9px] font-bold text-gray-400 uppercase">
                                {Math.round(ext.extraction_confidence * 100)}%
                              </span>
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="p-4 text-sm text-gray-500 max-w-sm">
                        {verdict?.reason || 'Processing...'}
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr className="bg-blue-50/30 border-b border-gray-100">
                        <td colSpan="5" className="p-6 px-10">
                          <div className="grid grid-cols-2 gap-8">
                            <div>
                              <h4 className="font-bold text-xs uppercase tracking-wider text-gray-400 mb-2">Original Requirement</h4>
                              <p className="text-gray-800 text-sm bg-white p-4 rounded-xl shadow-sm border border-gray-100">{ext.criteria?.text}</p>
                            </div>
                            <div>
                              <div className="flex justify-between items-center mb-2">
                                <h4 className="font-bold text-xs uppercase tracking-wider text-gray-400">Source Evidence</h4>
                                <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded-lg border text-[8px] font-black uppercase tracking-widest ${routing.color}`}>
                                  <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                                  Verified {routing.type} Route
                                </div>
                              </div>
                              <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                                <div className="text-xs font-bold text-blue-600 mb-1 flex items-center gap-2">
                                  <svg className="w-3 h-3 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>
                                  {ext.source_document ? `${ext.source_document} (Page ${ext.source_page || 1})` : 'No document cited'}
                                </div>
                                <p className="text-gray-700 text-sm italic border-l-4 border-blue-400 pl-4 py-2 mb-3 mt-2 bg-blue-50/50 rounded-r-lg">
                                  "{ext.source_excerpt || 'No excerpt provided.'}"
                                </p>
                                
                                {verdict?.status === 'Needs Review' && verdict?.review_sub_reason && (
                                  <div className="mt-4 pt-4 border-t border-gray-100">
                                    <div className="text-[10px] font-black text-amber-600 uppercase tracking-widest mb-1">Ambiguity Detected</div>
                                    <span className="bg-amber-100 text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded">
                                      {verdict.review_sub_reason.replace('_', ' ')}
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>

                          {/* Manual Override Section */}
                          <div className="mt-8 pt-6 border-t border-gray-200">
                            <div className="flex items-center gap-2 mb-4">
                              <div className="w-8 h-8 bg-slate-900 rounded-lg flex items-center justify-center">
                                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                              </div>
                              <h3 className="text-sm font-black uppercase tracking-widest text-slate-900">Officer Governance Override</h3>
                            </div>
                            
                            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200">
                              <p className="text-xs text-slate-500 mb-4 font-medium italic">
                                As per CRPF Procurement Guidelines, manual overrides are permitted but must be justified. Every override is hashed and chained into the immutable Audit Log.
                              </p>
                              
                              <div className="flex flex-col md:flex-row gap-6">
                                <div className="flex-1">
                                  <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Override Justification</label>
                                  <textarea 
                                    className="w-full p-4 rounded-xl border border-slate-200 focus:ring-2 focus:ring-slate-900 transition text-sm h-24"
                                    placeholder="State the reason for this manual decision (e.g. Verified original physical certificate, Threshold met via clause 4.1 exemption...)"
                                    id={`override-reason-${ext.id}`}
                                  ></textarea>
                                </div>
                                <div className="flex flex-col gap-3 justify-end min-w-[200px]">
                                  <button 
                                    onClick={async () => {
                                      const reason = document.getElementById(`override-reason-${ext.id}`).value;
                                      if(!reason) return alert("Justification is mandatory for audit trail.");
                                      await axios.post(`${API_BASE_URL}/api/verdicts/${verdict.id}/override`, {
                                        officer_id: localStorage.getItem('officerId') || 'SYSTEM_OR_OFFICER',
                                        new_status: 'Eligible',
                                        reason: reason
                                      });
                                      window.location.reload();
                                    }}
                                    className="bg-emerald-600 text-white px-6 py-3 rounded-xl font-bold text-sm hover:bg-emerald-700 shadow-lg shadow-emerald-100 transition"
                                  >
                                    Mark as ELIGIBLE
                                  </button>
                                  <button 
                                    onClick={async () => {
                                      const reason = document.getElementById(`override-reason-${ext.id}`).value;
                                      if(!reason) return alert("Justification is mandatory for audit trail.");
                                      await axios.post(`${API_BASE_URL}/api/verdicts/${verdict.id}/override`, {
                                        officer_id: localStorage.getItem('officerId') || 'SYSTEM_OR_OFFICER',
                                        new_status: 'Not Eligible',
                                        reason: reason
                                      });
                                      window.location.reload();
                                    }}
                                    className="bg-red-600 text-white px-6 py-3 rounded-xl font-bold text-sm hover:bg-red-700 shadow-lg shadow-red-100 transition"
                                  >
                                    Mark as NOT ELIGIBLE
                                  </button>
                                </div>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default BidderDetail;
