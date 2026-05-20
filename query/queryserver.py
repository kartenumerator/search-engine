from dbm import dbm
from functools import lru_cache
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import time
from fastapi.responses import StreamingResponse
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import crossencodertest
from nltk import pos_tag
import didyoumean
import redis
import json
from fastapi import FastAPI, Query, Request
import asyncio
import anyio
import gemini

app = FastAPI()

r = redis.Redis(host="localhost", port=6379, db=0)
LOADED_PAGES = 3
stop_words = set(stopwords.words('english'))

lemmatizer = WordNetLemmatizer()
@lru_cache(maxsize=100000)
def lemmatize_cached(word, tag):
    return lemmatizer.lemmatize(word, pos=tag)


def get_wordnet_pos(tag):
    if tag.startswith('J'):
        return wordnet.ADJ # 'a'
    elif tag.startswith('V'):
        return wordnet.VERB # 'v'
    elif tag.startswith('N'):
        return wordnet.NOUN # 'n'
    elif tag.startswith('R'):
        return wordnet.ADV # 'r'
    else:
        return wordnet.NOUN # Default to Noun
    
# client = pymongo.MongoClient("mongodb://localhost:27017/")
# db = client.search_engine

m = dbm()
doc = m.db.words.find_one({"word":""})
# m.update_idf(doc)
# print(f"Time taken : {(time.time_ns()-start_time)/1000000000} s")

# query = "naruto uzumaki and sasuke uchiha porn"
def addnewwords(keys) :
    total_docs = m.db.global_vars.find_one({"_id":"totaldocs"})["total_num"]
    # words = []
    # for word in filtered_query :
    words = list(m.db.words.find({"word":{"$in":keys}}, {"word":1,"numberdocs":1}))
    # words.extend(checkingdoc)
    wordict = {}
    for word in words :
        word['idf'] = ((total_docs - word['numberdocs'] + 0.5)/(word['numberdocs']+0.5)) + 1
        wordict[word['word']] = word

    del words
    print('finished')

    # while True :
    docs = m.db.indexed_data.find({"word":{"$in":list(wordict.keys())}}, {"url":1, "word":1, "tf":1})
    # print(f'{idx} documents...')
    lenth = 0
    for doc in docs :
        lenth += 1
        try :
            weight = wordict[doc['word']]['idf']*doc['tf']
            r.zadd(doc['word'],{doc['url'] : weight})
        except Exception as e:
            #print(e)
            continue

def add_new_entries(results, wordict):
    print(len(results))
    for doc in results :
        for idx, word in enumerate(doc['matched_terms']) :
            try :
                weight = wordict[word]['idf']*doc['tf'][idx]
                # print(word,{doc['_id'] : weight})
                r.zadd(word,{doc['_id'] : weight})
            except Exception as e:
                print(e)
                continue

def gettokens(query):
    tokens = word_tokenize(query)
    filtered_query = []

    tagged_tokens = pos_tag(tokens)
    
    checkers = {}
    for word, tag in tagged_tokens:
        if word.lower() in stop_words or len(word) <= 1:
            continue
            
        wn_tag = get_wordnet_pos(tag)
        lemma = lemmatize_cached(word.lower(), wn_tag)
        if tag.startswith('N'):
            checkers[word.lower()]=lemma
            filtered_query.append(lemma)
        else :
            checkers[word.lower()]=word.lower()
            if lemma != word.lower() :
                filtered_query.append(word.lower())
            filtered_query.append(lemma)
    
    print(checkers)
    
    checkingdoc = list(m.db.words.find({"word":{"$in":[checkers[c] for c in checkers]}}, {"word":1,"numberdocs":1}))
    for doc in checkingdoc :
        found = False
        for d in checkers :
            if checkers[d] == doc['word']:
                found = True
                del checkers[d]
                break
        if not found :
            filtered_query.remove(doc['word'])
            
    
    # for word in list(checkers.keys()) :
    #     if r.exists(checkers[word]) :
    #         del checkers[word]
    #     else :
    #         filtered_query.remove(checkers[word])   
    
    subs = {}
    if len(checkers) > 0 :
        for word,check in checkers.items() :
            newword = (didyoumean.get_max_suggestion_word(check, m))
            filtered_query.append(newword)
            subs[word] = newword

    newquery = ""
    for token in tokens :
        if token in subs :
            newquery += subs[token]+" "
        else :
            newquery += token+" "

    print(f'filtered : {filtered_query}')
    return newquery, filtered_query, checkingdoc


