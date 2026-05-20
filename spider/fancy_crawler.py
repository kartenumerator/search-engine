
import random
import aiohttp
import asyncio
import bs4
from urllib.parse import urljoin,urlparse
from urllib.robotparser import RobotFileParser
import sqlite3
import datetime
from collections import defaultdict

# from rich.pretty import data
from pymongo import response
from selectolax.parser import HTMLParser

from rich.console import Console
from fancy_dbm import dbm
import multiprocessing
import mimetypes
import time
import traceback 
import window
import signal
import json
import os
import sys

# Get the absolute path to the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add it to the list of places Python looks for modules
sys.path.append(parent_dir)


import helper
from dotenv import load_dotenv

content = ""

load_dotenv()


#TODO : add REDIS

CONCURRENT_REQUESTS = 50
REQUEST_PER_HOST = 2

crawled_urls = 0
limit = 100000

robots = {}

headers = {
    "User-Agent": "MyBot/1.0 (contact: tpg4m3risb3st@gmail.com)",
    'Accept': 'text/html',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive'
}

useragents =[
    "MyBot/1.0 (contact: tpg4m3risb3st@gmail.com)",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
]

log_queue = multiprocessing.Queue()
manager = dbm(os.getenv("MONGO_HOST"),int(os.getenv("MONGO_PORT")),log_queue=log_queue)

semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
host_semaphores = defaultdict(lambda: asyncio.Semaphore(REQUEST_PER_HOST))
host_workers = defaultdict(int)
overbooked_hosts = {}

active_workers = 0

# log_json = {}
# with open("data.json", "r") as infile:
#     log_json = json.load(infile)

urlsqueue = multiprocessing.Queue()
def fetch_url_worker(manager, urlsqueue : multiprocessing.Queue):
    while True :
        if urlsqueue.qsize() < 2*CONCURRENT_REQUESTS:
            pipeline = [
                    {
                        "$match": {
                            "status": -2 
                        }
                    },
                    {
                        # 1. Sort BEFORE grouping so $first gets the correct record
                        "$sort": {
                            "upload_time": -1,
                            "timestamp": 1
                        }
                    },
                    {
                        # 2. Use $group to pick the first occurrence of each netloc
                        "$group": {
                            "_id": "$netloc",
                            "id": { "$first": "$_id" },
                            "url": { "$first": "$url" },
                            "upload_time": { "$first": "$upload_time" },
                            "timestamp": { "$first": "$timestamp" },
                            # Add any other fields you need here
                        }
                    },
                    {
                        # 3. Re-sort the final unique list
                        "$sort": {
                            "upload_time": -1,
                            "timestamp": 1
                        }
                    },
                    {
                        "$limit": 5*CONCURRENT_REQUESTS
                    }
                ]

            docs = list(manager.db.urls_to_crawl.aggregate(pipeline))
            manager.db.urls_to_crawl.update_many({'url':{'$in':[doc['url'] for doc in docs]}}, {'$set':{'status':1}})
            # manager.db.hosts.update_many({"netloc":{"$in":docs}},{"$inc":{"total":1}}, upsert=True)
            # docs = manager.retrieve_urls_to_crawl(limit=1000, overbooked_hosts=[])
            # print("fetched")
            for doc in reversed(docs) :
                urlsqueue.put(doc['url'])
        # time.sleep(0.1)


