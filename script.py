import json
import os

file_path = r'c:\desarrollos\antigravity\text game youtube estudio ejemplos\parsed_cases\w2Jwahp_z8o.json'

with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
    data = json.load(f)

# The encoding might be mangled in the file already if it was saved incorrectly. 
# Let's fix the known Spanish string if it's messed up.
justif = data.get('justificacion_scoring', '')
justif = justif.replace('interaccin', 'interacción')
justif = justif.replace('cumpleaos', 'cumpleaños')
justif = justif.replace('lǧdico', 'lúdico')
justif = justif.replace('economa', 'economía')
justif = justif.replace('transicin', 'transición')
data['justificacion_scoring'] = justif

translations = {
    "hey trouble": "hola problema",
    "hey how are you": "hola, ¿cómo estás?",
    "good just finished a late night workout looking nice fit for our date": "bien, recién termino mi entrenamiento nocturno, poniéndome en forma para nuestra cita",
    "that's great how's your week so far": "qué bueno, ¿cómo va tu semana hasta ahora?",
    "was pretty good enjoyed birthday festivities and you": "bastante bien, disfruté de los festejos de mi cumpleaños, ¿y tú?",
    "happy birthday mine was good with family and friends at home": "feliz cumpleaños, la mía estuvo bien, con familia y amigos en casa",
    "since it was last week i was kind of hoping you would jump out of the cake": "como fue la semana pasada, tenía la esperanza de que saltaras del pastel",
    "haha do you have whatsapp i'm not on here much": "jaja ¿tienes WhatsApp? no entro mucho por aquí",
    "hey it's alex": "hola, soy Alex"
}

for fase in data.get('fases', []):
    for msg in fase.get('mensajes', []):
        t = msg.get('texto', '')
        if t in translations:
            msg['texto'] = translations[t]

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
