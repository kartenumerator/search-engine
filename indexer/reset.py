import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client.search_engine
db.pages.update_many({}, {"$set": {"status": 0}})
# db.indexed_data.update_many({}, { "$unset": { "weight": "" } });
