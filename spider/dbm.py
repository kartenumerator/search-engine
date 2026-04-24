import pymongo
from schemas import (
    urls_to_crawl_schema,
    crawled_urls_schema,
    urls_to_crawl_index,
    crawled_urls_index,
    robots_index,
    robots_schema,
)
from pymongo.errors import DuplicateKeyError, BulkWriteError
import datetime
from urllib.parse import urlparse


class dbm:
    def __init__(self, host, port):

        self.client = pymongo.MongoClient(host, port)
        self.db = self.client.search_engine


        if "robots" not in self.db.list_collection_names():
            print(("c", "Creating robots collection with schema validation"))
            result = self.db.create_collection(
                "robots", validator=robots_schema
            )
            self.db.robots.create_index(robots_index, unique=True)
            print(("c", str(result)))

        if "urls_to_crawl" not in self.db.list_collection_names():
            print(("c", "Creating urls_to_crawl collection with schema validation"))
            result = self.db.create_collection(
                "urls_to_crawl", validator=urls_to_crawl_schema
            )
            self.db.urls_to_crawl.create_index(
                urls_to_crawl_index, unique=True
            )
            self.db.urls_to_crawl.create_index({"upload_time":pymongo.DESCENDING})
            print(("c", str(result)))
        
        if "reddits" not in self.db.list_collection_names():
            print(("c", "Creating reddits collection with schema validation"))
            result = self.db.create_collection(
                "reddits", validator={
                    '$jsonSchema': {
                        'bsonType': 'object',
                        'additionalProperties': True,
                        'required': ['url', 'upload_time'],
                        'properties': {
                            'url': {
                                'bsonType': 'string'
                            },
                            'netloc':{'bsonType':'string'},
                            'status':{
                                'bsonType':'int',
                                'description':'0 : uncrawled, 1:crawling, 2:crawled'
                            },
                            'upload_time': {
                                'bsonType': 'int'
                            },
                        }
                    }
                }
            )
            self.db.reddits.create_index({'url':1}, unique=True)
            print(("c", str(result)))

        if "global_vars" not in self.db.list_collection_names():
            self.db.create_collection("global_vars", validator={
                        '$jsonSchema': {
                            'bsonType': 'object',
                            'additionalProperties': True,
                            'required': ['_id', 'status'],
                            'properties': {
                                '_id':{'bsonType':'string'},
                                'status':{'bsonType':'int'},
                            }
                        }
                    })
            print(("c", "Created global_vars collection with schema validation"))
            self.db.global_vars.insert_one({"_id":"crawl_flag", "status":1})

        if "pages" not in self.db.list_collection_names():
            self.db.create_collection("pages", validator={
                        '$jsonSchema': {
                            'bsonType': 'object',
                            'additionalProperties': True,
                            'required': ['url','html'],
                            'properties': {
                                'url':{'bsonType':'string'},
                                'html':{'bsonType':'string'},
                                'status':{'bsonType':'int'},
                                'title':{'bsonType':'string'},
                                'meta_description':{'bsonType':'string'},          
                            }
                        }
                    })
            self.db.pages.create_index({'url':1}, unique=True)
            print(("c", "Created pages collection with schema validation"))
        self.crawled_urls = self.db.crawled_urls
        self.urls_to_crawl = self.db.urls_to_crawl
        self.reddits = self.db.reddits
        self.robots = self.db.robots

    def add_url_to_crawl(self, url, upload_time):
        try:
            self.urls_to_crawl.insert_one(
                {"url": url, "upload_time": upload_time}
            )
        except Exception as e:
            print(("c", f"[bold red]Error adding URL to crawl {url}[/bold red]: {e}"))

    def add_urls_to_crawl(self, urls):
        try:
            ops = []
            redops = []
            for url in urls :
                parsed = urlparse(url)
                doc = {"url":url, "netloc":parsed.hostname,"status":0}
                actn = (pymongo.UpdateOne(
                    {'url':url},
                    {
                        "$inc": {"upload_time": 1},
                        "$setOnInsert": {
                            **doc
                        }
                    },
                    upsert=True
                ))
                if parsed.hostname == "www.reddit.com" :
                    redops.append(actn)
                else :
                    ops.append(actn)
            if len(ops) > 0 :
                self.urls_to_crawl.bulk_write(ops, ordered=False)
            if len(redops) > 0 :
                self.reddits.bulk_write(redops, ordered=False)
            return None
        except BulkWriteError as err:
            print(("c", f"Duplicate URLs found while adding URLs to crawl {err}"))
            return None
        except Exception as e:
            print(("c", f"[bold red]Error adding URLs to crawl: {e}[/bold red]"))
            return None
        
    def check_flag_to_crawl(self):
        try:
            doc = self.db.global_vars.find_one({"_id":"crawl_flag"}, {"status": 1})
            return doc is not None and doc["status"] == 1
        except Exception as e:
            print(("c", f"[bold red]Error checking flag to crawl {e}[/bold red]"))
            return False
        
    def set_flag_to_crawl(self, value):
        try:
            self.db.global_vars.update_one({"_id":"crawl_flag"},{"$set":{"status":value}}, upsert=True)
        except Exception as e:
            print(("c", f"[bold red]Error setting flag to crawl {e}[/bold red]"))

    def retrieve_url(self,overbooked_hosts):
        try:
            doc = self.urls_to_crawl.find_one_and_update({"netloc":{"$nin":overbooked_hosts}, "status":0}, update={"$set":{"status":1}},sort=[("upload_time", pymongo.DESCENDING)], return_document=pymongo.ReturnDocument.AFTER)
            if doc is None :
                doc = self.urls_to_crawl.find_one_and_update({"netloc":{"$nin":overbooked_hosts}, "status":-1}, {"$set":{"status":1}}, return_document=pymongo.ReturnDocument.AFTER)
            
            if doc is None :
                return None 
            return doc["url"]
        except Exception as e:
            print(("c", f"[bold red]Error retrieving URL to crawl: {e}[/bold red]"))
            return None
        
    def retrieve_reddit_url(self):
        try:
            doc = self.reddits.find_one_and_update({"status":0}, update={"$set":{"status":1}},sort=[("upload_time", pymongo.DESCENDING)], return_document=pymongo.ReturnDocument.BEFORE)
            if doc is None :
                doc = self.reddits.find_one_and_update({"status":-1}, {"$set":{"status":1}}, return_document=pymongo.ReturnDocument.BEFORE)
            
            if doc is None :
                return None, None
            return (doc['url'], doc['status'])
        except Exception as e:
            print(("c", f"[bold red]Error retrieving URL to crawl: {e}[/bold red]"))
            return None, None

    def add_pages(self, pages):
        try :
            self.db.pages.insert_many(pages,ordered=False)
        except Exception as e:
            print(('c', f'[bold red]Error during adding crawled web pages to db : {e}[/bold red]'))
    

    def retrieve_urls_to_crawl(self, limit=100):
        try:
            urls = (
                self.urls_to_crawl.find()
                .sort("upload_time", pymongo.ASCENDING)
                .limit(limit)
            )

            tosend = []
            todel = []

            for doc in urls:
                tosend.append(doc["url"])
                todel.append(doc["_id"])

            if todel:
                self.urls_to_crawl.delete_many(
                    {"_id": {"$in": todel}}
                )

            return tosend
        except Exception as e:
            print(("c", f"[bold red]Error retrieving URLs to crawl: {e}[/bold red]"))
            return []

    def add_crawled_url(self, url):
        try:
            parsed = urlparse(url)
            self.urls_to_crawl.update_one({"url":url},{"$set":{"status":2}})
            return None
        except Exception as e:
            print(("c", f"[bold red]Error adding crawled URL {url}: {e}[/bold red]"))

    def remove_crawled_url(self, url):
        try:
            self.urls_to_crawl.update_one({"url":url},{"$set":{"status":-1}})
            return None
        except Exception as e:
            print(("c", f"[bold red]Error removing crawled URL {url}: {e}[/bold red]"))


    def remove_reddit_crawled_url(self, url):
        try:
            self.reddits.update_one({"url":url},{"$set":{"status":-1}})
            return None
        except Exception as e:
            print(("c", f"[bold red]Error removing crawled URL {url}: {e}[/bold red]"))
    
    def is_url_crawled(self, url):
        try:
            doc = self.urls_to_crawl.find_one(
                {"url": url},
                {"_id": 0, "status": 1},
            )
            return doc is not None and doc["status"] == 2
        except Exception as e:
            print(("c", f"[bold red]Error checking crawled URL {url}: {e}[/bold red]"))
            return False

    def add_robot_file(self, netloc, file_content):
        try:
            self.robots.insert_one(
                {"netloc": netloc, "file_content": file_content}
            )
        except Exception as e:
            print(("c", f"[bold red]Error adding robot file for {netloc}: {e}[/bold red]"))

    def get_robot_file(self, netloc):
        try:
            doc = self.robots.find_one(
                {"netloc": netloc},
                {"_id": 0, "file_content": 1},
            )
            return doc["file_content"] if doc else None
        except Exception as e:
            print(("c", f"[bold red]Error retrieving robot file for {netloc}: {e}[/bold red]"))
            return None