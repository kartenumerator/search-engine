import datetime

import pymongo
from schemas import (
    urls_to_crawl_schema,
    urls_to_crawl_index,
    robots_index,
    robots_schema,
)
from pymongo.errors import BulkWriteError
from urllib.parse import urlparse


class dbm:
    def __init__(self, host, port, log_queue):

        self.client = pymongo.MongoClient(host, port)
        self.db = self.client.search_engine
        self.log_queue = log_queue


        # if "robots" not in self.db.list_collection_names():
        #     self.log_queue.put(
        #         ("c", "Creating robots collection with schema validation")
        #     )
        #     result = self.db.create_collection(
        #         "robots", validator=robots_schema
        #     )
        #     self.db.robots.create_index(robots_index, unique=True)
        #     self.log_queue.put(("c", str(result)))

        if "urls_to_crawl" not in self.db.list_collection_names():
            self.log_queue.put(
                ("c", "Creating urls_to_crawl collection with schema validation")
            )
            result = self.db.create_collection(
                "urls_to_crawl", validator=urls_to_crawl_schema
            )
            self.db.urls_to_crawl.create_index(
                urls_to_crawl_index, unique=True
            )
            
            self.db.urls_to_crawl.create_index({"upload_time":pymongo.DESCENDING})
            self.log_queue.put(("c", str(result)))
        
        if "reddits" not in self.db.list_collection_names():
            self.log_queue.put(
                ("c", "Creating reddits collection with schema validation")
            )
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
            self.log_queue.put(("c", str(result)))


        if "hosts" not in self.db.list_collection_names():
            self.log_queue.put(
                ("c", "Creating hosts collection with schema validation")
            )
            result = self.db.create_collection(
                "hosts", validator={
                    '$jsonSchema': {
                        'bsonType': 'object',
                        'additionalProperties': True,
                        'required': ['netloc'],
                        'properties': {
                            'netloc':{'bsonType':'string'},
                            'failed':{
                                'bsonType':'int',
                            },
                            'total': {
                                'bsonType': 'int'
                            },
                        }
                    }
                }
            )
            self.db.hosts.create_index({'netloc':1}, unique=True)
            self.log_queue.put(("c", str(result)))

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
            self.log_queue.put(("c", "Created global_vars collection with schema validation"))
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
            self.log_queue.put(("c", "Created pages collection with schema validation"))

        self.crawled_urls = self.db.crawled_urls
        self.urls_to_crawl = self.db.urls_to_crawl
        self.reddits = self.db.reddits
        # self.robots = self.db.robots
        self.hosts = self.db.hosts

    def add_url_to_crawl(self, url, upload_time):
        try:
            self.urls_to_crawl.insert_one(
                {"url": url, "upload_time": upload_time}
            )
        except Exception as e:
            self.log_queue.put(
                ("c", f"[bold red]Error adding URL to crawl {url}[/bold red]: {e}")
            )

    def add_urls_to_crawl(self, urls, currhost):
        try:
            ops = []
            redops = []
            for url in urls :
                parsed = urlparse(url)
                doc = {"url":url, "netloc":parsed.hostname,"status":-2,"timestamp": datetime.datetime.now(datetime.timezone.utc)}
                actn = (pymongo.UpdateOne(
                    {'url':url},
                    {
                        "$inc": {"upload_time": 1},      # increment if exists
                        "$set":{"referrer":currhost},   # update referrer if exists
                        "$setOnInsert": {            # fields only for new docs
                            **doc
                        }
                    },
                    upsert=True
                ))
                if parsed.hostname == "www.reddit.com" :
                    redops.append(actn)
                else :
                    ops.append(actn)
            self.urls_to_crawl.bulk_write(ops, ordered=False)
            if len(redops) > 0 :
                self.reddits.bulk_write(redops, ordered=False)
            # self.urls_to_crawl.insert_many([{"url":u, "netloc":urlparse(u).hostname,"upload_time":self.urls_to_crawl.estimated_document_count()+1,"status":0} for u in urls], ordered=False)
            return None
        except BulkWriteError as err:
            self.log_queue.put(
                ("c", f"Duplicate URLs found while adding URLs to crawl {err}")
            )
            return None
        except Exception as e:
            self.log_queue.put(
                ("c", f"[bold red]Error adding URLs to crawl: {e}[/bold red]")
            )
            return None
        
    def check_flag_to_crawl(self):
        try:
            doc = self.db.global_vars.find_one({"_id":"crawl_flag"}, {"status": 1})
            return doc is not None and doc["status"] == 1
        except Exception as e:
            self.log_queue.put(
                ("c", f"[bold red]Error checking flag to crawl {e}[/bold red]")
            )
            return False
        
    def set_flag_to_crawl(self, value):
        try:
            self.db.global_vars.update_one({"_id":"crawl_flag"},{"$set":{"status":value}}, upsert=True)
        except Exception as e:
            self.log_queue.put(
                ("c", f"[bold red]Error setting flag to crawl {e}[/bold red]")
            )

    def retrieve_url(self,overbooked_hosts):
        try:
            doc = self.urls_to_crawl.find_one_and_update({"netloc":{"$nin":overbooked_hosts}, "status":0}, update={"$set":{"status":1}},sort=[("upload_time", pymongo.DESCENDING)], return_document=pymongo.ReturnDocument.AFTER)
            # self.add_crawled_url(doc["url"]) 
            if doc is None :
                doc = self.urls_to_crawl.find_one_and_update({"netloc":{"$nin":overbooked_hosts}, "status":-1}, {"$set":{"status":1}}, return_document=pymongo.ReturnDocument.AFTER)
            
            if doc is None :
                return None 
            self.hosts.update_one({"netloc":doc['netloc']},{"$inc":{"total":1}}, upsert=True)
            return doc["url"]
        except Exception as e:
            self.log_queue.put(
                ("c", f"[bold red]Error retrieving URL to crawl: {e}[/bold red]")
            )
            return None

    def add_pages(self, pages):
        try :
            self.db.pages.insert_many(pages,ordered=False)
        except Exception as e:
            self.log_queue.put(('c', f'[bold red]Error during adding crawled web pages to db : {e}[/bold red]'))
    

    def retrieve_urls_to_crawl(self, overbooked_hosts, limit=100 ):
        try:
            urls = list(
                self.urls_to_crawl.find({'netloc':{'$nin':overbooked_hosts}})
                .sort("upload_time", pymongo.ASCENDING)
                .limit(limit)
            )

            return urls
        except Exception as e:
            self.log_queue.put(
                ("c", f"[bold red]Error retrieving URLs to crawl: {e}[/bold red]")
            )
            return []

    def add_crawled_url(self, url):
        try:
            parsed = urlparse(url)
            # self.crawled_urls.insert_one(
            #     {"url":url,"netloc": parsed.netloc, "path": parsed.path, "status":0}
            # )
            self.urls_to_crawl.update_one({"url":url},{"$set":{"status":2}})
            self.hosts.update_one({"netloc":parsed.hostname},{"$inc":{"total":1}}, upsert=True)
            return None
        except Exception as e:
            self.log_queue.put(
                ("c", f"[bold red]Error adding crawled URL {url}: {e}[/bold red]")
            )

    def remove_crawled_url(self, url, toupdate=True):
        try:
            # parsed = urlparse(url)
            self.urls_to_crawl.update_one({"url":url},{"$set":{"status":-1}})
            if toupdate :
                return False
            hostname = urlparse(url).hostname
            doc = self.hosts.find_one_and_update({"netloc":hostname},{"$inc":{"failed":1, "total":1}}, return_document=pymongo.ReturnDocument.AFTER)
            if doc is not None and doc['total'] > 20 and doc['failed']/doc['total'] > 0.6 :
                self.urls_to_crawl.delete_many({"referrer":hostname, 'status':{"$in":[0,-1]}})
                self.urls_to_crawl.delete_many({"netloc":hostname, 'status':{"$in":[0,-1]}})
                self.log_queue.put(
                    ("c", f"[bold red]Removed all URLs with referrer {hostname} due to high failure rate[/bold red]")
                )
                self.hosts.delete_one({"netloc":hostname})
                return True
            return False
        except Exception as e:
            self.log_queue.put(
                ("c", f"[bold red]Error removing crawled URL {url}: {e}[/bold red]")
            )
            return False

    def is_url_crawled(self, url):
        try:
            doc = self.urls_to_crawl.find_one(
                {"url": url},
                {"_id": 0, "status": 1},
            )
            return doc is not None and doc["status"] == 2
        except Exception as e:
            self.log_queue.put(
                ("c", f"[bold red]Error checking crawled URL {url}: {e}[/bold red]")
            )
            return False

    def add_robot_file(self, netloc, file_content):
        try:
            self.robots.insert_one(
                {"netloc": netloc, "file_content": file_content}
            )
        except Exception as e:
            self.log_queue.put(
                ("c", f"[bold red]Error adding robot file for {netloc}: {e}[/bold red]")
            )

    def get_robot_file(self, netloc):
        try:
            doc = self.robots.find_one(
                {"netloc": netloc},
                {"_id": 0, "file_content": 1},
            )
            return doc["file_content"] if doc else None
        except Exception as e:
            self.log_queue.put(
                ("c", f"[bold red]Error retrieving robot file for {netloc}: {e}[/bold red]")
            )
            return None