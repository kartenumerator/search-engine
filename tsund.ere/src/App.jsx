import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Routes, Route, useNavigate, useLocation, Navigate, useSearchParams } from 'react-router-dom';
import { AnimatePresence, motion } from 'motion/react';
import Navbar from './components/Navbar';
import SearchAltar from './components/SearchAltar';
import ResultsDisplay from './components/ResultsDisplay';
import Documentation from './components/Documentation';
import toast, {Toaster} from 'react-hot-toast'

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();

  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [didyoumean, setDidyoumean] = useState('')
  const [results, setResults] = useState(null);
  // const [page, setPage] = useState(1);
  const [theme, setTheme] = useState('dark');
  const [aiSummary, setAiSummary] = useState('');
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);


  // const [view, setView] = useState('home');

  const view = location.pathname === '/docs' ? 'docs' : 'home';
  
  // const [rag,setRagText] = useState("");

  const controllerref = useRef(null)

  useEffect(() => {
    if (theme === 'newspaper') {
      document.body.classList.add('theme-newspaper');
    } else {
      document.body.classList.remove('theme-newspaper');
    }
  }, [theme]);

  const handleSearch = useCallback((q, page) => {
    const quer = q || query;
    if (!quer.trim()) return; 
    setIsSearching(true);
    setResults(null);

  	setAiSummary('')
	    
    if (controllerref.current) {
      controllerref.current.abort();
    }

    const controller = new AbortController();
    controllerref.current = controller;
  	console.log(page);
    async function search(){
      const queryString = new URLSearchParams({query:quer, page:page}).toString();
      // url.searchParams.set("query",query)/
      console.log(queryString)
      const api = import.meta.env.VITE_API;
      console.log(api)
      const res = await fetch(`${api}/search?${queryString}`, {signal:controller.signal,});
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      setIsGeneratingSummary(true);
	
      let buffer = "";
	  let summarised = false;
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
			if (!summarised){
				setAiSummary("Error while generating. Too many requests..");
				setIsGeneratingSummary(false);
			}
        	break;
        }

        buffer += decoder.decode(value, { stream: true });

        const parts = buffer.split("\n");
        buffer = parts.pop();
        
        for (const part of parts) {
          if (!part.trim()) continue;

          const data = JSON.parse(part);

          if (data.type === "rag") {
            setAiSummary(prev => prev + data.data);
            console.log(data.data);
            setIsGeneratingSummary(false);
            summarised = true;
          }
          else if (data.type == "search") {
            let results = [];

            if ((quer.trim() != data.data.query.trim())) {
              setDidyoumean(data.query);
            }else {
              setDidyoumean('');
            }
            
            if (data.data.results[0].cross_score < 0 && data.db != "mongod"){
              toast.loading("Better results will come in a minute!", {duration:5000})
            }
            for(let obj of data.data.results){
              console.log(obj);
              let ota = {id : results.length, title:obj.title, type:obj.url, content:obj.meta_description.slice(0,1200)+'...'};
              if (obj.poster) {
                ota.poster = obj.poster;
              }
              results.push(ota);
            }

            setIsSearching(false);
            setResults(results)
            navigate(`/s?q=${encodeURIComponent(quer)}&page=${encodeURIComponent(page)}`);

          }
        }
      }
    }

    search();
  }, [query, navigate]);

// const handleSearch = useCallback((oq, requestedPage) => {
//     const activeQuery = oq || query;
//     if (!activeQuery.trim()) return;
    
//     const targetPage = requestedPage || 1;
//     // setPage(targetPage);
//     setIsSearching(true);
//     setAiSummary('');
//     setIsGeneratingSummary(false);
    
//     // Update URL with query
    
