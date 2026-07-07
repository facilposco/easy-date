import json

file_path = r'c:\desarrollos\antigravity\text game youtube estudio ejemplos\parsed_cases\w2Jwahp_z8o.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

justif = data.get('justificacion_scoring', '')
justif = justif.replace("('hoping you would jump out of the cake')", "('esperando que saltaras del pastel')")
data['justificacion_scoring'] = justif

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
