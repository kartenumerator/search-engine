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

from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet

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

def process_text(html):
    text = re.sub(punctuation_remover_regex, '', html)
    words = word_tokenize(text)
    
    # filtered_text = [word.lower() for word in words if word.lower() not in stop_words]
    filtered_text = []
    for word in words :
        w = word.lower()
        if w not in stop_words :
            filtered_text.append(lemmatizer.lemmatize(w))

    # filtered = list(filtered_text)
    c = Counter(filtered_text)

    return c, len(filtered_text)

while(True):
    start_time = time.time_ns()
    retrieved = data_manager.retrieve_page_to_index()
    if retrieved is None:
        print("Empty queue, sleeping for 10 seconds")
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
    c, filtered_text = process_text(html)
    title,numtitle=  process_text(title)
    meta_description, nummeta = process_text(meta_description)

    # finaldict = {}
    for word in title :
        c[word] = c.get(word,0) + title[word]*5
    
    for word in meta_description :
        c[word] = c.get(word,0) + meta_description[word]*3
    # for word in filtered_text :
    #     hash[unique_list.index(word)] += 1

    complete_processing_time = (((time.time_ns() - start_time)/1000000000) - retrieval_time)
    if len(c.keys()) == 0 :
        data_manager.completed_page(retrieved['url'])
        continue
    data_manager.add_words(list(c.keys()), c, retrieved['url'],filtered_text+numtitle+nummeta)

    print(retrieved['url'])
    print(f'Indexed | retrieval : {retrieval_time}s | processing : {complete_processing_time}s | adding_operations : {((time.time_ns()-start_time)/1000000000 - retrieval_time - complete_processing_time)}')
