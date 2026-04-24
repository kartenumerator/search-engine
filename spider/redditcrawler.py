import re
import time
import requests
from urllib.parse import urlparse
from selectolax.parser import HTMLParser
import json
from dbm import dbm

manager = dbm("localhost", 27017)

while True:
    origurl, status = manager.retrieve_reddit_url()
    if origurl is None:
        print("No URLs to crawl. Waiting...")
        time.sleep(5)
        continue
    url = origurl
    # url = "https://www.reddit.com/search.json?q=anime&limit=100&sort=relevance"
    # url = "https://www.reddit.com/r/StremioAddons/comments/1rr0fve/guide_fastest_stremio_setup_aiostreams/"
    parsedurl = urlparse(url)

    print(url)
    # if parsedurl.netloc == "www.reddit.com" :
    if url[-1] == '/':
        url = url[:-1]+'.json'
    else :
        url = url+'.json'

    # print(parsedurl.path)
    html = ''
    fetchstart = time.time_ns()
    try :
        response = requests.get(url, headers={'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"})
        # print(response.status_code)
        if response.status_code == 429:
            print(f"Rate limited when fetching URL: {url}. Status Code: {response.status_code}. Retrying after delay.")

            if status == -1 :
                manager.add_crawled_url(origurl)
            else :
                manager.remove_reddit_crawled_url(origurl)

            time.sleep(5*60)  # Wait before retrying
            continue
        if response.status_code != 200:
            print(f"Error fetching URL: {url}, Status Code: {response.status_code}, {status}")
            if status == -1 :
                manager.add_crawled_url(origurl)
            else :
                manager.remove_reddit_crawled_url(origurl)
            continue
        html = response.text
    except Exception as e:
        print(f"Error fetching URL: {url}, Exception: {e}")
        if status == -1 :
            manager.add_crawled_url(origurl)
        else :
            manager.remove_reddit_crawled_url(origurl)
        continue
    # print(html['data'])
    # print()
    print(f"Fetched URL: {url} in {(time.time_ns() - fetchstart) / 1e9:.2f} seconds")
    processingstart = time.time_ns()
    def is_listing(data):
        return (
            isinstance(data, dict) and
            data.get("kind") == "Listing" and
            "children" in data.get("data", {})
        )

    def extract_post_urls(listing_json):
        urls = []

        if not is_listing(listing_json):
            raise ValueError("Not a listing")

        children = listing_json["data"]["children"]

        for child in children:
            if child.get("kind") != "t3":
                continue

            post = child["data"]

            # Full Reddit post URL
            permalink = post.get("permalink")
            if permalink:
                full_url = "https://www.reddit.com" + permalink
                urls.append(full_url)

        return urls
    try :
        json_data = json.loads(html)
    except Exception as e:
        print(f"Error parsing JSON from URL: {url}, Exception: {e}")
        if status == -1 :
            manager.add_crawled_url(origurl)
        else :
            manager.remove_reddit_crawled_url(origurl)
        continue
    
    if is_listing(json_data):
        # print("This is a listing")
        urls = extract_post_urls(json_data)
        manager.add_urls_to_crawl(urls)
        # print(len(urls))
        # print(*urls, sep='\n')
    elif isinstance(json_data, dict) and json_data.get("kind") == 'wikipage':
        # print("This is a wiki page")
        title = json_data["data"].get("title", "")
        content = json_data["data"].get("content_md", "")
        buffer = [{"url":origurl, "html":title+"\n"+content, "status":0, "title":title, "meta_description":content}]
        def extract_links(text):
            if not text:
                return []
            return re.findall(r'https?://\S+', text)

        links = []

        # Extract from post
        # post = json_data[0]["data"]["children"][0]["data"]
        links += extract_links(content)
        manager.add_pages(buffer)
        manager.add_urls_to_crawl(links)
    else :

        def extract_comments(comments, result):
            for child in comments.get("children", []):
                data = child.get("data", {})
                
                # Extract author and body
                author = data.get("author")
                body = data.get("body")
                
                if author and body:
                    result.append((author, body))
                
                # Recursively process replies
                replies = data.get("replies")
                if isinstance(replies, dict):
                    extract_comments(replies.get("data", {}), result)

        try :
            post = json_data[0]["data"]["children"][0]["data"]

            title = post.get("title")
            author = post.get("author")
            body = post.get("selftext","")
            # print(body)

            # print(f"Title: {title}\nAuthor: {author}\n")

            # The comments are in the second listing
            comments_data = json_data[1]["data"]

            # Extract
            results = []
            extract_comments(comments_data, results)

            # Print results
            data = title+"\n"+body+"\n"
            for user, text in results:
                data += (f"{user} {text}\n")
            
            buffer = [{"url":origurl, "html":data, "status":0, "title":title, "meta_description":body}]
            manager.add_pages(buffer)
            # print(tree.text(separator='\n', strip=True))
        except Exception as e:
            print(f"Error: {e}")


        def extract_links(text):
            if not text:
                return []
            return re.findall(r'https?://\S+', text)

        links = []

        # Extract from post
        # post = json_data[0]["data"]["children"][0]["data"]
        links += extract_links(body)

        # Extract from comments
        def recurse(node):
            for child in node.get("children", []):
                data = child.get("data", {})
                
                links.extend(extract_links(data.get("body", "")))
                
                replies = data.get("replies")
                if isinstance(replies, dict):
                    recurse(replies.get("data", {}))

        recurse(json_data[1]["data"])

        # Filter only Reddit links
        reddit_links = [l for l in links if "reddit.com" in l or "redd.it" in l]

        # print("All links:", links)
        # print("Reddit links:", reddit_links)
        manager.add_urls_to_crawl(links)
        print(f"Processed URL: {url} in {(time.time_ns() - processingstart) / 1e9:.2f} seconds")