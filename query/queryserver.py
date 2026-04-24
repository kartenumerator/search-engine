from dbm import dbm
from functools import lru_cache
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import time

from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import crossencodertest
from nltk import pos_tag
import didyoumean

from fastapi import FastAPI, Query

app = FastAPI()

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

@app.get("/search")
async def search(query: str = Query(..., description="Search query string")):
    # query = input("Enter query : ")

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
        else :
            checkers[word.lower()]=word.lower()
            if lemma != word.lower() and tag.startswith('N'):
                if tag.startswith('V'):
                    verb_branch.append({"case": {"$eq": ["$word", lemma]}, "then": 3})
                filtered_query.append(lemmatize_cached(word.lower(), wordnet.NOUN))
            filtered_query.append(lemma)
    
    print(checkers)
    checkingdoc = list(m.db.words.find({"word":{"$in":[checkers[c] for c in checkers]}}, {"word":1,"numberdocs":1}))
    for doc in checkingdoc :
        for d in checkers :
            if checkers[d] == doc['word']:
                del checkers[d]
                break
        
    
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
                # "docs": {"$push": "$$ROOT"},
                # Sum the individual term scores to get the final BM25 score for the document
                "bm25_score": {    
                    "$sum": {
                        "$multiply": [
                            {"$switch": {"branches": idf_branches, "default": 0}}, # IDF
                            "$tf" # TF
                        ]
                    }
                },
                "num_terms": {"$sum": ({
                    "$switch": {
                        "branches": verb_branch,
                        "default": 1
                    }
                } if len(verb_branch)>0 else 1)},
            }
        },
         {
             "$addFields":{
                 "final_score":{
                     "$multiply":[
                         "$bm25_score","$num_terms"
                     ]
                 }
             }
         },
        {
            "$sort": {
                "final_score": -1
            }
        },
        {
            "$limit": 10
        },
        
    ]

    docs = list(m.db.indexed_data.aggregate(pipeline, allowDiskUse=True))
    print(f"Fetching pages at {(time.time_ns() - start_time)/1000000000} s")

    hits = list(m.db.pages.find({"url":{"$in":[doc['_id'] for doc in docs]}}, {"_id":0,"url":1, "title":1, "html":1, "meta_description":1}))
    print(f"Reranking at {(time.time_ns() - start_time)/1000000000} s")
    
    if len(hits) == 0 :
        return {"Error":"No results found"}
    res = (crossencodertest.rerank(query, hits, 10))
    print(f"Results in {(time.time_ns() - start_time)/1000000000} s")

    for doc in res[:10] :
        del doc['html']
    return {"Results":res[:10], "query":newquery}
