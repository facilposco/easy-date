import sqlite3
import textwrap

conn = sqlite3.connect('textgame.db')
cursor = conn.cursor()
cursor.execute("SELECT raw_text FROM transcripts WHERE video_id = 'fGGmXL2vmos'")
row = cursor.fetchone()

if row:
    text = row[0]
    words = text.split()
    lines = []
    current_line = []
    for w in words:
        current_line.append(w)
        if len(current_line) >= 20:
            lines.append(' '.join(current_line))
            current_line = []
    if current_line:
        lines.append(' '.join(current_line))

    with open('fGGmXL2vmos_transcript.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"Total lines: {len(lines)}")
else:
    print("Not found")
