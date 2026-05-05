
import os
import redis 
from dbm import dbm
import gemini

m = dbm()

r = redis.Redis(host="localhost", port=6379, db=0)

# genai.configure(api_key="AIzaSyCMK0WypW8KMrHSecx121omq6VJw4NXREM")
# model = genai.GenerativeModel('gemini-2.0-flash')


# print(summarize_ten_docs("./my_documents"))

query = "what vinland saga about"
filtered_query = query.split(' ')

temp_key = "temp:result"
print(filtered_query)

missing_keys = []
for key in filtered_query :
    if not r.exists(key) :
        missing_keys.append(key)
# existence_results = results[:len(filtered_query)]
# missing_keys = [k for k, exists in zip(filtered_query, existence_results) if not exists]

pipe = r.pipeline()
# for key in filtered_query:
#     pipe.exists(key)
# Combine scores
pipe.zunionstore(temp_key, filtered_query, aggregate="SUM")
# Get top 10 results
pipe.zrevrange(temp_key, 0, 9, withscores=True)
# Cleanup
pipe.delete(temp_key)
results = pipe.execute()

combined_scores = results[1]
urls = []
for url, score in combined_scores:
    print(url.decode(), score)
    urls.append(url.decode())

hits = list(m.db.pages.find({"url":{"$in":urls}}, {"url":1, "title":1, "html":1, "meta_description":1}))
print(gemini.summarize_ten_docs(hits, query))