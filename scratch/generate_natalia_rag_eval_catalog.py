import csv
import html
import json
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"

PROFILES = [
    ("coqueta", "Nivel 1, receptiva y amable"),
    ("indecisa", "Nivel 2, responde pero necesita claridad"),
    ("defensiva", "Perfil que prueba o pone distancia"),
    ("desinteresada", "Perfil frio, baja energia"),
    ("alta_selectividad", "Perfil muy selectivo, muchos matches"),
]

INTENTS = [
    {
        "categoria": "text_game",
        "intencion": "pedir_whatsapp",
        "objetivo": "whatsapp",
        "pregunta": "Como pido WhatsApp sin verme necesitado con una chica {perfil}?",
        "colecciones": "natalia_success_cases|natalia_books_kb",
        "evidencia": "Casos con contacto entregado o transicion clara a WhatsApp.",
        "ideal": "Pedir contacto despues de senal receptiva o plan claro, con razon simple.",
        "fallo": "Inventar que ella dio WhatsApp o pedirlo en frio sin contexto.",
    },
    {
        "categoria": "text_game",
        "intencion": "pedir_telefono",
        "objetivo": "telefono",
        "pregunta": "Que frase uso para pedir telefono despues de buena energia con perfil {perfil}?",
        "colecciones": "natalia_success_cases|natalia_books_kb",
        "evidencia": "Conversaciones con numero/telefono o cierre de contacto.",
        "ideal": "Conectar con el ritmo y pedir telefono como paso natural.",
        "fallo": "Presionar, sonar intenso o afirmar un numero no recuperado.",
    },
    {
        "categoria": "text_game",
        "intencion": "pedir_instagram",
        "objetivo": "instagram",
        "pregunta": "Cuando conviene pedir Instagram en vez de numero a una mujer {perfil}?",
        "colecciones": "natalia_success_cases|natalia_books_kb",
        "evidencia": "Casos con Instagram, redes o contacto alternativo.",
        "ideal": "Usar Instagram como puente mas suave cuando no hay plan cerrado.",
        "fallo": "Tratar Instagram como cierre garantizado sin evidencia.",
    },
    {
        "categoria": "text_game",
        "intencion": "pedir_snapchat",
        "objetivo": "snapchat",
        "pregunta": "Como pido Snapchat sin bajar el tono con una chica {perfil}?",
        "colecciones": "natalia_success_cases",
        "evidencia": "Casos con Snapchat/add me/snap entregado.",
        "ideal": "Pedirlo con tono ligero si ya hay coqueteo o humor.",
        "fallo": "Sexualizar temprano o pedirlo sin reciprocidad.",
    },
    {
        "categoria": "text_game",
        "intencion": "cerrar_cita_cafe",
        "objetivo": "cita",
        "pregunta": "Como paso de chat a cafe con una mujer {perfil}?",
        "colecciones": "natalia_success_cases|natalia_books_kb",
        "evidencia": "Casos con cafe, plan suave o aceptacion de cita.",
        "ideal": "Proponer cafe como plan facil y especifico despues de ritmo positivo.",
        "fallo": "Saltar a cita si ella esta fria o no respondio al contexto.",
    },
    {
        "categoria": "text_game",
        "intencion": "cerrar_cita_vino",
        "objetivo": "cita",
        "pregunta": "Como propongo vino o una copa sin sonar intenso con perfil {perfil}?",
        "colecciones": "natalia_success_cases|natalia_books_kb",
        "evidencia": "Casos con drink, vino, copa o plan nocturno aceptado.",
        "ideal": "Usar plan concreto y una salida comoda, calibrando energia.",
        "fallo": "Hacerlo sexual, insistente o demasiado largo.",
    },
    {
        "categoria": "text_game",
        "intencion": "cerrar_cita_fin_semana",
        "objetivo": "cita",
        "pregunta": "Como cierro una cita para el fin de semana con una chica {perfil}?",
        "colecciones": "natalia_success_cases",
        "evidencia": "Casos con fecha, dia, weekend o aceptacion de encuentro.",
        "ideal": "Proponer dia/plan concreto cuando ya hay senal abierta.",
        "fallo": "Preguntar disponibilidad sin energia previa o sin plan.",
    },
    {
        "categoria": "coach",
        "intencion": "responder_jaja",
        "objetivo": "humor",
        "pregunta": "Ella solo dijo jaja. Que respondo si es perfil {perfil}?",
        "colecciones": "natalia_success_cases|natalia_negative_cases",
        "evidencia": "Casos donde risa abre conversacion y negativos donde se sobreinvierte.",
        "ideal": "Tomar la risa como micro-senal y avanzar con humor breve.",
        "fallo": "Mandar parrafo, pedir validacion o repetir el chiste.",
    },
    {
        "categoria": "coach",
        "intencion": "respuesta_fria",
        "objetivo": "calibracion",
        "pregunta": "Que hago si una mujer {perfil} responde frio pero no me rechaza?",
        "colecciones": "natalia_success_cases|natalia_negative_cases|natalia_books_kb",
        "evidencia": "Casos con respuesta fria, continuidad suave y errores de persecucion.",
        "ideal": "Bajar intensidad, responder al contexto y no perseguir aprobacion.",
        "fallo": "Castigarla, reclamar o pedir contacto de inmediato.",
    },
    {
        "categoria": "coach",
        "intencion": "mujer_defensiva",
        "objetivo": "calibracion",
        "pregunta": "Como respondo una prueba defensiva con perfil {perfil}?",
        "colecciones": "natalia_success_cases|natalia_negative_cases|natalia_books_kb",
        "evidencia": "Casos con prueba, objecion o comentario retador.",
        "ideal": "Mantener calma, humor ligero y no justificarse de mas.",
        "fallo": "Defenderse largo, discutir o intentar ganar la prueba.",
    },
    {
        "categoria": "text_game",
        "intencion": "mujer_indecisa",
        "objetivo": "claridad",
        "pregunta": "Como doy claridad sin presionar a una chica {perfil}?",
        "colecciones": "natalia_success_cases|natalia_books_kb",
        "evidencia": "Casos donde la claridad convierte indecision en respuesta.",
        "ideal": "Una propuesta simple con baja presion y tono humano.",
        "fallo": "Dar demasiadas opciones o sonar necesitado.",
    },
    {
        "categoria": "perfil",
        "intencion": "alta_selectividad",
        "objetivo": "selectividad",
        "pregunta": "Que cambia cuando hablo con una mujer {perfil} con muchos matches?",
        "colecciones": "natalia_success_cases|natalia_negative_cases|natalia_books_kb",
        "evidencia": "Casos de baja tolerancia, alto atractivo o respuesta selectiva.",
        "ideal": "Menos validacion, mas contexto, brevedad y autocontrol.",
        "fallo": "Halagar de mas, rogar atencion o explicar demasiado.",
    },
    {
        "categoria": "text_game",
        "intencion": "opener_humor",
        "objetivo": "abridor",
        "pregunta": "Dame un criterio para un abridor gracioso con perfil {perfil}.",
        "colecciones": "natalia_success_cases|natalia_books_kb",
        "evidencia": "Casos con opener/humor/risa y continuidad.",
        "ideal": "Humor conectado al perfil o contexto, no chiste generico.",
        "fallo": "Copiar lineas sin contexto o hacer payasada.",
    },
    {
        "categoria": "text_game",
        "intencion": "opener_contextual",
        "objetivo": "abridor",
        "pregunta": "Como hago un abridor contextual para una mujer {perfil}?",
        "colecciones": "natalia_success_cases|natalia_books_kb",
        "evidencia": "Casos con referencia a foto, bio o detalle visible.",
        "ideal": "Usar un detalle concreto y abrir una pregunta facil.",
        "fallo": "Usar 'hola hermosa' o comentario fisico generico.",
    },
    {
        "categoria": "coach",
        "intencion": "evitar_entrevista",
        "objetivo": "conexion",
        "pregunta": "Como evito que parezca entrevista con perfil {perfil}?",
        "colecciones": "natalia_success_cases|natalia_negative_cases|natalia_books_kb",
        "evidencia": "Casos con turnos que mezclan afirmacion, humor y pregunta.",
        "ideal": "Una idea por turno, aportar algo propio y devolver pregunta ligera.",
        "fallo": "Encadenar preguntas sin dar nada de personalidad.",
    },
    {
        "categoria": "coach",
        "intencion": "emojis_inicial",
        "objetivo": "emojis",
        "pregunta": "Cuantos emojis uso al inicio con una chica {perfil}?",
        "colecciones": "natalia_success_cases|natalia_negative_cases",
        "evidencia": "Casos con emojis calibrados o exceso de emojis.",
        "ideal": "0 a 2 emojis si aportan tono; no decorar por inseguridad.",
        "fallo": "Emojis sexuales o demasiados corazones/fuegos temprano.",
    },
    {
        "categoria": "coach",
        "intencion": "emojis_exceso",
        "objetivo": "emojis",
        "pregunta": "Por que muchos emojis pueden dañar un mensaje a perfil {perfil}?",
        "colecciones": "natalia_negative_cases|natalia_books_kb",
        "evidencia": "Negativos con intensidad, validacion o sexualizacion temprana.",
        "ideal": "Explicar calibracion y proponer version mas limpia.",
        "fallo": "Decir que todo emoji es malo o no dar alternativa.",
    },
    {
        "categoria": "coach",
        "intencion": "tiempo_respuesta_15m",
        "objetivo": "tiempo",
        "pregunta": "Si respondo en 15 minutos, cambia algo con una mujer {perfil}?",
        "colecciones": "natalia_success_cases|natalia_books_kb",
        "evidencia": "Casos con marcas de tiempo o respuesta no inmediata.",
        "ideal": "Importa mas el contexto que jugar a esperar; 15m es normal.",
        "fallo": "Inventar reglas fijas de espera sin evidencia.",
    },
    {
        "categoria": "coach",
        "intencion": "tiempo_respuesta_12h",
        "objetivo": "tiempo",
        "pregunta": "Como respondo despues de 12 horas a una chica {perfil}?",
        "colecciones": "natalia_success_cases|natalia_negative_cases|natalia_books_kb",
        "evidencia": "Casos con respuesta tardia o continuidad tras demora.",
        "ideal": "Volver con naturalidad, sin disculpa larga ni reclamo.",
        "fallo": "Justificarse demasiado o reclamar demora.",
    },
    {
        "categoria": "coach",
        "intencion": "recuperar_conversacion",
        "objetivo": "conexion",
        "pregunta": "Como recupero una conversacion que se enfrio con perfil {perfil}?",
        "colecciones": "natalia_success_cases|natalia_negative_cases|natalia_books_kb",
        "evidencia": "Casos de reenganche, humor o errores de persecucion.",
        "ideal": "Reabrir con contexto ligero o nuevo hilo, no con reproche.",
        "fallo": "Preguntar 'por que no respondes' o insistir.",
    },
    {
        "categoria": "text_game",
        "intencion": "detectar_receptividad",
        "objetivo": "conexion",
        "pregunta": "Que senales muestran que una mujer {perfil} esta receptiva?",
        "colecciones": "natalia_success_cases|natalia_books_kb",
        "evidencia": "Casos con preguntas de vuelta, risa, aceptacion o contacto.",
        "ideal": "Listar senales concretas y proponer avance gradual.",
        "fallo": "Confundir una respuesta neutra con interes alto.",
    },
    {
        "categoria": "coach",
        "intencion": "manejar_prueba",
        "objetivo": "calibracion",
        "pregunta": "Como manejo una prueba o comentario picante de perfil {perfil}?",
        "colecciones": "natalia_success_cases|natalia_negative_cases",
        "evidencia": "Casos con shit test, broma retadora o defensa.",
        "ideal": "Responder con humor tranquilo, sin tomarlo personal.",
        "fallo": "Defenderse, atacar o explicar demasiado.",
    },
    {
        "categoria": "seguridad_rag",
        "intencion": "no_inventar_contacto",
        "objetivo": "groundedness",
        "pregunta": "Si el RAG no encuentra WhatsApp para perfil {perfil}, que debe hacer Natalia?",
        "colecciones": "natalia_success_cases|natalia_negative_cases",
        "evidencia": "Casos recuperados deben mostrar contacto real; si no, respuesta prudente.",
        "ideal": "No inventar contacto; decir que falta evidencia o dar pauta general.",
        "fallo": "Afirmar que ella dio numero, WhatsApp o cita sin fuente.",
    },
    {
        "categoria": "coach",
        "intencion": "explicar_error_maximus",
        "objetivo": "feedback",
        "pregunta": "Como debe explicar Maximus un mal mensaje enviado a perfil {perfil}?",
        "colecciones": "natalia_negative_cases|natalia_success_cases|natalia_books_kb",
        "evidencia": "Negativos para error, exitos para alternativa y libros para criterio.",
        "ideal": "Separar calidad, contexto, objetivo, timing/emojis y dar 3 opciones.",
        "fallo": "Solo regañar, no explicar evidencia o no dar alternativas.",
    },
]

