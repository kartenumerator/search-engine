import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { useSearchParams } from 'react-router-dom';
// import katex from "katex";
// import "katex/dist/katex.min.css";
import ReactMarkdown from "react-markdown";

const ResultSkeleton = ({ isNewspaper }) => (
  <motion.div 
    initial={{ opacity: 0.5 }}
    animate={{ opacity: [0.3, 0.6, 0.3] }}
    transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
    className={`glass-morphism p-8 rounded-[2.5rem] relative overflow-hidden ${isNewspaper ? 'border-ink/20 bg-ink/5 rounded-none border-dashed' : 'border-dashed border-white/10'}`}
  >
    <div className="flex justify-between items-start mb-6">
       <div className={`h-4 w-24 rounded-full animate-pulse border ${isNewspaper ? 'bg-ink/10 border-ink/10' : 'bg-white/5 border-white/5'}`}></div>
       <div className={`h-4 w-4 rounded-full animate-pulse ${isNewspaper ? 'bg-accent/10' : 'bg-accent/20'}`}></div>
    </div>
    <div className="space-y-3">
      <div className={`h-6 w-3/4 rounded-lg animate-pulse ${isNewspaper ? 'bg-ink/20' : 'bg-white/10'}`}></div>
      <div className={`h-4 w-full rounded-md animate-pulse ${isNewspaper ? 'bg-ink/10' : 'bg-white/5'}`}></div>
      <div className={`h-4 w-5/6 rounded-md animate-pulse ${isNewspaper ? 'bg-ink/10' : 'bg-white/5'}`}></div>
    </div>
  </motion.div>
);

const TypewriterText = ({ text, onComplete }) => {
  const [displayedText, setDisplayedText] = React.useState("");
  
  React.useEffect(() => {
    let index = 0;
    setDisplayedText("");
    const interval = setInterval(() => {
      if (index < text.length) {
        setDisplayedText((prev) => prev + text[index]);
        index++;
      } else {
        clearInterval(interval);
        if (onComplete) onComplete();
      }
    }, 8);
    return () => clearInterval(interval);
  }, [text, onComplete]);

  return (
    <p className="leading-relaxed">
      {displayedText}
      {(displayedText.length < text.length || displayedText.length < 1200) && (
        <motion.span 
          animate={{ opacity: [0, 1, 0] }} 
          transition={{ repeat: Infinity, duration: 0.8 }}
          className="inline-block w-1.5 h-4 bg-accent ml-1 align-middle"
        />
      )}
    </p>
  );
};

