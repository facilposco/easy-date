import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'
}

proxies = {
    'http': 'http://b1bf7cccb79805e29868:0f98e1edfd0fac2f@gw.dataimpulse.com:823',
    'https': 'http://b1bf7cccb79805e29868:0f98e1edfd0fac2f@gw.dataimpulse.com:823'
}

url = "https://www.reddit.com/r/tinder/top/.rss"
print(f"Probando RSS: {url}")
try:
    r = requests.get(url, headers=headers, proxies=proxies, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print("¡Éxito!")
        print(r.text[:500])
except Exception as e:
    print(f"Error: {e}")
