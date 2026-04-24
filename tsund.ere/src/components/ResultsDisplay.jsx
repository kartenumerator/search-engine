import React from 'react';
import { motion } from 'motion/react';

const ResultSkeleton = () => (
  <motion.div 
    initial={{ opacity: 0.5 }}
    animate={{ opacity: [0.3, 0.6, 0.3] }}
    transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
    className="glass-morphism p-8 rounded-[2.5rem] relative overflow-hidden border-dashed border-white/10"
  >
    <div className="flex justify-between items-start mb-6">
       <div className="h-4 w-24 bg-white/5 rounded-full animate-pulse border border-white/5"></div>
       <div className="h-4 w-4 rounded-full bg-accent/20 animate-pulse"></div>
    </div>
    <div className="space-y-3">
      <div className="h-6 w-3/4 bg-white/10 rounded-lg animate-pulse"></div>
      <div className="h-4 w-full bg-white/5 rounded-md animate-pulse"></div>
      <div className="h-4 w-5/6 bg-white/5 rounded-md animate-pulse"></div>
    </div>
    
    {/* Wireframe lines */}
    <div className="absolute inset-0 pointer-events-none opacity-20">
      <div className="absolute top-0 left-1/4 w-[1px] h-full bg-gradient-to-b from-transparent via-white/20 to-transparent"></div>
      <div className="absolute top-0 left-2/4 w-[1px] h-full bg-gradient-to-b from-transparent via-white/20 to-transparent"></div>
      <div className="absolute top-1/2 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>
    </div>
  </motion.div>
);

const ResultsDisplay = ({ query, setQuery, onSearch, isSearching, results, didyoumean, onBack }) => {
  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full flex-1 flex flex-col h-full overflow-hidden p-6 pt-20"
    >
      <div className="flex flex-col mb-10 w-full max-w-4xl mx-auto">
        <div className="flex flex-col glass-morphism rounded-[2.5rem] overflow-hidden transition-all hover:bg-white/[0.05] border-white/10 shadow-2xl">
          <div className="flex items-center p-2">
            <motion.button 
              onClick={onBack}
              className="w-12 h-12 rounded-full flex items-center justify-center hover:bg-white/10 transition-colors ml-1"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <span className="material-symbols-outlined text-base">arrow_back</span>
            </motion.button>
            
            <form 
              onSubmit={(e) => { e.preventDefault(); onSearch(); }}
              className="flex-1 flex items-center px-4"
            >
              <input 
                className="bg-transparent border-none outline-none focus:ring-0 text-lg font-medium tracking-tight w-full placeholder:text-ink/20 py-2"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Refine your desire..."
              />
              <button 
                type="submit"
                disabled={isSearching}
                className="w-10 h-10 rounded-full flex items-center justify-center hover:text-accent transition-colors group"
              >
                <span className={`material-symbols-outlined text-xl transition-transform ${isSearching ? 'animate-spin text-accent' : 'group-hover:scale-110'}`}>
                  {isSearching ? 'progress_activity' : 'search'}
                </span>
              </button>
            </form>
          </div>
          
          {/* Top Loading Bar */}
          <div className="h-[2px] w-full bg-white/5 relative">
            <motion.div 
              className="absolute h-full bg-accent"
              initial={{ width: 0, opacity: 0 }}
              animate={isSearching ? { 
                width: ["0%", "100%"],
                opacity: 1
              } : { 
                width: "0%",
                opacity: 0
              }}
              transition={isSearching ? { 
                duration: 1.5, 
                repeat: Infinity, 
                ease: "linear"
              } : { duration: 0.3 }}
            />
          </div>
        </div>

        {didyoumean && !isSearching && (
          <motion.div 
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center space-x-2 pl-16 text-sm mt-4"
          >
            <span className="opacity-40 font-mono tracking-tighter uppercase text-[10px]">Suggestion //</span>
            <button 
              onClick={() => { setQuery(didyoumean); onSearch(didyoumean); }}
              className="text-accent hover:text-ink transition-colors font-bold tracking-tight"
            >
              {didyoumean}
            </button>
          </motion.div>
        )}
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto custom-scrollbar pr-4 pb-20">
        {isSearching ? (
          <>
            <ResultSkeleton />
            <ResultSkeleton />
            <ResultSkeleton />
          </>
        ) : (
          results.map((result, i) => (
            <motion.div 
              key={result.id}
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              onClick={()=>{window.open(result.type,'_blank')}}
              className="glass-morphism p-8 rounded-[2.5rem] hover:bg-white/[0.07] transition-all group cursor-pointer relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 w-1 h-full bg-accent scale-y-0 group-hover:scale-y-100 transition-transform origin-top"></div>
              <div className="flex justify-between items-start mb-4">
                 <span className="text-[9px] font-mono px-3 py-1 rounded-full border border-white/5 bg-white/5 uppercase tracking-tighter">{result.type}</span>
                 <span className="material-symbols-outlined text-accent text-xs opacity-0 group-hover:opacity-100 transition-all group-hover:rotate-12">auto_awesome</span>
              </div>
              <h3 className="text-xl font-bold mb-3 tracking-tight group-hover:text-accent transition-colors">{result.title}</h3>
              <p className="text-ink/50 text-sm leading-relaxed font-light">{result.content}</p>
            </motion.div>
          ))
        )}

        {!isSearching && (
          <div className="py-12 border-t border-white/5 text-center opacity-30">
            <p className="text-[10px] font-mono uppercase tracking-[0.3em]">End_Of_Archive</p>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default ResultsDisplay;
