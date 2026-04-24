import dbm
import datetime
from rich.live import Live
from urllib.parse import urlparse
from rich.console import Console

console = Console()
mng = dbm.dbm("localhost", 27017)

seed_urls = [
    # Major databases
    "https://myanimelist.net",
    "https://anilist.co",
    "https://kitsu.io",
    "https://www.animenewsnetwork.com",
    "https://anidb.net",
    "https://www.livechart.me",
    "https://www.crunchyroll.com",
    "https://www.funimation.com",
    "https://www.netflix.com/browse/genre/7424",
    "https://www.hidive.com",
    
    # News & blogs
    "https://www.animenewsnetwork.com",
    "https://otakumode.com",
    "https://www.crunchyroll.com/news",
    "https://comicbook.com/anime",
    "https://www.cbr.com/category/anime",
    "https://www.ign.com/anime",
    "https://screenrant.com/tag/anime",
    "https://gamerant.com/tag/anime",
    "https://www.animenation.net/blog",
    "https://honeysanime.com",
    
    # Forums & communities
    "https://www.reddit.com/r/anime",
    "https://myanimelist.net/forum",
    "https://anilist.co/forum",
    "https://anime.stackexchange.com",
    "https://boards.4channel.org/a",
    "https://discord.com/invite/anime",
    "https://otakuusamagazine.com",
    "https://www.fandom.com/topics/anime",
    "https://www.resetera.com/forums/anime-and-manga.8",
    "https://www.crunchyroll.com/forum",
    
    # Streaming / watch sites (legal)
    "https://www.crunchyroll.com/videos/anime",
    "https://www.netflix.com/in/browse/genre/7424",
    "https://www.amazon.com/anime",
    "https://www.hulu.com/hub/anime",
    "https://www.hidive.com/stream",
    "https://www.youtube.com/c/CrunchyrollCollection",
    "https://www.youtube.com/c/MuseAsia",
    "https://www.youtube.com/c/AniOneAsia",
    "https://www.youtube.com/c/NetflixAnime",
    "https://www.youtube.com/c/AnimeLog",
    
    # Wiki / info
    "https://en.wikipedia.org/wiki/Anime",
    "https://en.wikipedia.org/wiki/List_of_anime_series",
    "https://naruto.fandom.com",
    "https://onepiece.fandom.com",
    "https://bleach.fandom.com",
    "https://attackontitan.fandom.com",
    "https://dragonball.fandom.com",
    "https://pokemon.fandom.com",
    "https://jujutsukaisen.fandom.com",
    "https://demonslayer.fandom.com",
    
    # Studio / official
    "https://www.toei-animation.com",
    "https://www.ghibli.jp",
    "https://www.madhouse.co.jp",
    "https://www.ufotable.com",
    "https://www.bones.co.jp",
    "https://www.witstudio.co.jp",
    "https://www.production-ig.co.jp",
    "https://www.sunrise-inc.co.jp",
    "https://www.aniplex.co.jp",
    "https://www.tv-tokyo.co.jp/anime"
]
searchterms = [
    "naruto",
    "one piece",
    "attack on titan",
    "death note",
    "demon slayer",
    "jujutsu kaisen",
    "dragon ball",
    "bleach",
    "tokyo ghoul",
    "chainsaw man",
    "fullmetal alchemist",
    "my hero academia",
    "spy x family",
    "hunter x hunter",
    "vinland saga",
    "black clover",
    "code geass",
    "steins gate",
    "re zero",
    "your name"
]
reddit_urls = [
    'https://www.reddit.com/search.json?q=isekai&limit=100&sort=relevance'
]
# for term in searchterms:
#     reddit_urls.append(f'https://www.reddit.com/search.json?q={"+".join(term.split(" "))}&limit=100&sort=relevance')
# tst = mng.db.urls_to_crawl.find({'status':0}).sort("upload_time", -1).limit(1)
# print(list(tst))
# with Live(console=console, screen=False, vertical_overflow="crop") as live:
mng.add_urls_to_crawl(reddit_urls)  
# print(mng.add_urls_to_crawl(seed_urls)) #[{"url": url, "netloc":urlparse(url).netloc ,"upload_time": mng.urls_to_crawl.estimated_document_count()+1, "status":0} for url in seed_urls]))
# print(retrieve_url())
# url = retrieve_url()
# print(url)