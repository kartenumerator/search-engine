import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
# import bs4
from dbm import dbm
import string
import time
from collections import Counter
import re
import time

from urllib.parse import urlparse
import sys
import os 

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add it to the list of places Python looks for modules
sys.path.append(parent_dir)

# Now you can import your file by its name (without .py)
import helper
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from nltk import pos_tag
from multiprocessing import Process, Queue

from functools import lru_cache

@lru_cache(maxsize=100000)
@lru_cache(maxsize=100000)
def lemmatize_cached(word, tag):
    return lemmatizer.lemmatize(word, pos=tag)


def get_wordnet_pos(tag):
    if tag.startswith('J'):
        return wordnet.ADJ # 'a'
    elif tag.startswith('V'):
        return wordnet.VERB # 'v'
    elif tag.startswith('N'):
        return wordnet.NOUN # 'n'
    elif tag.startswith('R'):
        return wordnet.ADV # 'r'
    else:
        return wordnet.NOUN # Default to Noun
data_manager = dbm()

resources = {'corpora/stopwords' : 'stopwords','tokenizers/punkt':'punkt','tokenizers/punkt_tab':'punkt_tab', 'wordnet':'wordnet'}

for resource_name in resources :
    try:
        nltk.data.find(resource_name)
        print(f"'{resource_name}' is installed.")
    except LookupError as e:
        # print(e)
        print(f"'{resource_name}' not found. You can download it using nltk.download('{resource_name}')")
        nltk.download(resources[resource_name])

# Get English stopwords and tokenize
stop_words = set(stopwords.words('english'))
# print(stop_words)
punctuation_remover_regex = re.compile(r"[^\w\s]")
# punctuation_remover = str.maketrans('','',string.punctuation)
lemmatizer = WordNetLemmatizer()

db_actions_queue = Queue()

def db_worker(db_actions_queue:Queue, pagequeue:Queue):
    data_manager = dbm()
    try :
        while True:
            try :
                action, params = db_actions_queue.get_nowait()
                if action == "add_words":
                    words, word_counts, url, total_words = params
                    data_manager.add_words(words, word_counts, url, total_words)
                elif action == "stop":
                    break
            except Exception as e :
                print("no tasks")
            
            if pagequeue.qsize() < 50 :
                print("fetching pages..")
                docs = list(data_manager.db.pages.find({"status":0}, {"html":1,"url":1,"meta_description":1,"title":1}).limit(50))
                urls = []
                for doc in docs :
                    pagequeue.put(doc)
                    urls.append(doc['url'])
                data_manager.db.pages.update_many({"url":{"$in":urls}}, {"$set":{"status":1}})
                print("fetched pages...")
                if len(docs) < 50 :
                    print("No more pages to index..")
                    if data_manager.get_flag_to_crawl() == 0 :
                        # print("Updating idf since crawler has paused.")
                        # data_manager.update_idf()
                        data_manager.set_flag_to_crawl(1)
            time.sleep(0.5)

    except KeyboardInterrupt as e:
        print(f"DB worker encountered an error: {e}, adding remaining tasks back to main queue.")
        while db_actions_queue.empty() is False:
            action, params = db_actions_queue.get()
            if action == "add_words":
                words, word_counts, url, total_words = params
                data_manager.add_words(words, word_counts, url, total_words)

pagequeue = Queue()

db_process = Process(target=db_worker, args=(db_actions_queue,pagequeue,))
db_process.start()

def process_url(url):
    parsed = urlparse(url)
    host_tokens = re.split(r'[\-_.]+', parsed.hostname)
    tokens = re.split(r'[/\-_.]+', parsed.path)
    return (host_tokens , tokens[1:])

def process_text(html):
    text = re.sub(punctuation_remover_regex, '', html)
    words = word_tokenize(text)
    
    # filtered_text = [word.lower() for word in words if word.lower() not in stop_words]
    filtered_text = []
    
    tagged_tokens = pos_tag(words)

    for word, tag in tagged_tokens:
        if word.lower() in stop_words or len(word) <= 1 or not helper.check_only_english_alphanum_symbols(word.lower()) :
            continue
        wn_tag = get_wordnet_pos(tag)
        if len(word) > 1 and not tag.startswith('N'):
            filtered_text.append(word.lower())
        lemma = lemmatize_cached(word.lower(), wn_tag)
        if len(lemma) > 1 :
            filtered_text.append(lemma)

    # for word in words :
    #     w = word.lower()
    #     if w not in stop_words and len(w) > 1:
    #         filtered_text.append(lemmatize_cached(w))

    # filtered = list(filtered_text)
    c = Counter(filtered_text)

    return c, len(filtered_text)

while(True):
    start_time = time.time_ns()
    # retrieved = data_manager.retrieve_page_to_index()
    retrieved = pagequeue.get()
    if retrieved is None:
        if data_manager.get_flag_to_crawl() == 0 :
            # print("Updating idf since crawler has paused.")
            # data_manager.update_idf()
            data_manager.set_flag_to_crawl(1)
        # time.sleep(10)
        continue
    
    retrieval_time = (time.time_ns()-start_time)/1000000000
    html = retrieved["html"]
    title = retrieved["title"]
    meta_description = retrieved["meta_description"]
    # soup = bs4.BeautifulSoup(html, "lxml")

    # for tag in soup.find_all(["script","style","nav","header","footer"]):
    #     tag.decompose()
    
    # text = soup.getText(" ",strip=True)
    host_tokens, url_tokens = process_url(retrieved['url'])
    c, filtered_text = process_text(html)
    title,numtitle=  process_text(title)
    meta_description, nummeta = process_text(meta_description)

    # finaldict = {}
    for word in host_tokens :
        c[word] = c.get(word,0) + 70

    for word in url_tokens :
        c[word] = c.get(word,0) + 50
    
    for word in title :
        c[word] = c.get(word,0) + title[word]*50
    
    for word in meta_description :
        c[word] = c.get(word,0) + meta_description[word]*25 
    # for word in filtered_text :
    #     hash[unique_list.index(word)] += 1

    complete_processing_time = (((time.time_ns() - start_time)/1000000000) - retrieval_time)
    if len(c.keys()) == 0 :
        data_manager.db.pages.delete_one({"_id": retrieved["_id"]})
        continue

    db_actions_queue.put( ("add_words", (list(c.keys()), c, retrieved['url'],filtered_text+numtitle+nummeta)) )
    # data_manager.add_words(list(c.keys()), c, retrieved['url'],filtered_text+numtitle+nummeta)

    print(retrieved['url'])
    print(f'Indexed | retrieval : {retrieval_time}s | processing : {complete_processing_time}s | adding_operations : {((time.time_ns()-start_time)/1000000000 - retrieval_time - complete_processing_time)}')
