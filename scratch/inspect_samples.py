import sqlite3

conn = sqlite3.connect("textgame.db")
cursor = conn.cursor()

# Get 5 samples from transcripts
cursor.execute("SELECT video_id, status, raw_text, message FROM transcripts WHERE status = 'success' LIMIT 3")
rows = cursor.fetchall()
print("--- TRANSCRIPTS SAMPLES ---")
for r in rows:
    print(f"Video ID: {r[0]}, Status: {r[1]}")
    print(f"Message: {r[3]}")
    print(f"Raw Text Preview: {r[2][:200]}...")
    print("-" * 40)

# Get 5 samples from reddit_conversations
cursor.execute("SELECT post_id, title, post_type, body_text FROM reddit_conversations WHERE body_text != '' LIMIT 5")
rows = cursor.fetchall()
print("\n--- REDDIT CONVERSATIONS SAMPLES ---")
for r in rows:
    print(f"Post ID: {r[0]}, Type: {r[2]}")
    print(f"Title: {r[1]}")
    print(f"Body Text Preview: {r[3][:200]}...")
    print("-" * 40)

conn.close()
