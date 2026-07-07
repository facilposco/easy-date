import os
import xml.etree.ElementTree as ET
import traceback
from curl_cffi import requests
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("PROXY_HOST")
port = os.getenv("PROXY_PORT")
user = os.getenv("PROXY_USERNAME")
password = os.getenv("PROXY_PASSWORD")

proxy_url = f"http://{user}:{password}@{host}:{port}"
proxies = {"http": proxy_url, "https": proxy_url}

try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    # Test RSS endpoint instead of JSON
    res = requests.get('https://www.reddit.com/r/Tinder/top.rss?t=all', headers=headers, impersonate='chrome120', proxies=proxies, timeout=20)
    
    if res.status_code == 200:
        print("RSS feed fetched successfully!")
        print(f"Content length: {len(res.content)}")
    else:
        print(f"Failed with status code: {res.status_code}")
except Exception as e:
    traceback.print_exc()
