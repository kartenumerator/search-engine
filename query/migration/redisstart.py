import redis
from dbm import dbm
import time

m = dbm()

r = redis.Redis(host="localhost", port=6379, db=0)

# r.set("key", "value")
# print(r.get("key"))

total_docs = m.db.global_vars.find_one({"_id":"totaldocs"})["total_num"]
# words = []
# for word in filtered_query :
words = list(m.db.words.find({"numberdocs":{"$gt":5}}, {"word":1,"numberdocs":1}).sort({"numberdocs":-1}))
# words.extend(checkingdoc)
wordict = {}
for word in words :
    word['idf'] = ((total_docs - word['numberdocs'] + 0.5)/(word['numberdocs']+0.5)) + 1
    wordict[word['word']] = word

del words
print('finished')

print(len(wordict))
pipe = r.pipeline(transaction=False)
idx = 0
while True :
    print(idx)
    #if idx > 0 and idx % 100 == 0 :
    #    print("executing")
    #    pipe.execute()
    pipe = r.pipeline(transaction=False)
        
    start_time = time.time_ns()
    docs = m.db.indexed_data.find({"word":{"$in":list(wordict.keys())[idx*100:idx*100 + 100]}}, {"url":1, "word":1, "tf":1})
    print(f"docs retrieved : {(time.time_ns() - start_time)/1000000000} s")
    lenth = 0
    for doc in docs :
        lenth += 1
        # try :
        try :
            weight = wordict[doc['word']]['idf']*doc['tf']
        #if r.exists(word) :

            pipe.zadd(doc['word'], {doc['url']:weight})
        except Exception as e:
            print(e)
            continue
    idx += 1
    pipe.execute()
    print(f"batch updated : {(time.time_ns() - start_time)/1000000000} s")
    


# idx = 51
# while True :
#     start_time = time.time_ns()
#     docs = m.db.indexed_data.find({}, {"url":1, "word":1, "tf":1}).skip(idx * 1000000).limit(1000000)
#     print(f"docs retrieved : {(time.time_ns() - start_time)/1000000000} s")
#     print(f'{idx} documents...')
#     lenth = 0
#     pipe = r.pipeline(transaction=False)
#     for doc in docs :
#         lenth += 1
#         # try :
#         word = doc['word'].lower()
#         try :
#             weight = wordict[word]['idf']*doc['tf']
#         #if r.exists(word) :

#             pipe.zincrby(word, weight, doc['url'])
#         except Exception as e:
#             print(e)
#             continue
#         #else :
#         #    r.zadd(doc['word'],{doc['url'] : weight})
#         # except Exception as e:
#         #     #print(e)
#         #     continue
#     idx += 1
#     pipe.execute()
#     print(f"batch updated : {(time.time_ns() - start_time)/1000000000} s")
#     if lenth < 1000000 :
#         break

print('finished')