def query_redis(query, page:int=1):
    start_time = time.time_ns()
    
    newquery,filtered_query, checkingdoc = gettokens(query)

    print(f'Showing results for : {newquery}')
    print("tokenised query")
    temp_key = "temp:result"

    print(filtered_query)

    missing_keys = []
    for key in filtered_query :
        if not r.exists(key) :
            missing_keys.append(key)

    print(missing_keys)

    # addnewwords(missing_keys)

    pipe = r.pipeline()

    # Combine scores
    pipe.zunionstore(temp_key, filtered_query, aggregate="SUM")

    # Get top 10 results
    pipe.zrevrange(temp_key, (int((page-1)/LOADED_PAGES)*LOADED_PAGES*10), (int((page-1)/LOADED_PAGES)*LOADED_PAGES*10)+LOADED_PAGES*10, withscores=True)

    # Cleanup
    pipe.delete(temp_key)

    results = pipe.execute()
    combined_scores = results[1]

    urls = []
    for url, score in combined_scores:
        print(url.decode(), score)
        urls.append(url.decode())

    print(f"Fetching pages at {(time.time_ns() - start_time)/1000000000} s")

    hits = list(m.db.pages.find({"url":{"$in":urls}}, {"_id":0, "url":1, "title":1, "html":1, "meta_description":1, "poster":1}))
    print(f"Reranking at {(time.time_ns() - start_time)/1000000000} s")
    #print(len(docs))
    #print(docs[0])
    #for doc in docs :
        #print(doc,end='\n\n')

    if len(urls) == 0:
        print("No results found...")
        return newquery, None, filtered_query, checkingdoc
        # return json.dumps({"type":"search", "data":{"results":[], "query":"No results found..."}})+'\n'
        # return
    else : 
        res = (crossencodertest.rerank(newquery, hits, LOADED_PAGES*10))
        print(f"Results in {(time.time_ns() - start_time)/1000000000} s")

        for doc in res:
            print(doc['url'], doc['cross_score'])
            # urls.append(url.decode())

        return newquery, res[((page-1)%LOADED_PAGES)*10:((page-1)%LOADED_PAGES)*10 + 10], filtered_query, checkingdoc
        # tosumdocs = []
        # for doc in res[:10] :
        #     tosumdocs.append({"title":doc['title'], 'html':doc['html'], 'url':doc['url'], 'meta_description':doc['meta_description']})
        #     del doc['html']
        # return {"Results":res[:10], "query":newquery}
        # return json.dumps({"type":"search", "data":{"results":res[:10], "query":newquery}}) + '\n'
        
