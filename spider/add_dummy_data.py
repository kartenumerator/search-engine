import dbm
import datetime
from rich.live import Live
from urllib.parse import urlparse
from rich.console import Console

console = Console()
mng = dbm.dbm("localhost", 27017)
seed_urls = [
    "https://wotaku.wiki/misc"
]


with Live(console=console, screen=False, vertical_overflow="crop") as live:
    
    print(mng.add_urls_to_crawl([{"url": url, "netloc":urlparse(url).netloc ,"upload_time": mng.urls_to_crawl.estimated_document_count()+1, "status":0} for url in seed_urls]))
# print(retrieve_url())
# url = retrieve_url()
# print(url)