import sqlite3
import bs4


conn = sqlite3.connect('db/crawled_pages.db')
cursor = conn.cursor()
# query = "SELECT * FROM pages ORDER BY id DESC LIMIT 1"
query = "SELECT html FROM pages WHERE url = 'https://www.freecodecamp.org/learn'"
cursor.execute(query)
last_row = cursor.fetchone() # Fetch the single resulting row
# print(last_row[0])  # Print the HTML content

soup = bs4.BeautifulSoup(last_row[0], "lxml")
for tag in soup.find_all(["script","style","nav","header","footer"]):
    tag.decompose()
# text = soup.getText(" ",strip=True)
print(soup.prettify())
conn.close()
