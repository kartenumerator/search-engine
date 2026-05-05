from dbm import dbm
from urllib.parse import urlparse
from pymongo import UpdateMany, UpdateOne
# for i in range(0,457, 100):
#     print(i)
m = dbm()

idx = 0
BATCH_SIZE = 2000000
uniq = set()
ops = set()
while True :
    print(f"At {idx*BATCH_SIZE}")
    docs = list(m.db.indexed_data.find({}).limit(BATCH_SIZE).skip(idx*BATCH_SIZE))
    for doc in docs :
        # if urlparse(doc['url']).hostname == 'comix.to':
        #     ops.add(doc['url'])
        uniq.add(doc['url'])
    if len(ops) > 0:
        print(f'updating {len(ops)} comix urls')
        m.db.indexed_data.update_many({"url":{"$in":list(ops)}}, {"$mul":{"tf":0.2}})
        ops = set()
    print(len(uniq))
    idx += 1
    if len(docs) < BATCH_SIZE :
        print("done")
        break

with open("allurls.txt", "a") as f:
    for url in uniq :
        f.write(f'{url}\n')
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