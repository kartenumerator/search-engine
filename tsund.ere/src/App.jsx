import React, { useState, useCallback } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import Navbar from './components/Navbar.jsx';
import SearchAltar from './components/SearchAltar.jsx';
import ResultsDisplay from './components/ResultsDisplay.jsx';

export default function App() {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [didyoumean, setDidyoumean] = useState('')
  const [results, setResults] = useState(null);

  const handleSearch = useCallback(() => {
    if (!query.trim()) return;
    setIsSearching(true);
    
    const queryString = new URLSearchParams({query:query}).toString();
    // url.searchParams.set("query",query)/
    console.log(queryString)
    fetch("/search?"+queryString)
      .then(response => response.json()) // Converts response body to JSON
      .then(data => {
        console.log(data)
        let results = []
        
        if ((query.trim() != data.query.trim())) {
          setDidyoumean(data.query)
        }else {
          setDidyoumean('')
        }

        for(let obj of data.Results){
          console.log(obj)
          results.push({id : results.length, title:obj.title, type:obj.url,content:obj.meta_description.slice(0,1200)+'...'})
        }

        setIsSearching(false);
        setResults(results)
      })   // Handles the parsed data
      .catch(error => console.error('Network Error:', error));
    // Alchemical delay
    // setTimeout(() => {
    //   const str = "best anime"
    //   if (query != str){
    //     setDidyoumean(str)
    //   }else {
    //     setDidyoumean('')
    //   }
    //   setResults([
    //     { id: 1, title: 'The Chronomancer\'s Lost Journals', type: 'CODE_FRAGMENT', content: 'Entry 442: Time is not a river, but a series of interconnected pools...' },
    //     { id: 2, title: 'Visual Echoes of the Void', type: 'VISUAL_RECORD', content: 'A recurring pattern detected in the cosmic background radiation.' },
    //     { id: 3, title: 'Recursive Logic in Spellcasting', type: 'ARCANE_LOGIC', content: 'How self-referential incantations increase mana efficiency by 24%.' }
    //   ]);
    //   setIsSearching(false)
    // }, 1200);
  }, [query]);

  const reset = () => {
    setQuery('');
    setResults(null);
    setIsSearching(false);
  };

  return (
    <div className="flex bg-bg text-ink font-body min-h-screen overflow-hidden selection:bg-ink selection:text-bg">
      
      <Navbar onReset={reset} />
      
      <main className="flex-1 flex flex-col min-h-screen">
        <AnimatePresence mode="wait">
          {!results ? (
            <SearchAltar 
              key="landing"
              query={query}
              setQuery={setQuery}
              onSearch={handleSearch}
              isSearching={isSearching}
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
              onBack={() => setResults(null)}
            />
          )}
        </AnimatePresence>
      </main>

      {/* Decorative background image - adapted for technical theme */}
    </div>
  );
}