//     // Alchemical delay for results
//     setTimeout(() => {
//       const str = "best anime"
//       if (activeQuery !== str){
//         setDidyoumean(str)
//       } else {
//         setDidyoumean('')
//       }
//       const mockResults = [
//         { 
//           id: 1, 
//           title: 'The Chronomancer\'s Lost Journals', 
//           type: 'CODE_FRAGMENT', 
//           content: 'Entry 442: Time is not a river, but a series of interconnected pools...',
//           poster: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=1000'
//         },
//         { 
//           id: 2, 
//           title: 'Visual Echoes of the Void', 
//           type: 'VISUAL_RECORD', 
//           content: 'A recurring pattern detected in the cosmic background radiation.',
//           poster: 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=1000'
//         },
//         { 
//           id: 3, 
//           title: 'Recursive Logic in Spellcasting', 
//           type: 'ARCANE_LOGIC', 
//           content: 'How self-referential incantations increase mana efficiency by 24%.' 
//         },
//         { 
//           id: 4, 
//           title: 'Spectral Frequency Modulation', 
//           type: 'CODE_FRAGMENT', 
//           content: 'Optimizing the resonance between ethereal and physical data packets.' 
//         },
//         { 
//           id: 5, 
//           title: 'Digital Necromancy: A Guide', 
//           type: 'ARCANE_LOGIC', 
//           content: 'Retrieving deleted soul-data from the universal recycle bin.' 
//         },
//         { 
//           id: 6, 
//           title: 'Phantasmal Data Visualization', 
//           type: 'VISUAL_RECORD', 
//           content: 'Mapping high-dimensional ghost-space into 3D human perception.',
//           poster: 'https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=1000'
//         }
//       ];
//       setResults(mockResults);
//       setIsSearching(false);

//       // Start generating summary after results are "fetched"
//       setIsGeneratingSummary(true);
//       navigate(`/s?q=${encodeURIComponent(activeQuery)}&page=${encodeURIComponent(targetPage)}`);

//       setTimeout(() => {
//         setAiSummary(`Deciphering fragments for "${activeQuery}"... Our algorithms have identified a convergence of Chronomancy records and Spectral data. The primary resonance suggests that your query intersects with highly volatile ARCANE_LOGIC clusters located in the outer rims of the digital void. Exercise caution when merging these data streams. Additionally, we have detected secondary echo-signatures emanating from the deep-time archive, which indicates that your search may have triggered a temporal ripple. This ripple could potentially manifest as ghost-data in your results. Proceed with alchemical precision and maintain your focus on the core transmutation objectives.`);
//         setIsGeneratingSummary(false);
//       }, 1500);

//     }, 1200);
//   }, [query, navigate]);

  const handleNavigate = (view) => {
    if (view === 'docs') {
      navigate('/docs');
    } else {
      navigate('/');
    }
  };

  const reset = () => {
    setQuery('');
    setResults(null);
    setIsSearching(false);
    setAiSummary('');
 	setIsGeneratingSummary(false);
  };


  return (
    <div className="flex bg-bg text-ink font-body h-screen overflow-hidden selection:bg-ink selection:text-bg relative">
      {/* Global Background Blur Overlay */}
      <div className="fixed inset-0 backdrop-blur-[40px] pointer-events-none z-[1]" />
      
      <div className="relative z-10 flex w-full h-full overflow-hidden">
        <Navbar 
          onReset={reset} 
          onNavigate={handleNavigate} 
          theme={theme} 
          setTheme={setTheme} 
          currentView={view} 
        />
        
        <main className="flex-1 relative flex flex-col overflow-hidden">
          <AnimatePresence mode="wait">
            <Routes location={location} key={location.pathname}>
              <Route path="/" element={
                 <motion.div
                  key="landing"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                  className="flex-1 flex flex-col"
                >
                  <SearchAltar 
                    query={query}
                    setQuery={setQuery}
                    onSearch={handleSearch}
                    isSearching={isSearching}
                    theme={theme}
                  />
                </motion.div>
              } />
              
              <Route path="/s" element={
                 
                  <motion.div
                    key="results"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 flex flex-col"
                  >
                    <ResultsDisplay 
                      // query={query}
                      // setQuery={setQuery}
                      onSearch={handleSearch}
                      // isSearching={isSearching}
                      // setIsSearching={setIsSearching}
                      didyoumean={didyoumean}
                      results={results}
                      // page={page}
                      // setPage={setPage}
                      theme={theme}
                      aiSummary={aiSummary}
                      isGeneratingSummary={isGeneratingSummary}
                      onBack={() => {
                        setResults(null);
                        navigate('/');
                      }}
                    />
                  </motion.div>
                
              } />
              
              <Route path="/docs" element={
                <motion.div
                  key="docs"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                  className="absolute inset-0 flex flex-col z-20"
                >
                  <Documentation theme={theme} />
                </motion.div>
              } />
            </Routes>
          </AnimatePresence>
        </main>
      </div>
      <Toaster />
    </div>
  );
}
