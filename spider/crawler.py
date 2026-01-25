import aiohttp
import asyncio
import bs4
from urllib.parse import urljoin,urlparse
from urllib.robotparser import RobotFileParser
import sqlite3
import datetime
from rich.live import Live
from rich.console import Console
from dbm import dbm
import multiprocessing
import time
import traceback

console = Console()
content = ""

manager = dbm("localhost",27017)

#TODO : add REDIS

CONCURRENT_REQUESTS = 50

crawled_urls = 0
limit = 1000

crawled_list = []

robots = {}

conn = sqlite3.connect('./db/crawledpages.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY,
        url TEXT NOT NULL,
        html TEXT NOT NULL
    )
''')
headers = {
    "User-Agent": "MyBot/1.0 (contact: tpg4m3risb3st@gmail.com)"
}

useragents =[
    "MyBot/1.0 (contact: tpg4m3risb3st@gmail.com)",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
]

# urls = [
#     "https://en.wikipedia.org/wiki/Gintama",
#     # "https://iol.co.za/technology/2007-09-28-nintendo-wii-launches-in-south-africa/",
#     # "https://en.wikipedia.org/wiki/File:Gee!!_I_wish_I_were_a_man,_I'd_join_the_Navy_Be_a_man_and_do_it_-_United_States_Navy_recruiting_station_-_-_Howard_Chandler_Christy_1917._LCCN2002712088.jpg"
# ]

# urls = retrieve_urls_to_crawl(limit=50)
semaphore = asyncio.Semaphore(200)

async def get_robots(session, url,live):
    global robots, headers
    parsedjoinedurl = urlparse(url)
    
    def add_robot_to_db(netloc, file_content,live):
        tmpmng = dbm("localhost",27017)
        tmpmng.add_robot_file(netloc, file_content,live=live)

    try :
        robots_response_text = manager.get_robot_file(parsedjoinedurl.netloc,live)
        if robots_response_text is None:
            # print("Not in db")
            async with session.get(f"{parsedjoinedurl.scheme}://{parsedjoinedurl.netloc}/robots.txt", headers=headers) as robots_response:
                # print(robots_response.status)
                if robots_response.status == 200:
                    robots_response_text = await robots_response.text()
                    
                    if parsedjoinedurl.netloc in robots:
                        return
                    p = multiprocessing.Process(target=add_robot_to_db, args=(parsedjoinedurl.netloc, robots_response_text,live))
                    p.start()
                    # rp = RobotFileParser()
                    # rp.parse(robots_response_text.splitlines())
                    # robots[parsedjoinedurl.netloc] = rp
                    
                else:

                    if parsedjoinedurl.netloc in robots:
                        return
                    p = multiprocessing.Process(target=add_robot_to_db, args=(parsedjoinedurl.netloc, ""))
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

async def fetch_data(session,live):

    global headers,limit,robots,semaphore,crawled_urls,conn,cursor,manager,crawled_list

    while(crawled_urls) < limit:
        urls = []

        url = manager.retrieve_url(live)
        # print(url)
        if url is None:
            print("No URL to crawl, exiting")
            return 
        print(f"Starting task: {url}")
        data = ""
        async with semaphore:
            try:
                # await asyncio.sleep(0.5)
                async with session.get(url, headers=headers) as response:
                    data = await response.text()

                    if response.status == 200:
                        # limit -= 1
                        crawled_urls += 1
                        update_content(live)

                        cursor.execute("INSERT INTO pages (url, html) VALUES (?, ?)", (url, data))
                        conn.commit()

                        soup = bs4.BeautifulSoup(data, 'html.parser')

                        robot_tasks = []
                        retrieving_robots = []
                        extracted_links = []

                        for link in soup.find_all('a'):
                            parsedjoinedurl = urlparse(urljoin(url, link.get('href')))
                            if parsedjoinedurl.scheme not in ("http","https") or "wikipedia" not in parsedjoinedurl.netloc:
                                continue
                            else :
                                # print(newurl)joined_url
                                newurl = f"{parsedjoinedurl.scheme}://{parsedjoinedurl.netloc}{parsedjoinedurl.path}"
                                if not manager.is_url_crawled(parsedjoinedurl.netloc, parsedjoinedurl.path,live) and newurl not in urls and newurl not in crawled_list:
                                    # print(robots)
                                    if parsedjoinedurl.netloc not in robots:
                                        # print(f"Retrieving robots file for {parsedjoinedurl.scheme}://{parsedjoinedurl.netloc}/robots.txt") 
                                        extracted_links.append(newurl)
                                        if parsedjoinedurl.netloc not in retrieving_robots:
                                            robot_tasks.append(get_robots(session, newurl,live))

                                        retrieving_robots.append(parsedjoinedurl.netloc)

                                    elif robots[parsedjoinedurl.netloc] is None or robots[parsedjoinedurl.netloc].can_fetch('*', parsedjoinedurl.path):
                                        if(len(urls)+crawled_urls>=limit):
                                            break
                                        crawled_list.append(newurl)
                                        urls.append(newurl)
                                        
                        if len(robot_tasks) > 0:
                            await asyncio.gather(*robot_tasks)
                            for link in extracted_links:
                                if(len(urls)+crawled_urls>=limit):
                                    break
                                parsedjoinedurl = urlparse(link)
                                
                                if link not in crawled_list and link not in urls and (robots[parsedjoinedurl.netloc] is None or robots[parsedjoinedurl.netloc].can_fetch('*', parsedjoinedurl.path)):
                                    urls.append(link)
                                    crawled_list.append(link)
                    else:
                        print(f"Couldnt retrieve {url} | status {response.status}")
                        # headers["User-Agent"] = useragents[0 if headers["User-Agent"] == useragents[1] else 1]
            except Exception as e:
                print(f"Error fetching {url}: {e}.")
                traceback.print_exc()
        

        print(f"Completed task: {url}")
        # urls.remove(url)
        # completed_urls.append(url)
        currenturl = urlparse(url)

        # t = time.time_ns()
        # tmpmng = dbm("localhost",27017)
        ret = manager.add_urls_to_crawl(urls=[{'url': u, 'upload_time': datetime.datetime.now()} for u in urls],live=live)
        if ret is not None :
            crawled_list.extend(ret)
        manager.add_crawled_url(currenturl.netloc, currenturl.path,live)
        
        # print(f"DB updated in {time.time_ns()-t} ns")
        
        # manager.add_urls_to_crawl(urls=[{'url': u, 'upload_time': datetime.datetime.now()} for u in urls])
        # manager.add_crawled_url(currenturl.netloc, currenturl.path)
        # return data

def update_content(live):
    global content,crawled_urls,limit
    content = f"Crawled URLs: [bold green]{crawled_urls}[/bold green] | Remaining limit: [bold red]{limit}[/bold red]"
    live.update(content)

async def main():
    global limit,content
    # tasks = [fetch_data(url) for url in urls]
    # print("Tasks created, starting to gather results...")
    # results = await asyncio.gather(*tasks)
    # print(f'at the start {retrieve_url()}')
    with Live(console=console, screen=False, vertical_overflow="crop") as live:
        async with aiohttp.ClientSession() as session:
            # start_time = time.time()
            tasks = [fetch_data(session,live) for i in range(CONCURRENT_REQUESTS)]
            await asyncio.gather(*tasks)
            
            print("Tasks completed, processing results...")
            live.update(content)

if __name__ == '__main__':
    asyncio.run(main())