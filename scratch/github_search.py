import urllib.request
import json
import traceback

try:
    with open("scratch/github_results.txt", "w", encoding="utf-8") as f:
        req1 = urllib.request.Request('https://api.github.com/search/repositories?q=reddit+scraper&sort=stars&order=desc', headers={'User-Agent': 'Mozilla/5.0'})
        res1 = urllib.request.urlopen(req1)
        data1 = json.loads(res1.read())
        
        f.write("=== TOP REDDIT SCRAPERS BY STARS ===\n")
        for r in data1['items'][:5]:
            f.write(f"- {r['full_name']} ({r['stargazers_count']} stars): {r['description']} | Last updated: {r['updated_at']}\n")

        f.write("\n=== TOP REDDIT OVERALL BY STARS ===\n")
        req2 = urllib.request.Request('https://api.github.com/search/repositories?q=reddit&sort=stars&order=desc', headers={'User-Agent': 'Mozilla/5.0'})
        res2 = urllib.request.urlopen(req2)
        data2 = json.loads(res2.read())
        for r in data2['items'][:5]:
            f.write(f"- {r['full_name']} ({r['stargazers_count']} stars): {r['description']} | Last updated: {r['updated_at']}\n")
except Exception as e:
    traceback.print_exc()
