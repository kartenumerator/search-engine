import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';

const SearchAltar = ({ query, setQuery, onSearch, isSearching, theme }) => {
  const [isFocused, setIsFocused] = useState(false);

  const isNewspaper = theme === 'newspaper';

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full flex-1 flex flex-col items-center justify-center px-6"
    >
      <div className="relative mb-10 flex flex-col items-center z-[5]">
        {!isNewspaper && (
          <AnimatePresence>
            {!isFocused && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.3 }}
                exit={{ opacity: 0 }}
                className="absolute -inset-20 bg-accent/20 blur-[120px] rounded-full pointer-events-none"
                transition={{ duration: 0.5 }}
              />
            )}
          </AnimatePresence>
        )}
        <motion.h1 
          className={`text-5xl md:text-[8rem] font-bold tracking-tighter uppercase text-ink relative ${isNewspaper ? 'font-serif italic' : ''}`}
          animate={isNewspaper ? {} : { y: [0, -10, 0] }}
          transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
        >
          tsund.ere
        </motion.h1>
        {!isNewspaper && (
          <motion.div 
            className="h-[1px] w-48 bg-gradient-to-r from-transparent via-accent to-transparent mt-4"
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ delay: 0.5, duration: 1.5 }}
          />
        )}
        {isNewspaper && (
          <div className="mt-4 flex space-x-8 text-[10px] font-mono opacity-60 uppercase tracking-widest border-b border-ink/20 pb-2">
            <span>Vol. XXIII No. 154</span>
            <span>{new Date().toLocaleDateString()}</span>
            <span>Price: One Soul</span>
          </div>
        )}
      </div>

      <div className="w-full max-w-xl relative group">
        {/* The "Solid" Rounded Rectangle Background - Color Layer */}
        {!isNewspaper && (
          <motion.div 
            className="absolute -inset-x-4 md:-inset-x-8 top-0 -bottom-16 md:-bottom-24 rounded-b-[2.5rem] md:rounded-b-[4rem] rounded-t-[2rem] pointer-events-none z-0 overflow-hidden"
            initial={{ opacity: 0.2 }}
            animate={{ 
              opacity: isFocused ? 1 : 0.4,
              background: isFocused 
                ? 'linear-gradient(180deg, rgba(0,255,255,0.7) 0%, rgba(122,0,255,0.6) 50%, rgba(255,0,122,0.5) 100%)'
                : 'linear-gradient(180deg, rgba(0,255,255,0.8) 0%, rgba(122,0,255,0.7) 50%, rgba(255,0,122,0.6) 100%)'
            }}
            transition={{ duration: 0.8 }}
          />
        )}

        {/* Separate Backdrop Blur Layer */}
        {!isNewspaper && (
          <motion.div 
            className="fixed -inset-x-4 md:-inset-x-20 top-0 -bottom-24 md:-bottom-34 rounded-b-[2.5rem] md:rounded-b-[4rem] rounded-t-[2rem] pointer-events-none z-[0] backdrop-blur-[30px] md:backdrop-blur-[40px] p-2"
            style={{ opacity: 1, background:'rgba(0,0,0,0.4)'}}
          />
        )}

        <motion.form 
          onSubmit={(e) => { e.preventDefault(); onSearch(query, 1); }}
          className={`relative flex flex-col glass-morphism rounded-[1.5rem] md:rounded-[2rem] overflow-hidden group shadow-2xl z-10 transition-all duration-500 ${
            isNewspaper 
              ? 'bg-white/40 border-ink/20' 
              : (isFocused ? 'bg-black/70 border-white/30' : 'bg-black/50 border-white/10')
          }`}
          whileHover={isNewspaper ? {} : { scale: 1.01 }}
        >
          <div className="flex items-center p-1 md:p-1.5 px-2">
            <div className="pl-3 md:pl-4 pr-1 md:pr-2 flex items-center justify-center">
              <motion.span 
                className={`material-symbols-outlined text-lg md:text-xl transition-colors ${isFocused || isSearching ? 'text-accent' : 'text-ink/30'}`}
                animate={isSearching ? { rotate: 360, color: isNewspaper ? '#1a365d' : '#00ffff' } : {}}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              >
                {isSearching ? 'orbit' : 'search'}
              </motion.span>
            </div>
            <input 
              className="w-full bg-transparent border-none focus:ring-0 text-ink font-body text-base md:text-xl py-3 md:py-4 placeholder:text-ink/20 outline-none" 
              placeholder={isNewspaper ? "Search the classifieds..." : "Input your intent to transmute..."} 
              type="text"
              value={query}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              onChange={(e) => setQuery(e.target.value)}
            />
            <div className="pr-1 md:pr-2">
              <button 
                type="submit"
                disabled={isSearching}
                className={`${
                  isNewspaper 
                    ? 'bg-ink text-bg font-bold border-2 border-ink hover:bg-transparent hover:text-ink' 
                    : 'bg-[linear-gradient(135deg,#00ffff,rgba(0,122,255,0.8))] text-bg shadow-[0_0_20px_rgba(0,255,255,0.2)]'
                } font-heavy py-2.5 md:py-3 px-5 md:px-8 rounded-full hover:scale-105 active:scale-95 transition-all duration-300 font-headline uppercase tracking-widest text-[10px] md:text-[12px] disabled:opacity-50`}
              >
                {isSearching ? '...' : (isNewspaper ? 'QUERY' : 'SEARCH')}
              </button>
            </div>
          </div>
          
          {/* Loading Bar */}
          <div className={`h-[2px] w-full ${isNewspaper ? 'bg-ink/5' : 'bg-white/5'} relative`}>
            <motion.div 
              className="absolute h-full bg-accent"
              initial={{ width: "0%", opacity: 0 }}
              animate={isSearching ? { 
                width: "100%",
                opacity: 1
              } : { 
                width: "0%",
                opacity: 0
              }}
              transition={isSearching ? { 
                duration: 3.2, 
                ease: "linear"
              } : { duration: 0.3 }}
            />
          </div>
        </motion.form>
      </div>
    </motion.div>
  );
};

export default SearchAltar;
