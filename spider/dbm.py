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


class dbm:
    def __init__(self, host, port):

        self.client = pymongo.MongoClient(host, port)
        self.db = self.client.search_engine

        if "robots" not in self.db.list_collection_names():
            print("[DB] Creating robots collection with schema validation")
            result = self.db.create_collection(
                "robots", validator=robots_schema
            )
            self.db.robots.create_index(robots_index, unique=True)
            print(result)

        if "urls_to_crawl" not in self.db.list_collection_names():
            print("[DB] Creating urls_to_crawl collection with schema validation")
            result = self.db.create_collection(
                "urls_to_crawl", validator=urls_to_crawl_schema
            )
            self.db.urls_to_crawl.create_index(
                urls_to_crawl_index, unique=True
            )
            print(result)

        if "crawled_urls" not in self.db.list_collection_names():
            print("[DB] Creating crawled_urls collection with schema validation")
            result = self.db.create_collection(
                "crawled_urls", validator=crawled_urls_schema
            )
            self.db.crawled_urls.create_index(
                crawled_urls_index, unique=True)
            print(result)

        self.crawled_urls = self.db.crawled_urls
        self.urls_to_crawl = self.db.urls_to_crawl
        self.robots = self.db.robots

    def add_url_to_crawl(self, url, upload_time):
        try:
            self.urls_to_crawl.insert_one(
                {"url": url, "upload_time": upload_time}
            )
        except Exception as e:
            print(f"[ERROR] Error adding URL to crawl {url}: {e}")

    def add_urls_to_crawl(self, urls):
        try:
            self.urls_to_crawl.insert_many(urls, ordered=False)
            return None
        except BulkWriteError as err:
            # Duplicate URLs are expected at scale
            return [
                e["keyValue"]["url"]
                for e in err.details.get("writeErrors", [])
            ]
        except Exception as e:
            print(f"[ERROR] Error adding URLs to crawl: {e}")
            return None

    def retrieve_url(self, overbooked_hosts):
        try:
            doc = self.urls_to_crawl.find_one(
                {"netloc": {"$nin": overbooked_hosts}},
                sort=[("upload_time", pymongo.ASCENDING)],
            )
            if doc:
                self.urls_to_crawl.delete_one({"_id": doc["_id"]})
                return doc["url"]
            return None
        except Exception as e:
            print(f"[ERROR] Error retrieving URL to crawl: {e}")
            return None

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
            print(f"[ERROR] Error retrieving URLs to crawl: {e}")
            return []

    def add_crawled_url(self, netloc, path):
        try:
            self.crawled_urls.insert_one(
                {"netloc": netloc, "path": path, "status":0}
            )
        except Exception as e:
            print(
                f"[ERROR] Error adding crawled URL {netloc}{path}: {e}"
            )

    def is_url_crawled(self, netloc, path):
        try:
            doc = self.crawled_urls.find_one(
                {"netloc": netloc, "path": path},
                {"_id": 1},
            )
            return doc is not None
        except Exception as e:
            print(
                f"[ERROR] Error checking crawled URL {netloc}{path}: {e}"
            )
            return False

    def add_robot_file(self, netloc, file_content):
        try:
            self.robots.insert_one(
                {"netloc": netloc, "file_content": file_content}
            )
        except Exception as e:
            print(
                f"[ERROR] Error adding robot file for {netloc}: {e}"
            )

    def get_robot_file(self, netloc):
        try:
            doc = self.robots.find_one(
                {"netloc": netloc},
                {"_id": 0, "file_content": 1},
            )
            return doc["file_content"] if doc else None
        except Exception as e:
            print(
                f"[ERROR] Error retrieving robot file for {netloc}: {e}"
            )
            return None
