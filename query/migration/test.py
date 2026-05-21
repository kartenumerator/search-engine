from dbm import dbm

import pymongo

m = dbm()

# words = []
# docs = list(m.db.words.find({"numberdocs":{"$lt":5}}))
# print(len(docs))
# print(docs[0])

# for doc in docs :
#     words.append(doc['word'])

# idx = 0
# for i in range(31000,len(docs),50000):
#     idx = i+50000
#     res = m.db.indexed_data.delete_many({"word":{"$in":words[i:idx]}})
#     print(res)
# res = m.db.indexed_data.delete_many({"word":{"$in":words[idx:]}})
# print(res)

words = []
with open('uselesswords.txt', 'r') as f:
    words = f.read().splitlines()
print(len(words))
# m.db.indexed_data.update_many()
idx = 1
while True :
    print(idx)
    docs = list(m.db.indexed_data.find({"word":{"$in":words[0:10000]}}).skip(idx*1000000).limit(1000000))
    print(len(docs))
    ops = []
    for doc in docs :
        ops.append(pymongo.UpdateOne({"word":doc['word'].lower(), "url":doc['url']}, {"$inc":{"tf":doc['tf']}}, upsert=True))
    print(f'performing {len(ops)} operations...')
    m.db.indexed_data.bulk_write(ops, ordered=False)

    idx += 1
    if len(docs) < 1000000 :
        print('finished')
        break
