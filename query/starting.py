from dbm import dbm

from pymongo import UpdateMany, UpdateOne

m = dbm()

def generate_kgrams(word, k=3):
    word = f"${word}$"
    return [word[i:i+k] for i in range(len(word) - k + 1)]

idx = 0
while True :
    wordops = []
    kgramops = []
    docs = list(m.db.words.find({"status":{"$ne":2}}, {"word":1}).limit(10000))
    idx += len(docs)
    wrds = []
    for doc in docs :
        wrd = doc['word']
        wrds.append(wrd)
        kgrams = generate_kgrams(wrd)
        for kg in kgrams :
            kgramops.append(UpdateOne({"kgram":kg}, {"$addToSet":{"words":wrd}}, upsert=True))
    
    wordops.append(UpdateMany({'word':{"$in":wrds}},{'$set':{"status":2}}))
    try :
        print(f"Writing operations start...")
        m.db.words.bulk_write(wordops, ordered=False)
        m.db.kgrams.bulk_write(kgramops, ordered=False)
        print(f"Processed {idx} documents.")
    except Exception as e :
        print(e)
        break
