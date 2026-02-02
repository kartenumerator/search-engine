import random
import aiohttp
import asyncio
import sqlite3
import datetime
from collections import defaultdict
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from selectolax.parser import HTMLParser
from dbm import dbm

import multiprocessing
import time

content = ""

# ================= CONFIG =================

CONCURRENT_REQUESTS = 70
REQUEST_PER_HOST = 2

crawled_urls = 0
limit = 10000

robots = {}

# ================= SQLITE =================

conn = sqlite3.connect("./db/crawledpages.db")
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode=WAL;")
cursor.execute("PRAGMA synchronous=NORMAL;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,
    html TEXT NOT NULL
)
""")

# ================= HTTP =================

headers = {
    "User-Agent": "MyBot/1.0 (contact: tpg4m3risb3st@gmail.com)"
}

# ================= DB MANAGER =================

manager = dbm("localhost", 27017)

# ================= CONCURRENCY =================

semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
host_semaphores = defaultdict(lambda: asyncio.Semaphore(REQUEST_PER_HOST))
host_workers = defaultdict(int)

overbooked_hosts = set()
overbooked_lock = asyncio.Lock()

active_workers = 0

# ================= ROBOTS =================

async def get_robots(session, url):
    parsed = urlparse(url)

    def add_robot_to_db(netloc, content):
        tmp = dbm("localhost", 27017)
        tmp.add_robot_file(netloc, content)

    try:
        robots_txt = manager.get_robot_file(parsed.netloc)
        if robots_txt is None:
            async with session.get(
                f"{parsed.scheme}://{parsed.netloc}/robots.txt",
                headers=headers
            ) as r:
                if r.status == 200:
                    robots_txt = await r.text()
                    multiprocessing.Process(
                        target=add_robot_to_db,
                        args=(parsed.netloc, robots_txt)
                    ).start()
                else:
                    robots_txt = ""
                    multiprocessing.Process(
                        target=add_robot_to_db,
                        args=(parsed.netloc, "")
                    ).start()

        if robots_txt:
            rp = RobotFileParser()
            rp.parse(robots_txt.splitlines())
            robots[parsed.netloc] = rp
        else:
            robots[parsed.netloc] = None

    except Exception as e:
        print(f"[ROBOTS ERROR] {parsed.netloc}: {e}")
        robots[parsed.netloc] = None

# ================= SQLITE WRITER =================

sqlite_queue = asyncio.Queue()

async def sqlite_worker(batch_size=100, flush_interval=1.0):
    buffer = []
    last_flush = time.time()

    while True:
        try:
            url, html = await asyncio.wait_for(
                sqlite_queue.get(),
                timeout=flush_interval
            )
            buffer.append((url, html))
            sqlite_queue.task_done()
        except asyncio.TimeoutError:
            pass

        if buffer and (
            len(buffer) >= batch_size or
            time.time() - last_flush >= flush_interval
        ):
            cursor.executemany(
                "INSERT INTO pages (url, html) VALUES (?, ?)",
                buffer
            )
            conn.commit()
            buffer.clear()
            last_flush = time.time()

# ================= FETCH WORKER =================

async def fetch_data(session, wid):
    global crawled_urls, active_workers

    active_workers += 1

    while crawled_urls < limit:
        urls = []

        url = manager.retrieve_url(list(overbooked_hosts))
        if url is None:
            print("[INFO] No URL to crawl, worker exiting")
            active_workers -= 1
            return

        current = urlparse(url)

        host_workers[current.netloc] += 1
        async with overbooked_lock:
            if host_workers[current.netloc] >= REQUEST_PER_HOST:
                overbooked_hosts.add(current.netloc)

        # print(f"[{wid}] START {url}")

        async with semaphore:
            async with host_semaphores[current.netloc]:
                try:
                    async with session.get(
                        url,
                        allow_redirects=True,
                        headers=headers
                    ) as response:

                        if response.status == 403:
                            print(f"[RATE LIMITED] {url}")
                            await asyncio.sleep(5)

                        elif response.status == 200:
                            html = await response.text()
                            crawled_urls += 1
                            print(f"[{wid}] OK {url} | total={crawled_urls}")

                            await sqlite_queue.put((url, html))

                            tree = HTMLParser(html)

                            for node in tree.css("a"):
                                href = node.attrs.get("href")
                                if not href:
                                    continue

                                parsed = urlparse(urljoin(url, href))
                                if parsed.scheme not in ("http", "https"):
                                    continue

                                newurl = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

                                if manager.is_url_crawled(parsed.netloc, parsed.path):
                                    continue

                                if newurl not in urls:
                                    if crawled_urls + len(urls) >= limit:
                                        break
                                    urls.append(newurl)

                        else:
                            print(f"[{wid}] FAIL {url} status={response.status}")

                except asyncio.TimeoutError:
                    print(f"[TIMEOUT] {url}")
                    host_workers[current.netloc] = 999
                    async with overbooked_lock:
                        overbooked_hosts.add(current.netloc)

                except Exception as e:
                    print(f"[ERROR] {url}: {e}")

        host_workers[current.netloc] -= 1
        async with overbooked_lock:
            if (
                current.netloc in overbooked_hosts and
                host_workers[current.netloc] < REQUEST_PER_HOST
            ):
                overbooked_hosts.remove(current.netloc)

        if urls:
            manager.add_urls_to_crawl([
                {
                    "url": u,
                    "netloc": urlparse(u).netloc,
                    "upload_time": datetime.datetime.now()
                }
                for u in urls
            ])

        manager.add_crawled_url(current.netloc, current.path)

        # print(f"[{wid}] DONE {url}")
        print(crawled_urls)

    active_workers -= 1

# ================= MAIN =================

async def main():
    asyncio.create_task(sqlite_worker())

    connector = aiohttp.TCPConnector(
        limit=CONCURRENT_REQUESTS,
        limit_per_host=5,
        ttl_dns_cache=300,
        keepalive_timeout=60
    )

    timeout = aiohttp.ClientTimeout(
        total=60,
        connect=20,
        sock_read=40
    )

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers=headers
    ) as session:

        tasks = [
            fetch_data(session, i)
            for i in range(CONCURRENT_REQUESTS)
        ]

        await asyncio.gather(*tasks)

    print("[DONE] All tasks finished")

# ================= ENTRY =================

if __name__ == "__main__":
    asyncio.run(main())
