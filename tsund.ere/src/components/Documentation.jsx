import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion, useScroll, useSpring, useTransform, AnimatePresence } from 'motion/react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from 'rehype-katex';
import "katex/dist/katex.min.css";

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const Documentation = () => {
  const [DOCUMENTATION_CONTENT, setDocs] = useState("")
  const containerRef = useRef(null);
  const [sections, setSections] = useState([]);
  const [activeHeadingId, setActiveHeadingId] = useState(-1);
  const offset = 0.015;
  const { scrollYProgress } = useScroll({
    container: containerRef,
  });

  const scrollToHeading = (element) => {
    if (element && containerRef.current) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const delayedProgress = useTransform(
    scrollYProgress,
    (v) => Math.max(0, v + offset) // 3% lag
  );
  
  const scaleY = useSpring(delayedProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001
  });
  
  // Use a motion value for the diamond position to avoid state-triggering re-renders during scroll
  const progressPercent = useTransform(delayedProgress, [0, 1], ["0%", "100%"]);
  const [currentProgress, setCurrentProgress] = useState(0);

  useEffect(() => {
    // We still need this for the section markers highlighting which depends on state
    return delayedProgress.on('change', (v) => {
      setCurrentProgress(v * 100);
    });
  }, [scrollYProgress]);

  // Handle active section calculation based on viewport scroll position
  const handleScroll = () => {
    if (containerRef.current && sections.length > 0) {
      const container = containerRef.current;
      const containerRect = container.getBoundingClientRect();
      
      let activeIndex = -1;
      const scrollTriggerBuffer = 120; // Px from top of viewing container
      
      for (let i = 0; i < sections.length; i++) {
        const el = sections[i].element;
        if (el) {
          const rect = el.getBoundingClientRect();
          const relativeTop = rect.top - containerRect.top;
          if (relativeTop <= scrollTriggerBuffer) {
            activeIndex = i;
          }
        }
      }
      setActiveHeadingId(activeIndex);
    }
  };

  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll, { passive: true });
    }
    return () => {
      if (container) {
        container.removeEventListener('scroll', handleScroll);
      }
    };
  }, [sections]);

  useEffect(() => {
    fetch("/documentation.md").then(res => res.text()).then(text => setDocs(text))
    const parseHeadings = () => {


      if (containerRef.current) {
        const container = containerRef.current;
        const allElements = Array.from(container.querySelectorAll('h1, h2'));
        // Skip first h1 (the title "ArcaneSearch Documentation")
        const h1Elements = allElements.filter(el => el.tagName === 'H1').slice(1);
        const containerRect = container.getBoundingClientRect();
        const maxScroll = container.scrollHeight - container.clientHeight;

        const headingTree = h1Elements.map((h1El, index) => {
          const subheadings = [];
          let nextEl = h1El.nextElementSibling;
          
          while (nextEl) {
            if (nextEl.tagName === 'H1') {
              break;
            }
            if (nextEl.tagName === 'H2') {
              const h2Rect = nextEl.getBoundingClientRect();
              const h2RelativeTop = h2Rect.top - containerRect.top + container.scrollTop;
              const h2TopPercent = maxScroll > 0 ? (h2RelativeTop / maxScroll) * 100 : 0;
              
              subheadings.push({
                title: nextEl.innerText,
                element: nextEl,
                top: Math.min(100, Math.max(0, h2TopPercent))
              });
            }
            nextEl = nextEl.nextElementSibling;
          }

          const h1Rect = h1El.getBoundingClientRect();
          const h1RelativeTop = h1Rect.top - containerRect.top + container.scrollTop;
          const h1TopPercent = maxScroll > 0 ? (h1RelativeTop / maxScroll) * 100 : 0;

          return {
            id: index + 1,
            title: h1El.innerText.replace(/^\d+\.\s*/, ''),
            element: h1El,
            top: Math.min(100, Math.max(0, h1TopPercent)),
            subheadings
          };
        });

        setSections(headingTree);
      }
    };

    const timeoutId = setTimeout(parseHeadings, 600);
    window.addEventListener('resize', parseHeadings);
    
    return () => {
      window.removeEventListener('resize', parseHeadings);
      clearTimeout(timeoutId);
    };
  }, []);

  return (
    <div className="flex w-full h-full bg-bg/50 backdrop-blur-md pt-12 relative overflow-hidden" id="documentation-page">
      {/* Sidebar Progress Tracker & Animated Index */}
      <div className="w-16 md:w-80 flex-shrink-0 flex relative z-40 bg-bg/15 border-r border-glass-border">
        {/* Dynamic Vertical Scrollbar / Diamond Line Tracker & Aligned Headings */}
        <div className="w-full flex-shrink-0 relative">
          <div className="absolute top-24 bottom-24 w-0.5 left-1/2 -translate-x-1/2 md:left-12 md:translate-x-0 flex flex-col items-center">
            {/* Background Track */}
            <div className="absolute inset-0 bg-ink/10 rounded-full animate-pulse-slow" id="progress-track-bg">
              <motion.div 
                className="w-full bg-accent origin-top"
                style={{ scaleY, height: '100%' }}
                id="progress-fill"
              />
            </div>

            {/* Animated Head Indicator */}
            <motion.div 
              className="absolute left-1/2 -translate-x-1/2 w-4 h-4 bg-accent rotate-45 shadow-[0_0_20px_rgba(255,0,122,0.8)] flex items-center justify-center z-50 pointer-events-none"
              style={{ 
                top: progressPercent,
                marginTop: '-8px'
              }}
              id="progress-head"
            >
              <div className="w-1.5 h-1.5 bg-bg rounded-full" />
            </motion.div>
            
            {/* Section Markers */}
            <div className="absolute inset-0 pointer-events-none">
              {sections.map((section, index) => {
                const isReached = currentProgress >= section.top - 0.5;
                const isActive = activeHeadingId === index;
                return (
                  <div 
                    key={section.id}
                    className="absolute left-1/2 -translate-x-1/2 group pointer-events-auto cursor-pointer"
                    style={{ top: `${section.top}%` }}
                    onClick={() => scrollToHeading(section.element)}
                  >
                    {/* Glowing diamond system restored */}
                    <div className={cn(
                      "w-5 h-5 rotate-45 border-2 flex items-center justify-center transition-all duration-300",
                      isReached
                        ? "bg-accent border-accent text-bg scale-110 shadow-[0_0_12px_rgba(255,0,122,0.5)]" 
                        : "bg-bg border-ink/20 text-ink/40 hover:border-accent/40"
                    )}>
                      <span className="-rotate-45 text-[9px] font-bold font-mono">
                        {section.id}
                      </span>
                    </div>

                    {/* Integrated Headings with dynamic subheadings listed aligned with the progress bar */}
                    <div className="hidden md:flex flex-col absolute left-8 top-1/2 -translate-y-1/2 w-56 pl-2 pointer-events-auto select-none">
                      <span className={cn(
                        "text-[11px] font-body tracking-wide transition-all duration-300 hover:text-accent font-semibold block uppercase leading-snug whitespace-nowrap overflow-hidden text-ellipsis",
                        isActive 
                          ? "text-accent scale-[1.02] translate-x-1" 
                          : (isReached ? "text-ink/80" : "text-ink/40")
                      )}>
                        {index + 1}. {section.title}
                      </span>
                      
                      {/* Subheadings listing with springy transition shown when this specific heading is opened/reached */}
                      <AnimatePresence initial={false}>
                        {isActive && section.subheadings && section.subheadings.length > 0 && (
                          <motion.div
                            key={`sub-${section.id}`}
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ 
                              height: 'auto', 
                              opacity: 1,
                              transition: {
                                height: {
                                  type: "spring",
                                  stiffness: 220,
                                  damping: 20
                                },
                                opacity: { duration: 0.15 }
                              }
                            }}
                            exit={{ 
                              height: 0, 
                              opacity: 0,
                              transition: {
                                height: { duration: 0.2 },
                                opacity: { duration: 0.1 }
                              }
                            }}
                            className="absolute top-full left-0 overflow-hidden pl-3 border-l border-accent/25 ml-1 mt-1.5 space-y-1 flex flex-col items-start w-full"
                          >
                            {section.subheadings.map((sub, sIdx) => {
                              return (
                                <button
                                  key={sIdx}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    scrollToHeading(sub.element);
                                  }}
                                  className="text-left text-[9px] font-mono text-ink/50 hover:text-accent/90 tracking-normal transition-colors cursor-pointer block w-full truncate py-0.5"
                                  title={sub.title}
                                >
                                  ◇ {sub.title}
                                </button>
                              );
                            })}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                    
                    {/* Lightweight mobile tooltips */}
                    <div className="md:hidden absolute left-10 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-ink text-bg text-[10px] rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 whitespace-nowrap z-50 translate-x-2 group-hover:translate-x-0 shadow-xl border border-glass-border font-bold">
                      {section.title}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div 
        ref={containerRef}
        className="flex-1 h-full overflow-y-auto px-6 md:px-20 py-16 scroll-smooth custom-scrollbar relative"
        id="documentation-scroll-container"
      >
        <div className="max-w-4xl mx-auto prose prose-invert prose-li:text-ink/80 prose-headings:text-ink prose-p:text-ink/80 prose-strong:text-accent prose-table:text-ink/70 prose-th:border-ink/20 prose-td:border-ink/10 relative selection:bg-accent/30 font-body">
          <ReactMarkdown
            remarkPlugins={[remarkMath, remarkGfm]}
            rehypePlugins={[rehypeKatex]}
            components={{
              table: ({ children }) => (
                <div className="my-8 overflow-x-auto rounded-2xl border border-glass-border shadow-lg bg-bg/5 backdrop-blur-sm">
                  <table className="min-w-full divide-y divide-glass-border text-left text-xs">
                    {children}
                  </table>
                </div>
              ),
              thead: ({ children }) => (
                <thead className="bg-ink/5 font-mono text-[10px] tracking-wider text-accent uppercase">
                  {children}
                </thead>
              ),
              tbody: ({ children }) => (
                <tbody className="divide-y divide-glass-border/40 font-body">
                  {children}
                </tbody>
              ),
              tr: ({ children }) => (
                <tr className="hover:bg-ink/5 transition-colors duration-150">
                  {children}
                </tr>
              ),
              th: ({ children }) => (
                <th className="px-3 py-2 font-bold text-accent border-b border-glass-border tracking-wider text-[15px]">
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className="px-3 py-2 text-ink/80 leading-relaxed font-medium text-[15px]">
                  {children}
                </td>
              ),
              img: ({ src, alt }) => (
                <img
                  src={src}
                  alt={alt}
                  className="my-8 block w-full h-auto object-cover overflow-hidden rounded-2xl border border-glass-border shadow-2xl bg-ink/5"
                  referrerPolicy="no-referrer"
                />
              )
            }}
          >
            {DOCUMENTATION_CONTENT}
          </ReactMarkdown>
        </div>
        
        {/* Footer padding for scrollability - ensures last section can reach top */}
        <div className="h-[70vh]" />
      </div>
    </div>
  );
};

export default Documentation;
