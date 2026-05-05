import React, { useState, useCallback, useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import Navbar from './components/Navbar.jsx';
import SearchAltar from './components/SearchAltar.jsx';
import ResultsDisplay from './components/ResultsDisplay.jsx';

export default function App() {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [didyoumean, setDidyoumean] = useState('')
  const [results, setResults] = useState(null);
  const [page, setPage] = useState(1);
  const [theme, setTheme] = useState('dark');

  const [aiSummary, setAiSummary] = useState('');
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  
  // const [rag,setRagText] = useState("");

  const controllerref = useRef(null)

  useEffect(() => {
    if (theme === 'newspaper') {
      document.body.classList.add('theme-newspaper');
    } else {
      document.body.classList.remove('theme-newspaper');
    }
  }, [theme]);

  const handleSearch = useCallback((page) => {

    if (!query.trim()) return; 
    setIsSearching(true);

	setAiSummary('')
	    
    if (controllerref.current) {
      controllerref.current.abort();
    }

    const controller = new AbortController();
    controllerref.current = controller;
	console.log(page);
    async function search(){
      const queryString = new URLSearchParams({query:query, page:page}).toString();
      // url.searchParams.set("query",query)/
      console.log(queryString)

      const res = await fetch(`/search?${queryString}`, {signal:controller.signal,});
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

            if ((query.trim() != data.data.query.trim())) {
              setDidyoumean(data.query);
            }else {
              setDidyoumean('');
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
          }
        }
      }

      // fetch("/search?"+queryString, {signal:controller.signal,})
      //   .then(response => response.json()) // Converts response body to JSON
      //   .then(data => {
      //     console.log(data);
      //     let results = [];
          
      //     if ((query.trim() != data.query.trim())) {
      //       setDidyoumean(data.query);
      //     }else {
      //       setDidyoumean('');
      //     }

      //     for(let obj of data.Results){
      //       console.log(obj);
      //       let ota = {id : results.length, title:obj.title, type:obj.url,content:obj.meta_description.slice(0,1200)+'...'};
      //       if (obj.poster) {
      //         ota.poster = obj.poster;
      //       }
      //       results.push(ota);
      //     }

      //     setIsSearching(false);
      //     setResults(results)
      //   })   // Handles the parsed data
      //   .catch(error => console.error('Network Error:', error));
    }

    search();
  }, [query, page]);

  // const handleSearch = useCallback(() => {
  //   // const activeQuery = query;
  //   if (!query.trim()) return;
    
  //   // const targetPage = page || 1;
  //   setPage(page);
  //   setIsSearching(true);
    
  //   // Alchemical delay
  //   setTimeout(() => {
  //     const str = "best anime"
  //     if (query !== str){
  //       setDidyoumean(str)
  //     } else {
  //       setDidyoumean('')
  //     }
  //     setResults([
  //       { 
  //         id: 1, 
  //         title: 'The Chronomancer\'s Lost Journals', 
  //         type: 'CODE_FRAGMENT', 
  //         content: 'Entry 442: Time is not a river, but aKAJ FN GLKF JSBGLVS KHJDFNB ,SKVJ ESJN FLKS ZKDN DF LKCSJENF LAERGS LERJN FXKLZ SJMNCV LKJ SZNGLAKE JRSFNLI KJCN FLK WECKRJ; AORCLIEFNLJ series of interconnected pools...',
  //         poster: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=1000'
  //       },
  //       { 
  //         id: 2, 
  //         title: 'Visual Echoes of the Void', 
  //         type: 'VISUAL_RECORD', 
  //         content: 'A recurring pattern detected in the cosmic background radiation.',
  //         poster: 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=1000'
  //       },
  //       { 
  //         id: 3, 
  //         title: 'Recursive Logic in Spellcasting', 
  //         type: 'ARCANE_LOGIC', 
  //         content: 'How self-referential incantations increase mana efficiency by 24%.' 
  //       },
  //       { 
  //         id: 4, 
  //         title: 'Spectral Frequency Modulation', 
  //         type: 'CODE_FRAGMENT', 
  //         content: 'Optimizing the resonance between ethereal and physical data packets.' 
  //       },
  //       { 
  //         id: 5, 
  //         title: 'Digital Necromancy: A Guide', 
  //         type: 'ARCANE_LOGIC', 
  //         content: 'Retrieving deleted soul-data from the universal recycle bin.' 
  //       },
  //       { 
  //         id: 6, 
  //         title: 'Phantasmal Data Visualization', 
  //         type: 'VISUAL_RECORD', 
  //         content: 'Mapping high-dimensional ghost-space into 3D human perception.',
  //         poster: 'https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=1000'
  //       }
  //     ]);
  //     setIsSearching(false)
  //   }, 3200);
  // }, [query, page]);


  const reset = () => {
    setQuery('');
    setResults(null);
    setIsSearching(false);
    setAiSummary('');
 	setIsGeneratingSummary(false);
  };

  return (
    <div className="flex bg-bg text-ink font-body min-h-screen overflow-hidden selection:bg-ink selection:text-bg relative">
      {/* Global Background Blur Overlay */}
      <div className="fixed inset-0 backdrop-blur-[40px] pointer-events-none z-[1]" />
      
      <div className="relative z-10 flex w-full h-full">
        <Navbar onReset={reset} theme={theme} setTheme={setTheme} />
        
        <main className="flex-1 flex flex-col min-h-screen">
          <AnimatePresence mode="wait">
            {!results ? (
              <SearchAltar 
                key="landing"
                query={query}
                setQuery={setQuery}
                onSearch={handleSearch}
                isSearching={isSearching}
                theme={theme}
              />
            ) : (
              <ResultsDisplay 
                key="results"
                query={query}
                setQuery={setQuery}
                onSearch={handleSearch}
                isSearching={isSearching}
                didyoumean={didyoumean}
                results={results}
                page={page}
                setPage={setPage}
                theme={theme}
                aiSummary={aiSummary}
                isGeneratingSummary={isGeneratingSummary}
                onBack={() => setResults(null)}
              />
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