def query_mongod(newquery, page, filtered_query, checkingdoc):
    # tokens = word_tokenize(query)
    
    # newquery, filtered_query, checkingdoc = gettokens(query)

    print(f'Showing results for : {newquery} from mongodb')

    # print(verb_branch)
    # print("tokenised query")

    start_time = time.time_ns()

    total_docs = m.db.global_vars.find_one({"_id":"totaldocs"})["total_num"]
    words = []
    # for word in filtered_query :
    words = list(m.db.words.find({"word":{"$in":filtered_query}}, {"word":1,"numberdocs":1}))
    words.extend(checkingdoc)
    wordict = {}
    for word in words :
        word['idf'] = ((total_docs - word['numberdocs'] + 0.5)/(word['numberdocs']+0.5)) + 1
        # if word['idf'] < 5 :
        #     filtered_query.remove(word['word'])
        # else :
        wordict[word['word']] = word
    # m.db.words.find({"word":{"$in":filtered_query}},[{"$set":{"idf":{"$log":[{"$divide":[{"$add":[{"$toDouble":{"$subtract":[total_docs, "$numberdocs"]}},0.5]}, {"$add":[0.5, {"$toDouble":"$numberdocs"}]}]},10]}}}])
    # print(words)
    print(*wordict.items(), sep='\n')

    # Build the conditional logic for IDF injection
    # This maps: word -> idf_value
    idf_branches = [
        {"case": {"$eq": ["$word", word]}, "then": idf_val['idf']}
        for word, idf_val in wordict.items()
    ]

    # print(idf_branches)
    pipeline = [
        {
            "$match": {
                "word": {"$in": list(wordict.keys())},
                # "concurrent":True
            }
        },

        {
            "$group": {
                "_id": "$url",
                "matched_terms": {"$addToSet": "$word"},
                "tf": {"$push": "$tf"},
                # Sum the individual term scores to get the final BM25 score for the document
                "bm25_score": {    
                    "$sum": {
                        "$multiply": [
                            {"$switch": {"branches": idf_branches, "default": 0}}, # IDF
                            "$tf" # TF
                        ]
                    }
                },

                # "num_terms": {"$sum": 1},
            }
        },
        {
            "$sort": {
                "bm25_score": -1
            }
        },
        {
            "$skip":(int((page-1)/(LOADED_PAGES)))*10 
        },
        {
            "$limit": LOADED_PAGES*10
        },
        
    ]

    docs = list(m.db.indexed_data.aggregate(pipeline, allowDiskUse=True))
    print(f"Fetching pages at {(time.time_ns() - start_time)/1000000000} s")

    hits = list(m.db.pages.find({"url":{"$in":[doc['_id'] for doc in docs]}}, {"_id":0,"url":1, "title":1, "html":1, "meta_description":1, "poster":1}))
    print(f"Reranking at {(time.time_ns() - start_time)/1000000000} s")
    
    if len(hits) == 0 :
        return None
    res = (crossencodertest.rerank(newquery, hits, LOADED_PAGES*10))
    print(f"Results in {(time.time_ns() - start_time)/1000000000} s")

    # for doc in res[:10] :
    #     del doc['html']

    return res[((page-1)%LOADED_PAGES)*10:((page-1)%LOADED_PAGES)*10 + 10], docs, wordict

# async def generate(query: str, page:int=1):
    
#     newquery, result, filtered_query, checkingdoc = query_redis(query, page)
#     # print(result)

#     if result == None or result[0]['cross_score'] < 0:
#         if result != None :
#             yield json.dumps({"type":"search", "data":{"results":result, "query":(newquery if newquery!=None else query)}, "db":"cache"}) + '\n'
        
#         result, data, wordict = query_mongod((newquery if newquery!=None else query), page, filtered_query, checkingdoc)
#         add_new_entries(data, wordict)

#     if result == None :
#         print("No results found...")
#         yield json.dumps({"type":"search", "data":{"results":[], "query":"No results found...", "db":"mongod"}})+'\n'
#         return
    
#     # print(result)
#     yield json.dumps({"type":"search", "data":{"results":result, "query":(newquery if newquery!=None else query)}, "db":"mongod"}) + '\n'
#     tosumdocs = []
#     for doc in result :
#         tosumdocs.append({"title":doc['title'], 'html':doc['html'], 'url':doc['url'], 'meta_description':doc['meta_description']})
#         del doc['html']
#     # return {"Results":res[:10], "query":newquery}
#     if page != 1 :
#         return
#     try :
#         rag = gemini.summarize_ten_docs(tosumdocs, newquery)
#         yield json.dumps({"type":"rag", "data":rag})+'\n'
#     except Exception as e :
#         print(e)
#         return


