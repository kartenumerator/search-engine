from dbm import dbm

from pymongo import UpdateMany, UpdateOne
# for i in range(0,457, 100):
#     print(i)
m = dbm()

words = []
lowwords = []
with open("uselesswords.txt","r") as f:
    txt = f.read()
    words = txt.splitlines()
    lowwords = txt.lower().splitlines()

res = m.db.indexed_data.delete_many({"word":{"$in":words}})
print(res)
res2 = m.db.indexed_data.update_many({"word":{"$in":lowwords}},{"$mul":{"tf":2}})
print(res2)
# ops = []
# idx = 0
# for i in range(0,len(words),1000) :
#     idx = i+1000
#     print(f'processing {idx} documents')
#     docs = m.db.indexed_data.find({"word":{"$in":words[i:idx]}})
#     for doc in docs :
#         ops.append(UpdateOne({"word":doc['word'].lower(), "url":doc['url']},{"$inc":{"tf":doc['tf']}}, upsert=True))
#     m.db.indexed_data.bulk_write(ops)
#     print(f'processed..')

# print(f'processing {len(words)} documents')
# docs = m.db.indexed_data.find({"word":{"$in":words[idx : ]}})
# for doc in docs :
#     ops.append(UpdateOne({"word":doc['word'].lower()},{"$inc":{"tf":doc['tf']}}, upsert=True))
# m.db.indexed_data.bulk_write(ops)
# print(f'processed..')