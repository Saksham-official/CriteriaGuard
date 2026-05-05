import React from 'react';
import { useNavigate } from 'react-router-dom';
import Aurora from '../components/Aurora';

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen text-white selection:bg-blue-500/30 flex flex-col items-center justify-center p-6 text-center overflow-hidden relative">
      {/* Background Layers */}
      <div className="fixed inset-0 bg-black -z-20"></div>
      <div className="fixed inset-0 -z-10 opacity-70 pointer-events-none">
        <Aurora
          colorStops={["#7cff67", "#B497CF", "#5227FF"]}
          blend={0.5}
          amplitude={1.0}
          speed={1}
        />
      </div>

      {/* Header Badge */}
      <div className="animate-in fade-in slide-in-from-top-4 duration-1000 z-10">
        <span className="inline-block px-4 py-1.5 bg-white/5 border border-white/10 rounded-full text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-8 backdrop-blur-md">
          AI for Bharat - HackerEarth
        </span>
      </div>

      {/* Main Hero */}
      <div className="max-w-4xl animate-in fade-in zoom-in duration-1000 delay-200 z-10">
        <h1 className="text-5xl md:text-7xl font-black tracking-tighter leading-[0.95] mb-8">
          Tender eligibility, <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-blue-600">decided in seconds.</span>
        </h1>
        
        <p className="text-lg text-slate-400 font-medium max-w-2xl mx-auto mb-12 leading-relaxed">
          CriteriaGuard accelerates CRPF tender bids evaluation using 
          AI extraction and <span className="text-white">deterministic rule-based verdicts.</span>
        </p>

        <div className="flex flex-col md:flex-row items-center justify-center gap-4 mb-12">
          <button 
            onClick={() => navigate('/upload')}
            className="group relative px-8 py-4 bg-blue-600 rounded-2xl font-bold text-lg hover:bg-blue-500 transition-all shadow-2xl shadow-blue-500/20 active:scale-95 flex items-center gap-3 overflow-hidden w-full md:w-auto"
          >
            <span className="relative z-10">Begin Evaluation</span>
            <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 7l5 5m0 0l-5 5m5-5H6"></path>
            </svg>
            <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-blue-600 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </button>
          <div className="px-6 py-4 bg-white/5 border border-white/10 rounded-2xl flex items-center gap-3 backdrop-blur-md">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span className="text-xs font-black uppercase tracking-widest text-slate-400">Governance Ready</span>
          </div>
        </div>
      </div>

      {/* Philosophy Section - Human in the Loop */}
      <div className="max-w-4xl w-full bg-white/5 border border-white/10 p-8 md:p-12 rounded-[2.5rem] mt-12 animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-300 backdrop-blur-xl z-10">
        <div className="flex flex-col md:flex-row items-center gap-8 text-left">
          <div className="w-20 h-20 bg-blue-600 rounded-[1.5rem] flex items-center justify-center shrink-0 shadow-2xl shadow-blue-900/40">
            <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
          </div>
          <div>
            <h2 className="text-2xl font-black mb-3">Our Motive: Human-AI Collaboration</h2>
            <p className="text-slate-400 text-sm leading-relaxed">
              CriteriaGuard is not designed to replace procurement officers, but to <span className="text-blue-400 font-bold">augment their expertise.</span> 
              Our AI performs the repetitive labor of scanning thousands of pages, while the final verdict is always 
              presented to a human expert with clear "Explainable AI" flags for manual verification.
            </p>
          </div>
        </div>
      </div>

      {/* Feature Cards / How it Works */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl w-full mt-24 animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-500 z-10">
        <div className="bg-white/5 border border-white/10 p-8 rounded-[2rem] text-left backdrop-blur-md group hover:bg-white/10 transition-all">
          <div className="w-12 h-12 bg-blue-600/20 rounded-2xl flex items-center justify-center text-blue-400 mb-6 group-hover:scale-110 transition-transform">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
          </div>
          <h3 className="text-xl font-bold mb-3">1. Tender Analysis</h3>
          <p className="text-sm text-slate-400 leading-relaxed">Upload the master Tender PDF. AI extracts mandatory clauses, numeric thresholds, and required certifications automatically.</p>
        </div>

        <div className="bg-white/5 border border-white/10 p-8 rounded-[2rem] text-left backdrop-blur-md group hover:bg-white/10 transition-all">
          <div className="w-12 h-12 bg-purple-600/20 rounded-2xl flex items-center justify-center text-purple-400 mb-6 group-hover:scale-110 transition-transform">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
          </div>
          <h3 className="text-xl font-bold mb-3">2. Bidder Evaluation</h3>
          <p className="text-sm text-slate-400 leading-relaxed">Bulk upload bidder responses. Our engine routes files through Native parsing or OCR pipelines to verify evidence against criteria.</p>
        </div>

        <div className="bg-white/5 border border-white/10 p-8 rounded-[2rem] text-left backdrop-blur-md group hover:bg-white/10 transition-all">
          <div className="w-12 h-12 bg-emerald-600/20 rounded-2xl flex items-center justify-center text-emerald-400 mb-6 group-hover:scale-110 transition-transform">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
          </div>
          <h3 className="text-xl font-bold mb-3">3. Audit-Ready Results</h3>
          <p className="text-sm text-slate-400 leading-relaxed">Get a comparative matrix of eligible bidders. Every decision is cryptographically logged for 100% tamper-evident governance.</p>
        </div>
      </div>

      {/* Footer Branding */}
      <div className="mt-20 pb-12 flex items-center gap-2 opacity-30 grayscale hover:grayscale-0 hover:opacity-100 transition-all duration-500 cursor-default z-10">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-black text-white text-xs">CG</div>
        <span className="font-black tracking-tighter uppercase text-sm">CriteriaGuard</span>
      </div>
    </div>
  );
};

export default Landing;
