import json

with open('parsed_cases/G01G2HzjpFQ.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

data['justificacion_scoring'] = "Excelente economÃ­a de palabras y gestiÃ³n efectiva de barreras de interÃ©s inicial. Uso de respuestas ingeniosas ('incluso los mejores vendedores necesitan una noche libre para relajarse') y 'takeaways' efectivos ante pruebas de la chica ('si no hay quÃ­mica... un beso platÃ³nico'). Cierre logÃ­stico de alto nivel llevando la cita directo a casa (balcÃ³n)."

mensajes_dict = {
    "hello there": "hola",
    "hey sexy starburst": "hola sexy starburst",
    "hi yes i'm sexy starting": "hola sÃ­ soy sexy empezando",
    "what other sexy are you": "quÃ© otro tipo de sexy eres",
    "well i can't be what i want to be so just flirting nice to meet you alex": "bueno no puedo ser lo que quiero ser asÃ­ que solo coqueteo, un gusto conocerte alex",
    "ah spicy i see lol once i bend you over and give your behind a good spanking that spicy side will fade away right": "ah picante, ya veo jaja una vez que te doble y te dÃ© unas buenas nalgadas ese lado picante va a desaparecer, verdad",
    "i do not believe it is my nature": "no lo creo, estÃ¡ en mi naturaleza",
    "well hi good morning i like champagne i like your dog": "bueno hola buenos dÃ­as me gusta el champagne me gusta tu perro",
    "how about we split a bottle on my romantic balcony overlooking the city while my husky entertains us": "quÃ© tal si compartimos una botella en mi balcÃ³n romÃ¡ntico con vista a la ciudad mientras mi husky nos entretiene",
    "interesting what else does it offer me": "interesante, quÃ© mÃ¡s me ofreces",
    "you may be entitled to my world famous back massage": "puede que tengas derecho a mi mundialmente famoso masaje de espalda",
    "really i'm thinking maybe lol": "en serio, lo estoy pensando tal vez jaja",
    "if you're too shy i understand": "si eres muy tÃ­mida lo entiendo",
    "not all only if i i don't have chemistry i can't counter it": "para nada, solo que si no hay quÃ­mica no puedo forzarla",
    "if there's no chemistry then all you'll get is a platonic kiss on the cheek goodbye": "si no hay quÃ­mica entonces todo lo que vas a recibir es un beso platÃ³nico en la mejilla de despedida",
    "lol": "jaja",
    "exactly i'm not active on here shoot me your number so romance doesn't end here": "exacto, no soy muy activo por aquÃ­, pÃ¡same tu nÃºmero para que el romance no termine aquÃ­",
    "hey it's alex from the internet": "hey soy alex de internet",
    "hi app de citas": "hola app de citas",
    "c": "c",
    "how's your day": "cÃ³mo va tu dÃ­a",
    "good just hanging out with this guy": "bien, solo pasando el rato con este chico",
    "beautiful": "hermoso",
    "thanks he says he's excited to meet you": "gracias, dice que estÃ¡ emocionado por conocerte",
    "b2 good": "b2 bien",
    "you free thursday or friday night": "estÃ¡s libre el jueves o viernes en la noche",
    "how's your monday it all depends my work is for commission and the more appointments i have the more sales": "cÃ³mo va tu lunes, todo depende, mi trabajo es por comisiÃ³n y mientras mÃ¡s citas tenga mÃ¡s ventas",
    "even the best sales people need a relaxing night off": "incluso los mejores vendedores necesitan una noche libre para relajarse",
    "lol what can you think of for those days": "jaja quÃ© tienes pensado para esos dÃ­as",
    "again i was splitting a bottle of wine on my romantic balcony": "de nuevo, pensaba en compartir una botella de vino en mi balcÃ³n romÃ¡ntico",
    "not like wine": "no me gusta el vino",
    "drink of choice": "bebida de preferencia",
    "champagne or coffee": "champagne o cafÃ©",
    "all right champagne on the romantic balcony it is then": "muy bien, entonces serÃ¡ champagne en el balcÃ³n romÃ¡ntico",
    "good night see you soon": "buenas noches nos vemos pronto",
    "ola linda": "hola linda",
    "hola how are you": "hola cÃ³mo estÃ¡s",
    "good just finishing up a workout looking nice and fit for our date": "bien, justo terminando de entrenar, poniÃ©ndome guapo y en forma para nuestra cita",
    "ooh nice speaking of which what is your schedule looking like": "ooh genial, hablando de eso, cÃ³mo se ve tu horario",
    "hi finish my job now the day that works for me is friday": "hola acabo de terminar de trabajar, el dÃ­a que me funciona es el viernes",
    "alright friday night it is perfect thanks": "perfecto, el viernes en la noche entonces, gracias",
    "hi boy thank you": "hola chico gracias",
    "hey still good for tonight": "hey, todavÃ­a seguimos en pie para esta noche",
    "okay": "ok",
    "can you pick me up what time": "puedes pasar por mÃ­ a quÃ© hora",
    "what part town are you and how's 9 30 or 10": "en quÃ© parte de la ciudad estÃ¡s y quÃ© te parece a las 9 30 o 10",
    "oh cool you're super close but yeah no problem i'll get you an uber": "oh genial estÃ¡s sÃºper cerca pero sÃ­ no hay problema te pido un uber",
    "really okay": "en serio, ok",
    "10 cool": "a las 10 genial",
    "do you have ig by the way": "por cierto, tienes ig",
    "let me know if it's safe to relax or not": "avÃ­same si es seguro relajarme o no",
    "added": "te agreguÃ©",
    "safe to relax if i stay at home or not": "seguro para relajarme si me quedo en casa o no",
    "ah nah you're definitely cute we will relax together": "ah no, definitivamente eres linda, nos relajaremos juntos",
    "okay so 9 45": "ok entonces 9 45",
    "almost ready": "casi listo",
    "okay i'll tell you": "ok te aviso",
    "ready": "lista",
    "cool calling uber now": "genial, pidiendo el uber ahora",
    "coming": "ya llega"
}

for fase in data.get('fases', []):
    for msg in fase.get('mensajes', []):
        if msg.get('texto') in mensajes_dict:
            msg['texto'] = mensajes_dict[msg['texto']]
            
with open('parsed_cases/G01G2HzjpFQ.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

