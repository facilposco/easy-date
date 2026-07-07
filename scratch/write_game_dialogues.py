import json

dialogues_data = {
  "game_title": "Simulador de Juego de Texto Real - v1.0",
  "levels": [
    {
      "level_id": 1,
      "girl_name": "Natalia",
      "name": "Nivel 1: El Match Directo (Bumble)",
      "description": "Natalia tiene rulos, es bajita y responde de forma coqueta y corta. Mantén un roleplay divertido y lidera hacia el número.",
      "starting_lives": 4,
      "steps": [
        {
          "step_id": 1,
          "her_message": "[Chat vacío - Envías abridor]",
          "her_time": "Inicio de conversación",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "hey chica problema", "is_correct": True},
            {"text": "¡Hola hermosa! ¿Cómo estás hoy? 😍", "is_correct": False},
            {"text": "Hola Natalia, qué lindo tu perfil. ¿Qué tal tu semana?", "is_correct": False},
            {"text": "Hola, ¿buscas algo serio por aquí?", "is_correct": False}
          ],
          "coach_feedback_correct": "¡Excelente abridor! Lanzas un reto juguetón llamándola 'chica problema' que la desmarca de la aburrida pila de mensajes.",
          "coach_feedback_incorrect": "Demasiado sumiso o genérico. El clásico saludo no despierta ningún interés.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato denota prisa; esperar más de 2 horas en Bumble enfría la ventana de atención."
        },
        {
          "step_id": 2,
          "her_message": "esa soy yo totalmente jaja ¿cómo va tu día?",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "increíble, acabo de terminar de entrenar y ando poniéndome en forma para nuestra cita", "is_correct": True},
            {"text": "Muy bien, aquí en la oficina trabajando. ¿Y tú?", "is_correct": False},
            {"text": "Normal, nada especial. ¿Qué haces?", "is_correct": False},
            {"text": "Cansado, ojalá estuvieras aquí para relajarme", "is_correct": False}
          ],
          "coach_feedback_correct": "Asumes la cita de inmediato con alta vibración y demuestras que eres un hombre activo.",
          "coach_feedback_incorrect": "Responder lógicamente sobre tu trabajo o quejarte de tu cansancio destruye el misterio.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Ella tardó 15 min. Si contestas de inmediato, te ves desesperado. Si tardas más de 2 horas, perderás el impulso y la fluidez."
        },
        {
          "step_id": 3,
          "her_message": "me gusta eso, perfecto ¿dónde vives? yo en brickell ¿y tú?",
          "her_time": "Tardó: 20 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "perfecto para que nuestro romance florezca ja ja", "is_correct": True},
            {"text": "Vivo en Downtown, súper cerca. Deberíamos vernos ya.", "is_correct": False},
            {"text": "Yo vivo en Kendall, un poco lejos. ¿Tienes auto?", "is_correct": False},
            {"text": "Vivo en Brickell también. ¿En qué edificio estás?", "is_correct": False}
          ],
          "coach_feedback_correct": "Tomas su dato geográfico y lo usas para redoblar el chiste del 'romance', evitando sonar como un interrogatorio de mudanza.",
          "coach_feedback_incorrect": "Entrar en detalles logísticos o presionar para verse de inmediato le quita la vibra lúdica.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder instantáneamente te quita valor. Esperar más de 2 horas romperá el ritmo."
        },
        {
          "step_id": 4,
          "her_message": "jaja qué loco. ¿te gusta el vino? es mi favorito",
          "her_time": "Tardó: 30 min",
          "allowed_time_indices": [2, 3], # 1h o 2h
          "options": [
            {"text": "bien, deberíamos compartir una botella pronto", "is_correct": True},
            {"text": "¡A mí también! Me encanta el Cabernet Sauvignon. ¿A ti?", "is_correct": False},
            {"text": "No me gusta el alcohol, prefiero ir al cine.", "is_correct": False},
            {"text": "Te invito una botella hoy mismo en la noche a mi casa", "is_correct": False}
          ],
          "coach_feedback_correct": "Aceptas su gusto e introduces la propuesta indirecta de cita ('compartir una botella pronto') con naturalidad.",
          "coach_feedback_incorrect": "Ponerse demasiado técnico sobre vinos o invitarla directo a tu casa de inmediato apaga la atracción.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato muestra prisa. Esperar 1h o 2h asienta la propuesta."
        },
        {
          "step_id": 5,
          "her_message": "seguro ¿cuánto tiempo llevas soltero?",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "como un año ya", "is_correct": True},
            {"text": "Uff, hace mucho, me han roto el corazón varias veces 🥺", "is_correct": False},
            {"text": "Acabo de terminar hace una semana, ando despechado", "is_correct": False},
            {"text": "No me gusta estar soltero, busco novia urgente", "is_correct": False}
          ],
          "coach_feedback_correct": "Respuesta limpia, directa y con estabilidad emocional. Un año muestra madurez.",
          "coach_feedback_incorrect": "Hacer drama sobre tus ex o demostrar que buscas novia con urgencia asusta a cualquiera.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder al instante (Ahora mismo) denota desesperación. Espera de 15m a 1h."
        },
        {
          "step_id": 6,
          "her_message": "¿y qué estás buscando ahora?",
          "her_time": "Tardó: 10 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "una chica genial con la que tenga química ¿y tú?", "is_correct": True},
            {"text": "Busco una relación seria que termine en matrimonio", "is_correct": False},
            {"text": "Solo busco algo casual de una noche", "is_correct": False},
            {"text": "Lo que sea que surja, no tengo planes", "is_correct": False}
          ],
          "coach_feedback_correct": "Encuadre equilibrado. Buscas química y pasarla bien, sin sonar cerrado pero tampoco urgido.",
          "coach_feedback_incorrect": "Exigir matrimonio asusta; proponer sexo de una noche directamente suena vulgar.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato te resta misterio. Espera de 15m a 1h."
        },
        {
          "step_id": 7,
          "her_message": "jaja yo igual, nada súper serio pero química primero",
          "her_time": "Tardó: 2 dias",
          "allowed_time_indices": [5, 6], # 12h o 24h (para 2 días de retraso)
          "options": [
            {"text": "me alegra que estemos en la misma sintonía ¿te gusta el vino blanco?", "is_correct": True},
            {"text": "Perdón por tardar tanto, andaba súper ocupado", "is_correct": False},
            {"text": "Sí, andaba ocupado. ¿Qué hiciste en estos días?", "is_correct": False},
            {"text": "Jaja te tardaste mucho en contestar", "is_correct": False}
          ],
          "coach_feedback_correct": "Ignoras su retraso, no te disculpas por nada y retomas la logística del vino de forma tranquila.",
          "coach_feedback_incorrect": "Reclamar por su demora o pedir disculpas por el tiempo demuestra inseguridad extrema.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Si ella tardó 2 días, debes darle espacio. Contestar en 12h o 24h demuestra que tienes tu propio ritmo de vida."
        },
        {
          "step_id": 8,
          "her_message": "mucho, pero prefiero los tintos",
          "her_time": "Tardó: 25 min",
          "allowed_time_indices": [2, 3], # 1h o 2h
          "options": [
            {"text": "démosle una oportunidad y compartamos una botella entonces", "is_correct": True},
            {"text": "Qué mal, a mí solo me gusta el blanco", "is_correct": False},
            {"text": "Bueno, entonces compramos una de cada uno hoy", "is_correct": False},
            {"text": "Deberías probar el blanco, te va a gustar", "is_correct": False}
          ],
          "coach_feedback_correct": "Cierre directo de la cita. Aceptas su gusto (tinto) y propones compartir la botella concretamente.",
          "coach_feedback_incorrect": "Ponerte a discutir sobre vinos o insistir en el blanco devalúa tu empatía.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Deja pasar entre 1h y 2h para mantener el ritmo maduro."
        },
        {
          "step_id": 9,
          "her_message": "suena genial ¿qué noches estás libre próximamente?",
          "her_time": "Tardó: 20 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "lo sabré mañana bien. pásame tu número para coordinar", "is_correct": True},
            {"text": "Estoy libre hoy, mañana y el viernes, ¿cuándo quieres?", "is_correct": False},
            {"text": "No sé, ando muy ocupado esta semana", "is_correct": False},
            {"text": "Dame tu WhatsApp y te aviso", "is_correct": False}
          ],
          "coach_feedback_correct": "Demuestras que tu tiempo es valioso (no sabes tu agenda de memoria) y lideras pidiendo el número para salir de la app.",
          "coach_feedback_incorrect": "Mostrarte disponible 24/7 devalúa tu estatus; pedir el WhatsApp de forma seca rompe la fluidez.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de golpe denota impaciencia. Espera al menos 15 minutos."
        },
        {
          "step_id": 10,
          "her_message": "[Su número] jaja me encanta cómo lo dices",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "Excelente, te escribo en la noche. Cuídate 😉", "is_correct": True},
            {"text": "¡SIII! Te escribo ya mismo 😍", "is_correct": False},
            {"text": "Ok te guardo", "is_correct": False},
            {"text": "Gracias hermosa", "is_correct": False}
          ],
          "coach_feedback_correct": "Cierre y retirada impecable. Mantienes el misterio y concretas el paso a WhatsApp.",
          "coach_feedback_incorrect": "Sobre-excitación con corazones rompe la atracción masculina construida.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Confirmación sobria y tranquila en un lapso normal."
        }
      ]
    },
    {
      "level_id": 2,
      "girl_name": "Sofía",
      "name": "Nivel 2: El Banter y las Pruebas (Hinge)",
      "description": "Sofía es expresiva, lanza pruebas culturales y de congruencia. Debes sostener tu marco con humor exagerado.",
      "starting_lives": 3,
      "steps": [
        {
          "step_id": 1,
          "her_message": "[Chat vacío - Envías abridor]",
          "her_time": "Inicio de conversación",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "Gracias Sofía, tú tampoco te ves nada mal. Entonces, ¿esta es la parte donde empezamos un romance fugaz, nos casamos y nos divorciamos en tiempo récord? 🤔", "is_correct": True},
            {"text": "Hola Sofía, gracias por el match. Eres hermosa. 😍", "is_correct": False},
            {"text": "Hola, ¿cómo estás? Qué gusto coincidir.", "is_correct": False},
            {"text": "Hola guapa, ¿qué te gustó de mi perfil?", "is_correct": False}
          ],
          "coach_feedback_correct": "¡Abridor de oro! Creas un escenario cómico de boda/divorcio rápido que le da material infinito para seguirte el juego.",
          "coach_feedback_incorrect": "Saludos planos o halagos gratuitos te ponen en la fila de los aburridos de inmediato.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Esperar demasiado reduce el impacto del match."
        },
        {
          "step_id": 2,
          "her_message": "Mi mejor amiga me lo tradujo y entendí lo que dijiste, jaja. ¿Eres de por aquí?",
          "her_time": "Tardó: 20 min",
          "allowed_time_indices": [2, 3], # 1h o 2h
          "options": [
            {"text": "Eso significa que vivo aquí parte del año pero viajo bastante. Parece que te vendría mejor que hablemos en español.", "is_correct": True},
            {"text": "Jaja qué bueno. Sí, vivo aquí hace 5 años.", "is_correct": False},
            {"text": "Ah no hablas inglés, qué mal. Sí, soy de aquí.", "is_correct": False},
            {"text": "¿Tu amiga es bonita? Jaja. Sí, vivo en Brickell.", "is_correct": False}
          ],
          "coach_feedback_correct": "Demuestras estatus (viajas) y le propones de forma caballerosa cambiar a su idioma para facilitar las cosas.",
          "coach_feedback_incorrect": "Respuestas literales de geografía que matan la tensión juguetona.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Ella metió a su amiga en la conversación. Esperar 1h o más equilibra la balanza."
        },
        {
          "step_id": 3,
          "her_message": "Oye, ¡qué atrevido! Jaja. Sí hablo inglés, fui a la universidad, por favor... Dios mío, qué loco estás.",
          "her_time": "Tardó: 25 min",
          "allowed_time_indices": [2, 3], # 1h o 2h
          "options": [
            {"text": "Jaja, dijiste que tu amiga te tradujo, solo intentaba ayudarte. 😂 Me alegra ver que eres segura, educada y con carácter.", "is_correct": True},
            {"text": "Perdón, no quise ofenderte de verdad 🥺", "is_correct": False},
            {"text": "Jaja yo no soy loco, tú eres la loca", "is_correct": False},
            {"text": "¿Qué tiene de malo ser chico blanco?", "is_correct": False}
          ],
          "coach_feedback_correct": "No te disculpas. Reencuadras tu comentario como ayuda y le das cumplidos condicionados a su personalidad ('segura, educada, carácter').",
          "coach_feedback_incorrect": "Pedir disculpas de inmediato mata tu estatus de hombre seguro.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Cuando una chica te lanza un test dramático, contestar rápido te hace ver reactivo. Espera 1h o 2h."
        },
        {
          "step_id": 4,
          "her_message": "Es que solo me tradujo 'chico blanco' y volteé los ojos.",
          "her_time": "Tardó: 40 min",
          "allowed_time_indices": [3, 4], # 2h o 4h
          "options": [
            {"text": "Por suerte hablo fluido tanto 'chico blanco' como 'latina con carácter', así que no ocuparemos traductor en nuestras citas. Aunque tal vez ocupemos un guardaespaldas para protegerme de tus encantos. 😇", "is_correct": True},
            {"text": "Jaja, qué chistosa. Pásame tu número.", "is_correct": False},
            {"text": "No soy como los otros chicos blancos, te lo prometo", "is_correct": False},
            {"text": "¿Por qué volteaste los ojos? ¿Te caigo mal?", "is_correct": False}
          ],
          "coach_feedback_correct": "Excelente calibración. Adoptas el chiste cultural y asumes la cita pintándote a ti mismo como el 'inocente' de forma divertida.",
          "coach_feedback_incorrect": "Explicaciones defensivas sobre tu raza o forzar el número muy rápido.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Esperar entre 2h y 4h le da espacio al chiste y demuestra desapego."
        },
        {
          "step_id": 5,
          "her_message": "Bueno, Douglas. Jaja.",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "Gracias. Me alegra que lo apruebes. Dime Sofía, ¿es tan divertido bromear contigo en persona como lo es por chat?", "is_correct": True},
            {"text": "Jaja sí. ¿Qué haces hoy?", "is_correct": False},
            {"text": "¿Cuándo salimos a comprobarlo?", "is_correct": False},
            {"text": "Jaja obvio que sí", "is_correct": False}
          ],
          "coach_feedback_correct": "Tomas su respuesta y abres la puerta para la transición al mundo real de forma fluida.",
          "coach_feedback_incorrect": "Presionar de forma devalúa tu atracción; respuestas planas rompen la tensión.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato te hace ver sin planes."
        },
        {
          "step_id": 6,
          "her_message": "Aprecio tu confianza. Mi número es [Número]. ¿Cuál es el tuyo?",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "Aquí tienes el mío. Te escribo en un rato 😉", "is_correct": True},
            {"text": "¡SIII! Te agrego ya y te llamo", "is_correct": False},
            {"text": "Ok, te hablo por WhatsApp ahora", "is_correct": False},
            {"text": "Gracias linda", "is_correct": False}
          ],
          "coach_feedback_correct": "Intercambias el número con tranquilidad sin verte desesperado.",
          "coach_feedback_incorrect": "Demostrar desesperación al recibir el número devalúa tu valor.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde con calma, no al instante."
        },
        {
          "step_id": 7,
          "her_message": "Hola, agendado. Tengo que conseguir un teléfono de emergencia, así que de verdad disculpa si desaparezco de la nada jaja",
          "her_time": "Tardó: 20 min",
          "allowed_time_indices": [2, 3], # 1h o 2h
          "options": [
            {"text": "No te preocupes, si es más fácil coordinar nuestra primera cita por aquí rápido, no tengo problema. ¿Cómo andas de tiempos estos días?", "is_correct": True},
            {"text": "Uy qué mal, ojalá lo arregles pronto. Avísame.", "is_correct": False},
            {"text": "No te preocupes, te espero lo que sea necesario", "is_correct": False},
            {"text": "¿Por qué falla tu teléfono? ¿Qué marca es?", "is_correct": False}
          ],
          "coach_feedback_correct": "Aprovechas su excusa del teléfono para proponer organizar la cita directamente sin perder tiempo en chats eternos.",
          "coach_feedback_incorrect": "Charlas aburridas sobre teléfonos o sumisión extrema.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato te hace ver pegado a la pantalla."
        },
        {
          "step_id": 8,
          "her_message": "Comprar un teléfono es mi prioridad ahora, ando corriendo con eso. ¡Mira mi nueva funda! Está padrísima. [Foto de funda]",
          "her_time": "Tardó: 50 min",
          "allowed_time_indices": [3, 4], # 2h o 4h
          "options": [
            {"text": "Ando ocupado durante el día, pero podría hacerme un espacio para tomar algo y charlar un rato en la noche, ya sea hoy o mañana.", "is_correct": True},
            {"text": "¡Qué linda funda! Te combina muy bien 😍", "is_correct": False},
            {"text": "Ah bueno, avísame cuando tengas libre", "is_correct": False},
            {"text": "Mejor dime qué día estás libre tú y nos vemos", "is_correct": False}
          ],
          "coach_feedback_correct": "Ignoras el desvío de la funda y mantienes tu liderazgo proponiendo opciones específicas de días y tu alta ocupación.",
          "coach_feedback_incorrect": "Ponerte a hablar de fundas te manda directo a la zona de amigos virtuales.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Esperar entre 2h y 4h demuestra que tienes tu propia vida."
        },
        {
          "step_id": 9,
          "her_message": "Jaja, me gusta la idea de tomar algo. Mañana en la noche me queda perfecto.",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "Hecho. Conozco un bar secreto muy cool cerca de Brickell. Te veo allá a las 8:30 pm. Ponte guapa. 😉", "is_correct": True},
            {"text": "¡Genial! ¿A dónde te gustaría ir?", "is_correct": False},
            {"text": "Perfecto, dime dónde nos vemos", "is_correct": False},
            {"text": "¡Súper! Paso por ti a tu casa a las 8:00 pm", "is_correct": False}
          ],
          "coach_feedback_correct": "Liderazgo total: decides el lugar, la hora, y le pones un desafío de broma ('ponte guapa').",
          "coach_feedback_incorrect": "Preguntar 'a dónde quieres ir' le pasa la carga de decisión a ella, mostrando falta de liderazgo.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Cierra la cita en un lapso normal."
        },
        {
          "step_id": 10,
          "her_message": "¡Trato hecho! Ya agendado, nos vemos mañana a las 8:30 pm.",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "Listo, nos vemos allá. Cuídate.", "is_correct": True},
            {"text": "¡No puedo esperar para verte! 😍", "is_correct": False},
            {"text": "Ok, avísame cuando salgas para allá", "is_correct": False},
            {"text": "¿Segura que no me vas a cancelar?", "is_correct": False}
          ],
          "coach_feedback_correct": "Confirmación sobria y masculina. Cierras el trato sin parecer necesitado.",
          "coach_feedback_incorrect": "Mostrar inseguridad o emoción devalúa tu atractivo final.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Cierre rápido y directo."
        }
      ]
    },
    {
      "level_id": 3,
      "girl_name": "Camila",
      "name": "Nivel 3: El Estira y Afloja (Tinder)",
      "description": "Conversación completa de Lss_cULdgPs.json. Tensión calibrada, doble cita con perros y paso rápido a WhatsApp.",
      "starting_lives": 2,
      "steps": [
        {
          "step_id": 1,
          "her_message": "[Chat vacío - Envías abridor]",
          "her_time": "Inicio de conversación",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "hey chica problema", "is_correct": True},
            {"text": "Qué lindo perro tienes, ¿cómo se llama?", "is_correct": False},
            {"text": "Hola Camila, me encantaron tus fotos de la playa", "is_correct": False},
            {"text": "Hola guapa, ¿qué haces hoy?", "is_correct": False}
          ],
          "coach_feedback_correct": "El abridor 'hey chica problema' funciona muy bien con chicas coquetas en Tinder para retar su atención.",
          "coach_feedback_incorrect": "Abrir hablando de su perro te hace ver predecible y aburrido.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder en un lapso normal (15m a 1h)."
        },
        {
          "step_id": 2,
          "her_message": "holis 💋",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "me gusta tu estilo", "is_correct": True},
            {"text": "¿Cómo estás linda? 😍", "is_correct": False},
            {"text": "¿Qué haces por Tinder?", "is_correct": False},
            {"text": "Hola, qué cortante jaja", "is_correct": False}
          ],
          "coach_feedback_correct": "Cumplido condicionado. 'Me gusta tu estilo' es relajado, no valida su belleza física y mantiene el flirteo.",
          "coach_feedback_incorrect": "Poner corazones o quejarse de su brevedad muestra debilidad.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato te hace ver muy disponible."
        },
        {
          "step_id": 3,
          "her_message": "gracias, me gusta tu perro. Los perros son increíbles. ¿Cómo estás hoy?",
          "her_time": "Tardó: 20 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "sí, es el mejor. ¿El de tu foto es tuyo?", "is_correct": True},
            {"text": "Estoy bien gracias, trabajando mucho. ¿Y tú?", "is_correct": False},
            {"text": "¡Sí! Los perros son lo mejor del mundo mundial", "is_correct": False},
            {"text": "Jaja gracias, mi perro liga más que yo", "is_correct": False}
          ],
          "coach_feedback_correct": "Validas a tu mascota con sobriedad y devuelves la pregunta sobre el suyo para mantener el confort.",
          "coach_feedback_incorrect": "Auto-deprecarse o hablar de trabajo aburrido rompe la vibra juguetona.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde en un lapso normal."
        },
        {
          "step_id": 4,
          "her_message": "sí, es un mini caniche",
          "her_time": "Tardó: 20 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "genial, podemos hacer una cita doble con ellos", "is_correct": True},
            {"text": "Qué bonito. ¿Cómo se llama?", "is_correct": False},
            {"text": "Ah, a mí no me gustan mucho los caniches", "is_correct": False},
            {"text": "Deberíamos juntar a los perros hoy mismo", "is_correct": False}
          ],
          "coach_feedback_correct": "Propuesta inteligente. La 'cita doble' con las mascotas es relajada y de bajísima presión.",
          "coach_feedback_incorrect": "Hacer preguntas de entrevista aburridas estanca el chat.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder muy rápido te hace ver ansioso."
        },
        {
          "step_id": 5,
          "her_message": "jajaja suena divertido",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "ojalá se lleven tan bien como nosotros lo haremos", "is_correct": True},
            {"text": "Sí, jaja. ¿Qué día puedes?", "is_correct": False},
            {"text": "Genial, pásame tu número", "is_correct": False},
            {"text": "Espero que tu perro no muerda al mío", "is_correct": False}
          ],
          "coach_feedback_correct": "Tensión calibrada. Proyectas de forma juguetona que ustedes dos se llevarán muy bien en la cita.",
          "coach_feedback_incorrect": "Acelerar la logística demasiado rápido corta la vibra del juego.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato te quita valor."
        },
        {
          "step_id": 6,
          "her_message": "seguro que sí. ¿Qué te gusta hacer para divertirte en Miami? Y espero que no te moleste mi atrevimiento, pero ¿me darías tu número?",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "dirijo un negocio y me mantengo bastante ocupado, disfruto viajar, ir al gym, leer y varias actividades atrevidas. Solo me falta un poco de Camila en mi vida. Mi número es [Número], me gusta el atrevimiento 😉", "is_correct": True},
            {"text": "Claro, mi número es [WhatsApp]. Escríbeme ya.", "is_correct": False},
            {"text": "Me gusta salir de fiesta y la playa. Pásame el tuyo mejor.", "is_correct": False},
            {"text": "¡Sí obvio! Toma: [WhatsApp]. ¿Qué hacemos hoy?", "is_correct": False}
          ],
          "coach_feedback_correct": "Demuestras alto valor (negocio/ocupado) e introduces tensión al entregar el contacto de forma madura.",
          "coach_feedback_incorrect": "Entregar el número de forma seca o mostrar desesperación debilita tu marco.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde con calma."
        },
        {
          "step_id": 7,
          "her_message": "hola guapo, soy Camila",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "ah, la chica linda del caniche", "is_correct": True},
            {"text": "¡Hola hermosa! Qué gusto que me escribas 😍", "is_correct": False},
            {"text": "Hola Camila, ¿cómo estás?", "is_correct": False},
            {"text": "Hola, ¿qué andas haciendo?", "is_correct": False}
          ],
          "coach_feedback_correct": "Saludas con seguridad y un cumplido condicionado juguetón, recordando su mascota.",
          "coach_feedback_incorrect": "Saludos urgidos o planos. Mantén la vibra arriba.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato te hace ver pegado a la pantalla."
        },
        {
          "step_id": 8,
          "her_message": "bueno sí, voy por la vida con mi pelo de colores y mi perro jaja",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "no me emociones demasiado 😉", "is_correct": True},
            {"text": "Jaja te ves muy bien con ese cabello", "is_correct": False},
            {"text": "¿Por qué te pintas el cabello de colores?", "is_correct": False},
            {"text": "Jaja qué chistosa eres", "is_correct": False}
          ],
          "coach_feedback_correct": "Desafías su autodescripción de manera divertida, frenando un poco su ego de forma sutil.",
          "coach_feedback_incorrect": "Halagar su estilo directamente o cuestionarlo destruye la vibra coqueta.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato le da demasiada atención a su físico."
        },
        {
          "step_id": 9,
          "her_message": "jaja no prometo nada... ¿y qué plan tienes para esta noche?",
          "her_time": "Tardó: 45 min",
          "allowed_time_indices": [3, 4], # 2h o 4h
          "options": [
            {"text": "pensaba tomar una copa de vino tinto en mi balcón, ando tranquilo. ¿Te apuntas a compartir la botella?", "is_correct": True},
            {"text": "Dime tú qué quieres hacer y yo te sigo", "is_correct": False},
            {"text": "¿Quieres ir de antro o a cenar a un lugar caro?", "is_correct": False},
            {"text": "Nada, aburrido en casa. ¿Quieres venir a acostarte?", "is_correct": False}
          ],
          "coach_feedback_correct": "Propuesta relajada y de alto valor. No requiere esfuerzo logístico pesado y la incluyes en tu plan.",
          "coach_feedback_incorrect": "Ser sumiso, proponer cenas caras (sobreinversión) o ser vulgarmente directo destruye tu atractivo.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Deja pasar entre 2h y 4h para mostrar que no es un impulso desesperado."
        },
        {
          "step_id": 10,
          "her_message": "suena súper tentador, acepto el vino. Mándame tu dirección.",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "Perfecto. Te veo a las 8:30 pm en mi lugar. Ven con buena vibra. 😉 [Dirección]", "is_correct": True},
            {"text": "¡Sí claro! Toma: [Dirección]. ¡Te espero ya!", "is_correct": False},
            {"text": "Ok, avísame cuando salgas por favor", "is_correct": False},
            {"text": "Genial, ¿quieres que vaya a buscarte?", "is_correct": False}
          ],
          "coach_feedback_correct": "Cierras la logística con firmeza, asumiendo el control y marcando una hora clara.",
          "coach_feedback_incorrect": "Ofrecerte de chofer gratis o mostrar demasiada impaciencia debilita el cierre.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Cierre rápido y directo."
        }
      ]
    },
    {
      "level_id": 4,
      "girl_name": "Isabella",
      "name": "Nivel 4: El Marco del Seductor (Tinder/WhatsApp)",
      "description": "Isabella es sumamente atractiva y defensiva. Debes sostener tu marco a través de un test de stripper/ sugar baby.",
      "starting_lives": 1,
      "steps": [
        {
          "step_id": 1,
          "her_message": "[Chat vacío - Envías abridor]",
          "her_time": "Inicio de conversación",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "hola chica problema", "is_correct": True},
            {"text": "Hola hermosa, eres la mujer más bella de Tinder 😍", "is_correct": False},
            {"text": "Hola Isabella, ¿cómo estás?", "is_correct": False},
            {"text": "Hola, ¿qué buscas en esta app?", "is_correct": False}
          ],
          "coach_feedback_correct": "El abridor 'hola chica problema' funciona de maravilla con chicas de alta resistencia para desarmar sus defensas.",
          "coach_feedback_incorrect": "Halagos exagerados las aburren al instante.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Abrir demasiado rápido o tardar demasiado reduce la ventana de match."
        },
        {
          "step_id": 2,
          "her_message": "oye, soy una niña buena jajaja",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "oh, yo también 😉", "is_correct": True},
            {"text": "Jaja no te creo nada", "is_correct": False},
            {"text": "Qué bueno, me gustan las niñas buenas", "is_correct": False},
            {"text": "Jaja seguro eres terrible en la cama", "is_correct": False}
          ],
          "coach_feedback_correct": "Espejeo de marco. Al responder 'yo también' con ironía, mantienes la dinámica lúdica.",
          "coach_feedback_incorrect": "Ponerse vulgar o validar de forma aburrida apaga la tensión.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato demuestra que estás vigilando la app."
        },
        {
          "step_id": 3,
          "her_message": "eso de niña buena apesta, creo que te ves mejor como chico de casa",
          "her_time": "Tardó: 45 min",
          "allowed_time_indices": [2, 3], # 1h o 2h
          "options": [
            {"text": "gracias, pero no te preocupes, soy demasiado dominante en la cama para eso", "is_correct": True},
            {"text": "¡Oye no digas eso, soy muy masculino!", "is_correct": False},
            {"text": "Jaja qué mala eres", "is_correct": False},
            {"text": "¿Por qué dices que apesta?", "is_correct": False}
          ],
          "coach_feedback_correct": "Tensión sexual máxima. Reencuadras su insulto/prueba ('chico de casa') con una aserción de alta masculinidad.",
          "coach_feedback_incorrect": "Ponerse a la defensiva o rogar por su aprobación destruye tu atractivo.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Te lanzó una prueba pesada. Responder rápido te hace ver reactivo e inseguro. Esperar entre 1h y 2h demuestra indiferencia."
        },
        {
          "step_id": 4,
          "her_message": "me gusta eso, siempre que pueda dominarte yo también está bien",
          "her_time": "Tardó: 20 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "por supuesto, especialmente con ese lindo trasero", "is_correct": True},
            {"text": "¡SIII! Pásame tu dirección ya 😍", "is_correct": False},
            {"text": "Jaja me asustas un poco", "is_correct": False},
            {"text": "Qué atrevida eres", "is_correct": False}
          ],
          "coach_feedback_correct": "Aceptas su propuesta juguetona y dejas ir un cumplido sexualizado pero calibrado sobre sus fotos.",
          "coach_feedback_incorrect": "Desesperación inmediata por la dirección o mostrar timidez.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder al instante te delata como desesperado."
        },
        {
          "step_id": 5,
          "her_message": "mido 1.65 y no tengo mucho trasero, no es verdad. Escríbeme.",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "toma mi número: [Número] y nos leemos por allá", "is_correct": True},
            {"text": "No te preocupes, a mí me gusta así", "is_correct": False},
            {"text": "Pásame tu número mejor", "is_correct": False},
            {"text": "Ok, agrégame tú: [WhatsApp]", "is_correct": False}
          ],
          "coach_feedback_correct": "Ella pide que le escribas. Le entregas tu número asumiendo la transición fluida a WhatsApp.",
          "coach_feedback_incorrect": "Seguir discutiendo sobre su cuerpo devalúa la charla.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Pásale tu número en el rango de 15m a 1h."
        },
        {
          "step_id": 6,
          "her_message": "hola",
          "her_time": "Tardó: 10 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "al que le gusta el trasero", "is_correct": True},
            {"text": "Hola hermosa, qué gusto tenerte aquí 😍", "is_correct": False},
            {"text": "¿Cómo estás? ¿Qué haces?", "is_correct": False},
            {"text": "Hola, ¿qué andas haciendo?", "is_correct": False}
          ],
          "coach_feedback_correct": "Retomas la broma del trasero de forma inmediata para mantener el confort y la tensión.",
          "coach_feedback_incorrect": "Saludos aburridos o sumisos pierden la inercia del match.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder al instante te quita misterio."
        },
        {
          "step_id": 7,
          "her_message": "bueno, no tengo suerte, soy delgada",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "oh basta, ambos sabemos que tienes buen trasero", "is_correct": True},
            {"text": "Bueno, no importa, me gustas de todas formas", "is_correct": False},
            {"text": "¿Por qué eres tan insegura?", "is_correct": False},
            {"text": "Jaja si tú lo dices", "is_correct": False}
          ],
          "coach_feedback_correct": "Reafirmas tu marco con seguridad ('ambos sabemos'). No caes en su juego para buscar validación fácil.",
          "coach_feedback_incorrect": "Validar su supuesta delgadez o cuestionar su psicología apaga la vibra.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde en un lapso normal (15m a 1h)."
        },
        {
          "step_id": 8,
          "her_message": "para mi tamaño de cuerpo sí lo tengo, gracias",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "eso está mejor, ¿eres de aquí originalmente?", "is_correct": True},
            {"text": "¡Qué bueno! Me alegro", "is_correct": False},
            {"text": "Deberías mandarme una foto para comprobarlo", "is_correct": False},
            {"text": "¿Qué edad tienes?", "is_correct": False}
          ],
          "coach_feedback_correct": "Validas su aceptación y cambias el tema de forma suave y madura hacia el confort geográfico.",
          "coach_feedback_incorrect": "Pedir fotos de forma desesperada o respuestas secas rompe el flujo.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde con calma (15m a 1h)."
        },
        {
          "step_id": 9,
          "her_message": "sí",
          "her_time": "Tardó: 20 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "ah, una chica de Florida", "is_correct": True},
            {"text": "Qué bien, a mí me encanta Florida", "is_correct": False},
            {"text": "¿En qué parte vives?", "is_correct": False},
            {"text": "Qué cortante eres", "is_correct": False}
          ],
          "coach_feedback_correct": "Comentario observador y relajado. Mantienes el marco sin forzar preguntas.",
          "coach_feedback_incorrect": "Hacer preguntas de entrevista aburridas o reclamar su brevedad.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde en un lapso normal."
        },
        {
          "step_id": 10,
          "her_message": "[Emoji: fiesta]",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "entonces dime lo básico: tatuajes, hijos, cosas raras", "is_correct": True},
            {"text": "Jaja ¿qué andas haciendo?", "is_correct": False},
            {"text": "¿Quieres salir mañana?", "is_correct": False},
            {"text": "Qué chistosa", "is_correct": False}
          ],
          "coach_feedback_correct": "Propuesta de confort divertida y retadora ('cosas raras') para que ella comparta sobre sí misma.",
          "coach_feedback_incorrect": "Preguntar qué hace o forzar la cita muy rápido rompe el ritmo.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Mantén la calma (15m a 1h)."
        },
        {
          "step_id": 11,
          "her_message": "ocupada, te escribo luego",
          "her_time": "Tardó: 20 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "ok, cuídate", "is_correct": True},
            {"text": "¿Por qué estás ocupada? ¿Qué haces?", "is_correct": False},
            {"text": "No te preocupes, aquí te espero", "is_correct": False},
            {"text": "Avísame apenas te liberes por favor", "is_correct": False}
          ],
          "coach_feedback_correct": "Muestras indiferencia absoluta y alto valor al aceptar que se vaya del chat con un simple 'ok, cuídate'.",
          "coach_feedback_incorrect": "Interrogar por qué está ocupada o rogar para que te escriba demuestra desesperación extrema.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Cierre de chat rápido en un lapso normal."
        },
        {
          "step_id": 12,
          "her_message": "hola. ¿qué harás mañana por la noche?",
          "her_time": "Tardó: 24 horas",
          "allowed_time_indices": [2, 3], # 1h o 2h
          "options": [
            {"text": "terminando un video, ¿qué onda?", "is_correct": True},
            {"text": "¡Hola! Nada, libre para ti. ¿Qué hacemos? 😍", "is_correct": False},
            {"text": "¿Por qué no me escribiste ayer?", "is_correct": False},
            {"text": "Estoy ocupado toda la semana", "is_correct": False}
          ],
          "coach_feedback_correct": "Demuestras que estás ocupado con tus proyectos y devuelves la pregunta con desapego.",
          "coach_feedback_incorrect": "Mostrarte 100% disponible o reclamarle por ayer destruye tu marco de valor.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Deja pasar entre 1h y 2h para equilibrar la balanza de poder."
        },
        {
          "step_id": 13,
          "her_message": "yendo a mr. Jones",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "¿quién es Jones?", "is_correct": True},
            {"text": "Ah, qué divertido, pásala súper", "is_correct": False},
            {"text": "¿A qué hora vas? ¿Puedo ir?", "is_correct": False},
            {"text": "Qué flojera ir de antro", "is_correct": False}
          ],
          "coach_feedback_correct": "Humor seco y desentendido ('¿quién es Jones?') que la obliga a explicar que es un club.",
          "coach_feedback_incorrect": "Preguntar si puedes ir o ponerte negativo corta la vibra.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde en un lapso normal."
        },
        {
          "step_id": 14,
          "her_message": "jajaja un club nocturno. [Screenshot de reseñas: 2.5 estrellas]",
          "her_time": "Tardó: 10 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "veo que tiene 2.5 estrellas jajaja", "is_correct": True},
            {"text": "Ah, no lo conozco, debe ser genial", "is_correct": False},
            {"text": "Qué mal lugar, no vayas", "is_correct": False},
            {"text": "Jaja qué chistoso", "is_correct": False}
          ],
          "coach_feedback_correct": "Te burlas del lugar en sintonía con su reseña, compartiendo el chiste con ella.",
          "coach_feedback_incorrect": "Respuestas aburridas o tomarlo muy en serio.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde en un lapso normal."
        },
        {
          "step_id": 15,
          "her_message": "está prendido, me voy a casa, aburrida soltera jajaja",
          "her_time": "Tardó: 30 min",
          "allowed_time_indices": [2, 3], # 1h o 2h
          "options": [
            {"text": "me imagino. Estaré libre un poco más tarde mañana por la noche, deberías pasar por un trago o dos", "is_correct": True},
            {"text": "Qué bueno que te vayas a casa, es peligroso", "is_correct": False},
            {"text": "¿Quieres que vaya a tu casa ahora?", "is_correct": False},
            {"text": "Dime cuándo estás libre y nos vemos en un bar", "is_correct": False}
          ],
          "coach_feedback_correct": "Lanzas la propuesta tranquila de cita en tu espacio (trago) aprovechando su aburrimiento y soltería.",
          "coach_feedback_incorrect": "Ofrecerte a ir a su casa de inmediato suena muy urgido de sexo casual.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Espera de 1h a 2h para asentar el marco."
        },
        {
          "step_id": 16,
          "her_message": "ok lo haré",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "planes esta noche y ya hicimos planes para mañana", "is_correct": True},
            {"text": "¡Perfecto! Te paso mi dirección", "is_correct": False},
            {"text": "Genial, avísame cuando salgas", "is_correct": False},
            {"text": "Ok, te espero entonces", "is_correct": False}
          ],
          "coach_feedback_correct": "Estableces límites. Ella tardó en confirmar. Dejas claro tu orden y tu tiempo.",
          "coach_feedback_incorrect": "Mostrarte demasiado alegre o sumiso le quita valor a tu tiempo.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde en un lapso normal."
        },
        {
          "step_id": 17,
          "her_message": "solo busco citas pagadas para ser honesta, tipo que me pagas si salimos",
          "her_time": "Tardó: 20 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "no pago por sexo ni por citas, y si eso es lo que querías, debiste decirlo desde el principio. Qué aburrido.", "is_correct": True},
            {"text": "¿Cuánto cobras por cita? Quizá podamos arreglar... 💸", "is_correct": False},
            {"text": "Qué interesada eres, qué mal de tu parte", "is_correct": False},
            {"text": "Bueno, te invito a cenar y te doy un regalo", "is_correct": False}
          ],
          "coach_feedback_correct": "¡MARCO DE HIERRO! Te retiras de inmediato al ver que busca dinero. Esto demuestra el máximo valor: no te dejas comprar.",
          "coach_feedback_incorrect": "Aceptar negociar o insultarla te devalúa por completo. Retirarse con dignidad es la única opción.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responder de inmediato denota que te afectó su mensaje."
        },
        {
          "step_id": 18,
          "her_message": "bueno, lo siento",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "¿solo conoces gente por dinero?", "is_correct": True},
            {"text": "No te preocupes, te perdono", "is_correct": False},
            {"text": "¿Por qué eres así?", "is_correct": False},
            {"text": "Jaja no pasa nada", "is_correct": False}
          ],
          "coach_feedback_correct": "Pregunta de confort y curiosidad sin juzgarla directamente, manteniéndote calmado en tu marco.",
          "coach_feedback_incorrect": "Pedir perdón tú o tratar de minimizar el test rompe el marco.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Responde con tranquilidad."
        },
        {
          "step_id": 19,
          "her_message": "¿es eso raro? en realidad soy stripper, recién empecé de escort, mi amiga me recomendó eso",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [2, 3], # 1h o 2h
          "options": [
            {"text": "¿y crees que diciéndome a unas horas de nuestra cita que solo quieres verte por dinero me va a dar ganas de salir contigo?", "is_correct": True},
            {"text": "Ah, eres stripper, qué cool. Vamos", "is_correct": False},
            {"text": "Qué mal que hagas eso", "is_correct": False},
            {"text": "Bueno, entonces salgamos gratis", "is_correct": False}
          ],
          "coach_feedback_correct": "Desafías su lógica de forma asertiva, haciéndola ver que su enfoque es incongruente con generar interés real.",
          "coach_feedback_incorrect": "Aceptar la cita rápido tras enterarte que es stripper o ponerte moralista apaga el chat.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Esperar entre 1h y 2h."
        },
        {
          "step_id": 20,
          "her_message": "jajaja quieres salir conmigo, no te culpo, soy increíble",
          "her_time": "Tardó: 15 min",
          "allowed_time_indices": [1, 2], # 15m o 1h
          "options": [
            {"text": "bueno, definitivamente estás perdiendo puntos ahora mismo. Nos vemos mañana.", "is_correct": True},
            {"text": "¡Sí, eres increíble! Te veo mañana", "is_correct": False},
            {"text": "Jaja qué payasa eres", "is_correct": False},
            {"text": "No, ya no quiero verte", "is_correct": False}
          ],
          "coach_feedback_correct": "Mantienes la compostura, la calificas negativamente con humor ('perdiendo puntos') y dejas abierta la cita con sobriedad.",
          "coach_feedback_incorrect": "Validar su ego o enojarte con insultos destruye tu estatus masculino final.",
          "coach_feedback_time_incorrect": "Fallo de Tiempo: Cierre rápido y directo."
        }
      ]
    }
  ]
}

with open("scratch/game_dialogues.json", "w", encoding="utf-8") as f:
    json.dump(dialogues_data, f, indent=2, ensure_ascii=False)
print("Updated game_dialogues.json with exact unaltered conversations v1.1.")
