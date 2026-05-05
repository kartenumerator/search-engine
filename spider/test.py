import datetime
from dbm import dbm
import os
from urllib.parse import urlparse

m = dbm("localhost",27017)

# indexedurls = []
# with open('allurls.txt', 'r') as f:
#     indexedurls = f.read().splitlines()

# comixurls = []
# for url in indexedurls :
#     if urlparse(url).hostname == 'comix.to':
#         comixurls.append(url)

res = m.db.indexed_data.update_many({"url":{"$regex":"comix.to"}}, {"$mul":{"tf":0.5}})
# print(f"updating indexes for {len(comixurls)}")
# m.db.indexed_data.delete_many({"url":{"$in":comixurls}})
# print(f"updating indexes for {len(comixurls)}")
# m.db.pages.update_many({"url":{"$in":comixurls}}, {"$set":{"status":0}})
# print(f"updating indexes for {len(comixurls)}")
#m.db.pages.update_many({"url":{"$nin":indexedurls}}, {"$set":{"status":-1}})
# res = m.db.pages.delete_many({"url":{"$regex":"comix.to"}})

print(res)
