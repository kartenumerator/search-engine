import pymongo
import sqlite3
from dotenv import load_dotenv
import os
import time

load_dotenv()

class dbm:
    def __init__(self):        
        self.client = pymongo.MongoClient(os.getenv("MONGO_HOST"), int(os.getenv("MONGO_PORT")))
        self.db = self.client.search_engine
        if "indexed_data" not in self.db.list_collection_names():
            print("Creating the indexed_data collection")
            result = self.db.create_collection(
                "indexed_data", validator={
                '$jsonSchema': {
                    'bsonType': 'object',
                    'additionalProperties': True,
                    'required': ['url', 'word'],
                    'properties': {
                        'word':{'bsonType':'string'},
                        'url':{'bsonType':'string'},
                        'tf':{'bsonType':'double'},
                        'weight':{'bsonType':'double'},
                        'idf':{'bsonType':'double'}
                    }
                }
            }
            )
            self.db.indexed_data.create_index({'word':1,'url':1}, unique=True)

        if "words" not in self.db.list_collection_names():
            print("Creating the indexed_data collection")
            result = self.db.create_collection(
                "words", validator={
                '$jsonSchema': {
                    'bsonType': 'object',
                    'additionalProperties': True,
                    'required': ['word'],
                    'properties': {
                        'word':{'bsonType':'string'},
                        'numberdocs':{'bsonType':'int'}                        
                    }
                }
            }
            )
            self.db.words.create_index({'word':1}, unique=True)


        # self.conn = sqlite3.connect(os.getenv("SQLITE_PATH"))
        # self.cursor = self.conn.cursor()
        # self.cursor.execute("PRAGMA journal_mode=WAL;")
        # self.cursor.execute("PRAGMA synchronous=NORMAL;")



    def retrieve_page_to_index(self):
        # doc = self.db.crawled_urls.find_one_and_update({"status":0},{"$set":{"status":1}},return_document=pymongo.ReturnDocument.BEFORE)
        doc = self.db.pages.find_one_and_update({"status":0},{"$set":{"status":1}},return_document=pymongo.ReturnDocument.AFTER)
        
        if doc is None :
            print("Crawled list is empty, waiting 10 seconds for crawler.")
            # doc = self.db.words.find_one({"word":""})
            # self.update_idf(doc)
            time.sleep(10)
            return None
        
        # self.cursor.execute(f'SELECT * FROM pages WHERE url = ?', (doc["url"],))
        # ret = self.cursor.fetchone()
        # if ret is None :
        #     self.db.crawled_urls.update_one({"url":doc["url"]},{"$set":{"status":-1}})
        #     time.sleep(1)
        #     return None
        # print(ret)
        return doc
    
    def completed_page(self,url):
        try:
            self.db.pages.update_one({"url":url},{"$set":{"status":2}})
        except Exception as e:
            print(f'Exception occured while updating db {e}')

    def add_words(self, words, hash, url, terms):
        try:
            # indexed_data_op = []
            words_op = []
            # i = 0
            # self.db.words.update_many({"word":{"$in":words}},{"$inc":{"numberdocs":1}},upsert=True)
            self.db.indexed_data.insert_many([{'url':url, 'word':word, 'tf':(hash[word]/terms)} for word in words], ordered=False)
            
            for word in words :
            #     indexed_data_op.append(pymongo.InsertOne({'url':url,'word':word.lower(),'tf':(hash[i]/terms)}))
                words_op.append(pymongo.UpdateOne({"word":word},{"$inc":{"numberdocs":1}},upsert=True))
            #     i += 1
            self.completed_page(url)
            # self.db.indexed_data.bulk_write(indexed_data_op,ordered=False)
            self.db.words.bulk_write(words_op,ordered=False)
            doc = self.db.words.find_one_and_update({"word":""},{"$inc":{"numberdocs":1}},upsert=True, return_document=pymongo.ReturnDocument.AFTER)

            if doc["numberdocs"] % 1000 == 0 :
                print(f'Updating idf of documents. Current number of documents : {doc["numberdocs"]}')
                # self.update_idf(doc)
        except Exception as e:
            print(f"Updating word data to mongo db failed due to error : {e}")

    def update_idf(self,doc):
        total_docs = doc["numberdocs"]
        try:
            self.db.indexed_data.aggregate(
                [
                    {
                        "$lookup": {
                            "from": "words",
                            "localField": "word",
                            "foreignField": "word",
                            "as": "word_info"
                        }
                    },
                    {
                        "$set": {
                            "weight": {
                                "$multiply":["$tf",
                                {"$log": [
                                    {"$divide":[{"$toDouble":total_docs}, {"$toDouble":{ "$arrayElemAt": ["$word_info.numberdocs", 0] }}]},
                                    10
                                    # {"$arrayElemAt": ["$product.price", 0]}
                                ]}]
                            },

                            # "weight": {"$multiply": ["$tf", "$idf"]}

                        }
                    },
                    {
                        "$unset": "word_info"
                    },
                    {
                    "$merge": {
                        "into": "indexed_data",
                        "on": "_id",
                        "whenMatched": "merge"
                    }
                }
                ]
            )
        except Exception as e:
            print(f"Updating idf failed due to error : {e}")
        
        return
    
    def update_idf(self, words):
        try:
            operations = []
            for word in words :
                doc = self.db.words.find_one({"word":word})
                if doc is None :
                    print(f"Word {word} not found in words collection")
                    return
                total_docs = self.db.words.find_one({"word":""})["numberdocs"]
                
                
                operations.append(pymongo.UpdateMany(
                    {"word":word},
                    [
                        {
                            "$set": {
                                "weight": {
                                    "$multiply":["$tf",
                                    {"$log": [
                                        {"$divide":[{"$toDouble":total_docs}, {"$toDouble":doc["numberdocs"]}]},
                                        10
                                    ]}]
                                }
                            }
                        }
                    ]
                ))
            self.db.indexed_data.bulk_write(operations,ordered=False)
        except Exception as e:
            print(f"Updating idf failed due to error : {e}")
        return