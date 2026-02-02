import random
import aiohttp
import asyncio
import bs4
from urllib.parse import urljoin,urlparse
from urllib.robotparser import RobotFileParser
import sqlite3
import datetime
from collections import defaultdict

from selectolax.parser import HTMLParser

from rich.console import Console
from fancy_dbm import dbm
import multiprocessing

import time
import traceback
import window
import signal

import os

from dotenv import load_dotenv

content = ""

load_dotenv()


#TODO : add REDIS

CONCURRENT_REQUESTS = 60
REQUEST_PER_HOST = 1

crawled_urls = 0
limit = 100000

# crawled_list = []

robots = {}

# conn = sqlite3.connect(os.getenv("SQLITE_PATH"))
# cursor = conn.cursor()
# cursor.execute("PRAGMA journal_mode=WAL;")
# cursor.execute("PRAGMA synchronous=NORMAL;")

# cursor.execute('''
#     CREATE TABLE IF NOT EXISTS pages (
#         id INTEGER PRIMARY KEY,
#         url TEXT NOT NULL,
#         html TEXT NOT NULL
#     )
# ''')

headers = {
    "User-Agent": "MyBot/1.0 (contact: tpg4m3risb3st@gmail.com)"
}

useragents =[
    "MyBot/1.0 (contact: tpg4m3risb3st@gmail.com)",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
]

log_queue = multiprocessing.Queue()
manager = dbm(os.getenv("MONGO_HOST"),int(os.getenv("MONGO_PORT")),log_queue=log_queue)
# urls = [
#     "https://en.wikipedia.org/wiki/Gintama",
#     # "https://iol.co.za/technology/2007-09-28-nintendo-wii-launches-in-south-africa/",
#     # "https://en.wikipedia.org/wiki/File:Gee!!_I_wish_I_were_a_man,_I'd_join_the_Navy_Be_a_man_and_do_it_-_United_States_Navy_recruiting_station_-_-_Howard_Chandler_Christy_1917._LCCN2002712088.jpg"
# ]

# urls = retrieve_urls_to_crawl(limit=50)
semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
host_semaphores = defaultdict(lambda: asyncio.Semaphore(REQUEST_PER_HOST))
host_workers = defaultdict(int)
overbooked_hosts = set()
overbooked_lock = asyncio.Lock()

# retrieve_lock = asyncio.Lock()

active_workers = 0

