import React from 'react';

const Navbar = ({ onReset, onNavigate, theme, setTheme, currentView }) => {
  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'newspaper' : 'dark');
  };

  return (
    <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-4 md:px-8 h-15 glass-morphism rounded-b-2xl border-t-0 border-glass-border">
      <div className="flex items-center space-x-3 md:space-x-4">
        <h1 
          className="text-xs md:text-[20px] font-bold tracking-tighter uppercase cursor-pointer hover:text-accent transition-colors"
          onClick={() => {
            onReset();
            onNavigate('home');
          }}
        >
          tsund.ere
        </h1>
        <div className="hidden sm:flex items-center space-x-3 px-3 py-0.5 rounded-full bg-ink/5 border border-ink/5">
          <div className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse"></div>
          <span className="text-[9px] font-mono opacity-50 uppercase tracking-widest">Active_Session</span>
        </div>
      </div>
      <div className="flex items-center space-x-4 md:space-x-8 text-[10px] md:text-sm font-bold uppercase tracking-[0.2rem] md:tracking-[0.15em]">
        <button 
          onClick={() => onNavigate('docs')}
          className={cn(
            "hover:text-accent transition-colors cursor-pointer",
            currentView === 'docs' && "text-accent"
          )}
        >
          Documentation
        </button>
        <div 
          onClick={toggleTheme}
          className={`w-8 h-8 rounded-full shadow-lg flex items-center justify-center hover:scale-110 transition-transform cursor-pointer ${theme === 'newspaper' ? 'bg-accent text-white border-2 border-accent' : 'glass-morphism'}`}
        >
          <span className="material-symbols-outlined text-base">
            {theme === 'newspaper' ? 'bolt' : 'bolt'}
          </span>
        </div>
      </div>
    </nav>
  );
};

// Simple utility if we can't import from elsewhere
function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}

export default Navbar;