async def get_robots(session, url):
    global robots, headers
    parsedjoinedurl = urlparse(url)
    
    def add_robot_to_db(netloc, file_content,log_queue):
        tmpmng = dbm(os.getenv('MONGO_HOST'),os.getenv('MONGO_PORT'),log_queue=log_queue)
        tmpmng.add_robot_file(netloc, file_content)

    try :
        robots_response_text = manager.get_robot_file(parsedjoinedurl.netloc)
        if robots_response_text is None:
            # print("Not in db")
            async with session.get(f"{parsedjoinedurl.scheme}://{parsedjoinedurl.netloc}/robots.txt", headers=headers) as robots_response:
                # print(robots_response.status)
                if robots_response.status == 200:
                    robots_response_text = await robots_response.text()
                    
                    if parsedjoinedurl.netloc in robots:
                        return
                    p = multiprocessing.Process(target=add_robot_to_db, args=(parsedjoinedurl.netloc, robots_response_text,log_queue))
                    p.start()
                    # rp = RobotFileParser()
                    # rp.parse(robots_response_text.splitlines())
                    # robots[parsedjoinedurl.netloc] = rp
                    
                else:

                    if parsedjoinedurl.netloc in robots:
                        return
                    p = multiprocessing.Process(target=add_robot_to_db, args=(parsedjoinedurl.netloc, "",log_queue))
                    p.start()
                    # print("No robots file")
                    robots_response_text = ""

        if robots_response_text == "":
            robots[parsedjoinedurl.netloc] = None
        else:
            rp = RobotFileParser()
            rp.parse(robots_response_text.splitlines())
            robots[parsedjoinedurl.netloc] = rp
                
    except Exception as e:
        # print(f"Error fetching robots.txt for {url}: {e}.")
        robots[parsedjoinedurl.netloc] = None

sqlite_queue = asyncio.Queue()

async def sqlite_worker(batch_size=100, flush_interval=5.0):
    # global log_json

    buffer = []
    last_flush = time.time()
    
    try :
        while True:
            try:
                url, data, title, meta_description = sqlite_queue.get_nowait()
                buffer.append({"url":url, "html":data, "status":0, "title":title, "meta_description":meta_description})
                sqlite_queue.task_done()

            except asyncio.QueueEmpty:
                await asyncio.sleep(flush_interval)
                # pass

            for host in list(overbooked_hosts.keys()):
                if time.time() - overbooked_hosts[host] > 300:  # 5 minutes cooldown
                    host_workers[host] = 0
                    del overbooked_hosts[host]
            # Flush conditions
            if (
                not run.is_set() and 
                (len(buffer) >= batch_size or
                (buffer and time.time() - last_flush >= flush_interval))
            ):
                log_queue.put(("c","[bold green]Pushing to sqlite[/bold green]"))
                # try :
                #     with open("data.json", "w") as outfile:
                #         json.dump(log_json, outfile)
                # except Exception as e:
                #     log_queue.put(("c",f"[red]Error writing log_json to file: {e}[/red]"))

                manager.add_pages(buffer)
                log_queue.put(("c","[bold green]Pushed to sqlite[/bold green]"))
                # cursor.executemany(
                #     "INSERT INTO pages (url, html) VALUES (?, ?)",
                #     buffer
                # )
                # conn.commit()
                buffer.clear()
                last_flush = time.time()
    except asyncio.CancelledError :
        log_queue.put(("c","Adding remaining buffer..."))
        
        while not sqlite_queue.empty() :
            url, data, title, meta_description = sqlite_queue.get_nowait()
            buffer.append({"url":url, "html":data, "status":0, "title":title, "meta_description":meta_description})
            sqlite_queue.task_done()
        
        manager.add_pages(buffer)
                
        # cursor.executemany(
        #     "INSERT INTO pages (url, html) VALUES (?, ?)",
        #     buffer
        # )
        # conn.commit()
        buffer.clear()
        return




run = asyncio.Event()

