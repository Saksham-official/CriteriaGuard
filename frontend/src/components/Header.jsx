import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Header = () => {
  const [officerId, setOfficerId] = useState(localStorage.getItem('officerId') || '');
  const [isEditing, setIsEditing] = useState(!localStorage.getItem('officerId'));
  const navigate = useNavigate();
  const location = useLocation();

  const isLanding = location.pathname === '/';

  const handleSave = () => {
    if (officerId.trim()) {
      localStorage.setItem('officerId', officerId.trim());
      setIsEditing(false);
      window.location.reload();
    }
  };

  return (
    <header className={`
      px-8 py-4 flex justify-between items-center fixed top-0 w-full z-50 transition-all duration-500
      ${isLanding 
        ? 'bg-black/20 backdrop-blur-2xl border-b border-white/10' 
        : 'bg-white/70 backdrop-blur-2xl border-b border-slate-200 shadow-sm'}
    `}>
      <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
        </div>
        <span className={`text-xl font-black tracking-tighter ${isLanding ? 'text-white' : 'text-slate-900'}`}>
          Criteria<span className="text-blue-600">Guard</span>
        </span>
      </div>

      <div className="flex items-center gap-4">
        {isEditing ? (
          <div className={`flex items-center gap-2 p-1 rounded-xl border ${isLanding ? 'bg-white/10 border-white/10' : 'bg-slate-100 border-slate-200'}`}>
            <input 
              type="text" 
              placeholder="Enter Officer ID..." 
              value={officerId}
              onChange={(e) => setOfficerId(e.target.value)}
              className={`bg-transparent px-3 py-1.5 text-sm font-bold outline-none w-40 ${isLanding ? 'text-white placeholder:text-white/30' : 'text-slate-900 placeholder:text-slate-400'}`}
              onKeyPress={(e) => e.key === 'Enter' && handleSave()}
            />
            <button 
              onClick={handleSave}
              className="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-xs font-black uppercase tracking-widest hover:bg-blue-700 transition"
            >
              Identify
            </button>
          </div>
        ) : (
          <div className={`
            flex items-center gap-3 px-4 py-2 rounded-2xl group transition-all shadow-xl
            ${isLanding ? 'bg-white/10 border border-white/10 hover:bg-white/20' : 'bg-emerald-50 border border-emerald-100 hover:bg-emerald-100/50'}
          `}>
            <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
            </div>
            <div>
              <p className={`text-[10px] font-black uppercase tracking-widest leading-none mb-1 ${isLanding ? 'text-emerald-400' : 'text-emerald-600'}`}>Active Officer</p>
              <p className={`text-sm font-bold leading-none ${isLanding ? 'text-white' : 'text-slate-900'}`}>{officerId}</p>
            </div>
            <button 
              onClick={() => setIsEditing(true)}
              className={`ml-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded ${isLanding ? 'hover:bg-white/10 text-white/50 hover:text-white' : 'hover:bg-emerald-200 text-emerald-700'}`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
