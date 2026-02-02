from dbm import dbm
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import time

from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet

stop_words = set(stopwords.words('english'))

lemmatizer = WordNetLemmatizer()
# client = pymongo.MongoClient("mongodb://localhost:27017/")
# db = client.search_engine

m = dbm()
doc = m.db.words.find_one({"word":""})
# m.update_idf(doc)
# print(f"Time taken : {(time.time_ns()-start_time)/1000000000} s")

# query = "naruto uzumaki and sasuke uchiha porn"
query = input("Enter your search query: ")
tokens = word_tokenize(query)
filtered_query = [lemmatizer.lemmatize(word.lower()) for word in tokens if word.lower() not in stop_words]
start_time = time.time_ns()
m.update_idf(filtered_query)
print(f"idf updated in {(time.time_ns()-start_time)/1000000000} s")
pipeline = [
    {
        "$match": {
            "word": {"$in": filtered_query}
        }
    },
    {
        "$group": {
            "_id": "$url",
            "words": {"$addToSet": "$word"},
        }
    },
    {
        "$match": {
            "$expr": {
                "$eq": [{"$size": "$words"}, len(filtered_query)]
            }
        }
    },
    {
        "$lookup": {
            "from": "indexed_data",   # safer than hardcoding
            "let": {"cat": "$_id"},
            "pipeline": [
                {
                    "$match": {
                        "$expr": {
                            "$and": [
                                {"$eq": ["$url", "$$cat"]},
                                {"$in": ["$word", filtered_query]}
                            ]
                        }
                    }
                },
                {"$project": {"_id": 0, "word": 1, "tf": 1, "weight": 1, "idf": 1,"url":1}}
            ],
            "as": "docs"
        }
    },
    {
        "$addFields": {
            "totalWeight": { "$ifNull": [{ "$sum": "$docs.weight" }, 0 ] }
        }
    },
    {"$sort": {"totalWeight": -1}},
    # {"$unwind": "$docs"},
    # {"$replaceRoot": {"newRoot": "$docs"}}
]

result = list(m.db.indexed_data.aggregate(pipeline, allowDiskUse=True))
    
print(f'final results in {(time.time_ns()-start_time)/1000000000} s')
print(*result[0:20], sep="\n\n")