async def fetch_data(session,id):

    global headers,limit,robots,semaphore,crawled_urls,manager,log_queue,active_workers,overbooked_hosts,run, urlsqueue

    active_workers += 1
    while not run.is_set() and (crawled_urls) < limit:
        async with semaphore:
            urls = []

            # url = manager.retrieve_url(list(overbooked_hosts.keys()))
            try :
                log_queue.put((id,f'retrieving url'))
                url = urlsqueue.get_nowait()
                rejected = []
                rejlocs = []
                while urlparse(url).hostname in overbooked_hosts.keys() :
                    log_queue.put(("a",f'overbooked url : {url}'))
                    rejected.append(urls)
                    rejlocs.append(urlparse(url).hostname)
                    url = urlsqueue.get_nowait()
                    await asyncio.sleep(1)
                    # print(url)
                if len(rejected) > 0 :
                    manager.db.urls_to_crawl.update_many({'url':{'$in':rejected}}, {'$set':{'status':0}})
                    # manager.db.hosts.update_many({"netloc":{"$in":rejlocs}}, {"$inc":{"toFtal":-1}})
            except Exception as e:
                log_queue.put(("a", "[red]No URL to crawl, waiting for 5 seconds[/red]"))
                # active_workers -= 1
                await asyncio.sleep(1)
                continue
            
            currenturl = urlparse(url)
            # reddit = False
            # if currenturl.netloc == "www.reddit.com" :
            #     reddit = True
            #     if url[-1] == '/':
            #         url = url[:-1]+'.json'
            #     else :
            #         url = url+'.json'
            
            host_workers[currenturl.hostname] += 1
            if(host_workers[currenturl.hostname] >= REQUEST_PER_HOST) :
                overbooked_hosts[currenturl.hostname] = time.time()
            log_queue.put((id, url))
            log_queue.put(("a", f"Starting task: {url}"))
            data = ""
            log_queue.put((id, f'[bold yellow]{url}[/bold yellow]'))
            async with host_semaphores[urlparse(url).hostname]:
                try:
                    # await asyncio.sleep(0.5)
                    log_queue.put((id, f'[bold blue]{url}[/bold blue]'))
        
                    async with session.get(url, allow_redirects=True,headers=headers) as response:
                        
                        if response.status == 403 or response.status == 429:
                            log_queue.put(("a", f"[red]Rate limited by {url}[/red]"))

                            manager.remove_crawled_url(url, True)
                            host_workers[currenturl.netloc] = 51
                            overbooked_hosts[currenturl.netloc] = time.time()
                            await asyncio.sleep(5)
                            # headers["User-Agent"] = useragents[0 if headers["User-Agent"] == useragents[1] else 1]
                        elif response.status == 200:
                            
                            if not response.headers.get("Content-Type", "").lower().startswith("text/html"):
                                log_queue.put((id, f'[bold red]{url}[/bold red]'))
                                log_queue.put(("a", f"[red]Non-HTML content at {url}, skipping.[/red]"))
                                manager.remove_crawled_url(url, False)
                                continue
                                
                            # if not response.headers.get("Lan")

                            manager.add_crawled_url(url=url)
                            encoding = response.charset  # may be None
                            # raw = await read_throttled(response, bandwidth_limiter)
                            # data = raw.decode(encoding=encoding or 'utf-8', errors='replace')

                            total = 0
                            chunks = []
                            async for chunk in response.content.iter_chunked(8192):
                                total += len(chunk)
                                if total > 4*1024*1024 :
                                    log_queue.put(('c',f'[bold red]too big to handle {url}[/bold red]'))
                                    raise ValueError("tooooo big")
                                    
                                chunks.append(chunk)
                                
                            raw = b"".join(chunks)
                            data = raw.decode(encoding or "utf-8", errors="replace")
                            # limit -= 1


                            log_queue.put((id, f'[bold green]{url}[/bold green]'))
                            crawled_urls += 1
                            update_content()

                            # cursor.execute("INSERT INTO pages (url, html) VALUES (?, ?)", (url, data))
                            # conn.commit()

                            tree = HTMLParser(data)

                            title_node = tree.css_first('title')
                            title = title_node.text(strip=True) if title_node else 'No title'

                            meta_node = tree.css_first('meta[name="description"]')
                            meta_description = meta_node.attributes.get('content', 'No metadata') if meta_node else 'No metadata'
                            if meta_description is None or meta_description.strip() == '':
                                meta_description = 'No metadata'
                            # log_queue.put(("a", f"[green]metadata : {meta_description}[/green]"))

                            for tag in tree.css('script, style, nav, header, footer'):
                                tag.decompose()
                            
                            data = tree.body.text(separator='\n', strip=True)

                            cleaned = [line for line in data.splitlines() if line.strip()]
                            cleaneddata = "\n".join(cleaned)
                            if ("anime" not in cleaneddata.lower() and "anime" not in title.lower() and "anime" not in meta_description.lower() and "ani" not in url.lower()) and ("manga" not in cleaneddata.lower() and "manga" not in title.lower() and "manga" not in meta_description.lower() and "manga" not in url.lower()): 
                                # log_queue.put(("a", f"[red]Anime or Manga content not found in {url}[/red]"))
                                continue
                            
                            if len(cleaneddata) > 100:  # Example threshold, adjust as needed
        
                                log_queue.put((id, f'[bold orange]{url}[/bold orange]'))
                                await sqlite_queue.put((url, cleaneddata, title, meta_description))
                                log_queue.put((id, f'[bold green]{url}[/bold green]'))

                            # soup = bs4.BeautifulSoup(data, 'html.parser')

                            robot_tasks = []
                            extracted_links = []

                            for node in tree.css("a"):
                                link = node.attrs.get("href")
                                parsedjoinedurl = urlparse(urljoin(url, link))
                                if parsedjoinedurl.scheme not in ("http","https") or parsedjoinedurl.netloc == '' :
                                    continue
                                else :
                                    # print(newurl)joined_url
                                    newurl = f"{parsedjoinedurl.scheme}://{parsedjoinedurl.netloc}{parsedjoinedurl.path}"
                                    # mtype,encoding = mimetypes.guess_type(newurl)
                                    # if mtype is not None and not mtype.startswith("text/html"):
                                    #     continue
                                    is_not_html, ext = helper.check_url_extension(newurl)
                                    if is_not_html :
                                        continue
                                    if not manager.is_url_crawled(newurl) and newurl not in urls:
                                        if(len(urls)+crawled_urls>=limit):
                                            break
                                        # crawled_list.append(newurl)
                                        urls.append(newurl)
                                            
                            if len(robot_tasks) > 0:
                                await asyncio.gather(*robot_tasks)
                                for link in extracted_links:
                                    if(len(urls)+crawled_urls>=limit):
                                        break
                                    parsedjoinedurl = urlparse(link)
                                    
                                    if  link not in urls and (robots[parsedjoinedurl.netloc] is None or robots[parsedjoinedurl.netloc].can_fetch('*', parsedjoinedurl.path)):
                                        urls.append(link)
                                        # crawled_list.append(link)
                        else:
                            if manager.remove_crawled_url(url, False) :
                                host_workers[currenturl.netloc] = 51
                                overbooked_hosts[currenturl.netloc] = time.time()

                            log_queue.put((id, f'[bold red]{url}[/bold red]'))
                            log_queue.put(("a", f"Couldnt retrieve {url} | status [red]{response.status}[/red]"))
                            # headers["User-Agent"] = useragents[0 if headers["User-Agent"] == useragents[1] else 1]
                except asyncio.TimeoutError as e :
                    log_queue.put(("a", f"[red]Error fetching {url}: {e}.[/red]"))
                    log_queue.put(("c", f"[red]{url}[/red]"))
                    # if currenturl.netloc in log_json:
                    #     log_json[currenturl.netloc] += 1
                    # else :
                        # log_json[currenturl.netloc] = 1
                    if manager.remove_crawled_url(url, False) :

                        host_workers[currenturl.netloc] = 51
                        overbooked_hosts[currenturl.netloc] = time.time()
                    
                    # host_workers[currenturl.netloc] = 51
                    # async with overbooked_lock:
                    #     overbooked_hosts[currenturl.netloc] = time.time()
                except Exception as e:

                    log_queue.put((id, f'[bold red]{url}[/bold red]'))
                    log_queue.put(("a", f"[red]Error fetching {url}: {e}.[/red]"))

                    if manager.remove_crawled_url(url, False) :

                        host_workers[currenturl.netloc] = 51
                        overbooked_hosts[currenturl.netloc] = time.time()
                    # traceback.print_exc()
            

            log_queue.put(("a", f"[green]Completed task: {url}[/green]"))
            host_workers[currenturl.hostname] -= 1

            if currenturl.hostname in overbooked_hosts and host_workers[currenturl.hostname] < REQUEST_PER_HOST:
                del overbooked_hosts[currenturl.hostname]
            # urls.remove(url)
            # completed_urls.append(url)

            # t = time.time_ns()
            # tmpmng = dbm("localhost",27017)
            if len(urls) > 0:
                ret = manager.add_urls_to_crawl(urls=urls, currhost=currenturl.hostname)
                # if ret is not None :
                #     crawled_list.extend(ret)

        # print(f"{id} peace out.")
        await asyncio.sleep(random.uniform(0.1,0.5))
                
        
    active_workers -= 1
    log_queue.put((id, f''))
    log_queue.put(('a', f'{id} peace out'))
        # print(f"DB updated in {time.time_ns()-t} ns")
        
        # manager.add_urls_to_crawl(urls=[{'url': u, 'upload_time': datetime.datetime.now()} for u in urls])
        # manager.add_crawled_url(currenturl.netloc, currenturl.path)
        # return data

