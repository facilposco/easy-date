import re

filename = 'c:\\desarrollos\\antigravity\\text game youtube estudio ejemplos\\simulador_v1.0.html'
with open(filename, 'r', encoding='utf-8') as f:
    lines = f.readlines()

ids = []
for i, line in enumerate(lines):
    matches = re.findall(r'id=[\'\"]([^\'\"]+)[\'\"]', line)
    if matches:
        for m in matches:
            ids.append(m)

print(set(ids))
