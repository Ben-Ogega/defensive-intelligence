import requests
from bs4 import BeautifulSoup

url = "https://parts-crossreference.com/search?q=716003"
response = requests.get(url)
print(response.status_code)