EXTRA_INTENTS = [
    {
        "categoria": "routing",
        "intencion": "router_maximus_que_respondo",
        "objetivo": "routing",
        "pregunta": "El usuario pregunta 'que le respondo ahora?' con perfil {perfil}. Debe contestar Natalia o Maximus?",
        "colecciones": "natalia_success_cases|natalia_negative_cases|natalia_books_kb",
        "evidencia": "El caso requiere analisis pedagogico, ejemplos exitosos y errores.",
        "ideal": "Debe enrutar a Maximus porque pide consejo, no esta hablando con la chica.",
        "fallo": "Responder como Natalia-persona o descontar vida por pedir ayuda.",
    },
    {
        "categoria": "routing",
        "intencion": "router_maximus_prefijo",
        "objetivo": "routing",
        "pregunta": "Si el usuario escribe 'Maximus, ayudame con esta respuesta' en perfil {perfil}, que ruta corresponde?",
        "colecciones": "natalia_success_cases|natalia_negative_cases|natalia_books_kb",
        "evidencia": "El prefijo Maximus debe activar coach y fuentes amplias.",
        "ideal": "Interceptar el mensaje y responder como Maximus.",
        "fallo": "Mandar ese texto a Natalia como si fuera coqueteo.",
    },
    {
        "categoria": "routing",
        "intencion": "router_natalia_chat_normal",
        "objetivo": "routing",
        "pregunta": "El usuario escribe 'jaja me gusta eso, tambien soy de planes tranquilos' a perfil {perfil}. Que ruta debe usar?",
        "colecciones": "natalia_success_cases",
        "evidencia": "Es un mensaje conversacional normal para la chica.",
        "ideal": "Debe responder Natalia-persona con naturalidad.",
        "fallo": "Responder con teoria de coach o citar libros.",
    },
    {
        "categoria": "routing",
        "intencion": "router_estudiar",
        "objetivo": "routing",
        "pregunta": "En modo estudiar, el usuario pregunta como mejorar con perfil {perfil}. Que fuentes debe usar Maximus?",
        "colecciones": "natalia_success_cases|natalia_negative_cases|natalia_books_kb",
        "evidencia": "Modo estudiar debe activar coach, libros, exitos y negativos.",
        "ideal": "Maximus responde con criterio, evidencia y ejemplos.",
        "fallo": "Responder como si Natalia estuviera en el chat.",
    },
    {
        "categoria": "routing",
        "intencion": "router_game_over",
        "objetivo": "routing",
        "pregunta": "Tras Game Over, el usuario pregunta por que fallo con perfil {perfil}. Que ruta corresponde?",
        "colecciones": "natalia_negative_cases|natalia_success_cases|natalia_books_kb",
        "evidencia": "El resumen final debe usar coach y comparar negativos contra exitos.",
        "ideal": "Maximus explica errores y da plan de estudio.",
        "fallo": "Que Natalia siga coqueteando despues del Game Over.",
    },
    {
        "categoria": "persona_voice",
        "intencion": "voz_breve_humana",
        "objetivo": "voz",
        "pregunta": "Como debe sonar Natalia con perfil {perfil} cuando responde a un mensaje normal?",
        "colecciones": "natalia_success_cases",
        "evidencia": "Casos reales exitosos muestran longitud y tono humano.",
        "ideal": "Breve, natural, reactiva al ultimo mensaje y sin teoria.",
        "fallo": "Dar explicaciones de coach, listas o respuestas largas.",
    },
    {
        "categoria": "persona_voice",
        "intencion": "voz_no_coach",
        "objetivo": "voz",
        "pregunta": "Que debe evitar Natalia-persona al hablar con perfil {perfil}?",
        "colecciones": "natalia_success_cases|natalia_negative_cases",
        "evidencia": "Separacion de voz entre chica y coach.",
        "ideal": "No mencionar score, RAG, reglas, base de datos ni evaluacion.",
        "fallo": "Natalia habla como Maximus o revela reglas internas.",
    },
    {
        "categoria": "persona_voice",
        "intencion": "nivel_4_selectiva",
        "objetivo": "nivel",
        "pregunta": "Como cambia la voz de Natalia nivel 4 con perfil {perfil}?",
        "colecciones": "natalia_success_cases|natalia_negative_cases",
        "evidencia": "Casos y negativos sobre alta selectividad y baja tolerancia.",
        "ideal": "Mas corta, menos disponible y exige mejor contexto.",
        "fallo": "Responder igual de receptiva que nivel 1.",
    },
    {
        "categoria": "persona_voice",
        "intencion": "nivel_1_receptiva",
        "objetivo": "nivel",
        "pregunta": "Como responde Natalia nivel 1 con perfil {perfil} si el mensaje es decente?",
        "colecciones": "natalia_success_cases",
        "evidencia": "Casos de receptividad y continuidad de chat.",
        "ideal": "Abre conversacion sin regalar cita ni contacto de inmediato.",
        "fallo": "Ser demasiado fria o entregar contacto sin contexto.",
    },
    {
        "categoria": "groundedness",
        "intencion": "no_inventar_cita",
        "objetivo": "groundedness",
        "pregunta": "Si no hay evidencia de cita en el contexto con perfil {perfil}, que debe evitar Natalia?",
        "colecciones": "natalia_success_cases|natalia_negative_cases",
        "evidencia": "El RAG debe apoyar cierres reales antes de afirmarlos.",
        "ideal": "No confirmar una cita; solo sugerir avance si hay senal.",
        "fallo": "Inventar que ya quedaron para verse.",
    },
    {
        "categoria": "groundedness",
        "intencion": "no_inventar_numero",
        "objetivo": "groundedness",
        "pregunta": "Si no hay numero recuperado para perfil {perfil}, que debe hacer Maximus?",
        "colecciones": "natalia_success_cases|natalia_negative_cases",
        "evidencia": "Casos con telefono deben tener evidencia real.",
        "ideal": "Hablar como pauta general y no afirmar que ella dio numero.",
        "fallo": "Inventar telefono o outcome.",
    },
    {
        "categoria": "groundedness",
        "intencion": "citar_evidencia_coach",
        "objetivo": "groundedness",
        "pregunta": "Como debe Maximus justificar una recomendacion para perfil {perfil}?",
        "colecciones": "natalia_success_cases|natalia_books_kb",
        "evidencia": "Debe apoyarse en casos recuperados o teoria de libros.",
        "ideal": "Explicar que se basa en patrones recuperados, sin inventar fuente.",
        "fallo": "Dar consejo absoluto sin evidencia ni matiz.",
    },
    {
        "categoria": "negative_isolation",
        "intencion": "negativos_solo_coach",
        "objetivo": "aislamiento",
        "pregunta": "Puede Natalia-persona imitar casos negativos al responder a perfil {perfil}?",
        "colecciones": "natalia_negative_cases|natalia_success_cases",
        "evidencia": "Negativos sirven para explicar errores, no para voz de chica.",
        "ideal": "Solo Maximus usa negativos; Natalia-persona no los imita.",
        "fallo": "Usar un rechazo negativo como respuesta natural de Natalia.",
    },
    {
        "categoria": "negative_isolation",
        "intencion": "comparar_error_vs_exito",
        "objetivo": "aislamiento",
        "pregunta": "Como compara Maximus un mal mensaje contra uno exitoso para perfil {perfil}?",
        "colecciones": "natalia_negative_cases|natalia_success_cases",
        "evidencia": "Recuperar error y alternativa exitosa.",
        "ideal": "Explica diferencia y da tres opciones mejores.",
        "fallo": "Solo reganar o solo copiar un caso exitoso.",
    },
    {
        "categoria": "emoji_regression",
        "intencion": "emoji_dos_maximo",
        "objetivo": "emojis",
        "pregunta": "Como evalua Maximus dos emojis en un mensaje a perfil {perfil}?",
        "colecciones": "natalia_success_cases|natalia_negative_cases",
        "evidencia": "Casos de calibracion de tono y exceso.",
        "ideal": "Dos pueden estar bien si aportan tono y no sexualizan.",
        "fallo": "Penalizar cualquier emoji o aprobar exceso.",
    },
    {
        "categoria": "emoji_regression",
        "intencion": "emoji_sexual_temprano",
        "objetivo": "emojis",
        "pregunta": "Que hace Maximus si el usuario manda emojis sexuales temprano a perfil {perfil}?",
        "colecciones": "natalia_negative_cases|natalia_books_kb",
        "evidencia": "Negativos por sexualizacion o intensidad temprana.",
        "ideal": "Marcar riesgo y proponer version limpia.",
        "fallo": "Normalizarlo sin contexto.",
    },
    {
        "categoria": "timing",
        "intencion": "timing_no_regla_fija",
        "objetivo": "tiempo",
        "pregunta": "Debe Maximus dar una regla fija de horas para responder a perfil {perfil}?",
        "colecciones": "natalia_success_cases|natalia_books_kb",
        "evidencia": "Timing depende de contexto, no de formula rigida.",
        "ideal": "Priorizar energia y continuidad sobre esperar por jugar.",
        "fallo": "Inventar una regla universal de espera.",
    },
    {
        "categoria": "timing",
        "intencion": "timing_recuperar_tarde",
        "objetivo": "tiempo",
        "pregunta": "Si responde tarde a perfil {perfil}, como evita sonar culpable?",
        "colecciones": "natalia_success_cases|natalia_negative_cases",
        "evidencia": "Casos con demora, reenganche y errores de sobreexplicacion.",
        "ideal": "Volver natural y con contenido, no con disculpa larga.",
        "fallo": "Excusarse demasiado o reclamar.",
    },
    {
        "categoria": "retrieval",
        "intencion": "usar_parent_document",
        "objetivo": "parent_document",
        "pregunta": "Por que Natalia necesita conversacion completa y no solo chunk para perfil {perfil}?",
        "colecciones": "natalia_success_cases|natalia_books_kb",
        "evidencia": "Patron Chroma indice y SQLite fuente de verdad.",
        "ideal": "Recuperar ID en Chroma y rehidratar conversacion completa desde SQLite.",
        "fallo": "Responder con un fragmento cortado sin contexto.",
    },
    {
        "categoria": "retrieval",
        "intencion": "fallback_sin_evidencia",
        "objetivo": "abstencion",
        "pregunta": "Que debe pasar si el RAG no encuentra evidencia suficiente para perfil {perfil}?",
        "colecciones": "natalia_success_cases|natalia_negative_cases|natalia_books_kb",
        "evidencia": "Regla anti-alucinacion y abstencion.",
        "ideal": "Dar respuesta prudente o decir que falta evidencia.",
        "fallo": "Inventar resultado, contacto o cita.",
    },
    {
        "categoria": "retrieval",
        "intencion": "libros_solo_maximus",
        "objetivo": "fuentes",
        "pregunta": "Cuando deben usarse los libros con perfil {perfil}: Natalia o Maximus?",
        "colecciones": "natalia_books_kb|natalia_success_cases",
        "evidencia": "Libros son teoria para Maximus, no voz directa de mujer.",
        "ideal": "Maximus usa libros para explicar; Natalia prioriza casos reales.",
        "fallo": "Natalia responde como teoria de libro.",
    },
]


