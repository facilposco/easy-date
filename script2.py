import json

file_path = r'c:\desarrollos\antigravity\text game youtube estudio ejemplos\parsed_cases\w2Jwahp_z8o.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

justif = data.get('justificacion_scoring', '')
justif = justif.replace('interacci\ufffdn', 'interacción')
justif = justif.replace('cumplea\ufffdos', 'cumpleaños')
justif = justif.replace('l\ufffddico', 'lúdico')
justif = justif.replace('econom\ufffda', 'economía')
justif = justif.replace('transici\ufffdn', 'transición')
justif = justif.replace('inversi\ufffdn', 'inversión')
data['justificacion_scoring'] = justif

for fase in data.get('fases', []):
    for msg in fase.get('mensajes', []):
        t = msg.get('texto', '')
        t = t.replace('\ufffdc\ufffdmo est\ufffds?', '¿cómo estás?')
        t = t.replace('reci\ufffdn', 'recién')
        t = t.replace('poni\ufffdndome', 'poniéndome')
        t = t.replace('qu\ufffd bueno, \ufffdc\ufffdmo', 'qué bueno, ¿cómo')
        t = t.replace('disfrut\ufffd', 'disfruté')
        t = t.replace('cumplea\ufffdos, \ufffdy t\ufffd?', 'cumpleaños, ¿y tú?')
        t = t.replace('cumplea\ufffdos, la m\ufffda', 'cumpleaños, la mía')
        t = t.replace('ten\ufffda', 'tenía')
        t = t.replace('\ufffdtienes WhatsApp? no entro mucho por aqu\ufffd', '¿tienes WhatsApp? no entro mucho por aquí')
        msg['texto'] = t

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
