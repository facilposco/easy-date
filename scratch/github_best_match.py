import urllib.request
import json

try:
    with open("scratch/github_best_match.txt", "w", encoding="utf-8") as f:
        # Default sort (best match)
        req = urllib.request.Request('https://api.github.com/search/repositories?q=reddit', headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req)
        data = json.loads(res.read())
        
        f.write("=== REDDIT REPOS (BEST MATCH) ===\n")
        for r in data['items'][:15]:
            f.write(f"{r['full_name']} | Stars: {r['stargazers_count']} | Updated: {r['updated_at']} | Desc: {r['description']}\n")
            
        # Top stars specifically for reddit scraping
        req2 = urllib.request.Request('https://api.github.com/search/repositories?q=reddit+scrape+OR+reddit+scraper&sort=stars&order=desc', headers={'User-Agent': 'Mozilla/5.0'})
        res2 = urllib.request.urlopen(req2)
        data2 = json.loads(res2.read())
        
        f.write("\n=== REDDIT SCRAPING REPOS (STARS) ===\n")
        for r in data2['items'][:15]:
            f.write(f"{r['full_name']} | Stars: {r['stargazers_count']} | Updated: {r['updated_at']} | Desc: {r['description']}\n")

except Exception as e:
    print(e)