# @app.get("/search")
# async def search(query: str = Query(..., description="Search query string"), page:int=1):
#     return StreamingResponse(generate(query, page), media_type="application/json")

active_requests = {}

def sync_query_redis(query, page):
    """
    Wraps the synchronous query_redis function.
    Ensure everything inside query_redis (including gettokens) is synchronous.
    """
    # This is exactly your existing query_redis logic
    return query_redis(query, page)

def sync_query_mongod(newquery, page, filtered_query, checkingdoc):
    """
    Wraps your synchronous MongoDB pipeline and reranking.
    """
    return query_mongod(newquery, page, filtered_query, checkingdoc)

def sync_add_new_entries(data, wordict):
    """
    Wraps the synchronous redis background filling.
    """
    return add_new_entries(data, wordict)

# thread_limiter = anyio.CapacityLimiter(5)

async def generate(query: str, page: int, client_host: str):
    try:
        # 1. Offload Redis query & tokenization to a worker thread
        newquery, result, filtered_query, checkingdoc = await anyio.to_thread.run_sync(
            sync_query_redis, query, page
        )

        if result is None or result[0]['cross_score'] < 0:
            if result is not None:
                yield json.dumps({
                    "type": "search", 
                    "data": {"results": result, "query": (newquery if newquery else query)}, 
                    "db": "cache"
                }) + '\n'
                # Short yield pause allowing the event loop to check for cancellations
                await asyncio.sleep(0.001) 
            
            # 2. Offload MongoDB aggregation and Cross-Encoder to thread pool
            mongod_res = await anyio.to_thread.run_sync(
                sync_query_mongod, (newquery if newquery else query), page, filtered_query, checkingdoc
            )
            
            if mongod_res is None:
                print("No results found...")
                yield json.dumps({"type": "search", "data": {"results": [], "query": "No results found...", "db": "mongod"}}) + '\n'
                return
            
            result, data, wordict = mongod_res
            
            # Fire-and-forget cache populate or run in thread
            await anyio.to_thread.run_sync(sync_add_new_entries, data, wordict)

        if result is None:
            yield json.dumps({"type": "search", "data": {"results": [], "query": "No results found...", "db": "mongod"}}) + '\n'
            return
        
        yield json.dumps({
            "type": "search", 
            "data": {"results": result, "query": (newquery if newquery else query)}, 
            "db": "mongod"
        }) + '\n'
        await asyncio.sleep(0.001)

        tosumdocs = []
        for doc in result:
            tosumdocs.append({"title": doc['title'], 'html': doc['html'], 'url': doc['url'], 'meta_description': doc['meta_description']})
            # Try to avoid mutability side-effects if shared across cache, but matches original logic:
            if 'html' in doc: del doc['html']
            
        if page != 1:
            return

        try:
            # 3. Assuming gemini.summarize_ten_docs makes synchronous network requests, thread it too
            rag = await anyio.to_thread.run_sync(gemini.summarize_ten_docs, tosumdocs, newquery)
            yield json.dumps({"type": "rag", "data": rag}) + '\n'
        except Exception as e:
            print(f"RAG Error: {e}")
            return

    except asyncio.CancelledError:
        print(f"[-] Request canceled for host: {client_host}")
        # Clean up anything if required here
        raise
    finally:
        # Clean up the task registry when the generator finishes or is killed
        if active_requests.get(client_host) == asyncio.current_task():
            active_requests.pop(client_host, None)


@app.get("/search")
async def search(request: Request, query: str = Query(..., description="Search query string"), page: int = 1):
    client_host = request.client.host
    
    # Check if this host already has an execution thread working
    if client_host in active_requests:
        print(f"[!] New request received from {client_host}. Canceling older request.")
        old_task = active_requests[client_host]
        old_task.cancel()  # This raises CancelledError inside the generator execution context

    # Register the current running framework task
    current_task = asyncio.current_task()
    active_requests[client_host] = current_task

    return StreamingResponse(
        generate(query, page, client_host), 
        media_type="application/json"
    )