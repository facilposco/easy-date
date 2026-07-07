import json
import traceback
from curl_cffi import requests

try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    res = requests.get('https://www.reddit.com/r/Tinder/top.json?limit=100&t=all', headers=headers, impersonate='chrome110')
    if res.status_code == 200:
        data = res.json()
        galleries = [c for c in data['data']['children'] if 'gallery_data' in c['data']]
        print(f"Found {len(galleries)} gallery posts.")
        for g in galleries[:3]:
            print(f"- {g['data']['title']} (Images: {len(g['data']['gallery_data']['items'])})")
    else:
        print(f"Failed with status code: {res.status_code}")
except Exception as e:
    traceback.print_exc()
