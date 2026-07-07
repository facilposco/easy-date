import json

file_path = r"c:\desarrollos\antigravity\text game youtube estudio ejemplos\parsed_cases\khMAhchh02A.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

translations = {
    "hi": "hola",
    "hey troublemaker": "hey problemática",
    "that's me totally how's your day going": "esa soy yo totalmente cómo va tu día",
    "amazing just finished up a big parkour looking nice and fit for our date": "increíble acabo de terminar un gran parkour viéndome bien y en forma para nuestra cita",
    "i like that perfect where do you live in brickell what about you": "me gusta eso perfecto, dónde vives, en brickell ¿y tú?",
    "perfect for our romance to blossom ha ha": "perfecto para que nuestro romance florezca ja ja",
    "crazy exactly do you like wine it's my favorite": "locura exacto te gusta el vino es mi favorito",
    "good we should split a bottle sometime soon": "bien deberíamos compartir una botella pronto",
    "for sure how long you've been single": "seguro cuánto tiempo llevas soltero",
    "about a year now": "como un año ya",
    "and what are you looking for now": "y qué estás buscando ahora",
    "a cool girl i have chemistry with what about you": "una chica genial con la que tenga química ¿y tú?",
    "wow that took two days ha ha same": "wow eso tomó dos días ja ja yo igual",
    "glad we're on the same page do you like white wine": "me alegra que estemos en la misma sintonía te gusta el vino blanco",
    "a lot red ones": "mucho los tintos",
    "let's give it another shot and split a bottle sometime then": "démosle otra oportunidad y compartamos una botella en algún momento entonces",
    "sounds great what evenings are you free next": "suena genial qué noches estás libre próximamente",
    "i'm going to know tomorrow. sounds good shoot me your number for romance arrangement purposes": "lo sabré mañana. suena bien pásame tu número para propósitos de arreglos románticos",
    "haha i love flowers": "jaja me encantan las flores",
    "i still waiting for the romantic arrangement purposes lol": "todavía sigo esperando los propósitos de arreglos románticos lol"
}

for fase in data.get("fases", []):
    for msg in fase.get("mensajes", []):
        if "texto" in msg:
            original = msg["texto"]
            if original in translations:
                msg["texto"] = translations[original]

# Escribir de vuelta
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Traducción completada y guardada.")