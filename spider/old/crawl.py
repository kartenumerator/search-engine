import aiohttp
import asyncio
import bs4
from urllib.parse import urljoin,urlparse
import sqlite3
import datetime
from rich.live import Live
from rich.console import Console
from database_manager import is_url_crawled, add_crawled_url, retrieve_urls_to_crawl, add_urls_to_crawl

console = Console()
content = ""

#TODO : add REDIS

CONCURRENT_REQUESTS = 50

crawled_urls = 0
limit = 1000

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

# page = requests.get("https://www.ndtv.com/world", headers=headers).text
# print(page)

# urls = [
#     "https://en.wikipedia.org/wiki/Gintama",
#     # "https://iol.co.za/technology/2007-09-28-nintendo-wii-launches-in-south-africa/",
#     # "https://en.wikipedia.org/wiki/File:Gee!!_I_wish_I_were_a_man,_I'd_join_the_Navy_Be_a_man_and_do_it_-_United_States_Navy_recruiting_station_-_-_Howard_Chandler_Christy_1917._LCCN2002712088.jpg"
# ]

urls = retrieve_urls_to_crawl(limit=50)
# completed_urls = []
semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

async def get_robots(session, url):
    global robots, headers
    parsedjoinedurl = urlparse(url)
    print(f"Retrieving robots file for {parsedjoinedurl.scheme}://{parsedjoinedurl.netloc}/robots.txt")
    # await (get_robots(session, url))
    try :
        async with session.get(f"{parsedjoinedurl.scheme}://{parsedjoinedurl.netloc}/robots.txt", headers=headers) as robots_response:
            print(robots_response.status)
            if robots_response.status == 200:
                robots[parsedjoinedurl.netloc] = []
                myturn = False
                for line in (await robots_response.text()).splitlines():
                    if line.startswith("User-agent:"):
                        myturn = (line.split("User-agent:")[1].strip() == "*")
                    if myturn and line.startswith("Disallow:"):
                        # print(line.split("Disallow:")[1].strip())
                        robots[parsedjoinedurl.netloc].append(line.split("Disallow:")[1].strip())
            else:
                # print("No robots file")
                robots[parsedjoinedurl.netloc] = []
    except Exception as e:
        print(f"Error fetching robots.txt for {url}: {e}.")
        robots[parsedjoinedurl.netloc] = []

async def fetch_data(session,url,live):

    global headers,urls,limit,robots,semaphore,crawled_urls,conn,cursor
    print(f"Starting task: {url}")
    data = ""
    async with semaphore:
        try:
            # await asyncio.sleep(0.5)
            async with session.get(url, headers=headers) as response:
                data = await response.text()

                if response.status == 200:
                    limit -= 1
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
                        if parsedjoinedurl.scheme not in ("http","https"):
                            continue
                        else :
                            # print(newurl)joined_url
                            newurl = f"{parsedjoinedurl.scheme}://{parsedjoinedurl.netloc}{parsedjoinedurl.path}"
                            if not is_url_crawled(parsedjoinedurl.netloc, parsedjoinedurl.path) and newurl not in urls:
                                if parsedjoinedurl.netloc not in robots:
                                    # print(f"Retrieving robots file for {parsedjoinedurl.scheme}://{parsedjoinedurl.netloc}/robots.txt") 
                                    extracted_links.append(newurl)
                                    if parsedjoinedurl.netloc not in retrieving_robots:
                                        robot_tasks.append(get_robots(session, newurl))

                                    retrieving_robots.append(parsedjoinedurl.netloc)

                                elif (parsedjoinedurl.path not in robots[parsedjoinedurl.netloc]):
                                    if(len(urls)>=limit):
                                        break
                                    urls.append(newurl)
                                    
                    if len(robot_tasks) > 0:
                        await asyncio.gather(*robot_tasks)
                        for link in extracted_links:
                            if(len(urls)>=limit):
                                break
                            parsedjoinedurl = urlparse(link)
                            if link not in urls and (parsedjoinedurl.path not in robots[parsedjoinedurl.netloc]):
                                urls.append(link)
                else:
                    print(f"Couldnt retrieve {url} | status {response.status}")
                    # headers["User-Agent"] = useragents[0 if headers["User-Agent"] == useragents[1] else 1]
        except Exception as e:
            print(f"Error fetching {url}: {e}.")
    
    print(f"Completed task: {url}")
    urls.remove(url)
    # completed_urls.append(url)
    currenturl = urlparse(url)
    add_crawled_url(currenturl.netloc, currenturl.path)
    return data

def update_content(live):
    global content,crawled_urls,urls,limit
    content = f"Crawled URLs: [bold green]{crawled_urls}[/bold green] | Pending URLs: [bold yellow]{len(urls)}[/bold yellow] | Remaining limit: [bold red]{limit}[/bold red]"
    live.update(content)

async def main():
    global urls,limit,content
    # tasks = [fetch_data(url) for url in urls]
    # print("Tasks created, starting to gather results...")
    # results = await asyncio.gather(*tasks)

    with Live(console=console, screen=False, vertical_overflow="crop") as live:
        async with aiohttp.ClientSession() as session:
            while len(urls) > 0:
                # start_time = time.time()
                tasks = [fetch_data(session, url,live) for url in urls]
                await asyncio.gather(*tasks)
                
                print("Tasks completed, processing results...")

                add_urls_to_crawl([{"url": url, "upload_time": datetime.datetime.now()} for url in urls])
                urls.clear()
                urls = retrieve_urls_to_crawl(limit=min(100,limit))
                live.update(content)

if __name__ == '__main__':
    asyncio.run(main())