last_update_time = 0
last_update_counter = 0
def update_content():
    global content,crawled_urls,limit,log_queue,active_workers,last_update_time,last_update_counter
    content = f"Crawled URLs: [bold green]{crawled_urls}[/bold green] | Active Workers : [bold blue]{active_workers}[/bold blue] | Current limit: [bold red]{limit}[/bold red] | Speed: [bold yellow]{(crawled_urls - last_update_counter)/(time.time() - last_update_time) if last_update_time !=0 else 0:.2f} URLs/sec[/bold yellow]"
    log_queue.put(("header", content))
    last_update_time = time.time()
    last_update_counter = crawled_urls
    # .update(content)

def handle_interrupt(a,b):
    print("Graceful shutdown")
    run.set()
    

async def main():
    global limit,content,headers,run, active_workers
    # tasks = [fetch_data(url) for url in urls]
    # print("Tasks created, starting to gather results...")
    # results = await asyncio.gather(*tasks)
    # print(f'at the start {retrieve_url()}')
    # with (console=console, screen=False, vertical_overflow="crop") as :

    signal.signal(signalnum=signal.SIGINT, handler=handle_interrupt)

    urlfetcher = multiprocessing.Process(target=fetch_url_worker, args=(manager,urlsqueue))
    urlfetcher.start()

    display = multiprocessing.Process(target=window.main, args=(log_queue,CONCURRENT_REQUESTS), daemon=True)
    display.start()
    connector = aiohttp.TCPConnector(
        limit=CONCURRENT_REQUESTS,              # total open connections
        limit_per_host=REQUEST_PER_HOST,      # critical
        ttl_dns_cache=300,
        keepalive_timeout=30
    )

    timeout = aiohttp.ClientTimeout(
        total=30,
        connect=10,
        sock_read=20
    )

    writertask = asyncio.create_task(sqlite_worker())
    async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=headers) as session:
        # start_time = time.time()
        tasks = [asyncio.create_task(fetch_data(session,i), name=f'{i}') for i in range(CONCURRENT_REQUESTS)]
        try :
            while True :
                flag = manager.check_flag_to_crawl()
                while not flag :
                    log_queue.put(("a", "[red]Crawling paused. Waiting for 1 minute before checking again...[/red]"))
                    await asyncio.sleep(60)
                    flag = manager.check_flag_to_crawl()

                active_workers = 0
                await asyncio.gather(*tasks)
                log_queue.put(("a", "[green]Tasks completed, processing results...[/green]"))
                # manager.set_flag_to_crawl(0)
                # break
        finally:
            # ---- CLEANUP ----
            # await asyncio.gather(*tasks, return_exceptions=True)
            # await asyncio.gather(writertask, return_exceptions=True)
            writertask.cancel()
            await sqlite_queue.join()

            manager.client.close()

            if urlfetcher.is_alive() :
                urlfetcher.terminate()
                urlfetcher.join()

            if display.is_alive():
                display.terminate()
                display.join()

            print("[red]Shutdown complete[/red]")
                
            


        # .update(content)

if __name__ == '__main__':
    asyncio.run(main())
