from dbm import dbm
import json
import pymongo
import requests
import time
import sys

manager = dbm('localhost', 27017)
BATCH_SIZE = 100

start = time.time_ns()
nreq = 0
while True :
    offset = manager.db.global_vars.find_one_and_update({"_id":"mdoffset"},{"$inc":{"status":BATCH_SIZE}},return_document=pymongo.ReturnDocument.BEFORE)
    # offset = 0
    if offset == -1 :
        print("Finished crawling mangas..")
        sys.exit(0)
    url = f"https://api.mangadex.org/manga?limit={BATCH_SIZE-1}&offset={offset['status']}"

    html = ''
    fetchstart = time.time_ns()
    try :
        response = requests.get(url, headers={'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"})
        # print(response.status_code)
        if response.status_code == 429:
            print(f"Rate limited when fetching URL: {url}. Status Code: {response.status_code}. Retrying after delay.")
            time.sleep(5*60)  # Wait before retrying
            continue
        if response.status_code != 200:
            print(f"Error fetching URL: {url}, Status Code: {response.status_code}")
            continue
        html = response.text
    except Exception as e:
        print(f"Error fetching URL: {url}, Exception: {e}")
        continue
    
    print(f'fetched page in {(time.time_ns() - fetchstart)/1000000000} s')
    nreq += 1
    data = json.loads(html)
    if data["total"] <= offset['status']+BATCH_SIZE :
        manager.db.global_vars.update_one({"_id":"mdoffset"},{"$set":{"status":-1}})
    
    ops = []
    for mn in data["data"] :
        manga = mn['attributes']
        title = ''
        tags = ''
        descr = ''
        for tag in manga['tags']:
            for name in tag['attributes']['name'].items():
                if name[0] == 'en' or name[0] == 'ja-ro':
                    tags += name[1]+" | "
        if "ja-ro" in manga['title'].keys() or "en" in manga['title'].keys() :
            title += list(manga['title'].items())[0][1]
        for titles in manga['altTitles']:
            if list(titles.items())[0][0].lower() == 'ja-ro' or list(titles.items())[0][0].lower() == 'en' :
                title += f' | {list(titles.items())[0][1]}'
        for desc in manga['description'] :
            if desc == 'en' or desc == 'ja-ro' :
                descr += manga['description'][desc]
        
        tags += 'Read Manga Online'
        url = f'https://mangadex.org/title/{mn["id"]}'
        # print(f'title : {title}\ntags:{tags}\ndescription : {descr}\nurl:{url}\n\n')

        print(f'Adding url : {url}')
        ops.append(pymongo.InsertOne({"url":url,"html":descr,"meta_description":tags,"status":0,"title":title}))

    print(f'Processed page at {(time.time_ns() - fetchstart)/1000000000} s')
    manager.db.pages.bulk_write(ops)

    print(f'Added page at {(time.time_ns() - fetchstart)/1000000000} s')
    
    if nreq >= 5 and time.time_ns()-start < 1000000000 :
        print("too many requests, waiting...")
        time.sleep(1 - (time.time_ns()+start)/1000000000)
        start = time.time_ns()
        nreq = 0
    # break
    


