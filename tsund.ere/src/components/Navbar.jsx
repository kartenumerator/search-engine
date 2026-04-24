import React from 'react';

const Navbar = ({ onReset }) => {
  return (
    <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-8 h-12 glass-morphism rounded-b-2xl border-t-0">
      <div className="flex items-center space-x-4">
        <h1 
          className="text-sm font-bold tracking-tighter uppercase cursor-pointer hover:text-accent transition-colors"
          onClick={onReset}
        >
          tsund.ere
        </h1>
        <div className="hidden sm:flex items-center space-x-3 px-3 py-0.5 rounded-full bg-white/5 border border-white/5">
          <div className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse"></div>
          <span className="text-[9px] font-mono opacity-50 uppercase tracking-widest">Active_Session</span>
        </div>
      </div>
      <div className="flex items-center space-x-6 text-[9px] font-bold uppercase tracking-[0.2em]">
        <button className="hover:text-accent transition-colors" onClick={onReset}>Archive</button>
        <button className="hover:text-accent transition-colors">Manifesto</button>
        <div className="w-6 h-6 rounded-full glass-morphism flex items-center justify-center hover:scale-110 transition-transform cursor-pointer">
          <span className="material-symbols-outlined text-[14px]">bolt</span>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
