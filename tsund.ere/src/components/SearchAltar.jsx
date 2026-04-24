import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';

const SearchAltar = ({ query, setQuery, onSearch, isSearching }) => {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full flex-1 flex flex-col items-center justify-center px-6"
    >
      <div className="relative mb-10 flex flex-col items-center z-[5]">
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
        <motion.h1 
          className="text-8xl md:text-[8rem] font-bold tracking-tighter uppercase text-ink relative border-white"
          animate={{ y: [0, -10, 0] }}
          transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
        >
          tsund.ere
        </motion.h1>
        <motion.div 
          className="h-[1px] w-48 bg-gradient-to-r from-transparent via-accent to-transparent mt-4"
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ delay: 0.5, duration: 1.5 }}
        />
      </div>

      <div className="w-full max-w-xl relative group">
        {/* The "Solid" Rounded Rectangle Background - Color Layer */}
        <motion.div 
          className="absolute -inset-x-8 top-0 -bottom-24 rounded-b-[4rem] rounded-t-[2rem] pointer-events-none z-0 overflow-hidden"
          initial={{ opacity: 0.2 }}
          animate={{ 
            opacity: isFocused ? 1 : 0.4,
            background: isFocused 
              ? 'linear-gradient(180deg, rgba(0,255,255,0.7) 0%, rgba(122,0,255,0.6) 50%, rgba(255,0,122,0.5) 100%)'
              : 'linear-gradient(180deg, rgba(0,255,255,0.8) 0%, rgba(122,0,255,0.7) 50%, rgba(255,0,122,0.6) 100%)'
          }}
          transition={{ duration: 0.8 }}
        />

        {/* Separate Backdrop Blur Layer - Sits over the color but behind the form */}
        <motion.div 
          className="fixed -inset-x-20 top-0 -bottom-34 rounded-b-[4rem] rounded-t-[2rem] pointer-events-none z-[0] backdrop-blur-[40px] p-2"
          style={{ opacity: 1, background:'rgb(0,0,0,0.4)'}}
        />

        <motion.form 
          onSubmit={(e) => { e.preventDefault(); onSearch(); }}
          className={`relative flex flex-col glass-morphism rounded-[2rem] overflow-hidden group shadow-2xl z-10 transition-all duration-500 ${
            isFocused ? 'bg-black/70 border-white/30' : 'bg-black/50 border-white/10'
          }`}
          whileHover={{ scale: 1.01 }}
        >
          <div className="flex items-center p-1.5 px-2">
            <div className="pl-4 pr-2 flex items-center justify-center">
              <motion.span 
                className={`material-symbols-outlined text-xl transition-colors ${isFocused || isSearching ? 'text-accent' : 'text-ink/30'}`}
                animate={isSearching ? { rotate: 360, color: '#00ffff' } : {}}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              >
                {isSearching ? 'orbit' : 'auto_awesome'}
              </motion.span>
            </div>
            <input 
              className="w-full bg-transparent border-none focus:ring-0 text-ink font-body text-xl py-4 placeholder:text-ink/10 outline-none" 
              placeholder="Input your intent to transmute..." 
              type="text"
              value={query}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              onChange={(e) => setQuery(e.target.value)}
            />
            <div className="pr-2">
              <button 
                type="submit"
                disabled={isSearching}
                className="bg-[linear-gradient(135deg,#00ffff,rgba(0,122,255,0.8))] text-bg font-heavy py-3 px-8 rounded-full hover:scale-105 active:scale-95 transition-all duration-300 font-headline uppercase tracking-widest text-[12px] disabled:opacity-50 shadow-[0_0_20px_rgba(0,255,255,0.2)]"
              >
                {isSearching ? '...' : 'SEARCH'}
              </button>
            </div>
          </div>
          
          {/* Loading Bar */}
          <div className="h-[2px] w-full bg-white/5 relative">
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
