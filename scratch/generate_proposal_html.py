import json
import os
from datetime import datetime

HTML_PATH = "propuesta_conversaciones.html"
TIME_TICKS = [
    "Ahora mismo",
    "15m",
    "1h",
    "2h",
    "4h",
    "12h",
    "24h",
    "2 dias"
]

# Definición de las 4 conversaciones 100% reales, completas y sin alteraciones del significado
# Traducidas a un español latino ultra natural y de alto impacto
dialogues = {
  "version": "1.1",
  "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
  "levels": [
    {
      "level_id": 1,
      "girl_name": "Natalia",
      "level_name": "Nivel 1: El Match Directo (Bumble)",
      "description": "Conversación completa extraída de khMAhchh02A.json. Flujo directo y natural, liderando hacia el número.",
      "steps": [
        {
          "step_id": 1,
          "contexto_inicial": "Haces Match con Natalia en Bumble. El chat está vacío y debes tomar la iniciativa con un abridor interesante.",
          "her_time": "Inicio de conversación",
          "her_message": "[Chat vacío - Envías abridor]",
          "correct_option": "hey chica problema",
          "decoys": [
            "¡Hola hermosa! ¿Cómo estás hoy? 😍",
            "Hola Natalia, qué lindo tu perfil. ¿Qué tal tu semana?",
            "Hola, ¿buscas algo serio por aquí?"
          ],
          "allowed_time_indices": [1, 2], # 15m a 1h
          "coach_feedback_correct": "¡Excelente abridor! Lanzas un reto juguetón llamándola 'chica problema' que la desmarca de la aburrida pila de mensajes.",
          "coach_feedback_incorrect": "Demasiado sumiso o genérico. El clásico saludo no despierta ningún interés.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato denota prisa; esperar más de 2 horas en Bumble enfría la ventana de atención."
        },
        {
          "step_id": 2,
          "her_time": "Tardó: 15 min",
          "her_message": "esa soy yo totalmente jaja ¿cómo va tu día?",
          "correct_option": "increíble, acabo de terminar de entrenar y ando poniéndome en forma para nuestra cita",
          "decoys": [
            "Muy bien, aquí en la oficina trabajando. ¿Y tú?",
            "Normal, nada especial. ¿Qué haces?",
            "Cansado, ojalá estuvieras aquí para relajarme"
          ],
          "allowed_time_indices": [1, 2], # 15m a 1h
          "coach_feedback_correct": "Asumes la cita de inmediato con alta vibración y demuestras que eres un hombre activo.",
          "coach_feedback_incorrect": "Responder lógicamente sobre tu trabajo o quejarte de tu cansancio destruye el misterio.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder al instante (Ahora mismo) denota desesperación. Espera de 15m a 1h."
        },
        {
          "step_id": 3,
          "her_time": "Tardó: 20 min",
          "her_message": "me gusta eso, perfecto ¿dónde vives? yo en brickell ¿y tú?",
          "correct_option": "perfecto para que nuestro romance florezca ja ja",
          "decoys": [
            "Vivo en Downtown, súper cerca. Deberíamos vernos ya.",
            "Yo vivo en Kendall, un poco lejos. ¿Tienes auto?",
            "Vivo en Brickell también. ¿En qué edificio estás?"
          ],
          "allowed_time_indices": [1, 2], # 15m a 1h
          "coach_feedback_correct": "Tomas su dato geográfico y lo usas para redoblar el chiste del 'romance', evitando sonar como un interrogatorio de mudanza.",
          "coach_feedback_incorrect": "Entrar en detalles logísticos o presionar para verse de inmediato le quita la vibra lúdica."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Mantén la fluidez respondiendo entre 15 min y 1 hora."
        },
        {
          "step_id": 4,
          "her_time": "Tardó: 30 min",
          "her_message": "jaja qué loco. ¿te gusta el vino? es mi favorito",
          "correct_option": "bien, deberíamos compartir una botella pronto",
          "decoys": [
            "¡A mí también! Me encanta el Cabernet Sauvignon. ¿A ti?",
            "No me gusta el alcohol, prefiero ir al cine.",
            "Te invito una botella hoy mismo en la noche a mi casa"
          ],
          "allowed_time_indices": [2, 3], # 1h a 2h
          "coach_feedback_correct": "Aceptas su gusto e introduces la propuesta indirecta de cita ('compartir una botella pronto') con naturalidad.",
          "coach_feedback_incorrect": "Ponerte demasiado técnico sobre vinos o invitarla directo a tu casa de inmediato apaga la atracción."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de golpe muestra prisa. Esperar 1h o 2h asienta la propuesta."
        },
        {
          "step_id": 5,
          "her_time": "Tardó: 15 min",
          "her_message": "seguro ¿cuánto tiempo llevas soltero?",
          "correct_option": "como un año ya",
          "decoys": [
            "Uff, hace mucho, me han roto el corazón varias veces 🥺",
            "Acabo de terminar hace una semana, ando despechado",
            "No me gusta estar soltero, busco novia urgente"
          ],
          "allowed_time_indices": [1, 2], # 15m a 1h
          "coach_feedback_correct": "Respuesta limpia, directa y con estabilidad emocional. Un año muestra madurez.",
          "coach_feedback_incorrect": "Hacer drama sobre tus ex o demostrar que buscas novia con urgencia asusta a cualquiera."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde con templanza en un lapso normal."
        },
        {
          "step_id": 6,
          "her_time": "Tardó: 10 min",
          "her_message": "¿y qué estás buscando ahora?",
          "correct_option": "una chica genial con la que tenga química ¿y tú?",
          "decoys": [
            "Busco una relación seria que termine en matrimonio",
            "Solo busco algo casual de una noche",
            "Lo que sea que surja, no tengo planes"
          ],
          "allowed_time_indices": [1, 2], # 15m a 1h
          "coach_feedback_correct": "Encuadre equilibrado. Buscas química y pasarla bien, sin sonar cerrado pero tampoco urgido.",
          "coach_feedback_incorrect": "Exigir matrimonio asusta; proponer sexo de una noche directamente suena vulgar."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato te resta misterio."
        },
        {
          "step_id": 7,
          "her_time": "Tardó: 2 dias",
          "her_message": "jaja yo igual, nada súper serio pero química primero",
          "correct_option": "me alegra que estemos en la misma sintonía ¿te gusta el vino blanco?",
          "decoys": [
            "Perdón por tardar tanto, andaba súper ocupado",
            "Sí, andaba ocupado. ¿Qué hiciste en estos días?",
            "Jaja te tardaste mucho en contestar"
          ],
          "allowed_time_indices": [4, 5], # 4h a 12h
          "coach_feedback_correct": "Ignoras su retraso (tardó 2 días), no te disculpas por nada y retomas la logística del vino de forma tranquila.",
          "coach_feedback_incorrect": "Reclamar por su demora o pedir disculpas por el tiempo demuestra inseguridad extrema."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Si tardó 2 días, debes darle espacio. Contestar en 4h a 12h demuestra que tienes tu propio ritmo de vida."
        },
        {
          "step_id": 8,
          "her_time": "Tardó: 25 min",
          "her_message": "mucho, pero prefiero los tintos",
          "correct_option": "démosle una oportunidad y compartamos una botella entonces",
          "decoys": [
            "Qué mal, a mí solo me gusta el blanco",
            "Bueno, entonces compramos una de cada uno hoy",
            "Deberías probar el blanco, te va a gustar"
          ],
          "allowed_time_indices": [2, 3], # 1h a 2h
          "coach_feedback_correct": "Cierre directo de la cita. Aceptas su gusto (tinto) y propones compartir la botella concretamente.",
          "coach_feedback_incorrect": "Ponerte a discutir sobre vinos o insistir en el blanco devalúa tu empatía."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Deja pasar entre 1h y 2h para mantener el ritmo maduro."
        },
        {
          "step_id": 9,
          "her_time": "Tardó: 20 min",
          "her_message": "suena genial ¿qué noches estás libre próximamente?",
          "correct_option": "lo sabré mañana bien. pásame tu número para coordinar",
          "decoys": [
            "Estoy libre hoy, mañana y el viernes, ¿cuándo quieres?",
            "No sé, ando muy ocupado esta semana",
            "Dame tu WhatsApp y te aviso"
          ],
          "allowed_time_indices": [1, 2], # 15m a 1h
          "coach_feedback_correct": "Demuestras que tu tiempo es valioso (no sabes tu agenda de memoria) y lideras pidiendo el número para salir de la app.",
          "coach_feedback_incorrect": "Mostrarte disponible 24/7 devalúa tu estatus; pedir el WhatsApp de forma seca rompe la fluidez."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de golpe denota impaciencia. Espera al menos 15 minutos."
        },
        {
          "step_id": 10,
          "her_time": "Tardó: 15 min",
          "her_message": "[Su número] jaja me encanta cómo lo dices",
          "correct_option": "Excelente, te escribo en la noche. Cuídate 😉",
          "decoys": [
            "¡SIII! Te escribo ya mismo 😍",
            "Ok te guardo",
            "Gracias hermosa"
          ],
          "allowed_time_indices": [1, 2], # 15m a 1h
          "coach_feedback_correct": "Cierre y retirada impecable. Mantienes el misterio y concretas el paso a WhatsApp.",
          "coach_feedback_incorrect": "Sobre-excitación con corazones rompe la atracción masculina construida."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Confirmación sobria y tranquila en un lapso normal."
        }
      ]
    },
    {
      "level_id": 2,
      "girl_name": "Sofía",
      "level_name": "Nivel 2: El Banter y las Pruebas (Hinge)",
      "description": "Conversación completa de eE8lWAG-NAY.json. Banter ingenioso (chico blanco / latina) y transición lógica a WhatsApp.",
      "steps": [
        {
          "step_id": 1,
          "contexto_inicial": "Sofía te da match en Hinge. El chat está vacío y abres con una propuesta divertida exagerada.",
          "her_time": "Inicio de conversación",
          "her_message": "[Chat vacío - Envías abridor]",
          "correct_option": "Gracias Sofía, tú tampoco te ves nada mal. Entonces, ¿esta es la parte donde empezamos un romance fugaz, nos casamos y nos divorciamos en tiempo récord? 🤔",
          "decoys": [
            "Hola Sofía, gracias por el match. Eres hermosa. 😍",
            "Hola, ¿cómo estás? Qué gusto coincidir.",
            "Hola guapa, ¿qué te gustó de mi perfil?"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Abridor de alto impacto. Creas un escenario cómico de boda/divorcio rápido que le da material infinito para responder.",
          "coach_feedback_incorrect": "Halagos genéricos que la aburren de inmediato.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Esperar demasiado reduce el impacto del match."
        },
        {
          "step_id": 2,
          "her_time": "Tardó: 20 min",
          "her_message": "Mi mejor amiga me lo tradujo y entendí lo que dijiste, jaja. ¿Eres de por aquí?",
          "correct_option": "Eso significa que vivo aquí parte del año pero viajo bastante. Parece que te vendría mejor que hablemos en español.",
          "decoys": [
            "Jaja qué bueno. Sí, vivo aquí hace 5 años.",
            "Ah no hablas inglés, qué mal. Sí, soy de aquí.",
            "¿Tu amiga es bonita? Jaja. Sí, vivo en Brickell."
          ],
          "allowed_time_indices": [2, 3], # 1h a 2h
          "coach_feedback_correct": "Demuestras estatus (viajas) y le propones de forma caballerosa cambiar a su idioma para facilitar las cosas.",
          "coach_feedback_incorrect": "Respuestas literales de geografía que matan la tensión juguetona."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Dale espacio tras mencionar a su amiga."
        },
        {
          "step_id": 3,
          "her_time": "Tardó: 25 min",
          "her_message": "Oye, ¡qué atrevido! Jaja. Sí hablo inglés, fui a la universidad, por favor... Dios mío, qué loco estás.",
          "correct_option": "Jaja, dijiste que tu amiga te tradujo, solo intentaba ayudarte. 😂 Me alegra ver que eres segura, educada y con carácter.",
          "decoys": [
            "Perdón, no quise ofenderte de verdad 🥺",
            "Jaja yo no soy loco, tú eres la loca",
            "¿Qué tiene de malo ser chico blanco?"
          ],
          "allowed_time_indices": [2, 3], # 1h a 2h
          "coach_feedback_correct": "No te disculpas. Reencuadras tu comentario como ayuda y le das cumplidos condicionados a su personalidad ('segura, educada, carácter').",
          "coach_feedback_incorrect": "Pedir disculpas de inmediato mata tu estatus de hombre seguro."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Muestra calma ante su acusación juguetona."
        },
        {
          "step_id": 4,
          "her_time": "Tardó: 40 min",
          "her_message": "Es que solo me tradujo 'chico blanco' y volteé los ojos.",
          "correct_option": "Por suerte hablo fluido tanto 'chico blanco' como 'latina con carácter', así que no ocuparemos traductor en nuestras citas. Aunque tal vez ocupemos un guardaespaldas para protegerme de tus encantos. 😇",
          "decoys": [
            "Jaja, qué chistosa. Pásame tu número.",
            "No soy como los otros chicos blancos, te lo prometo",
            "¿Por qué volteaste los ojos? ¿Te caigo mal?"
          ],
          "allowed_time_indices": [3, 4], # 2h a 4h
          "coach_feedback_correct": "Excelente calibración. Adoptas el chiste cultural y asumes la cita pintándote a ti mismo como el 'inocente' de forma divertida.",
          "coach_feedback_incorrect": "Explicaciones defensivas sobre tu raza o forzar el número muy rápido."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Esperar de 2h a 4h le da espacio al chiste."
        },
        {
          "step_id": 5,
          "her_time": "Tardó: 15 min",
          "her_message": "Bueno, Douglas. Jaja.",
          "correct_option": "Gracias. Me alegra que lo apruebes. Dime Sofía, ¿es tan divertido bromear contigo en persona como lo es por chat?",
          "decoys": [
            "Jaja sí. ¿Qué haces hoy?",
            "¿Cuándo salimos a comprobarlo?",
            "Jaja obvio que sí"
          ],
          "allowed_time_indices": [1, 2], # 15m a 1h
          "coach_feedback_correct": "Tomas su respuesta y abres la puerta para la transición al mundo real de forma fluida.",
          "coach_feedback_incorrect": "Presionar de forma brusca o respuestas cortas que cortan la tensión."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde en un lapso normal."
        },
        {
          "step_id": 6,
          "her_time": "Tardó: 15 min",
          "her_message": "Aprecio tu confianza. Mi número es [Número]. ¿Cuál es el tuyo?",
          "correct_option": "Aquí tienes el mío. Te escribo en un rato 😉",
          "decoys": [
            "¡SIII! Te agrego ya y te llamo",
            "Ok, te hablo por WhatsApp ahora",
            "Gracias linda"
          ],
          "allowed_time_indices": [1, 2], # 15m a 1h
          "coach_feedback_correct": "Intercambias el número con tranquilidad sin verte desesperado.",
          "coach_feedback_incorrect": "Demostrar desesperación al recibir el número devalúa tu valor."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde con calma."
        },
        {
          "step_id": 7,
          "her_time": "Tardó: 20 min",
          "her_message": "Hola, agendado. Tengo que conseguir un teléfono de emergencia, así que de verdad disculpa si desaparezco de la nada jaja",
          "correct_option": "No te preocupes, si es más fácil coordinar nuestra primera cita por aquí rápido, no tengo problema. ¿Cómo andas de tiempos estos días?",
          "decoys": [
            "Uy qué mal, ojalá lo arregles pronto. Avísame.",
            "No te preocupes, te espero lo que sea necesario",
            "¿Por qué falla tu teléfono? ¿Qué marca es?"
          ],
          "allowed_time_indices": [2, 3], # 1h a 2h
          "coach_feedback_correct": "Aprovechas su excusa del teléfono para proponer organizar la cita directamente sin perder tiempo en chats eternos.",
          "coach_feedback_incorrect": "Charlas aburridas sobre teléfonos o sumisión extrema."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato te hace ver pegado a la pantalla."
        },
        {
          "step_id": 8,
          "her_time": "Tardó: 50 min",
          "her_message": "Comprar un teléfono es mi prioridad ahora, ando corriendo con eso. ¡Mira mi nueva funda! Está padrísima. [Foto de funda]",
          "correct_option": "Ando ocupado durante el día, pero podría hacerme un espacio para tomar algo y charlar un rato en la noche, ya sea hoy o mañana.",
          "decoys": [
            "¡Qué linda funda! Te combina muy bien 😍",
            "Ah bueno, avísame cuando tengas libre",
            "Mejor dime qué día estás libre tú y nos vemos"
          ],
          "allowed_time_indices": [3, 4], # 2h a 4h
          "coach_feedback_correct": "Ignoras el desvío de la funda y mantienes tu liderazgo proponiendo opciones específicas de días y tu alta ocupación.",
          "coach_feedback_incorrect": "Ponerte a hablar de fundas te manda directo a la zona de amigos virtuales."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Esperar entre 2h y 4h demuestra que tienes tu propia vida."
        },
        {
          "step_id": 9,
          "her_time": "Tardó: 15 min",
          "her_message": "Jaja, me gusta la idea de tomar algo. Mañana en la noche me queda perfecto.",
          "correct_option": "Hecho. Conozco un bar secreto muy cool cerca de Brickell. Te veo allá a las 8:30 pm. Ponte guapa. 😉",
          "decoys": [
            "¡Genial! ¿A dónde te gustaría ir?",
            "Perfecto, dime dónde nos vemos",
            "¡Súper! Paso por ti a tu casa a las 8:00 pm"
          ],
          "allowed_time_indices": [1, 2], # 15m a 1h
          "coach_feedback_correct": "Liderazgo total: decides el lugar, la hora, y le pones un desafío agradable ('ponte guapa').",
          "coach_feedback_incorrect": "Preguntar 'a dónde quieres ir' le pasa la carga de decisión a ella, mostrando falta de liderazgo."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Cierra la cita en un lapso normal."
        },
        {
          "step_id": 10,
          "her_time": "Tardó: 15 min",
          "her_message": "¡Trato hecho! Ya agendado, nos vemos mañana a las 8:30 pm.",
          "correct_option": "Listo, nos vemos allá. Cuídate.",
          "decoys": [
            "¡No puedo esperar para verte! 😍",
            "Ok, avísame cuando salgas para allá",
            "¿Segura que no me vas a cancelar?"
          ],
          "allowed_time_indices": [1, 2], # 15m a 1h
          "coach_feedback_correct": "Confirmación sobria y masculina. Cierras el trato sin parecer necesitado.",
          "coach_feedback_incorrect": "Mostrar inseguridad o emoción exagerada devalúa tu atractivo final."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Cierre rápido y directo."
        }
      ]
    },
    {
      "level_id": 3,
      "girl_name": "Camila",
      "level_name": "Nivel 3: El Estira y Afloja (Tinder)",
      "description": "Conversación completa de Lss_cULdgPs.json. Tensión calibrada, doble cita con perros y paso rápido a WhatsApp.",
      "steps": [
        {
          "step_id": 1,
          "contexto_inicial": "Haces Match con Camila. Ella tiene fotos con su perro en la playa. El chat está vacío y debes enviar el primer mensaje (abrador) para captar su atención.",
          "her_time": "Inicio de conversación",
          "her_message": "[Chat vacío - Envías abridor]",
          "correct_option": "hey chica problema",
          "decoys": [
            "Qué lindo perro tienes, ¿cómo se llama?",
            "Hola Camila, me encantaron tus fotos de la playa",
            "Hola guapa, ¿qué haces hoy?"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "El abridor 'hey chica problema' funciona muy bien con chicas coquetas en Tinder para retar su atención.",
          "coach_feedback_incorrect": "Abrir hablando de su perro te hace ver predecible y aburrido.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder en un lapso normal."
        },
        {
          "step_id": 2,
          "her_time": "Tardó: 15 min",
          "her_message": "holis 💋",
          "correct_option": "me gusta tu estilo",
          "decoys": [
            "¿Cómo estás linda? 😍",
            "¿Qué haces por Tinder?",
            "Hola, qué cortante jaja"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Cumplido condicionado. 'Me gusta tu estilo' es relajado, no valida su belleza física y mantiene el flirteo.",
          "coach_feedback_incorrect": "Poner corazones o quejarse de su brevedad muestra debilidad.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato te hace ver muy disponible."
        },
        {
          "step_id": 3,
          "her_time": "Tardó: 20 min",
          "her_message": "gracias, me gusta tu perro. Los perros son increíbles. ¿Cómo estás hoy?",
          "correct_option": "sí, es el mejor. ¿El de tu foto es tuyo?",
          "decoys": [
            "Estoy bien gracias, trabajando mucho. ¿Y tú?",
            "¡Sí! Los perros son lo mejor del mundo mundial",
            "Jaja gracias, mi perro liga más que yo"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Validas a tu mascota con sobriedad y devuelves la pregunta sobre el suyo para mantener el confort.",
          "coach_feedback_incorrect": "Auto-deprecarse o hablar de trabajo aburrido rompe la vibra juguetona.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde en un lapso normal."
        },
        {
          "step_id": 4,
          "her_time": "Tardó: 20 min",
          "her_message": "sí, es un mini caniche",
          "correct_option": "genial, podemos hacer una cita doble con ellos",
          "decoys": [
            "Qué bonito. ¿Cómo se llama?",
            "Ah, a mí no me gustan mucho los caniches",
            "Deberíamos juntar a los perros hoy mismo"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Propuesta inteligente. La 'cita doble' con las mascotas es relajada y de bajísima presión.",
          "coach_feedback_incorrect": "Hacer preguntas de entrevista aburridas estanca el chat.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder muy rápido te hace ver ansioso."
        },
        {
          "step_id": 5,
          "her_time": "Tardó: 15 min",
          "her_message": "jajaja suena divertido",
          "correct_option": "ojalá se lleven tan bien como nosotros lo haremos",
          "decoys": [
            "Sí, jaja. ¿Qué día puedes?",
            "Genial, pásame tu número",
            "Espero que tu perro no muerda al mío"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Tensión calibrada. Proyectas de forma juguetona que ustedes dos se llevarán muy bien en la cita.",
          "coach_feedback_incorrect": "Acelerar la logística demasiado rápido corta la vibra del juego.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato te quita valor."
        },
        {
          "step_id": 6,
          "her_time": "Tardó: 15 min",
          "her_message": "seguro que sí. ¿Qué te gusta hacer para divertirte en Miami? Y espero que no te moleste mi atrevimiento, pero ¿me darías tu número?",
          "correct_option": "dirijo un negocio y me mantengo bastante ocupado, disfruto viajar, ir al gym, leer y varias actividades atrevidas. Solo me falta un poco de Camila en mi vida. Mi número es [Número], me gusta el atrevimiento 😉",
          "decoys": [
            "Claro, mi número es [WhatsApp]. Escríbeme ya.",
            "Me gusta salir de fiesta y la playa. Pásame el tuyo mejor.",
            "¡Sí obvio! Toma: [WhatsApp]. ¿Qué hacemos hoy?"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Demuestras alto valor (negocio/ocupado) e introduces tensión al entregar el contacto de forma madura.",
          "coach_feedback_incorrect": "Entregar el número de forma seca o mostrar desesperación debilita tu marco.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde con calma."
        },
        {
          "step_id": 7,
          "her_time": "Tardó: 15 min",
          "her_message": "hola guapo, soy Camila",
          "correct_option": "ah, la chica linda del caniche",
          "decoys": [
            "¡Hola hermosa! Qué gusto que me escribas 😍",
            "Hola Camila, ¿cómo estás?",
            "Hola, ¿qué andas haciendo?"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Saludas con seguridad y un cumplido condicionado juguetón, recordando su mascota.",
          "coach_feedback_incorrect": "Saludos urgidos o planos. Mantén la vibra arriba.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato te hace ver pegado a la pantalla."
        },
        {
          "step_id": 8,
          "her_time": "Tardó: 15 min",
          "her_message": "bueno sí, voy por la vida con mi pelo de colores y mi perro jaja",
          "correct_option": "no me emocione demasiado 😉",
          "decoys": [
            "Jaja te ves muy bien con ese cabello",
            "¿Por qué te pintas el cabello de colores?",
            "Jaja qué chistosa eres"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Desafías su autodescripción de manera divertida, frenando un poco su ego de forma sutil.",
          "coach_feedback_incorrect": "Halagar su estilo directamente o cuestionarlo destruye la vibra coqueta.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato le da demasiada atención a su físico."
        },
        {
          "step_id": 9,
          "her_time": "Tardó: 45 min",
          "her_message": "jaja no prometo nada... ¿y qué plan tienes para esta noche?",
          "correct_option": "pensaba tomar una copa de vino tinto en mi balcón, ando tranquilo. ¿Te apuntas a compartir la botella?",
          "decoys": [
            "Dime tú qué quieres hacer y yo te sigo",
            "¿Quieres ir de antro o a cenar a un lugar caro?",
            "Nada, aburrido en casa. ¿Quieres venir a acostarte?"
          ],
          "allowed_time_indices": [3, 4], # 2h a 4h
          "coach_feedback_correct": "Propuesta relajada y de alto valor (tu balcón, vino, relajado). No requiere esfuerzo logístico y la incluyes en tu plan.",
          "coach_feedback_incorrect": "Ser sumiso, proponer cenas caras (sobreinversión) o ser vulgarmente directo destruye tu atractivo.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Deja pasar entre 2h y 4h para mostrar que no es un impulso desesperado."
        },
        {
          "step_id": 10,
          "her_time": "Tardó: 15 min",
          "her_message": "suena súper tentador, acepto el vino. Mándame tu dirección.",
          "correct_option": "Perfecto. Te veo a las 8:30 pm en mi lugar. Ven con buena vibra. 😉 [Dirección]",
          "decoys": [
            "¡Sí claro! Toma: [Dirección]. ¡Te espero ya!",
            "Ok, avísame cuando salgas por favor",
            "Genial, ¿quieres que vaya a buscarte?"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Cierras la logística con firmeza, asumiendo el control y marcando una hora clara.",
          "coach_feedback_incorrect": "Ofrecerte de chofer gratis o mostrar demasiada impaciencia debilita el cierre.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Cierre rápido y directo."
        }
      ]
    },
    {
      "level_id": 4,
      "girl_name": "Isabella",
      "level_name": "Nivel 4: El Marco del Seductor (Tinder/WhatsApp)",
      "description": "Conversación completa de wCi7ExnudpU.json (20 pasos). Alta resistencia, test de stripper/sugar baby y cierre asertivo.",
      "steps": [
        {
          "step_id": 1,
          "contexto_inicial": "Haces Match con Isabella en Tinder. El chat está vacío y debes enviar el primer mensaje (abrador) para captar su atención.",
          "her_time": "Inicio de conversación",
          "her_message": "[Chat vacío - Envías abridor]",
          "correct_option": "hola chica problema",
          "decoys": [
            "Hola hermosa, eres la mujer más bella de Tinder 😍",
            "Hola Isabella, ¿cómo estás?",
            "Hola, ¿qué buscas en esta app?"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "El abridor 'hola chica problema' funciona de maravilla con chicas de alta resistencia para desarmar sus defensas.",
          "coach_feedback_incorrect": "Halagos exagerados las aburren al instante.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Abrir demasiado rápido o tardar demasiado reduce la ventana de match."
        },
        {
          "step_id": 2,
          "her_time": "Tardó: 15 min",
          "her_message": "oye, soy una niña buena jajaja",
          "correct_option": "oh, yo también 😉",
          "decoys": [
            "Jaja no te creo nada",
            "Qué bueno, me gustan las niñas buenas",
            "Jaja seguro eres terrible en la cama"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Espejeo de marco. Al responder 'yo también' con ironía, mantienes la dinámica lúdica.",
          "coach_feedback_incorrect": "Ponerse vulgar o validar de forma aburrida apaga la tensión.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato demuestra que estás vigilando la app."
        },
        {
          "step_id": 3,
          "her_time": "Tardó: 45 min",
          "her_message": "eso de niña buena apesta, creo que te ves mejor como chico de casa",
          "correct_option": "gracias, pero no te preocupes, soy demasiado dominante en la cama para eso",
          "decoys": [
            "¡Oye no digas eso, soy muy masculino!",
            "Jaja qué mala eres",
            "¿Por qué dices que apesta?"
          ],
          "allowed_time_indices": [2, 3], # 1h a 2h
          "coach_feedback_correct": "Tensión sexual máxima. Reencuadras su insulto/prueba ('chico de casa') con una aserción de alta masculinidad.",
          "coach_feedback_incorrect": "Ponerse a la defensiva o rogar por su aprobación destruye tu atractivo.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Te lanzó una prueba pesada. Responder rápido te hace ver reactivo e inseguro. Esperar entre 1h y 2h demuestra indiferencia."
        },
        {
          "step_id": 4,
          "her_time": "Tardó: 20 min",
          "her_message": "me gusta eso, siempre que pueda dominarte yo también está bien",
          "correct_option": "por supuesto, especialmente con ese lindo trasero",
          "decoys": [
            "¡SIII! Pásame tu dirección ya 😍",
            "Jaja me asustas un poco",
            "Qué atrevida eres"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Aceptas su propuesta juguetona y dejas ir un cumplido sexualizado pero calibrado sobre sus fotos.",
          "coach_feedback_incorrect": "Desesperación inmediata por la dirección o mostrar timidez.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder al instante te delata como desesperado."
        },
        {
          "step_id": 5,
          "her_time": "Tardó: 15 min",
          "her_message": "mido 1.65 y no tengo mucho trasero, no es verdad. Escríbeme.",
          "correct_option": "toma mi número: [Número] y nos leemos por allá",
          "decoys": [
            "No te preocupes, a mí me gusta así",
            "Pásame tu número mejor",
            "Ok, agrégame tú: [WhatsApp]"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Ella pide que le escribas. Le entregas tu número asumiendo la transición fluida a WhatsApp.",
          "coach_feedback_incorrect": "Seguir discutiendo sobre su cuerpo devalúa la charla.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Pásale tu número en el rango de 15m a 1h."
        },
        {
          "step_id": 6,
          "contexto_inicial": "Ya en WhatsApp. Te agregas y la saludas. Ella responde.",
          "her_time": "Tardó: 10 min",
          "her_message": "hola",
          "correct_option": "al que le gusta el trasero",
          "decoys": [
            "Hola hermosa, qué gusto tenerte aquí 😍",
            "¿Cómo estás? ¿Qué haces?",
            "Hola, ¿qué andas haciendo?"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Retomas la broma del trasero de forma inmediata para mantener el confort y la tensión.",
          "coach_feedback_incorrect": "Saludos aburridos o sumisos pierden la inercia del match."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder al instante te quita misterio."
        },
        {
          "step_id": 7,
          "her_time": "Tardó: 15 min",
          "her_message": "bueno, no tengo suerte, soy delgada",
          "correct_option": "oh basta, ambos sabemos que tienes buen trasero",
          "decoys": [
            "Bueno, no importa, me gustas de todas formas",
            "¿Por qué eres tan insegura?",
            "Jaja si tú lo dices"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Reafirmas tu marco con seguridad ('ambos sabemos'). No caes en su juego para buscar validación fácil.",
          "coach_feedback_incorrect": "Validar su supuesta delgadez o cuestionar su psicología apaga la vibra."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder en un lapso normal."
        },
        {
          "step_id": 8,
          "her_time": "Tardó: 15 min",
          "her_message": "para mi tamaño de cuerpo sí lo tengo, gracias",
          "correct_option": "eso está mejor, ¿eres de aquí originalmente?",
          "decoys": [
            "¡Qué bueno! Me alegro",
            "Deberías mandarme una foto para comprobarlo",
            "¿Qué edad tienes?"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Validas su aceptación y cambias el tema de forma suave y madura hacia el confort geográfico.",
          "coach_feedback_incorrect": "Pedir fotos de forma desesperada o respuestas secas rompe el flujo."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde con calma."
        },
        {
          "step_id": 9,
          "her_time": "Tardó: 20 min",
          "her_message": "sí",
          "correct_option": "ah, una chica de Florida",
          "decoys": [
            "Qué bien, a mí me encanta Florida",
            "¿En qué parte vives?",
            "Qué cortante eres"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Comentario observador y relajado. Mantienes el marco sin forzar preguntas.",
          "coach_feedback_incorrect": "Hacer preguntas de entrevista aburridas o reclamar su brevedad."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde en un lapso normal."
        },
        {
          "step_id": 10,
          "her_time": "Tardó: 15 min",
          "her_message": "[Emoji: fiesta]",
          "correct_option": "entonces dime lo básico: tatuajes, hijos, cosas raras",
          "decoys": [
            "Jaja ¿qué andas haciendo?",
            "¿Quieres salir mañana?",
            "Qué chistosa"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Propuesta de confort divertida y retadora ('cosas raras') para que ella comparta sobre sí misma.",
          "coach_feedback_incorrect": "Preguntar qué hace o forzar la cita muy rápido rompe el ritmo."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Mantén la calma."
        },
        {
          "step_id": 11,
          "her_time": "Tardó: 20 min",
          "her_message": "ocupada, te escribo luego",
          "correct_option": "ok, cuídate",
          "decoys": [
            "¿Por qué estás ocupada? ¿Qué haces?",
            "No te preocupes, aquí te espero",
            "Avísame apenas te liberes por favor"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Muestras indiferencia absoluta y alto valor al aceptar que se vaya del chat con un simple 'ok, cuídate'.",
          "coach_feedback_incorrect": "Interrogar por qué está ocupada o rogar para que te escriba demuestra desesperación extrema."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Cierre de chat rápido."
        },
        {
          "step_id": 12,
          "contexto_inicial": "Ella te vuelve a escribir al día siguiente por la tarde.",
          "her_time": "Tardó: 24 horas",
          "her_message": "hola. ¿qué harás mañana por la noche?",
          "correct_option": "terminando un video, ¿qué onda?",
          "decoys": [
            "¡Hola! Nada, libre para ti. ¿Qué hacemos? 😍",
            "¿Por qué no me escribiste ayer?",
            "Estoy ocupado toda la semana"
          ],
          "allowed_time_indices": [2, 3], # 1h a 2h
          "coach_feedback_correct": "Demuestras que estás ocupado con tus proyectos y devuelves la pregunta con desapego.",
          "coach_feedback_incorrect": "Mostrarte 100% disponible o reclamarle por ayer destruye tu marco de valor."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Deja pasar entre 1h y 2h para equilibrar la balanza de poder."
        },
        {
          "step_id": 13,
          "her_time": "Tardó: 15 min",
          "her_message": "yendo a mr. Jones",
          "correct_option": "¿quién es Jones?",
          "decoys": [
            "Ah, qué divertido, pásala súper",
            "¿A qué hora vas? ¿Puedo ir?",
            "Qué flojera ir de antro"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Humor seco y desentendido ('¿quién es Jones?') que la obliga a explicar que es un club.",
          "coach_feedback_incorrect": "Preguntar si puedes ir o ponerte negativo corta la vibra."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde en un lapso normal."
        },
        {
          "step_id": 14,
          "her_time": "Tardó: 10 min",
          "her_message": "jajaja un club nocturno. [Screenshot de reseñas: 2.5 estrellas]",
          "correct_option": "veo que tiene 2.5 estrellas jajaja",
          "decoys": [
            "Ah, no lo conozco, debe ser genial",
            "Qué mal lugar, no vayas",
            "Jaja qué chistoso"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Te burlas del lugar en sintonía con su reseña, compartiendo el chiste con ella.",
          "coach_feedback_incorrect": "Respuestas aburridas o tomarlo muy en serio."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde en un lapso normal."
        },
        {
          "step_id": 15,
          "her_time": "Tardó: 30 min",
          "her_message": "está prendido, me voy a casa, aburrida soltera jajaja",
          "correct_option": "me imagino. Estaré libre un poco más tarde mañana por la noche, deberías pasar por un trago o dos",
          "decoys": [
            "Qué bueno que te vayas a casa, es peligroso",
            "¿Quieres que vaya a tu casa ahora?",
            "Dime cuándo estás libre y nos vemos en un bar"
          ],
          "allowed_time_indices": [2, 3], # 1h a 2h
          "coach_feedback_correct": "Lanzas la propuesta tranquila de cita en tu espacio (trago) aprovechando su aburrimiento y soltería.",
          "coach_feedback_incorrect": "Ofrecerte a ir a su casa de inmediato suena muy urgido de sexo casual."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Espera de 1h a 2h."
        },
        {
          "step_id": 16,
          "her_time": "Tardó: 15 min",
          "her_message": "ok lo haré",
          "correct_option": "planes esta noche y ya hicimos planes para mañana",
          "decoys": [
            "¡Perfecto! Te paso mi dirección",
            "Genial, avísame cuando salgas",
            "Ok, te espero entonces"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Estableces límites. Ella tardó en confirmar. Dejas claro tu orden y tu tiempo.",
          "coach_feedback_incorrect": "Mostrarte demasiado alegre o sumiso le quita valor a tu tiempo."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde en un lapso normal."
        },
        {
          "step_id": 17,
          "contexto_inicial": "Objeción de último minuto - Test de Citas Pagadas.",
          "her_time": "Tardó: 20 min",
          "her_message": "solo busco citas pagadas para ser honesta, tipo que me pagas si salimos",
          "correct_option": "no pago por sexo ni por citas, y si eso es lo que querías, debiste decirlo desde el principio. Qué aburrido.",
          "decoys": [
            "¿Cuánto cobras por cita? Quizá podamos arreglar... 💸",
            "Qué interesada eres, qué mal de tu parte",
            "Bueno, te invito a cenar y te doy un regalo"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "¡MARCO DE HIERRO! Te retiras de inmediato al ver que busca dinero. Esto demuestra el máximo valor: no te dejas comprar.",
          "coach_feedback_incorrect": "Aceptar negociar o insultarla te devalúa por completo. Retirarse con dignidad es la única opción."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato denota que te afectó su mensaje."
        },
        {
          "step_id": 18,
          "her_time": "Tardó: 15 min",
          "her_message": "bueno, lo siento",
          "correct_option": "¿solo conoces gente por dinero?",
          "decoys": [
            "No te preocupes, te perdono",
            "¿Por qué eres así?",
            "Jaja no pasa nada"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Pregunta de confort y curiosidad sin juzgarla directamente, manteniéndote calmado en tu marco.",
          "coach_feedback_incorrect": "Pedir perdón tú o tratar de minimizar el test rompe el marco."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde con tranquilidad."
        },
        {
          "step_id": 19,
          "her_time": "Tardó: 15 min",
          "her_message": "¿es eso raro? en realidad soy stripper, recién empecé de escort, mi amiga me recomendó eso",
          "correct_option": "¿y crees que diciéndome a unas horas de nuestra cita que solo quieres verte por dinero me va a dar ganas de salir contigo?",
          "decoys": [
            "Ah, eres stripper, qué cool. Vamos",
            "Qué mal que hagas eso",
            "Bueno, entonces salgamos gratis"
          ],
          "allowed_time_indices": [2, 3], # 1h a 2h
          "coach_feedback_correct": "Desafías su lógica de forma asertiva, haciéndola ver que su enfoque es incongruente con generar interés real.",
          "coach_feedback_incorrect": "Aceptar la cita rápido tras enterarte que es stripper o ponerte moralista apaga el chat."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Esperar entre 1h y 2h."
        },
        {
          "step_id": 20,
          "her_time": "Tardó: 15 min",
          "her_message": "jajaja quieres salir conmigo, no te culpo, soy increíble",
          "correct_option": "bueno, definitivamente estás perdiendo puntos ahora mismo. Nos vemos mañana.",
          "decoys": [
            "¡Sí, eres increíble! Te veo mañana",
            "Jaja qué payasa eres",
            "No, ya no quiero verte"
          ],
          "allowed_time_indices": [1, 2],
          "coach_feedback_correct": "Mantienes la compostura, la calificas negativamente con humor ('perdiendo puntos') y dejas abierta la cita con sobriedad.",
          "coach_feedback_incorrect": "Validar su ego o enojarte con insultos destruye tu estatus masculino final."
          , "coach_feedback_time_incorrect": "Fallo de Tiempo: Cierre sólido."
        }
      ]
    }
  ]
}

def generate_html():
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Propuesta de Conversaciones Reales - v{dialogues['version']}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: #141928;
            --text-main: #f0f4f8;
            --text-muted: #94a3b8;
            --accent: #ff3c6e;
            --accent-blue: #3b82f6;
            --green: #10b981;
            --red: #ef4444;
            --border: rgba(255, 255, 255, 0.05);
        }}
        body {{
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 40px 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        h1, h2, h3 {{
            font-family: 'Outfit', sans-serif;
        }}
        .header-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--accent);
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        .header-title h1 {{
            margin: 0;
            font-size: 2rem;
            color: #fff;
        }}
        .header-meta {{
            font-size: 0.8rem;
            color: var(--text-muted);
            text-align: right;
        }}
        .intro-box {{
            background: rgba(255, 60, 110, 0.04);
            border-left: 4px solid var(--accent);
            padding: 20px;
            border-radius: 0 12px 12px 0;
            margin-bottom: 30px;
        }}
        .level-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 40px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        .level-header {{
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding-bottom: 15px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .level-header h2 {{
            color: var(--accent);
            margin: 0;
            font-size: 1.5rem;
        }}
        .step-box {{
            background: rgba(0,0,0,0.25);
            border: 1px solid rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            position: relative;
        }}
        .step-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            border-bottom: 1px dashed rgba(255,255,255,0.05);
            padding-bottom: 8px;
        }}
        .step-number {{
            font-weight: bold;
            color: var(--accent-blue);
            font-size: 1.05rem;
        }}
        .time-badge {{
            background: rgba(16, 185, 129, 0.15);
            color: #a7f3d0;
            font-size: 0.75rem;
            padding: 3px 10px;
            border-radius: 12px;
            font-weight: bold;
        }}
        .chat-bubble-container {{
            display: flex;
            flex-direction: column;
            margin-bottom: 15px;
        }}
        .chat-bubble {{
            padding: 12px 16px;
            border-radius: 14px;
            max-width: 80%;
            font-size: 0.95rem;
            line-height: 1.4;
        }}
        .bubble-her {{
            background: #4c1d95;
            color: white;
            margin-right: auto;
            border-bottom-left-radius: 2px;
        }}
        .chat-time-label {{
            font-size: 0.75rem;
            color: var(--accent);
            font-weight: bold;
            margin-top: 5px;
            margin-left: 6px;
        }}
        .options-list {{
            list-style: none;
            padding: 0;
            margin: 15px 0;
        }}
        .option-item {{
            padding: 12px 14px;
            border-radius: 8px;
            margin-bottom: 8px;
            font-size: 0.9rem;
            border: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .option-correct {{
            background: rgba(16, 185, 129, 0.08);
            border-color: var(--green);
            color: #a7f3d0;
        }}
        .option-decoy {{
            background: rgba(255, 255, 255, 0.02);
            color: var(--text-muted);
        }}
        .dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            flex-shrink: 0;
        }}
        .dot-green {{ background: var(--green); }}
        .dot-grey {{ background: var(--text-muted); }}
        
        .time-options-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
            gap: 8px;
            margin: 15px 0;
        }}
        .time-tick-box {{
            padding: 8px 10px;
            border-radius: 6px;
            font-size: 0.78rem;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.06);
            background: rgba(255,255,255,0.02);
            color: var(--text-muted);
        }}
        .time-tick-winning {{
            border-color: var(--green);
            background: rgba(16, 185, 129, 0.15);
            color: #a7f3d0;
            font-weight: bold;
        }}
        .feedback-container {{
            margin-top: 20px;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border);
        }}
        .feedback {{
            font-size: 0.85rem;
            padding: 12px 15px;
            line-height: 1.5;
        }}
        .feedback-correct {{
            background: rgba(16, 185, 129, 0.04);
            border-left: 4px solid var(--green);
            color: #a7f3d0;
        }}
        .feedback-incorrect {{
            background: rgba(239, 68, 68, 0.04);
            border-left: 4px solid var(--red);
            color: #fca5a5;
            border-top: 1px solid var(--border);
        }}
        
        /* Calificaciones */
        .rating-box {{
            display: flex;
            gap: 10px;
            margin-top: 18px;
            align-items: center;
            border-top: 1px solid rgba(255,255,255,0.03);
            padding-top: 12px;
        }}
        .rating-btn {{
            background: rgba(255,255,255,0.02);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 6px 16px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.82rem;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }}
        .rating-btn:hover {{
            background: rgba(255,255,255,0.05);
            color: var(--text-main);
        }}
        .rating-btn.active-like {{
            background: rgba(16, 185, 129, 0.15);
            border-color: var(--green);
            color: #a7f3d0;
            font-weight: bold;
        }}
        .rating-btn.active-dislike {{
            background: rgba(239, 68, 68, 0.15);
            border-color: var(--red);
            color: #fca5a5;
            font-weight: bold;
        }}
        .copy-feedback-btn {{
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            font-family: Outfit, sans-serif;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
            transition: transform 0.2s;
        }}
        .copy-feedback-btn:active {{
            transform: scale(0.97);
        }}
        
        .qa-section {{
            background: rgba(59, 130, 246, 0.03);
            border: 1px solid rgba(59, 130, 246, 0.1);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 40px;
        }}
        .qa-section h2 {{
            color: var(--accent-blue);
            margin-top: 0;
            border-bottom: 1px solid rgba(59, 130, 246, 0.15);
            padding-bottom: 10px;
        }}
        .qa-item {{
            margin-bottom: 20px;
        }}
        .qa-question {{
            font-weight: bold;
            color: #fff;
            margin-bottom: 5px;
        }}
        .qa-answer {{
            color: var(--text-muted);
            font-size: 0.92rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <div class="header-title">
                <h1>Propuesta de Conversaciones Reales</h1>
            </div>
            <div class="header-meta">
                <strong>Versión:</strong> {dialogues['version']}<br>
                <strong>Actualizado:</strong> {dialogues['updated_at']}
            </div>
        </div>
        
        <div class="intro-box">
            <strong>Revolución Conversacional v1.1:</strong>
            <ul>
                <li><strong>100% Casos Reales e Íntegros:</strong> Las conversaciones se extrajeron de forma completa y continua de la base de datos SQLite (Bumble, Hinge y Tinder). No hay fusiones artificiales de finales de otros chats. Los niveles tienen longitudes reales (desde 9 hasta 20 pasos).</li>
                <li><strong>Calidad de Traducción (Español Latino):</strong> Se eliminaron todas las traducciones mecánicas provocadas por errores de dictado en inglés. Las frases han sido adaptadas a un lenguaje fluido, natural y de alta efectividad de mensajería latinoamericana.</li>
                <li><strong>Tiempos de Respuesta de la Chica:</strong> Se muestra el tiempo exacto que la chica se demoró en responder en cada paso, dando contexto real para tu calibración de tiempo.</li>
                <li><strong>Feedback unificado 👍 / 👎:</strong> Califica cada paso directamente. El botón de arriba te permite copiar tu feedback para enviármelo.</li>
            </ul>
        </div>
        
        <div class="qa-section">
            <h2>💡 Consultas y Sugerencias de Arquitectura</h2>
            <div class="qa-item">
                <div class="qa-question">1. ¿Cómo hacer que SQLite funcione como una Base de Datos Vectorial (estilo ChromaDB) sin dependencias pesadas?</div>
                <div class="qa-answer">
                    Podemos emular ChromaDB directamente en SQLite usando el módulo nativo <strong>FTS5 (Full-Text Search 5)</strong>, el cual ya he configurado en la inicialización de la base de datos.
                    FTS5 crea índices virtuales de texto y permite consultas rápidas por relevancia semántica usando la función <code>MATCH</code> y el ordenamiento automático <code>rank</code> basado en el algoritmo BM25 (relevancia de términos).
                    <br><br>
                    <strong>Para dar el siguiente paso de vectorización real (búsqueda de embeddings de similitud coseno):</strong>
                    Podemos compilar o habilitar la extensión <code>sqlite-vss</code> (Vector Similarity Search). VSS permite almacenar vectores floats (embeddings de Gemini o OpenAI) directamente en SQLite y realizar búsquedas de vecino más cercano (KNN) a alta velocidad en un solo archivo local.
                </div>
            </div>
            <div class="qa-item">
                <div class="qa-question">2. ¿Qué sugerencias tienes para que Natalia se entrene y entienda el contexto a la perfección?</div>
                <div class="qa-answer">
                    <strong>A. Alimentación de Roles y Contextos:</strong> Cada caso en SQLite debe ir acompañado de una metadata limpia: ELO social de la chica (resistencia inicial), tipo de perfil (strip-club, ejecutiva, etc.), y justificación clínica de por qué cada respuesta es ganadora o perdedora.
                    <br>
                    <strong>B. Base de Conocimiento Local (RAG):</strong> Configurar a Natalia para que, antes de generar opciones o dar feedback en el chat, ejecute una consulta SQLite semántica (usando FTS5) para extraer los 3 casos reales más similares al contexto actual y se alinee a esas respuestas humanas exitosas.
                </div>
            </div>
        </div>
"""

    for lvl in dialogues["levels"]:
        html_content += f"""
        <div class="level-card">
            <div class="level-header">
                <h2>{lvl['level_name']} (Chica: {lvl['girl_name']})</h2>
                <span style="color: var(--accent); font-family: Outfit; font-weight: bold; font-size: 1.1rem;">Nivel {lvl['level_id']}</span>
            </div>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin: -10px 0 20px 0;">{lvl['description']}</p>
        """
        
        for step in lvl["steps"]:
            ctx_html = f"<div style='font-size:0.85rem; color:var(--accent-blue); margin-bottom:10px;'>Contexto: {step['contexto_inicial']}</div>" if "contexto_inicial" in step else ""
            
            # Generar la grilla de opciones de tiempo
            time_ticks_html = ""
            winning_labels = []
            for idx, label in enumerate(TIME_TICKS):
                is_winning = idx in step["allowed_time_indices"]
                css_class = "time-tick-box time-tick-winning" if is_winning else "time-tick-box"
                check_icon = " ✓ Ganador" if is_winning else ""
                time_ticks_html += f'<div class="{css_class}">{label}{check_icon}</div>'
                if is_winning:
                    winning_labels.append(label)
            
            winning_range_str = " o ".join(winning_labels)
            
            html_content += f"""
            <div class="step-box" id="step-box-{lvl['level_id']}-{step['step_id']}">
                <div class="step-header">
                    <span class="step-number">Paso {step['step_id']}</span>
                    <span class="time-badge">Tiempos correctos: {winning_range_str}</span>
                </div>
                {ctx_html}
                <div class="chat-bubble-container">
                    <div class="chat-bubble bubble-her">
                        💬 {step['her_message']}
                    </div>
                    <div class="chat-time-label">⏱️ {step['her_time']}</div>
                </div>
                
                <h4 style="margin: 10px 0 5px 0; font-size:0.88rem; color: var(--text-main);">Opciones de Respuesta:</h4>
                <ul class="options-list">
                    <li class="option-item option-correct">
                        <span class="dot dot-green"></span>
                        <strong>(Correcta):</strong> {step['correct_option']}
                    </li>
            """
            
            for dec in step["decoys"]:
                html_content += f"""
                    <li class="option-item option-decoy">
                        <span class="dot dot-grey"></span>
                        <strong>(Decoy):</strong> {dec}
                    </li>
                """
                
            html_content += f"""
                </ul>

                <h4 style="margin: 15px 0 5px 0; font-size:0.85rem; color: var(--text-muted);">Opciones del Deslizador de Tiempo:</h4>
                <div class="time-options-grid">
                    {time_ticks_html}
                </div>
                
                <div class="feedback-container">
                    <div class="feedback feedback-correct">
                        <strong>✓ Si respondes bien:</strong> {step['coach_feedback_correct']}
                    </div>
                    <div class="feedback feedback-incorrect">
                        <strong>✗ Si fallas (Mensaje):</strong> {step['coach_feedback_incorrect']}
                        <br><br>
                        <strong>⏱️ Si fallas (Tiempo):</strong> {step['coach_feedback_time_incorrect']}
                    </div>
                </div>
                
                <div class="rating-box">
                    <span style="font-size: 0.8rem; color: var(--text-muted);">¿Qué tal este paso?</span>
                    <button class="rating-btn" id="like-btn-{lvl['level_id']}-{step['step_id']}" onclick="rateStep({lvl['level_id']}, {step['step_id']}, 'like')">👍 Me gusta</button>
                    <button class="rating-btn" id="dislike-btn-{lvl['level_id']}-{step['step_id']}" onclick="rateStep({lvl['level_id']}, {step['step_id']}, 'dislike')">👎 Cambiar / Mejorar</button>
                </div>
            </div>
            """
            
        html_content += "</div>"
        
    html_content += """
    </div>
    
    <script>
        // Sistema de calificación dinámico guardado en LocalStorage
        function rateStep(levelId, stepId, rating) {
            const key = `step_rating_${levelId}_${stepId}`;
            const currentRating = localStorage.getItem(key);
            
            const likeBtn = document.getElementById(`like-btn-${levelId}-${stepId}`);
            const dislikeBtn = document.getElementById(`dislike-btn-${levelId}-${stepId}`);
            
            if (currentRating === rating) {
                localStorage.removeItem(key);
                likeBtn.classList.remove('active-like');
                dislikeBtn.classList.remove('active-dislike');
            } else {
                localStorage.setItem(key, rating);
                if (rating === 'like') {
                    likeBtn.classList.add('active-like');
                    dislikeBtn.classList.remove('active-dislike');
                } else {
                    dislikeBtn.classList.add('active-dislike');
                    likeBtn.classList.remove('active-like');
                }
            }
        }
        
        // Cargar calificaciones guardadas en el inicio
        window.addEventListener('DOMContentLoaded', () => {
            const keys = Object.keys(localStorage);
            keys.forEach(key => {
                if (key.startsWith('step_rating_')) {
                    const parts = key.split('_');
                    const l = parts[2];
                    const s = parts[3];
                    const rating = localStorage.getItem(key);
                    if (rating) {
                        const btn = document.getElementById(`${rating}-btn-${l}-${s}`);
                        if (btn) {
                            btn.classList.add(rating === 'like' ? 'active-like' : 'active-dislike');
                        }
                    }
                }
            });
        });
        
        function copyFeedbackJSON() {
            const feedback = {};
            let count = 0;
            const keys = Object.keys(localStorage);
            keys.forEach(key => {
                if (key.startsWith('step_rating_')) {
                    const parts = key.split('_');
                    const l = parts[2];
                    const s = parts[3];
                    const rating = localStorage.getItem(key);
                    if (rating) {
                        if (!feedback[l]) feedback[l] = {};
                        feedback[l][s] = rating;
                        count++;
                    }
                }
            });
            
            if (count === 0) {
                alert("Por favor, califica al menos una pregunta antes de copiar.");
                return;
            }
            
            const jsonString = JSON.stringify(feedback, null, 2);
            navigator.clipboard.writeText(jsonString).then(() => {
                alert(`¡Feedback copiado al portapapeles! (${count} preguntas calificadas). Pégalo en nuestro chat para que lo revise.`);
            }).catch(err => {
                console.error("Error al copiar:", err);
                alert("Error al copiar al portapapeles.");
            });
        }
    </script>
</body>
</html>
"""

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated proposed HTML review file at: {HTML_PATH}")

if __name__ == "__main__":
    generate_html()
