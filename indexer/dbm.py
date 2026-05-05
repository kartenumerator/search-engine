import signal
import pymongo
import sqlite3
from dotenv import load_dotenv
import os
import sys
import time
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add it to the list of places Python looks for modules
sys.path.append(parent_dir)
import helper
from multipledispatch import dispatch

load_dotenv()

K = 1
B = 0.75

class dbm:
    def __init__(self):        
        self.client = pymongo.MongoClient(os.getenv("MONGO_HOST"), int(os.getenv("MONGO_PORT")))
        self.db = self.client.search_engine
        
        signal.signal(signal.SIGINT, self.handle_sigint)

        self.admin = self.client.admin
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
        

        # if "live_for_search" not in self.db.list_collection_names():
        #     print("Creating the live_for_search collection")
        #     result = self.db.create_collection(
        #         "live_for_search", validator={
        #         '$jsonSchema': {
        #             'bsonType': 'object',
        #             'additionalProperties': True,
        #             'required': ['url', 'word'],
        #             'properties': {
        #                 'word':{'bsonType':'string'},
        #                 'url':{'bsonType':'string'},
        #                 # 'tf':{'bsonType':'double'},
        #                 'weight':{'bsonType':'double'},
        #                 # 'idf':{'bsonType':'double'}
        #             }
        #         }
        #     }
        #     )
        #     self.db.live_for_search.create_index({'word':1,'weight':1})
        #     self.db.live_for_search.create_index({'word':1,'url':1}, unique=True)

        if "words" not in self.db.list_collection_names():
            print("Creating the words collection")
            result = self.db.create_collection(
                "words", validator={
                '$jsonSchema': {
                    'bsonType': 'object',
                    'additionalProperties': True,
                    'required': ['word'],
                    'properties': {
                        'word':{'bsonType':'string'},
                        'numberdocs':{'bsonType':'int'},
                        'idf':{'bsonType':'double'}                        
                    }
                }
            }
            )
            self.db.words.create_index({'word':1}, unique=True)
        
        if "kgrams" not in self.db.list_collection_names():
            print("Creating the kgrams collection")
            result = self.db.create_collection(
                "kgrams", validator={
                '$jsonSchema': {
                    'bsonType': 'object',
                    'additionalProperties': True,
                    'required': ['kgram'],
                    'properties': {
                        'kgram':{'bsonType':'string'},
                        'words':{'bsonType':'array', 'items':{'bsonType':'string'}}                        
                    }
                }
            }
            )
            self.db.kgrams.create_index({'kgram':1}, unique=True)


        # self.conn = sqlite3.connect(os.getenv("SQLITE_PATH"))
        # self.cursor = self.conn.cursor()
        # self.cursor.execute("PRAGMA journal_mode=WAL;")
        # self.cursor.execute("PRAGMA synchronous=NORMAL;")

    def handle_sigint(self, signum, frame):
        print("Closing database connections...")
        self.client.close()
        # self.conn.close()
        print("Database connections closed. Exiting now.")
        exit(0)

    def retrieve_page_to_index(self):
        doc = self.db.pages.find_one_and_update({"status":0},{"$set":{"status":1}},return_document=pymongo.ReturnDocument.AFTER)
        
        if doc is None :
            print("Crawled list is empty, waiting 10 seconds for crawler.")
            time.sleep(10)
            return None
        
        return doc
    
    def get_flag_to_crawl(self):
        doc = self.db.global_vars.find_one({"_id":"crawl_flag"})
        if doc is None :
            self.db.global_vars.insert_one({"_id":"crawl_flag","status":1})
            return 1
        return doc["status"]
    
    def set_flag_to_crawl(self, flag):
        try:
            self.db.global_vars.update_one({"_id":"crawl_flag"},{"$set":{"status":flag}},upsert=True)
        except Exception as e:
            print(f"Exception occured while updating crawl flag in db : {e}")
        return

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
            if terms == 0 :
                terms = 1
            self.db.indexed_data.insert_many([{'url':url, 'word':word, 'tf':((hash[word]/terms)/(K+(hash[word]/terms)))} for word in words], ordered=False)
            # idexops = [{'url':url, 'word':word, 'tf':((hash[word]/terms)/(K+(hash[word]/terms)))} for word in words]

            #kgops = []
            for word in words :
            #     indexed_data_op.append(pymongo.InsertOne({'url':url,'word':word.lower(),'tf':(hash[i]/terms)}))
                #kgrams = helper.generate_kgrams(word)
                #kgops.append(pymongo.UpdateMany({"kgram":{"$in":kgrams}}, {"$addToSet":{"words":word}}))
                words_op.append(pymongo.UpdateOne({"word":word},{"$inc":{"numberdocs":1}},upsert=True))
            #     i += 1
            self.completed_page(url)
            # self.db.indexed_data.bulk_write(indexed_data_op,ordered=False)
            self.db.words.bulk_write(words_op,ordered=False)
            # self.db.kgrams.bulk_write(kgops, ordered=False)
            doc = self.db.global_vars.find_one_and_update({"_id":"totaldocs"},{"$inc":{"total_num":1}},upsert=True, return_document=pymongo.ReturnDocument.AFTER)
            
            # return (words_op, idexops)
            # if doc["total_num"] % 1000 == 0 :
            #     print(f'Updating idf of documents. Current number of documents : {doc["total_num"]}')
            #     # self.update_idf(doc)
        except Exception as e:
            print(f"Updating word data to mongo db failed due to error : {e}")
            # return None,None

    @dispatch()
    def update_idf(self):
        total_docs = self.db.global_vars.find_one({"_id":"totaldocs"})["total_num"]
        try:
            self.db.words.update_many({"word":{"$ne":""}},[{"$set":{"idf":{"$log":[{"$divide":[{"$add":[{"$toDouble":{"$subtract":[total_docs, "$numberdocs"]}},0.5]}, {"$add":[0.5, {"$toDouble":"$numberdocs"}]}]},10]}}}])
            print("Updated idf values in words collection")
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
                                "$multiply":["$tf",{"$arrayElemAt": ["$word_info.idf", 0]}]
                            },

                            # "weight": {"$multiply": ["$tf", "$idf"]}

                        }
                    },
                    {
                        "$unset": "word_info"
                    },
                    {
                        "$merge": {
                            "into": "live_for_search",
                            "on": "_id",
                            "whenMatched": "merge"
                        }
                    }
                ]
            )
        except Exception as e:
            print(f"Updating idf failed due to error : {e}")
        
        return
    
    @dispatch(list)
    def update_idf(self, words):
        try:
            total_docs = self.db.global_vars.find_one({"_id":"totaldocs"})["total_num"]
            self.db.words.update_many({"word":{"$in":words}},[{"$set":{"idf":{"$log":[{"$divide":[{"$add":[{"$toDouble":{"$subtract":[total_docs, "$numberdocs"]}},0.5]}, {"$add":[0.5, {"$toDouble":"$numberdocs"}]}]},10]}}}])
            self.db.indexed_data.aggregate(
                [
                    {
                        "$match": {
                            "word": {"$in": words}
                        }
                    },
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
                                "$multiply":["$tf",{"$arrayElemAt": ["$word_info.idf", 0]}]
                                # {"$log": [
                                #     {"$divide":[{"$add":[{"$toDouble":{"$subtract":[total_docs, {"$arrayElemAt": ["$word_info.numberdocs", 0] }]}},0.5]}, {"$add": [0.5, {"$toDouble":{ "$arrayElemAt": ["$word_info.numberdocs", 0] }}]}]},
                                #     10
                                #     # {"$arrayElemAt": ["$product.price", 0]}
                                # ]}]
                            },

                            # "weight": {"$multiply": ["$tf", "$idf"]}

                        }
                    },
                    {
                        "$unset": "word_info"
                    },
                    {
                        "$merge": {
                            "into": "live_for_search",
                            "on": "_id",
                            "whenMatched": "merge",
                            # "whenNotMatched": "upsert"
                        }
                    }
                ]
            )

            # operations = []
            # for word in words :
            #     doc = self.db.words.find_one({"word":word})
            #     if doc is None :
            #         print(f"Word {word} not found in words collection")
            #         return
            #     total_docs = self.db.words.find_one({"word":""})["numberdocs"]
                
                
            #     operations.append(pymongo.UpdateMany(
            #         {"word":word},
            #         [
            #             {
            #                 "$set": {
            #                     "weight": {
            #                         "$multiply":["$tf",
            #                         {"$log": [
            #                             {"$divide":[{"$add":[{"$toDouble":{"$subtract":[total_docs, {"$arrayElemAt": ["$word_info.numberdocs", 0] }]}},0.5]}, {"$add": [0.5, {"$toDouble":{ "$arrayElemAt": ["$word_info.numberdocs", 0] }}]}]},
            #                         10
            #                         ]}]
            #                     }
            #                 }
            #             }
            #         ]
            #     ))
            # self.db.indexed_data.bulk_write(operations,ordered=False)
        except Exception as e:
            print(f"Updating idf failed due to error : {e}")
        return
