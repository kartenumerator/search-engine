from dbm import dbm

manager = dbm('localhost', 27017)
with open("approvedlist.txt", "r") as f:
    line = f.readline()
    approvedlist = line.split(",")
    approvedlist = [url.strip() for url in approvedlist]
    fixingurl = []
    for url in approvedlist:
        doc = manager.db.pages.find_one({"url": url})
        if doc is None :
            fixingurl.append(url)
    print(fixingurl)
    manager.db.urls_to_crawl.update_many({'url':{'$in':fixingurl}}, {'$set':{'status':0}})