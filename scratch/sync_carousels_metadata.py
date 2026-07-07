import sqlite3
import json
import os

DB_PATH = "textgame.db"
META_PATH = "scratch/reddit_deep_metadata.json"

def main():
    if not os.path.exists(META_PATH):
        print(f"Error: {META_PATH} does not exist.")
        return

    # Load existing metadata
    with open(META_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Filter out existing multi cases to avoid duplicates
    metadata = [m for m in metadata if m.get("type") != "multi"]

    # Connect to DB and fetch 10 carousels
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT post_id, title, url, image_urls, local_image_paths 
        FROM reddit_conversations 
        WHERE post_type = 'carousel' 
        LIMIT 10
    """)
    rows = cursor.fetchall()
    conn.close()

    print(f"Fetched {len(rows)} carousels from SQLite.")

    for idx, row in enumerate(rows, 1):
        post_id, title, url, img_urls_json, local_paths_json = row
        
        try:
            image_urls = json.loads(img_urls_json) if img_urls_json else []
            local_paths = json.loads(local_paths_json) if local_paths_json else []
        except Exception as e:
            print(f"Error parsing JSON for {post_id}: {e}")
            continue

        # Adjust backslashes to forward slashes for cross-platform links
        local_paths = [p.replace("\\", "/") for p in local_paths]

        metadata.append({
            "id": f"multi_{idx}",
            "type": "multi",
            "title": title,
            "post_url": url,
            "image_paths": local_paths,
            "image_urls": image_urls
        })

    # Save updated metadata
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)

    print(f"Successfully synced metadata. Total cases in JSON: {len(metadata)}")

if __name__ == "__main__":
    main()