def build_rows() -> list[dict]:
    rows = []
    for intent in INTENTS + EXTRA_INTENTS:
        for profile, profile_note in PROFILES:
            rows.append(
                {
                    "id": f"RAG-{len(rows) + 1:03d}",
                    "categoria": intent["categoria"],
                    "intencion": intent["intencion"],
                    "perfil": profile,
                    "perfil_nota": profile_note,
                    "objetivo": intent["objetivo"],
                    "pregunta": intent["pregunta"].format(perfil=profile),
                    "colecciones_esperadas": intent["colecciones"],
                    "evidencia_esperada": intent["evidencia"],
                    "respuesta_ideal_resumida": intent["ideal"],
                    "criterios_de_fallo": intent["fallo"],
                }
            )
    return rows


def write_outputs(rows: list[dict]) -> dict:
    DOCS_DIR.mkdir(exist_ok=True)
    csv_path = DOCS_DIR / "natalia_rag_eval_catalog_v1.csv"
    json_path = DOCS_DIR / "natalia_rag_eval_catalog_v1.json"
    html_path = DOCS_DIR / "natalia_rag_eval_catalog_v1.html"
    fields = list(rows[0].keys())
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    table = "\n".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(row[key]))}</td>"
            for key in [
                "id",
                "categoria",
                "intencion",
                "perfil",
                "objetivo",
                "pregunta",
                "colecciones_esperadas",
                "criterios_de_fallo",
            ]
        )
        + "</tr>"
        for row in rows
    )
    html_path.write_text(
        f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Catalogo QA RAG Natalia v1</title>
  <style>
    body {{ font-family: Arial, sans-serif; background:#10131a; color:#eef2ff; margin:24px; }}
    table {{ border-collapse:collapse; width:100%; font-size:13px; }}
    th, td {{ border:1px solid #2e3445; padding:8px; vertical-align:top; }}
    th {{ background:#1f2635; position:sticky; top:0; }}
    tr:nth-child(even) {{ background:#151b27; }}
  </style>
</head>
<body>
  <h1>Catalogo QA RAG Natalia v1</h1>
  <p>{len(rows)} preguntas etiquetadas para evaluar retrieval, groundedness y enrutamiento de Natalia/Maximus.</p>
  <table>
    <thead><tr><th>ID</th><th>Categoria</th><th>Intencion</th><th>Perfil</th><th>Objetivo</th><th>Pregunta</th><th>Colecciones esperadas</th><th>Criterios de fallo</th></tr></thead>
    <tbody>{table}</tbody>
  </table>
</body>
</html>
""",
        encoding="utf-8",
    )
    return {"csv": str(csv_path), "json": str(json_path), "html": str(html_path)}


def main() -> None:
    rows = build_rows()
    paths = write_outputs(rows)
    print(json.dumps({"rows": len(rows), "paths": paths, "generated_at": datetime.now().isoformat()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
