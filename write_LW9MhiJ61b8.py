import json

data = {
  "video_id": "LW9MhiJ61b8",
  "scoring": 4,
  "error_tipo": "Pérdida de Marco (Frame) ante Shit Tests",
  "justificacion_error": "El emisor arranca con un marco sólido, pero empieza a usar respuestas robotizadas y a sobre-explicarse. La pérdida total ocurre cuando él repite por error la misma frase ('¿te gusta el vino?') que ya había usado en la app. Al verse descubierto por un shit test de la chica, en lugar de mantener su seguridad, entra en pánico y se disculpa usando excusas lógicas, matando la atracción.",
  "punto_quiebre": {
    "mensaje_error": "Perdón, tuve problemas familiares y de trabajo que me han quitado mucho tiempo estas últimas dos semanas, pero ya estoy bien",
    "explicacion": "Al justificarse y pedir disculpas por un descuido (repetir una línea de texto), demuestra extrema necesidad y falta de congruencia, cediendo su poder ante la chica. En su lugar, debió mantener la diversión y adueñarse de su error con humor (ej. 'Solo se lo pregunto a las más lindas' o 'Es mi cuestionario oficial para pasar de ronda')."
  },
  "mensajes": [
    { "autor": "El", "texto": "Desliza a la derecha para un posible buen trasero" },
    { "autor": "Ella", "texto": "Posiblemente sea bueno, posiblemente seas un catfish. 50/50" },
    { "autor": "Ella", "texto": "¿Vale la pena el riesgo? 🥺" },
    { "autor": "El", "texto": "Dímelo tú, ¿lo vales?" },
    { "autor": "Ella", "texto": "Por supuesto, nunca lo dudes" },
    { "autor": "El", "texto": "Me arriesgaré, pareces mi tipo" },
    { "autor": "Ella", "texto": "Cuéntame, ¿cuál es tu tipo ideal?" },
    { "autor": "El", "texto": "Linda, aventurera, activa, sumisa o la del buen trasero, inocente pero con un lado salvaje" },
    { "autor": "Ella", "texto": "Interesante, puros rasgos encantadores. ¿Cómo te describirías tú aparte de lo que dice tu bio?" },
    { "autor": "El", "texto": "Uff, ¿por dónde empiezo? Confiado, divertido, rubio, dominante, con grandes habilidades orales, me encanta cantar, viajar, comer culo y la buena comida, eso me resume. Mi turno." },
    { "autor": "El", "texto": "¿Ya te dejé sin palabras?" },
    { "autor": "Ella", "texto": "Me quitaste el aliento" },
    { "autor": "El", "texto": "Y ni siquiera he empezado, ¿crees que me puedas seguir el ritmo?" },
    { "autor": "Ella", "texto": "Lo dudo, pero por favor continúa" },
    { "autor": "El", "texto": "Seguro que puedes, sigue quitándome el aliento y déjame morir" },
    { "autor": "Ella", "texto": "Soy muy confiada, relajada, me encanta el buen coqueteo y no tomarme las cosas en serio a menos que sea necesario. Súper ambiciosa y enfocada. Amo la comida y la cultura. Espontánea, divertida y me encantan los retos" },
    { "autor": "El", "texto": "Me gusta que seas relajada y confiada, me hace pensar que tienes mente abierta. Suenas como alguien a quien disfrutaría conocer más en persona, pero tienes que seguirme el juego con el coqueteo :):):)" },
    { "autor": "El", "texto": "¿Te gusta el vino?" },
    { "autor": "Ella", "texto": "Jaja no te preocupes, me encanta el coqueteo. De hecho soy bartender así que sé mucho de vinos, soy un poco exigente con eso jajaja. Igual no soy mucho de beber, ¿y tú?" },
    { "autor": "El", "texto": "Yo tampoco soy de beber mucho pero me encanta un buen vino. Definitivamente tú vas a escoger la botella para nuestra cita romántica (siempre y cuando sea dulce) y no te preocupes, te detendré después de una copa" },
    { "autor": "Ella", "texto": "¿Qué buscas exactamente?" },
    { "autor": "El", "texto": "Vino blanco dulce, y conocer a una chica cool con la que tenga química, sexo sucio y abrazos. Algo casual al principio pero abierto a más. Cero interesado en hookups sin sentido ya" },
    { "autor": "Ella", "texto": "Jaja Dios, los blancos dulces siempre son los mejores. Diría lo mismo... Pero para ser honesta, no estoy intentando conocer a nadie durante la pandemia. Tengo personas en mi vida a las que debo cuidar y no sería inteligente" },
    { "autor": "El", "texto": "Te entiendo totalmente, planeemos algo cuando todo esto termine, pasémonos los números" },
    { "autor": "Ella", "texto": "Suena bien, ¿cuál es el tuyo? Yo te escribo" },
    { "autor": "Ella", "texto": "Hola lindo, ¿[Nombre] es tu nombre real?" },
    { "autor": "El", "texto": "Jaja no, es mi apodo. Mi nombre real es [Nombre] pero nadie me llama así" },
    { "autor": "Ella", "texto": "Bastante único" },
    { "autor": "El", "texto": "No olvides guardar mi contacto con corazoncitos y brillos" },
    { "autor": "Ella", "texto": "Claro, no esperaba menos jaja" },
    { "autor": "El", "texto": "¿Ya lo descubriste?" },
    { "autor": "Ella", "texto": "Wow, ¿se te ocurrió a ti solito?" },
    { "autor": "El", "texto": "Lo pasé por un chat de 300 personas primero" },
    { "autor": "Ella", "texto": "Uff increíble, siempre supe que eras gracioso" },
    { "autor": "El", "texto": "Espero que tú también lo seas" },
    { "autor": "Ella", "texto": "Por supuesto, nunca lo dudes" },
    { "autor": "El", "texto": "Ya veremos eso en una cita romántica, ¿te gusta el vino?" },
    { "autor": "Ella", "texto": "¿Siempre le haces a todas la misma pregunta?" },
    { "autor": "El", "texto": "Perdón, tuve problemas familiares y de trabajo que me han quitado mucho tiempo estas últimas dos semanas, pero ya estoy bien" }
  ]
}

with open("failed_cases/LW9MhiJ61b8.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