const AISummary = ({ summary, isLoading, isNewspaper }) => {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [isTypingFinished, setIsTypingFinished] = React.useState(false);
  const [showButton, setShowButton] = React.useState(false);
  const textRef = React.useRef(null);

  const handleTypingComplete = React.useCallback(() => {
    setIsTypingFinished(true);
  }, []);

  React.useEffect(() => {
    if (isTypingFinished && textRef.current) {
      const isLong = textRef.current.scrollHeight > textRef.current.offsetHeight;
      setShowButton(isLong);
    }
  }, [isTypingFinished, isExpanded]);

  if (!summary && !isLoading) return null;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`mb-10 p-6 md:p-8 relative border-l-2 border-accent/30 ${
        isNewspaper ? 'bg-ink/5 border-ink/40 font-serif' : 'glass-morphism rounded-[1.5rem] md:rounded-[2rem] bg-white/[0.02]'
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className="material-symbols-outlined text-accent animate-pulse">psychology</span>
          <h4 className="text-[10px] md:text-xs font-mono lowercase tracking-[0.3em] opacity-50">tsundere says.</h4>
        </div>
        {showButton && (
          <button 
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-[10px] font-mono uppercase tracking-widest text-accent hover:underline flex items-center"
          >
            {isExpanded ? 'Show Less' : 'Full Intel'}
            <span className="material-symbols-outlined text-xs ml-1">
              {isExpanded ? 'expand_less' : 'expand_more'}
            </span>
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <motion.div 
              animate={{ width: ["0%", "60%", "40%", "80%"] }}
              transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
              className="h-2 bg-accent/20 rounded-full"
            />
            <span className="text-[8px] font-mono animate-pulse">SYNTACTIC_ASSEMBLY...</span>
          </div>
          <div className="h-2 w-full bg-accent/5 rounded-full overflow-hidden">
            <motion.div 
              animate={{ x: ["-100%", "100%"] }}
              transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
              className="h-full w-24 bg-gradient-to-r from-transparent via-accent/40 to-transparent"
            />
          </div>
        </div>
      ) : (
        <div 
          ref={textRef}
          className={`text-sm md:text-base transition-all duration-500 overflow-hidden ${
            isNewspaper ? 'italic' : 'text-ink/80'
          } ${!isExpanded ? 'line-clamp-4' : ''}`}
        >
          {isTypingFinished ? (
            <p className="leading-relaxed"><ReactMarkdown>{summary}</ReactMarkdown></p>
          ) : (
            <TypewriterText text={summary.slice(0,800)+'...'} onComplete={handleTypingComplete} />
          )}
        </div>
      )}

      {/* Decorative corners for tech feel */}
      {!isNewspaper && (
        <>
          <div className="absolute top-4 right-4 w-2 h-2 border-t border-r border-white/20"></div>
          <div className="absolute bottom-4 right-4 w-2 h-2 border-b border-r border-white/20"></div>
        </>
      )}
    </motion.div>
  );
};

const ResultsDisplay = ({onSearch, results, didyoumean, onBack, theme, aiSummary, isGeneratingSummary }) => {
  const isNewspaper = theme === 'newspaper';
  const [searchParams] = useSearchParams();
  const q = searchParams.get('q'); // For URL like /search?q=react
  const p = searchParams.get('page'); // For URL like /search?q=react
  
  const [query,setQuery] = React.useState(q)
  const [page, setPage] = React.useState(parseInt(p))
  
  useEffect(()=>{
    if(results == null){
      // setIsSearching(true);
      onSearch(query, page);
    }
  }, [])

  const handleNext = () => {
  	setPage(page+1)
    onSearch(query, page+1);
  };

  const handlePrev = () => {
    if (page > 1) {
  	  setPage(page-1)
      onSearch(query, page-1);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={`w-full flex-1 flex flex-col h-full p-4 md:p-6 pt-24 md:pt-32 overflow-y-auto custom-scrollbar`}
    >
      <div className="flex flex-col mb-6 md:mb-10 w-full max-w-4xl mx-auto">
        <div className={`flex flex-col glass-morphism overflow-hidden transition-all shadow-2xl ${
          isNewspaper ? 'bg-transparent border-x-0 border-y-2 border-ink rounded-none shadow-none' : 'rounded-[2rem] md:rounded-[2.5rem] bg-white/[0.05] border-white/10'
        }`}>
          <div className="flex items-center p-1.5 md:p-2">
            <motion.button 
              onClick={() => { onBack(); setPage(1); }}
              className={`w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center transition-colors ml-1 ${isNewspaper ? 'hover:bg-ink hover:text-bg' : 'hover:bg-white/10'}`}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <span className="material-symbols-outlined text-sm md:text-base">arrow_back</span>
            </motion.button>
            
            <form 
              onSubmit={(e) => { e.preventDefault(); onSearch(query, 1); }}
              className="flex-1 flex items-center px-2 md:px-4"
            >
              <input 
                className={`bg-transparent border-none outline-none focus:ring-0 text-base md:text-lg font-medium tracking-tight w-full placeholder:text-ink/20 py-2 ${isNewspaper ? 'font-serif' : ''}`}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={isNewspaper ? "Refine your inquiry..." : "Refine your desire..."}
              />
              <button 
                type="submit"
                disabled={(results==null)}
                className={`w-8 h-8 md:w-10 md:h-10 rounded-full flex items-center justify-center transition-colors group ${isNewspaper ? 'hover:bg-ink hover:text-bg' : 'hover:text-accent'}`}
              >
                <span className={`material-symbols-outlined text-lg md:text-xl transition-transform ${(results==null) ? 'animate-spin text-accent' : 'group-hover:scale-110'}`}>
                  {(results==null) ? 'progress_activity' : 'search'}
                </span>
              </button>
            </form>
          </div>
          
          {/* Top Loading Bar */}
          <div className={`h-[2px] w-full relative ${isNewspaper ? 'bg-ink/10' : 'bg-white/5'}`}>
            <motion.div 
              className="absolute h-full bg-accent"
              initial={{ width: 0, opacity: 0 }}
              animate={(results==null) ? { 
                width: ["0%", "100%"],
                opacity: 1
              } : { 
                width: "0%",
                opacity: 0
              }}
              transition={(results==null) ? { 
                duration: 1.5, 
                repeat: Infinity, 
                ease: "linear"
              } : { duration: 0.3 }}
            />
          </div>
        </div>

        {didyoumean && !(results==null) && (
          <motion.div 
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className={`flex items-center space-x-2 pl-4 md:pl-16 text-sm mt-3 md:mt-4 ${isNewspaper ? 'italic' : ''}`}
          >
            <span className="opacity-40 font-mono tracking-tighter uppercase text-[9px] md:text-[10px]">Suggestion //</span>
            <button 
              onClick={() => { setQuery(didyoumean); onSearch(query, 1); }}
              className="text-accent hover:text-ink transition-colors font-bold tracking-tight text-xs md:text-sm"
            >
              {didyoumean}
            </button>
          </motion.div>
        )}
      </div>

      <div className="flex-1 space-y-4 pr-4 pb-20">
        <div className="max-w-4xl mx-auto w-full">
          {!(results==null) && (
            <AISummary 
              summary={aiSummary} 
              isLoading={isGeneratingSummary} 
              isNewspaper={isNewspaper} 
            />
          )}
          
          {(results==null) ? (
            <div className="space-y-4 ">
              <ResultSkeleton isNewspaper={isNewspaper} />
              <ResultSkeleton isNewspaper={isNewspaper} />
              <ResultSkeleton isNewspaper={isNewspaper} />
            </div>
          ) : (
            results.map((result, i) => (
            <motion.div 
              key={result.id}
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              onClick={()=>{window.open(result.type,'_blank')}}
              className={`glass-morphism p-6 md:p-8 transition-all group cursor-pointer relative overflow-hidden flex mb-4 ${
                isNewspaper 
                  ? 'bg-ink/5 border-ink/10 rounded-2xl hover:bg-ink/10' 
                  : 'rounded-[1.5rem] md:rounded-[2.5rem] hover:bg-white/[0.07]'
              }`}
              whileHover={{ scale: 1 }}
            >
              <div className="flex-1 min-w-0">
                <div className="absolute top-0 left-0 w-1 h-full bg-accent scale-y-0 group-hover:scale-y-100 transition-transform origin-top"></div>
                <div className="flex justify-between items-start mb-4">
                   <span className={`text-[9px] font-mono px-3 py-1 rounded-full border uppercase tracking-tighter ${isNewspaper ? 'border-ink/20 bg-ink/5' : 'border-white/5 bg-white/5'}`}>{result.type}</span>
                   <span className="material-symbols-outlined text-accent text-xs opacity-0 group-hover:opacity-100 transition-all group-hover:rotate-12">auto_awesome</span>
                </div>
                <h3 className={`text-lg md:text-xl font-bold mb-2 md:mb-3 tracking-tight group-hover:text-accent transition-colors break-words overflow-hidden ${isNewspaper ? 'font-headline leading-tight' : ''}`}>{result.title}</h3>
                <p className={`text-ink/60 text-xs md:text-sm leading-relaxed break-words overflow-hidden ${isNewspaper ? 'font-serif' : 'font-light'}`}>{result.content}</p>
                {isNewspaper && <div className="mt-4 text-[10px] font-bold underline cursor-pointer opacity-40 group-hover:opacity-100 transition-opacity">Read Full Article &rarr;</div>}
              </div>

              {result.poster && (
                <div className={`hidden md:block w-32 lg:w-48 h-auto shrink-0 ml-6 lg:ml-8 border bg-ink/5 overflow-hidden ${isNewspaper ? 'grayscale border-ink/10 rounded-xl' : 'rounded-2xl border-white/10 shadow-xl'}`}>
                  <img 
                    src={result.poster} 
                    alt={result.title} 
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 opacity-80"
                    referrerPolicy="no-referrer"
                  />
                </div>
              )}
            </motion.div>
          ))
        )}

        {!(results==null) && results.length > 0 && (
          <div className={`flex flex-col items-center py-12 space-y-4`}>
            <div className="flex items-center space-x-12">
              <motion.button
                onClick={handlePrev}
                disabled={page === 1}
                className={`flex flex-col items-center group transition-all ${
                  page === 1 ? 'opacity-10 cursor-not-allowed' : 'opacity-40 hover:opacity-100'
                }`}
                whileHover={page !== 1 ? { x: -5 } : {}}
              >
                <span className="material-symbols-outlined text-3xl mb-1">chevron_left</span>
                <span className="text-[9px] font-mono tracking-[0.2em] uppercase">Archive_Prev</span>
              </motion.button>

              <div className="flex flex-col items-center px-4">
                <span className="text-xl font-bold tracking-tighter text-accent">{page}</span>
                <span className="text-[10px] font-mono tracking-widest opacity-20 uppercase mb-1">Index</span>
              </div>

              <motion.button
                onClick={handleNext}
                className={`flex flex-col items-center group opacity-40 hover:opacity-100 transition-all`}
                whileHover={{ x: 5 }}
              >
                <span className="material-symbols-outlined text-3xl mb-1">chevron_right</span>
                <span className="text-[9px] font-mono tracking-[0.2em] uppercase">Archive_Next</span>
              </motion.button>
            </div>

            <div className="pt-12 text-center opacity-20 w-full flex items-center justify-center space-x-4">
              <div className="h-[1px] w-12 bg-gradient-to-r from-transparent to-ink/20"></div>
              <p className="text-[8px] font-mono uppercase tracking-[0.4em]">Continuum_Synchronized</p>
              <div className="h-[1px] w-12 bg-gradient-to-l from-transparent to-ink/20"></div>
            </div>
          </div>
        )}
        </div>
      </div>
    </motion.div>
  );
};

export default ResultsDisplay;
