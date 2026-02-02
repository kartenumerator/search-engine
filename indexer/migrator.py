import pymongo
import sqlite3


client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client.search_engine

if "pages" not in db.list_collection_names():
    db.create_collection("pages", validator={
                '$jsonSchema': {
                    'bsonType': 'object',
                    'additionalProperties': True,
                    'required': ['url'],
                    'properties': {
                        'url':{'bsonType':'string'},
                        'html':{'bsonType':'string'},
                        'status':{'bsonType':'int'}                        
                    }
                }
            })
    db.pages.create_index({'url':1}, unique=True)

db.pages.update_many({},{"$set":{"status":0}})
# i = 1
# docs = cursor.execute("SELECT url,html FROM pages WHERE id=?",(i,)).fetchone()
# buffer = []
# while docs is not None:
#     print(f"migrating {i}th page")
#     buffer.append({"url":docs[0],"html":docs[1]})
#     if i %100 == 0:
#         print("pushing to mongod")
#         try:
#            db.pages.insert_many(buffer,ordered=False)
#         except Exception:
#             pass
#         buffer.clear()
#     i += 1
#     docs = cursor.execute("SELECT url,html FROM pages WHERE id=?",(i,)).fetchone()
#     # print(docs)

# try:
#    db.pages.insert_many(buffer,ordered=False)
# except Exception:
#     pass
# for i in range(num):
