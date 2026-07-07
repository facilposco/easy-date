import re

with open('transcript.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's split by sentences or small chunks and print parts with "number" or "date" or "smash" or "come over"
chunks = text.split("  ") if "  " in text else text.split(". ")
if len(chunks) < 10:
    # try splitting by '?'
    chunks = re.split(r'(?<=[.!?]) +', text)

for i, chunk in enumerate(chunks):
    if "number" in chunk.lower() or "date" in chunk.lower() or "close" in chunk.lower() or "tinder" in chunk.lower():
        # print around
        print(f"--- Chunk {i} ---")
        start = max(0, i-3)
        end = min(len(chunks), i+4)
        print(" ".join(chunks[start:end]))