async def get_robots(session, url):
    global robots, headers
    parsedjoinedurl = urlparse(url)
    
    def add_robot_to_db(netloc, file_content,log_queue):
        tmpmng = dbm("localhost",27017,log_queue=log_queue)
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

            # Flush conditions
            if (
                not run.is_set() and 
                (len(buffer) >= batch_size or
                (buffer and time.time() - last_flush >= flush_interval))
            ):
                log_queue.put(("c","[bold green]Pushing to sqlite[/bold green]"))
                manager.add_pages(buffer)
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

    global headers,limit,robots,semaphore,crawled_urls,manager,log_queue,active_workers,overbooked_hosts,run

    active_workers += 1
    while not run.is_set() and (crawled_urls) < limit:
        urls = []

        url = manager.retrieve_url(list(overbooked_hosts))

        if url is None:
            log_queue.put(("a", "[red]No URL to crawl, waiting for 5 seconds[/red]"))
            active_workers -= 1
            await asyncio.sleep(5)
            continue
        
        currenturl = urlparse(url)
        host_workers[currenturl.hostname] += 1
        async with overbooked_lock :
            if(host_workers[currenturl.hostname] >= REQUEST_PER_HOST) :
                overbooked_hosts.add(currenturl.hostname)
        log_queue.put((id, url))
        log_queue.put(("a", f"Starting task: {url}"))
        data = ""
        async with semaphore:
            async with host_semaphores[urlparse(url).hostname]:
                try:
                    # await asyncio.sleep(0.5)

                    log_queue.put((id, f'[bold yellow]{url}[/bold yellow]'))
                    async with session.get(url, allow_redirects=True,headers=headers) as response:
                        
                        if response.status == 403:
                            log_queue.put(("a", f"[red]Rate limited by {url}[/red]"))

                            manager.remove_crawled_url(url)
                            await asyncio.sleep(5)
                            # headers["User-Agent"] = useragents[0 if headers["User-Agent"] == useragents[1] else 1]
                        elif response.status == 200:
                            data = await response.text()
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

                            await sqlite_queue.put((url, data, title, meta_description))

                            # soup = bs4.BeautifulSoup(data, 'html.parser')

                            robot_tasks = []
                            retrieving_robots = []
                            extracted_links = []

                            for node in tree.css("a"):
                                link = node.attrs.get("href")
                                parsedjoinedurl = urlparse(urljoin(url, link))
                                if parsedjoinedurl.scheme not in ("http","https"):
                                    continue
                                else :
                                    # print(newurl)joined_url
                                    newurl = f"{parsedjoinedurl.scheme}://{parsedjoinedurl.netloc}{parsedjoinedurl.path}"
                                    if not manager.is_url_crawled(newurl) and newurl not in urls:
                                        # print(robots)
                                        # if parsedjoinedurl.netloc not in robots:
                                        #     # print(f"Retrieving robots file for {parsedjoinedurl.scheme}://{parsedjoinedurl.netloc}/robots.txt") 
                                        #     if len(retrieving_robots) < 10:
                                        #         extracted_links.append(newurl)
                                        #         if parsedjoinedurl.netloc not in retrieving_robots:
                                        #             robot_tasks.append(get_robots(session, newurl,))

                                        #         retrieving_robots.append(parsedjoinedurl.netloc)

                                        # elif robots[parsedjoinedurl.netloc] is None or robots[parsedjoinedurl.netloc].can_fetch('*', parsedjoinedurl.path):
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

                            manager.remove_crawled_url(url)
                            log_queue.put((id, f'[bold red]{url}[/bold red]'))
                            log_queue.put(("a", f"Couldnt retrieve {url} | status [red]{response.status}[/red]"))
                            # headers["User-Agent"] = useragents[0 if headers["User-Agent"] == useragents[1] else 1]
                except asyncio.TimeoutError as e :
                    log_queue.put(("a", f"[red]Error fetching {url}: {e}.[/red]"))
                    log_queue.put(("c", f"[red]{url}[/red]"))
                    manager.remove_crawled_url(url)
                    
                    # host_workers[currenturl.netloc] = 51
                    # async with overbooked_lock:
                    #     overbooked_hosts.add(currenturl.netloc)
                except Exception as e:

                    log_queue.put((id, f'[bold red]{url}[/bold red]'))
                    log_queue.put(("a", f"[red]Error fetching {url}: {e}.[/red]"))

                    manager.remove_crawled_url(url)
                    # traceback.print_exc()
            

            log_queue.put(("a", f"[green]Completed task: {url}[/green]"))
            host_workers[currenturl.hostname] -= 1
            async with overbooked_lock:
                if currenturl.hostname in overbooked_hosts and host_workers[currenturl.hostname] < REQUEST_PER_HOST:
                    overbooked_hosts.remove(currenturl.hostname)
            # urls.remove(url)
            # completed_urls.append(url)

            # t = time.time_ns()
            # tmpmng = dbm("localhost",27017)
            if len(urls) > 0:
                ret = manager.add_urls_to_crawl(urls=urls)
                # if ret is not None :
                #     crawled_list.extend(ret)

                
        
    active_workers -= 1
    log_queue.put((id, f''))
    log_queue.put(('a', f'{id} peace out'))
    # print(f"{id} peace out.")
    await asyncio.sleep(random.uniform(0.1, 0.5))
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
    global limit,content,headers,run
    # tasks = [fetch_data(url) for url in urls]
    # print("Tasks created, starting to gather results...")
    # results = await asyncio.gather(*tasks)
    # print(f'at the start {retrieve_url()}')
    # with (console=console, screen=False, vertical_overflow="crop") as :

    signal.signal(signalnum=signal.SIGINT, handler=handle_interrupt)

    display = multiprocessing.Process(target=window.main, args=(log_queue,CONCURRENT_REQUESTS), daemon=True)
    display.start()
    connector = aiohttp.TCPConnector(
        limit=CONCURRENT_REQUESTS,              # total open connections
        limit_per_host=5,      # critical
        ttl_dns_cache=300,
        keepalive_timeout=60
    )

    timeout = aiohttp.ClientTimeout(
        total=60,
        connect=20,
        sock_read=40
    )

    writertask = asyncio.create_task(sqlite_worker())
    async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=headers) as session:
        # start_time = time.time()
        tasks = [asyncio.create_task(fetch_data(session,i)) for i in range(CONCURRENT_REQUESTS)]
        try :
            await asyncio.gather(*tasks)
            log_queue.put(("a", "[green]Tasks completed, processing results...[/green]"))
        finally:
            # ---- CLEANUP ----
            # await asyncio.gather(*tasks, return_exceptions=True)
            # await asyncio.gather(writertask, return_exceptions=True)
            writertask.cancel()
            await sqlite_queue.join()

            manager.client.close()

            if display.is_alive():
                display.terminate()
                display.join()

            print("[red]Shutdown complete[/red]")
                
            


        # .update(content)

if __name__ == '__main__':
    asyncio.run(main())