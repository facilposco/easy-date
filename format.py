import os

with open('transcript.txt', 'r', encoding='utf-8') as f:
    text = f.read()

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

with open('transcript_formatted.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"Total lines: {len(lines)}")
