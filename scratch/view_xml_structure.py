import requests
import xml.etree.ElementTree as ET

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'
}

proxies = {
    'http': 'http://b1bf7cccb79805e29868:0f98e1edfd0fac2f@gw.dataimpulse.com:823',
    'https': 'http://b1bf7cccb79805e29868:0f98e1edfd0fac2f@gw.dataimpulse.com:823'
}

url = "https://www.reddit.com/r/tinder/search.rss?q=smooth+OR+success+OR+number&restrict_sr=on&sort=top&t=all"
r = requests.get(url, headers=headers, proxies=proxies)
if r.status_code == 200:
    root = ET.fromstring(r.content)
    namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
    entry = root.find('atom:entry', namespaces)
    if entry is not None:
        title = entry.find('atom:title', namespaces).text
        content = entry.find('atom:content', namespaces).text
        print(f"Title: {title}")
        print("Content:")
        print(content[:2000])
