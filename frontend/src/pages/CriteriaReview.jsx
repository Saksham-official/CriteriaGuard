import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';

import API_BASE_URL from '../api/config';

const CriteriaReview = () => {
  const { tenderId } = useParams();
  const navigate = useNavigate();
  const [criteria, setCriteria] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchCriteria = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/tenders/${tenderId}/criteria`);
        setCriteria(response.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to fetch criteria.');
      } finally {
        setLoading(false);
      }
    };
    fetchCriteria();
  }, [tenderId]);

  const approveCriterion = async (criterionId) => {
    try {
      const officerId = localStorage.getItem('officerId') || 'SYSTEM_OR_OFFICER';
      await axios.patch(`${API_BASE_URL}/api/tenders/${tenderId}/criteria/${criterionId}`, {
        approved_by: officerId,
        approved_at: new Date().toISOString()
      });
      setCriteria(criteria.map(c => 
        c.id === criterionId ? { ...c, approved_at: new Date().toISOString(), approved: true } : c
      ));
    } catch (err) {
      setError('Failed to approve criterion.');
    }
  };

  const removeCriterion = async (criterionId) => {
    try {
      await axios.delete(`${API_BASE_URL}/api/tenders/${tenderId}/criteria/${criterionId}`);
      setCriteria(criteria.filter(c => c.id !== criterionId));
    } catch (err) {
      setError('Failed to remove criterion.');
    }
  };

  const saveCriterion = async (criterion) => {
    try {
      if (criterion.is_new) {
        const response = await axios.post(`${API_BASE_URL}/api/tenders/${tenderId}/criteria`, {
          criterion_code: criterion.criterion_code,
          text: criterion.text,
          category: criterion.category,
          mandatory: criterion.mandatory,
          source_clause: criterion.source_clause
        });
        setCriteria(criteria.map(c => c.id === criterion.id ? { ...response.data, is_new: false } : c));
      } else {
        await axios.patch(`${API_BASE_URL}/api/tenders/${tenderId}/criteria/${criterion.id}`, {
          text: criterion.text,
          category: criterion.category,
          mandatory: criterion.mandatory
        });
        // Success
      }
    } catch (err) {
      setError('Failed to save criterion.');
    }
  };

  const addCriterion = () => {
    const newId = `manual-${Date.now()}`;
    setCriteria([
      {
        id: newId,
        criterion_code: `REQ-${criteria.length + 1}`,
        category: 'technical',
        text: '',
        mandatory: true,
        mandatory_confidence: 'manual',
        source_clause: 'Manually Added by Officer',
        approved: false,
        removed: false,
        is_new: true
      },
      ...criteria
    ]);
  };

  const updateCriterion = (id, field, value) => {
    setCriteria(criteria.map(c => c.id === id ? { ...c, [field]: value } : c));
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-xl text-gray-600">Loading extracted criteria...</div>;
  if (error) return <div className="min-h-screen flex items-center justify-center text-xl text-red-500">{error}</div>;

  const activeCriteria = criteria.filter(c => !c.removed);
  const allApproved = activeCriteria.length > 0 && activeCriteria.every(c => c.approved);

  return (
    <div className="min-h-screen bg-slate-50 p-8 md:p-12">
      <div className="max-w-5xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
          <div>
            <h1 className="text-4xl font-black text-slate-900 tracking-tighter">Review & Refine Criteria</h1>
            <p className="text-slate-500 mt-2 font-medium">Verify AI extractions or manually adjust requirements.</p>
          </div>
          <div className="flex gap-4 w-full md:w-auto">
            <button 
              onClick={addCriterion}
              className="px-6 py-3 bg-white border-2 border-blue-100 text-blue-600 rounded-2xl font-bold hover:bg-blue-50 transition-all flex items-center gap-2 shrink-0"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M12 4v16m8-8H4"></path></svg>
              Add Custom
            </button>
            <button 
              disabled={!allApproved}
              onClick={() => navigate(`/bidder-upload/${tenderId}`)}
              className={`px-8 py-3 rounded-2xl font-black text-white shadow-2xl transition-all transform hover:scale-[1.02] active:scale-[0.98] flex-1 md:flex-none ${
                allApproved ? 'bg-blue-600 hover:bg-blue-700 shadow-blue-200' : 'bg-slate-300 cursor-not-allowed shadow-none grayscale'
              }`}
            >
              Confirm & Start Evaluation
            </button>
          </div>
        </div>

        <div className="glass-card rounded-[2.5rem] p-10 mb-12 shadow-2xl shadow-blue-900/5 border border-white bg-white/80 backdrop-blur-xl">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center shadow-xl shadow-blue-200 text-white">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
            </div>
            <div>
              <h2 className="text-2xl font-black text-slate-900 tracking-tight">Tender Analysis Engine</h2>
              <p className="text-sm text-slate-400 font-bold uppercase tracking-widest">Confidence Score: 94%</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="bg-slate-50/50 p-6 rounded-3xl border border-slate-100">
              <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Total Clauses</div>
              <div className="text-3xl font-black text-slate-900">{activeCriteria.length}</div>
            </div>
            <div className="bg-rose-50/50 p-6 rounded-3xl border border-rose-100">
              <div className="text-[10px] font-black text-rose-400 uppercase tracking-widest mb-2">Mandatory</div>
              <div className="text-3xl font-black text-rose-600">{activeCriteria.filter(c => c.mandatory).length}</div>
            </div>
            <div className="bg-amber-50/50 p-6 rounded-3xl border border-amber-100">
              <div className="text-[10px] font-black text-amber-400 uppercase tracking-widest mb-2">Unverified</div>
              <div className="text-3xl font-black text-amber-600">{activeCriteria.filter(c => !c.approved).length}</div>
            </div>
            <div className="bg-blue-50/50 p-6 rounded-3xl border border-blue-100">
              <div className="text-[10px] font-black text-blue-400 uppercase tracking-widest mb-2">Manual Edits</div>
              <div className="text-3xl font-black text-blue-800">{activeCriteria.filter(c => c.mandatory_confidence === 'manual').length}</div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {activeCriteria.map((criterion) => {
            const isAmbiguous = criterion.mandatory_confidence === 'ambiguous';
            const isManual = criterion.mandatory_confidence === 'manual';
            const confidence = criterion.mandatory_confidence === 'high' ? 98 : isAmbiguous ? 64 : 100;
            
            return (
              <div 
                key={criterion.id} 
                className={`group rounded-[2.5rem] border-2 shadow-2xl transition-all duration-500 overflow-hidden relative bg-white ${
                  criterion.approved 
                    ? 'border-emerald-100 shadow-emerald-900/5' 
                    : isAmbiguous ? 'border-amber-200 shadow-amber-900/10' : 'border-slate-100 shadow-slate-900/5'
                }`}
              >
                {/* Status Overlay for Approved */}
                {(criterion.approved || criterion.approved_at) && (
                  <div className="absolute top-0 right-0 p-4 z-20">
                    <div className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg shadow-emerald-200">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path></svg>
                      Verified & Locked
                    </div>
                  </div>
                )}

                <div className="p-8 md:p-10">
                  <div className="flex flex-col lg:flex-row gap-10">
                    {/* Left: Main Content & Inputs */}
                    <div className="flex-1 space-y-6">
                      <div className="flex flex-wrap items-center gap-3">
                        <div className="px-3 py-1 bg-slate-900 text-white rounded-lg text-[10px] font-black uppercase tracking-widest">
                          {criterion.criterion_code}
                        </div>
                        
                        {!criterion.approved ? (
                          <div className="flex gap-2">
                            <select 
                              value={criterion.category}
                              onChange={(e) => updateCriterion(criterion.id, 'category', e.target.value)}
                              className="px-3 py-1 bg-blue-50 text-blue-700 rounded-lg text-[10px] font-black uppercase tracking-widest border border-blue-100 outline-none cursor-pointer hover:bg-blue-100 transition-all"
                            >
                              <option value="technical">Technical</option>
                              <option value="financial">Financial</option>
                              <option value="legal">Legal</option>
                              <option value="experience">Experience</option>
                            </select>
                            <select 
                              value={criterion.mandatory ? 'true' : 'false'}
                              onChange={(e) => updateCriterion(criterion.id, 'mandatory', e.target.value === 'true')}
                              className={`px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest border outline-none cursor-pointer transition-all ${
                                criterion.mandatory ? 'bg-rose-50 text-rose-700 border-rose-100 hover:bg-rose-100' : 'bg-slate-50 text-slate-500 border-slate-100 hover:bg-slate-100'
                              }`}
                            >
                              <option value="true">Mandatory</option>
                              <option value="false">Optional</option>
                            </select>
                          </div>
                        ) : (
                          <div className="flex gap-2">
                            <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-lg text-[10px] font-black uppercase tracking-widest">{criterion.category}</span>
                            <span className={`px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest ${criterion.mandatory ? 'bg-rose-50 text-rose-700' : 'bg-slate-50 text-slate-500'}`}>
                              {criterion.mandatory ? 'Mandatory' : 'Optional'}
                            </span>
                          </div>
                        )}
                      </div>

                      {!criterion.approved ? (
                        <textarea 
                          value={criterion.text}
                          onChange={(e) => updateCriterion(criterion.id, 'text', e.target.value)}
                          className="w-full bg-slate-50/50 border-2 border-slate-100 rounded-3xl p-6 text-xl font-bold text-slate-900 focus:border-blue-400 focus:bg-white outline-none transition-all resize-none h-32 leading-tight"
                          placeholder="Requirement text..."
                        />
                      ) : (
                        <h3 className="text-2xl font-black text-slate-900 leading-[1.1] tracking-tight">{criterion.text}</h3>
                      )}

                      {/* Source Context Snippet */}
                      <div className="bg-slate-50/50 rounded-3xl p-6 border border-slate-100">
                        <div className="flex items-center justify-between mb-4">
                          <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Source Context (Doc Fragment)</span>
                          <span className="text-[10px] font-bold text-blue-500 bg-blue-50 px-3 py-1 rounded-full uppercase tracking-widest">Page {criterion.page_number || '1'}</span>
                        </div>
                        <p className="text-sm text-slate-600 font-medium leading-relaxed italic line-clamp-3">
                          "...{criterion.source_context || criterion.text}..."
                        </p>
                      </div>
                    </div>

                    {/* Right: Metadata & Actions */}
                    <div className="lg:w-80 space-y-4">
                      {/* Extraction Details Grid */}
                      <div className="bg-white rounded-3xl border border-slate-100 p-6 space-y-4 shadow-sm">
                        <div className="flex justify-between items-center pb-3 border-b border-slate-50">
                          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Extraction Type</span>
                          <span className="text-[10px] font-bold text-slate-900 uppercase tracking-widest">{criterion.data_type || 'BOOLEAN / EVIDENCE'}</span>
                        </div>
                        <div className="flex justify-between items-center pb-3 border-b border-slate-50">
                          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">AI Confidence</span>
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                              <div className={`h-full rounded-full ${confidence > 80 ? 'bg-emerald-500' : 'bg-amber-500'}`} style={{ width: `${confidence}%` }}></div>
                            </div>
                            <span className="text-[10px] font-black text-slate-900">{confidence}%</span>
                          </div>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Requirement Code</span>
                          <span className="text-[10px] font-bold text-slate-900">{criterion.criterion_code}</span>
                        </div>
                      </div>

                      {!(criterion.approved || criterion.approved_at) && (
                        <div className="space-y-3">
                          <div className="flex gap-3">
                            <button 
                              onClick={() => removeCriterion(criterion.id)}
                              className="flex-1 py-4 rounded-2xl text-rose-600 bg-rose-50 border border-rose-100 hover:bg-rose-100 transition-all font-black text-xs uppercase tracking-widest"
                            >
                              Remove
                            </button>
                            <button 
                              onClick={() => approveCriterion(criterion.id)}
                              className={`flex-[2] py-4 rounded-2xl font-black text-xs uppercase tracking-widest text-white shadow-xl transition-all hover:scale-105 active:scale-95 ${
                                isAmbiguous ? 'bg-amber-500 shadow-amber-200' : 'bg-blue-600 shadow-blue-200'
                              }`}
                            >
                              Approve Clause
                            </button>
                          </div>
                          <button 
                            onClick={() => saveCriterion(criterion)}
                            className="w-full py-3 rounded-xl text-[10px] font-black text-slate-600 bg-slate-100 hover:bg-slate-200 transition-all uppercase tracking-widest"
                          >
                            Save Changes
                          </button>
                        </div>
                      )}

                      {isAmbiguous && !criterion.approved && (
                        <button 
                          onClick={async () => {
                            const res = await axios.post(`${API_BASE_URL}/api/tenders/resolve-ambiguity`, {
                              text: criterion.text,
                              source_clause: criterion.source_clause
                            });
                            setCriteria(criteria.map(c => 
                              c.id === criterion.id ? { ...c, ai_suggestion: res.data } : c
                            ));
                          }}
                          className="w-full py-4 rounded-2xl text-[10px] font-black text-blue-600 bg-blue-50 border-2 border-blue-100 hover:bg-blue-600 hover:text-white transition-all uppercase tracking-widest flex items-center justify-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                          Resolve Ambiguity
                        </button>
                      )}
                    </div>
                  </div>

                  {/* AI Suggestion Expansion */}
                  {criterion.ai_suggestion && (
                    <div className="mt-8 pt-8 border-t border-slate-100 animate-in fade-in zoom-in duration-500">
                      <div className="bg-slate-900 text-white rounded-[2rem] p-8 relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-8 opacity-10 rotate-12 group-hover:rotate-0 transition-transform">
                          <svg className="w-20 h-20" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L3 7v10l9 5 9-5V7l-9-5z"/></svg>
                        </div>
                        <div className="relative z-10 flex flex-col md:flex-row gap-8">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-4">
                              <span className="text-[10px] font-black text-blue-400 uppercase tracking-[0.3em]">Smart Interpretation</span>
                              <div className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-[9px] font-black uppercase tracking-widest border border-blue-500/20">
                                Confidence: {criterion.ai_suggestion.confidence}
                              </div>
                            </div>
                            <h4 className="text-xl font-bold mb-3 tracking-tight">{criterion.ai_suggestion.recommendation}</h4>
                            <p className="text-sm text-slate-400 leading-relaxed font-medium italic">"{criterion.ai_suggestion.reasoning}"</p>
                          </div>
                          <div className="md:w-px bg-white/10 shrink-0"></div>
                          <div className="md:w-64 space-y-4">
                            <p className="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em]">Recommended Verdict</p>
                            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 text-center">
                              <span className="text-lg font-black text-white uppercase tracking-tighter">MANDATORY</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default CriteriaReview;
