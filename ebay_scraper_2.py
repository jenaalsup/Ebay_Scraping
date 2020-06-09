import urllib3 
from bs4 import BeautifulSoup as b

base_url = "https://www.ebay.ca/sch/i.html?_from=R40&_nkw="
request = "xbox"
url_separator = "&_sacat=0&_pgn="
page_num = "1"

url = base_url + request + url_separator + page_num

import urllib.request
html = urllib.request.urlopen(url).read()
soup = b(html, "html.parser")

print("First test")
for post in soup.findAll("li", {"class" : "s-item"}):
  print("Second test")
  print(post)