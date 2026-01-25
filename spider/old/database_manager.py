import pymongo
import schemas
from pymongo import UpdateOne

client = pymongo.MongoClient("localhost",27017)

db = client.search_engine

if 'urls_to_crawl' not in db.list_collection_names():
    print("Creating urls_to_crawl collection with schema validation")
    result = db.create_collection('urls_to_crawl', validator=schemas.urls_to_crawl_schema)
    db.urls_to_crawl.create_index("url", unique=True)
    print(result)

if 'crawled_urls' not in db.list_collection_names():
    # crawled_urls = db.crawled_urls
    # crawled_urls.create_index("url", unique=True)
    print("Creating crawled_urls collection with schema validation")
    result = db.create_collection('crawled_urls', validator=schemas.crawled_urls_schema)
    db.crawled_urls.create_index({"netloc": pymongo.ASCENDING, "path": pymongo.ASCENDING}, unique=True)
    print(result)

crawled_urls = db.crawled_urls

urls_to_crawl = db.urls_to_crawl

def add_url_to_crawl(url, upload_time):
    try:
        urls_to_crawl.insert_one({'url': url, 'upload_time': upload_time})
    except Exception as e:
        print(f"Error adding URL to crawl {url}: {e}")

def add_urls_to_crawl(urls):
    # print(urls)
    try:
        # urls_to_crawl.bulk_write([
        #     UpdateOne({'url': url_dict['url']}, {'$set': url_dict}, upsert=True)
        #     for url_dict in urls
        # ], ordered=False)
        urls_to_crawl.insert_many(urls, ordered=False)
    except Exception as e:
        print(f"Error adding URLs to crawl: {e}")

def retrieve_url():
    try:
        doc = urls_to_crawl.find_one(sort=[('upload_time', pymongo.ASCENDING)])

        # print(f"Retrieved URL to crawl: {doc}")
        if doc:
            urls_to_crawl.delete_one({'_id': doc['_id']})
            return doc['url']
        else:
            return None
    except Exception as e:
        print(f"Error retrieving URL to crawl: {e}")
        return None

def retrieve_urls_to_crawl(limit=100):
    try:
        urls = urls_to_crawl.find().sort('upload_time', pymongo.ASCENDING).limit(limit)
        # tosend = [doc['url'] for doc in urls]
        # print([doc['_id'] for doc in urls])
        # urls_to_crawl.delete_many({'_id':{'$in':[doc['_id'] for doc in urls]}})
        tosend = []
        todel = []
        for doc in urls:
            tosend.append(doc['url'])
            todel.append(doc['_id'])
    
        urls_to_crawl.delete_many({'_id':{'$in':todel}})
        
        return tosend
    except Exception as e:
        print(f"Error retrieving URLs to crawl: {e}")
        return []

def add_crawled_url(netloc, path):
    try:
        crawled_urls.insert_one({'netloc': netloc, 'path': path})
    except Exception as e:
        print(f"Error adding crawled URL {netloc}{path}: {e}")

def is_url_crawled(netloc, path):
    try:
        doc = crawled_urls.find_one({'netloc': netloc, 'path': path}, {'_id': 1})
        return doc is not None
        # return doc is not None
    except Exception as e:
        print(f"Error checking crawled URL {netloc}{path}: {e}")
        return False