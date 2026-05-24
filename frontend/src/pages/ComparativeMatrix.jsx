import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';

import API_BASE_URL from '../api/config';

const ComparativeMatrix = () => {
  const { tenderId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMatrix = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/verdicts/tender/${tenderId}`);
        
        // Extract unique criteria
        const criteriaMap = {};
        response.data.extractions.forEach(ext => {
          if (ext.criteria && !criteriaMap[ext.criteria.id]) {
            criteriaMap[ext.criteria.id] = ext.criteria;
          }
        });
        
        setData({
          bidders: response.data.bidders,
          criteria: Object.values(criteriaMap),
          verdicts: response.data.verdicts
        });
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchMatrix();
  }, [tenderId]);

  if (loading) return <div className="text-center py-20 text-xl font-bold">Generating Comparison Matrix...</div>;

  const getVerdict = (bidderId, criterionId) => {
    return data.verdicts.find(v => v.bidder_id === bidderId && v.criterion_id === criterionId);
  };

  const renderStatusIcon = (status) => {
    switch (status) {
      case 'Eligible':
        return <span className="text-emerald-500 text-xl" title="Eligible">✅</span>;
      case 'Not Eligible':
        return <span className="text-red-500 text-xl" title="Not Eligible">❌</span>;
      case 'Needs Review':
        return <span className="text-amber-500 text-xl" title="Needs Review">⚠️</span>;
      default:
        return <span className="text-gray-300 text-xl">—</span>;
    }
  };

  const getBiddersRanking = () => {
    if (!data || !data.bidders || !data.bidders.length) return [];
    
    return [...data.bidders].map(bidder => {
      const bidderVerdicts = data.verdicts.filter(v => v.bidder_id === bidder.id);
      const passedCount = bidderVerdicts.filter(v => v.status === 'Eligible').length;
      const failedCount = bidderVerdicts.filter(v => v.status === 'Not Eligible').length;
      const reviewCount = bidderVerdicts.filter(v => v.status === 'Needs Review').length;
      const totalCount = bidderVerdicts.length;
      
      const failedMandatory = bidderVerdicts.filter(v => {
        const crit = data.criteria.find(c => c.id === v.criterion_id);
        return crit && crit.mandatory && v.status === 'Not Eligible';
      }).length;

      return {
        ...bidder,
        passedCount,
        failedCount,
        reviewCount,
        totalCount,
        failedMandatory
      };
    }).sort((a, b) => {
      if (a.failedMandatory !== b.failedMandatory) {
        return a.failedMandatory - b.failedMandatory;
      }
      return b.passedCount - a.passedCount;
    });
  };

  const rankings = getBiddersRanking();
  const topBidder = rankings.length > 0 && rankings[0].totalCount > 0 ? rankings[0] : null;

  return (
    <div className="min-h-screen p-6 md:p-10">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-6">
          <div>
            <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">Comparative Bidder Matrix</h1>
            <p className="text-slate-500 mt-2">Side-by-side eligibility comparison across all competing bidders.</p>
          </div>
          <div className="flex gap-4">
            <button 
              onClick={async () => {
                const officerId = localStorage.getItem('officerId') || 'SYSTEM_OR_OFFICER';
                window.open(`${API_BASE_URL}/api/reports/export/${tenderId}?officer_id=${officerId}`, '_blank');
              }}
              className="bg-slate-900 text-white px-5 py-2.5 rounded-xl font-bold hover:bg-slate-800 transition shadow-lg flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
              Download PDF Report
            </button>
            <button 
              onClick={() => navigate(`/dashboard/${tenderId}`)} 
              className="bg-white text-slate-700 border border-slate-200 px-5 py-2.5 rounded-xl font-semibold hover:bg-slate-50 transition shadow-sm"
            >
              &larr; Back to Dashboard
            </button>
          </div>
        </div>

        <div className="glass-card rounded-3xl shadow-2xl border border-slate-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-900 text-white">
                  <th className="p-6 sticky left-0 z-20 bg-slate-900 border-r border-slate-800 min-w-[300px]">
                    Criteria Requirement
                  </th>
                  {data.bidders.map(bidder => (
                    <th key={bidder.id} className="p-6 text-center min-w-[150px] border-r border-slate-800 last:border-0">
                      <div className="text-xs font-black uppercase tracking-widest text-slate-400 mb-1">Bidder</div>
                      <div className="font-bold truncate max-w-[120px] mx-auto" title={bidder.name}>
                        {bidder.name}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.criteria.map(criterion => (
                  <tr key={criterion.id} className="hover:bg-slate-50/50 transition">
                    <td className="p-6 sticky left-0 z-10 bg-white border-r border-slate-100 shadow-[2px_0_10px_rgba(0,0,0,0.02)]">
                      <div className="flex items-start gap-3">
                        <span className={`mt-1 flex-shrink-0 w-2 h-2 rounded-full ${criterion.mandatory ? 'bg-red-500' : 'bg-blue-400'}`}></span>
                        <div>
                          <div className="text-xs font-black text-slate-400 uppercase tracking-widest mb-1">
                            {criterion.category} {criterion.mandatory && '(Mandatory)'}
                          </div>
                          <div className="text-sm font-semibold text-slate-800 leading-snug">
                            {criterion.text}
                          </div>
                        </div>
                      </div>
                    </td>
                    {data.bidders.map(bidder => {
                      const verdict = getVerdict(bidder.id, criterion.id);
                      return (
                        <td key={`${bidder.id}-${criterion.id}`} className="p-6 text-center border-r border-slate-50 last:border-0">
                          <div className="flex flex-col items-center justify-center gap-1 group cursor-pointer" 
                               onClick={() => navigate(`/bidder/${tenderId}/${bidder.id}`)}>
                            <div className="transform group-hover:scale-125 transition duration-200">
                              {renderStatusIcon(verdict?.status)}
                            </div>
                            <div className="text-[10px] font-bold text-slate-400 opacity-0 group-hover:opacity-100 transition duration-200 uppercase tracking-tighter">
                              Details
                            </div>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {topBidder && (
          <div className="mt-12 bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950 p-8 rounded-[2rem] border border-slate-800 text-white shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl group-hover:bg-indigo-500/20 transition-all duration-700"></div>
            <div className="absolute bottom-0 left-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl group-hover:bg-blue-500/20 transition-all duration-700"></div>
            
            <div className="flex flex-col md:flex-row gap-6 items-start md:items-center relative z-10">
              <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-400/30 flex items-center justify-center text-3xl shadow-inner shrink-0">
                🏆
              </div>
              <div className="flex-1">
                <div className="text-[10px] font-black uppercase tracking-widest text-indigo-400 mb-1">
                  AI Evaluator Recommendation
                </div>
                <h2 className="text-2xl font-black tracking-tight">
                  Suggested Award: <span className="text-indigo-300 font-extrabold">{topBidder.name}</span>
                </h2>
                <p className="text-slate-400 text-sm mt-1.5 leading-relaxed font-medium">
                  Based on complete side-by-side criteria mapping, <span className="text-white font-bold">{topBidder.name}</span> demonstrates the highest alignment score, successfully passing <span className="text-emerald-400 font-bold">{topBidder.passedCount} out of {topBidder.totalCount || data.criteria.length}</span> criteria requirement ticks with <span className="text-white font-bold">{topBidder.failedMandatory === 0 ? "0 mandatory criteria failures" : `${topBidder.failedMandatory} mandatory criteria failures`}</span>.
                </p>
              </div>
              
              <div className="flex flex-col gap-2 shrink-0 w-full md:w-auto">
                <button
                  onClick={() => navigate(`/bidder/${tenderId}/${topBidder.id}`)}
                  className="px-6 py-3.5 bg-indigo-600 hover:bg-indigo-500 active:scale-95 text-white font-bold rounded-xl text-xs transition shadow-lg shadow-indigo-500/25 flex items-center justify-center gap-2"
                >
                  <span>View Details Report</span>
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="mt-8 flex gap-6 items-center justify-center text-xs font-bold text-slate-400 uppercase tracking-widest">
          <div className="flex items-center gap-2"><span className="text-xl">✅</span> Eligible</div>
          <div className="flex items-center gap-2"><span className="text-xl">❌</span> Not Eligible</div>
          <div className="flex items-center gap-2"><span className="text-xl">⚠️</span> Needs Review</div>
          <div className="ml-4 flex items-center gap-2 italic font-medium"><span className="w-2 h-2 rounded-full bg-red-500"></span> Mandatory</div>
          <div className="flex items-center gap-2 italic font-medium"><span className="w-2 h-2 rounded-full bg-blue-400"></span> Optional</div>
        </div>
      </div>
    </div>
  );
};

export default ComparativeMatrix;
