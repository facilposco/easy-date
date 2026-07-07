import requests
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

proxies = {
    'http': 'http://b1bf7cccb79805e29868:0f98e1edfd0fac2f@gw.dataimpulse.com:823',
    'https': 'http://b1bf7cccb79805e29868:0f98e1edfd0fac2f@gw.dataimpulse.com:823'
}

urls = [
    "https://old.reddit.com/r/tinder/top/.json?t=all&limit=5",
    "https://www.reddit.com/r/tinder/top/.json?t=all&limit=5",
    "https://oauth.reddit.com/r/tinder/top/.json?t=all&limit=5"
]

for url in urls:
    print(f"Probando: {url}")
    try:
        r = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print("¡Éxito!")
            print(r.json().get('data', {}).get('children', [])[0].get('data', {}).get('title'))
            break
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(2)
