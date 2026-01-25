import dbm
import datetime
from rich.live import Live
from rich.console import Console

console = Console()
mng = dbm.dbm("localhost", 27017)

with Live(console=console, screen=False, vertical_overflow="crop") as live:
    mng.add_url_to_crawl("https://en.wikipedia.org/wiki/Gintama", datetime.datetime.now(), live)
    print(mng.add_urls_to_crawl([{"url": "https://en.wikipedia.org/wiki/Gintama", "upload_time": datetime.datetime.now()},
                       {"url": "https://en.wikipedia.org/wiki/Death_Note", "upload_time": datetime.datetime.now()}], live))
# print(retrieve_url())
# url = retrieve_url()
# print(url)