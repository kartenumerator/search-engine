from functools import lru_cache
import json
from time import time
from urllib.parse import urlparse
import matplotlib.pyplot as plt
import numpy as np
from dbm import dbm

from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet

from nltk import pos_tag
import nltk
from pymongo import ReturnDocument, UpdateOne

manager = dbm()
nltk.download('averaged_perceptron_tagger_eng')
# list = manager.db.words.distinct("word")
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

while True:
        # 2. Find ONE document and mark it as 'Processing' atomically
        # This prevents other workers from picking it up
        doc = manager.db.words.find_one_and_update(
            filter={"status": {"$exists": False}},                # Only pick up new jobs
            update={"$set": {"status": 1}},   # Mark as locked/processing
            return_document=ReturnDocument.AFTER         # Get the updated doc
        )
        if doc is None:
            print("No documents to process. Sleeping...")
            time.sleep(5)  # Wait before checking again
            continue
        print(f"Processing document: word: {doc['word']}")
        tagged_tokens = pos_tag([doc['word']])
        newword = ""
        for word, tag in tagged_tokens:
            wn_tag = get_wordnet_pos(tag)
            newword = lemmatize_cached(word, wn_tag)
            # newword = lemma
        
        if newword != doc['word'] :
            with open("newfile.txt", "a") as file:
                file.write(f"{doc['word']} | {newword}\n")
            manager.db.words.update_one(
                {"word": newword},
                {"$inc":{"numberdocs": doc['numberdocs']}, "$setOnInsert": {"word": newword, "status": 1}},
                upsert=True
            )
            manager.db.words.delete_one({"_id": doc['_id']})


        # try:
        #     # 3. Process your document here
        #     print(f"Processing document: {doc['_id']}")
        #     # YOUR LOGIC HERE (e.g., lemmatization, API calls, etc.)
        #     time.sleep(1) 

        #     # 4. Update flag to 'Completed'
        #     manager.db.words.update_one(
        #         {"_id": doc["_id"]},
        #         {"$set": {"status": "Completed", "processed_at": time.time()}}
        #     )
        #     print(f"Finished: {doc['_id']}")

        # except Exception as e:
        #     # Handle errors by resetting the flag so it can be retried
        #     print(f"Error processing {doc['_id']}: {e}")
            # collection.update_one(
            #     {"_id": doc["_id"]},
            #     {"$set": {"status": "Pending"}}
            # )

# operations = [
#     UpdateOne(
#         {"url":url},                     # filter
#         {"$setOnInsert": {"url": url, "netloc":urlparse(url).hostname,"status":1, "upload_time":0}},   # only set if inserting
#         upsert=True
#     )
#     for url in list
# ]

# manager.db.urls_to_crawl.bulk_write(operations)

# Load JSON file
# with open('data.json', 'r') as f:
#     data = json.load(f)

# percentages = {}
# approveddomains =[]  
# for d in data.keys():
#     percentages[d] = (data[d][1]/(data[d][0]+data[d][1])) * 100
#     total = ((data[d][0]+data[d][1]-10) * 6/190) - 3
#     # print((0.5 + 0.5 * (total - 10)/(abs(total-10)+1)))
#     threshold = 60 - (0.5 + 0.5*(total)/(abs(total)+1))*20 
#     if percentages[d] > threshold and data[d][0]+data[d][1]>10:
#         print(f'{d} | {threshold} | total: {total} | approved: {data[d][1]} | rejected: {data[d][0]} | percentage: {percentages[d]:.2f}%')
#         approveddomains.append(d)

# print("deleting..")
# print(manager.db.urls_to_crawl.delete_many({"netloc":{"$nin":approveddomains}, "status":{"$in":[0,-1]}}))
# Extract keys and values
# labels = list(data.keys())
# val1 = [v[0] for v in data.values()]
# val2 = [v[1] for v in data.values()]

# # X-axis positions
# x = np.arange(len(labels))
# width = 0.35  # width of bars

# # Create plot
# plt.figure()

# plt.bar(x - width/2, val1, width, label='Value 1')
# plt.bar(x + width/2, val2, width, label='Value 2')

# # Labels and formatting
# plt.xlabel('Categories')
# plt.ylabel('Values')
# plt.title('Grouped Bar Chart from JSON')
# # plt.xticks(x, labels)
# plt.legend()

# plt.tight_layout()
# plt.show()