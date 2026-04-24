from dbm import dbm
import os
import time
import mimetypes
import sys

from pymongo.errors import BulkWriteError

# Get the absolute path to the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add it to the list of places Python looks for modules
sys.path.append(parent_dir)

# Now you can import your file by its name (without .py)
import helper
from urllib.parse import urlparse 
from pymongo import DeleteMany, InsertOne, UpdateMany, UpdateOne
manager = dbm()

words = []
with open('newfile.txt','r') as f :
    words = f.read().splitlines()

wordict = {}
for word in words :
    wordict[word.split("|")[0].strip()] = word.split("|")[1].strip()
lendict = {}
docs = list(manager.db.indexed_data.find({"word":{"$in":list(wordict.keys())}}))
print(len(docs))

indexops = []
for doc in docs : 
    if doc['word'] in lendict :
        lendict[doc['word']] += 1
    else :
        lendict[doc['word']] = 1
    indexops.append(InsertOne({"word": wordict[doc['word']], "url": doc['url'], "tf": doc['tf']}))

wordops = []
for word in lendict.keys() :
    wordops.append(UpdateOne({"word": word}, {"$set":{"numberdocs": lendict[word]}}, upsert=True))

print(f"Prepared {len(indexops)} index operations and {len(wordops)} word operations.")
try :
    manager.db.indexed_data.bulk_write(indexops, ordered=False)
except BulkWriteError as bwe :
    count = bwe.details.get("nInserted", 0)
    print(f"Number of documents inserted before error indexed_data: {count}")

try :
    manager.db.words.bulk_write(wordops, ordered=False)
except BulkWriteError as bwe :
    count = bwe.details.get("nInserted", 0)
    print(f"Number of documents inserted before error words: {count}")
# idx = 0
# indexops = []
# wordops = []
# for word in words :

#     if idx % 100 == 0 :
#         print(f'Performing bulk operations.')
#         try :
#             if wordops :
#                 manager.db.words.bulk_write(wordops, ordered=False)
#                 wordops = []
#             if indexops :
#                 manager.db.indexed_data.bulk_write(indexops, ordered=False)
#                 indexops = []
#         except Exception as e :
#             print(f"Error during bulk write: {e}")
#     actualword = word.split("|")[0].strip()
#     lemmatizedword = word.split("|")[1].strip()
#     docs = list(manager.db.indexed_data.find({"word":actualword}))
#     wordops.append(UpdateOne({"word": actualword}, {"$set": {"numberdocs": len(docs)}}, upsert=True))
#     for doc in docs :
#         indexops.append(UpdateOne({"word": lemmatizedword, "url": doc['url']}, {"$set":{"tf": doc['tf']}}, upsert=True))

#     idx += 1
#     print(f'Processed {idx} words', end='\r')
        
# words = []
# with open("approvedlist.txt", "r") as file:
#     words = file.read().splitlines()
#     # print(len(words))

# idx = 0
# for i in range(0, len(words), 10000):
#     batch = []
#     if i + 10000 > len(words) :
#         # print("last batch")
#         batch = words[i:]
#     else :
#         # print(i+100)
#         batch = words[i:i+10000]
#     res1 = manager.db.indexed_data.delete_many({'word':{'$in': batch}})
#     res2 = manager.db.words.delete_many({'word':{'$in': batch}})
#     idx += len(batch)
#     print(f"Deleted {res1.deleted_count} indexes")
#     print(f"Deleted {res2.deleted_count} words")
#     print(f"Deleted {idx} documents")



# wordops = []
# indexedops = []
# idx = 0
import langid

# text = "736x736"
# language, score = langid.classify(text)

# print(f"Detected Language: {language}") # Output: en
# print(f"Confidence Score: {score}")    # Unnormalized log-probability
# idx = 0
# # for url in urls:
# #     idx += 1
# #     print(f'{idx}th url', end='\r')
# #     result = manager.db.indexed_data.delete_many({"url": url})
#     # print(f"\nDeleted {result.deleted_count} indexed documents for {url}.")

# with open('approvedlist.txt', 'a') as f:
#     while True :
#         # if idx %100 == 0 :
#         #     print(f"\nDeleting {', '.join(indexedops)}...\n")
#         #     print(f'Processed {idx} documents', end='\r')
#         #     if wordops :
#         #         manager.db.words.bulk_write(wordops)
#         #         wordops = []
#         #     if indexedops :
#         #         result = manager.db.indexed_data.delete_many({"url": {"$in": indexedops}})
#         #         print(f"\nDeleted {result.deleted_count} non-HTML indexed documents.")
#         #         indexedops = []
#         # idx = 0
#         docss = manager.db.words.find(filter={'status':{'$ne':4}}, projection={'word': 1, '_id': 1}).limit(50000)
#         ops = []
#         for docs in docss : 
#             if docs is None :
#                 time.sleep(60*2)
#                 continue
            
#             url = docs['word']

#             # language, score = langid.classify(url)
#             is_english = helper.check_only_english_alphanum_symbols(url)
#             # is_not_html, ext = helper.check_url_extension(url)
#             ops.append(UpdateOne({"_id": docs['_id']}, {"$set": {"status": 4}}))
#             if not is_english :
#                 f.write(url + "\n")
#                 # indexedops.append(DeleteMany({"url": url}))
#                 # indexedops.append(url)
#                 # manager.db.indexed_data.delete_many({"url": url})
#                 # manager.db.pages.delete_one({"_id": docs['_id']})

#             print(f'Processed {idx} documents', end='\r')
#             idx += 1
#         manager.db.words.bulk_write(ops)