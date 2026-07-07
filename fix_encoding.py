import json

file_path = r'c:\desarrollos\antigravity\text game youtube estudio ejemplos\parsed_cases\khMAhchh02A.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for fase in data.get('fases', []):
    for msg in fase.get('mensajes', []):
        if 'texto' in msg:
            t = msg['texto']
            if 'hey problem' in t:
                msg['texto'] = 'hey problem\u00e1tica'
            elif 'vi' in t and 'ndome' in t:
                msg['texto'] = 'incre\u00edble acabo de terminar un gran parkour vi\u00e9ndome bien y en forma para nuestra cita'
            elif 'd' in t and 'nde vives' in t and 't' in t:
                msg['texto'] = 'me gusta eso perfecto, d\u00f3nde vives, en brickell \u00bfy t\u00fa?'
            elif 'cu' in t and 'nto tiempo' in t:
                msg['texto'] = 'seguro cu\u00e1nto tiempo llevas soltero'
            elif 'a' in t and 'o ya' in t:
                msg['texto'] = 'como un a\u00f1o ya'
            elif 'qu' in t and 'est' in t and 's buscando' in t:
                msg['texto'] = 'y qu\u00e9 est\u00e1s buscando ahora'
            elif 'tenga qu' in t and 'mica' in t and 'y t' in t:
                msg['texto'] = 'una chica genial con la que tenga qu\u00edmica \u00bfy t\u00fa?'
            elif 'tom' in t and 'dos d' in t:
                msg['texto'] = 'wow eso tom\u00f3 dos d\u00edas ja ja yo igual'
            elif 'sinton' in t:
                msg['texto'] = 'me alegra que estemos en la misma sinton\u00eda te gusta el vino blanco'
            elif 'd' in t and 'mosle otra oportunidad' in t and 'alg' in t:
                msg['texto'] = 'd\u00e9mosle otra oportunidad y compartamos una botella en alg\u00fan momento entonces'
            elif 'qu' in t and 'noches est' in t and 's libre pr' in t:
                msg['texto'] = 'suena genial qu\u00e9 noches est\u00e1s libre pr\u00f3ximamente'
            elif 'lo sabr' in t and 'ma' in t and 'ana' in t and 'p' in t and 'same tu n' in t:
                msg['texto'] = 'lo sabr\u00e9 ma\u00f1ana. suena bien p\u00e1same tu n\u00famero para prop\u00f3sitos de arreglos rom\u00e1nticos'
            elif 'todav' in t and 'a sigo esperando los prop' in t and 'sitos de arreglos rom' in t:
                msg['texto'] = 'todav\u00eda sigo esperando los prop\u00f3sitos de arreglos rom\u00e1nticos lol'
            elif 'esa soy yo totalmente c' in t and 'mo va tu d' in t:
                msg['texto'] = 'esa soy yo totalmente c\u00f3mo va tu d\u00eda'

# Fixing top-level 'justificacion_scoring' string which has mojibake 'econom\ufffda' etc.
if 'justificacion_scoring' in data:
    data['justificacion_scoring'] = "El Youtuber mantuvo un frame asertivo y directo desde el principio ('nice and fit for our date'). Tuvo excelente econom\u00eda de palabras y super\u00f3 exitosamente pausas de varios d\u00edas ('that took two days'). Logr\u00f3 redirigir la conversaci\u00f3n hacia una cita y conseguir el cierre de manera fluida y con humor ('romance arrangement purposes')."

# Escribir de vuelta
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)