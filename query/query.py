from dbm import dbm
from functools import lru_cache
import heapq
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import time

from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import crossencodertest
from nltk import pos_tag
import didyoumean
import redis 
import gemini


r = redis.Redis(host="localhost", port=6379, db=0)

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


while True :

    page = 1
    query = input("Enter query : ")
    start_time = time.time_ns()
    k1 = 1.2
    b = 0.75
    avg_doc_len = 500  # Replace with your actual average document length

    tokens = word_tokenize(query)
    filtered_query = []

    tagged_tokens = pos_tag(tokens)
    
    verb_branch = []
    checkers = {}
    for word, tag in tagged_tokens:
        if word.lower() in stop_words or len(word) <= 1:
            continue
            
        if tag.startswith('V'):
            verb_branch.append({"case": {"$eq": ["$word", word]}, "then": 3})
        else :
            verb_branch.append({"case": {"$eq": ["$word", word]}, "then": 2})

        wn_tag = get_wordnet_pos(tag)
        lemma = lemmatize_cached(word.lower(), wn_tag)
        if tag.startswith('N'):
            checkers[word.lower()]=lemma
            filtered_query.append(lemma)
        else :
            checkers[word.lower()]=word.lower()
            if lemma != word.lower() :
                if tag.startswith('V'):
                    verb_branch.append({"case": {"$eq": ["$word", lemma]}, "then": 3})
                filtered_query.append(word.lower())
            filtered_query.append(lemma)
    
    print(checkers)
    #checkingdoc = list(m.db.words.find({"word":{"$in":[checkers[c] for c in checkers]}}, {"word":1,"numberdocs":1}))
    #for doc in checkingdoc :
    #    for d in checkers :
    #        if checkers[d] == doc['word']:
    #            # filtered_query.append(checkers[d])
    #            del checkers[d]
    #            filtered_query.remove(checkers[d])
    #            break

    for word in list(checkers.keys()) :
        if r.exists(checkers[word]) :
            del checkers[word]
        else :
            filtered_query.remove(checkers[word])   
    
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

    print(f'Showing results for : {newquery}')

    # print(verb_branch)
    print("tokenised query")

    temp_key = "temp:result"

    print(filtered_query)

    missing_keys = []
    for key in filtered_query :
        if not r.exists(key) :
            missing_keys.append(key)
    # existence_results = results[:len(filtered_query)]
    # missing_keys = [k for k, exists in zip(filtered_query, existence_results) if not exists]

    print(missing_keys)

    addnewwords(missing_keys)

    pipe = r.pipeline()

    # for key in filtered_query:
    #     pipe.exists(key)

    # Combine scores
    pipe.zunionstore(temp_key, filtered_query, aggregate="SUM")

    # Get top 10 results
    pipe.zrevrange(temp_key, 0, 19, withscores=True)

    # Cleanup
    pipe.delete(temp_key)

    results = pipe.execute()
    

    combined_scores = results[1]

    urls = []
    for url, score in combined_scores:
        print(url.decode(), score)
        urls.append(url.decode())
    # start_time = time.time_ns()

    # total_docs = m.db.global_vars.find_one({"_id":"totaldocs"})["total_num"]
    # words = []
    # # for word in filtered_query :
    # words = list(m.db.words.find({"word":{"$in":filtered_query}}, {"word":1,"numberdocs":1}))
    # words.extend(checkingdoc)
    # wordict = {}
    # for word in words :
    #     word['idf'] = ((total_docs - word['numberdocs'] + 0.5)/(word['numberdocs']+0.5)) + 1

    #     if word['idf'] < 2 :
    #         filtered_query.remove(word['word'])
    #     else :
    #         wordict[word['word']] = word
    # # m.db.words.find({"word":{"$in":filtered_query}},[{"$set":{"idf":{"$log":[{"$divide":[{"$add":[{"$toDouble":{"$subtract":[total_docs, "$numberdocs"]}},0.5]}, {"$add":[0.5, {"$toDouble":"$numberdocs"}]}]},10]}}}])
    # # print(words)
    # print(*wordict.items(), sep='\n')

    # # Build the conditional logic for IDF injection
    # # This maps: word -> idf_value
    # idf_branches = [
    #     {"case": {"$eq": ["$word", word]}, "then": idf_val['idf']}
    #     for word, idf_val in wordict.items()
    # ]
    # # print(idf_branches)
    # pipeline = [
    #     {
    #         "$match": {
    #             "word": {"$in": list(wordict.keys())},
    #             # "concurrent":True
    #         }
    #     },

    #     {
    #         "$group": {
    #             "_id": "$url",
    #             "matched_terms": {"$addToSet": "$word"},
    #             "tf": {"$push": "$tf"},
    #             # Sum the individual term scores to get the final BM25 score for the document
    #             # "bm25_score": {    
    #             #     "$sum": {
    #             #         "$multiply": [
    #             #             {"$switch": {"branches": idf_branches, "default": 0}}, # IDF
    #             #             "$tf" # TF
    #             #         ]
    #             #     }
    #             # },

    #             "num_terms": {"$sum": 1},
    #         }
    #     },
    #     {
    #         "$sort": {
    #             "num_terms": -1
    #         }
    #     },
    #     {
    #         "$skip":page*10 
    #     },
    #     {
    #         "$limit": 100
    #     },
        
    # ]

    # docs = list(m.db.indexed_data.aggregate(pipeline, allowDiskUse=True))

    # res = []
    # for doc in docs :
    #     weight = 0
    #     for idx, word in enumerate(doc['matched_terms']):
    #         weight += doc['tf'][idx] * wordict[word]
    #     heapq.heappush(res, (weight, doc['url']))


    
    # print(*(heapq.nlargest(10, res)), sep='\n\n')
    # print(len(docs))
    # print(f"Fetching pages at {(time.time_ns() - start_time)/1000000000} s")

    hits = list(m.db.pages.find({"url":{"$in":urls}}, {"url":1, "title":1, "html":1, "meta_description":1}))
    print(f"Reranking at {(time.time_ns() - start_time)/1000000000} s")
    #print(len(docs))
    #print(docs[0])
    #for doc in docs :
        #print(doc,end='\n\n')

    if len(urls) == 0:
        print("No results found...")
    else : 
        res = (crossencodertest.rerank(newquery, hits, 10))
        print(f"Results in {(time.time_ns() - start_time)/1000000000} s")

        for doc in res[:10] :
            print(f"{doc['url']} | {doc['title']}\n")

        print('\n----------------------------------\n')
        print(gemini.summarize_ten_docs(res, newquery))
