import urllib.request
import json
import traceback

def fetch_repos(query, sort=None):
    url = f'https://api.github.com/search/repositories?q={query}&per_page=50'
    if sort:
        url += f'&sort={sort}&order=desc'
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    return data['items']

try:
    with open("scratch/github_top_50.txt", "w", encoding="utf-8") as f:
        # Search by Best Match
        f.write("=== TOP 50 REDDIT REPOS (BEST MATCH) ===\n")
        items_best = fetch_repos("reddit")
        for i, r in enumerate(items_best):
            desc = str(r['description']).replace('\n', ' ')
            f.write(f"{i+1}. {r['full_name']} | Stars: {r['stargazers_count']} | {desc}\n")
            
        f.write("\n=== TOP 50 REDDIT REPOS (BY STARS) ===\n")
        items_stars = fetch_repos("reddit", sort="stars")
        for i, r in enumerate(items_stars):
            desc = str(r['description']).replace('\n', ' ')
            f.write(f"{i+1}. {r['full_name']} | Stars: {r['stargazers_count']} | {desc}\n")
            
except Exception as e:
    traceback.print_exc()
