from dbm import dbm
from Levenshtein import distance
import heapq


# str1 = "helo"
# query = input("Enter query : ")

def jaccard_distance(str1, str2):
    # Convert strings to sets of words
    a = set(generate_kgrams(str1.lower()))
    b = set(generate_kgrams(str2.lower()))
    
    # print(a)
    # print(b)
    # Calculate Jaccard Similarity
    intersection = len(a.intersection(b))
    union = len(a.union(b))
    # print(intersection, union)
    # Calculate Jaccard Distance
    return 1 - (intersection/union) if union != 0 else 1 

def generate_kgrams(word, k=3):
    word = f"${word}$"
    return [word[i:i+k] for i in range(len(word) - k + 1)]

# str2 = "hellhole"
# print(jaccard_distance(str1,str2))

def get_max_suggestion_word(query, m):
    kgrams = generate_kgrams(query)
    docs = list(m.db.kgrams.find({"kgram":{"$in":kgrams}}))
    possiblewords = []

    wordset = set()
    for doc in docs :
        for word in doc['words']:
            if any( word in w for w in possiblewords ) :
                continue 
            score = jaccard_distance(query, word)
            # possiblewords.append((word,score))
            heapq.heappush(possiblewords, (score,word))

    # possiblewords = sorted(possiblewords, key=lambda x: x[1], reverse=False)
    topk = heapq.nsmallest(20,possiblewords)
    topkdict = {}
    
    levlist = []
    for word in topk :
        heapq.heappush(levlist, (distance(query.lower(),word[1]),word[1]))

    top5 = heapq.nsmallest(5, levlist)
    for word in top5 :

        topkdict[word[1]] = word[0]
    print(top5)

    wordocs = list(m.db.words.find({"word":{"$in":[word for s,word in top5 if s == top5[0][0]]}}, {"numberdocs":1, "word":1}))
    maxword = None
    print(wordocs)
    for doc in wordocs :
        # doc['numberdocs']/= (topkdict[doc['word']])*100
        if maxword is None or maxword['numberdocs'] < doc['numberdocs']:
            maxword = doc
    if maxword is None :
         return query
    return maxword['word']

# m = dbm()
# query = input("query : ")
# print(get_max_suggestion_word(query, m))
