#!/usr/bin/env python
"""Generate a safe synthesized report from six women/attraction books.

The report uses Chroma for retrieval and SQLite for book/source metadata.
It intentionally avoids printing source passages or literal quotes.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import chromadb

try:
    from ftfy import fix_text as ftfy_fix_text
except Exception:  # pragma: no cover - optional cleanup
    ftfy_fix_text = None


ROOT = Path(__file__).resolve().parent.parent
BOOKS_DB = ROOT / "books_kb" / "books_index.sqlite"
BOOKS_CHROMA = ROOT / "books_kb" / "chroma_books"
DOCS = ROOT / "docs"
OUTPUT_HTML = DOCS / "resumen_6_libros_psicologia_femenina.html"
COLLECTION_NAME = "natalia_books_kb"

DEFAULT_BOOKS = [
    "verdades_sobre_las_mujeres_que_nadie_quiere_que_sepas",
    "la_pildora_roja_verdades_sobre_las_mujeres_y_la_atraccion",
    "speed_seduction_book",
    "el_cerebro_femenino",
    "la_evolucion_del_deseo",
    "la_psicologia_oscura_detras_de_la_atraccion",
]

ATTRACTION_TEMPLATES = [
    {
        "label": "Confianza tranquila",
        "query": "confianza seguridad calma sin necesidad atraer mujeres",
        "tip": "Proyecta calma antes que intensidad: escribe y habla como alguien con vida propia, no como alguien que necesita aprobacion inmediata.",
    },
    {
        "label": "Curiosidad concreta",
        "query": "preguntas carismaticas curiosidad conversacion mujer",
        "tip": "Haz preguntas que abran una historia o preferencia concreta; es mas atractivo que interrogar o lanzar cumplidos genericos.",
    },
    {
        "label": "Humor ligero",
        "query": "humor coqueteo banter tension ligera",
        "tip": "Usa humor para aligerar y crear complicidad, manteniendolo amable; si ella no devuelve energia, baja el juego.",
    },
    {
        "label": "Escalada calibrada",
        "query": "escalada gradual reciprocidad senales avanzar despacio",
        "tip": "Avanza solo cuando hay reciprocidad: respuestas amplias, preguntas de vuelta, risas o interes claro. Sin esas senales, conserva ritmo bajo.",
    },
    {
        "label": "Cierre simple",
        "query": "invitar salir plan concreto cita sin presionar",
        "tip": "Cuando la conversacion ya tiene energia, propone un plan sencillo con una salida facil; claridad sin presion suele ganar a la insistencia.",
    },
    {
        "label": "Presentacion cuidada",
        "query": "presentacion personal fotos perfil higiene atractivo",
        "tip": "La atraccion empieza antes del mensaje: fotos claras, higiene, estilo simple y perfil coherente reducen friccion desde el primer vistazo.",
    },
    {
        "label": "Menos explicacion",
        "query": "no explicar demasiado misterio conversacion interes",
        "tip": "No llenes cada silencio con justificaciones; deja espacio para que ella invierta y pregunte tambien.",
    },
    {
        "label": "Marco respetuoso",
        "query": "respeto limites consentimiento coqueteo no manipular",
        "tip": "Mantiene un marco de respeto: coquetea sin empujar, no uses culpa ni presion, y toma un no o una respuesta fria como informacion.",
    },
    {
        "label": "Valor social real",
        "query": "vida social pasiones independencia atractivo",
        "tip": "Muestra una vida activa y elegible sin presumir: planes, gustos y criterio propio son mas fuertes que buscar validacion.",
    },
    {
        "label": "Texto claro",
        "query": "mensajes claros apps citas ortografia opener responder facil",
        "tip": "En apps, escribe corto, claro y facil de contestar; la buena energia se pierde si el mensaje exige demasiado esfuerzo.",
    },
]

PSYCHOLOGY_TEMPLATES = [
    {
        "label": "Seguridad emocional",
        "query": "mujeres seguridad emocional respeto confianza",
        "tip": "Muchas mujeres evaluan si el hombre se siente seguro de tratar: tono estable, respeto por limites y ausencia de presion pesan mucho.",
    },
    {
        "label": "Reciprocidad",
        "query": "senales interes reciprocidad mujer conversacion",
        "tip": "Interes no es solo responder: mira si ella pregunta, amplia, propone, bromea o sostiene el hilo. Esa reciprocidad guia el ritmo.",
    },
    {
        "label": "Contexto y timing",
        "query": "timing contexto estado emocional mujer cita",
        "tip": "El mismo mensaje puede funcionar o fallar por timing; lee cansancio, ocupacion, velocidad de respuesta y etapa de confianza.",
    },
    {
        "label": "Escucha antes de estrategia",
        "query": "escuchar entender mujeres conversacion necesidades",
        "tip": "Entenderla exige escuchar mas que aplicar tecnica: responde a lo que ella acaba de revelar, no a un guion prefabricado.",
    },
    {
        "label": "Autonomia",
        "query": "independencia decision mujer no controlar atraccion",
        "tip": "La atraccion mejora cuando ella conserva agencia: invita, no arrincones; su decision debe sentirse libre y respetada.",
    },
]

BOOK_SPECIFIC = {
    "verdades_sobre_las_mujeres_que_nadie_quiere_que_sepas": {
        "attraction": [
            ("No buscar aprobacion", "confianza no aprobacion mujer atraccion", "Muestra deseo sin pedir validacion: si tu mensaje busca que ella te apruebe, pierde fuerza; si comunica criterio propio, gana presencia."),
            ("Elegibilidad", "mujeres eligen valor liderazgo limites", "Haz visible que tienes opciones, estandares y vida propia; la atraccion sube cuando no actuas como si cualquier respuesta fuera un premio."),
            ("Liderazgo ligero", "lider iniciativa plan cita mujer", "Toma iniciativa con planes simples y concretos, pero deja espacio para que ella participe; liderar no es imponer."),
            ("Tension sin rudeza", "coqueteo tension respeto limites mujeres", "Crea tension con humor, contraste y seguridad, no con agresividad ni desprecio."),
            ("No entregarse completo", "no entregarse completo interes misterio mujer", "No pongas toda tu disponibilidad sobre la mesa al principio; deja que ella tambien invierta y descubra."),
            ("Diferenciacion", "ser diferente otros hombres mujeres", "Evita sonar como todos: menos cumplido generico y mas observacion especifica o juego conversacional."),
            ("Autocontrol emocional", "emociones control rechazo mujeres", "Si ella tarda, duda o te prueba, responde con calma; perder compostura baja tu atractivo."),
            ("Cierre con marco", "cierre cita plan whatsapp mujer", "Cuando hay energia, cierra con un plan claro o intercambio de contacto, no con una peticion insegura."),
            ("Respeto por limites", "limites respeto no presion mujer", "Mantener limites propios y respetar los de ella hace que el juego se sienta seguro y adulto."),
            ("Congruencia", "congruencia palabras acciones atraccion mujeres", "Lo que dices debe coincidir con tu energia y acciones; la incongruencia se percibe rapido."),
        ],
        "psychology": [
            ("Eleccion", "mujeres eligen seleccion atraccion", "El libro presenta a la mujer como agente de seleccion: conviene entender que ella evalua coherencia, valor y seguridad."),
            ("Pruebas sociales", "mujeres prueba hombre confianza", "Algunas respuestas frias o retadoras pueden funcionar como filtro; lo util es no reaccionar con ansiedad."),
            ("Inversion", "inversion mujer hombre conversacion", "La atraccion crece cuando ambos invierten; si solo empujas tu, la dinamica se desequilibra."),
            ("Seguridad", "mujer seguridad emocional lider", "La seguridad no es sumision: es sentir que el hombre tiene calma, criterio y respeto."),
            ("Polaridad", "polaridad masculino femenino deseo", "El libro trabaja la idea de polaridad: iniciativa masculina con receptividad femenina, sin convertirlo en rigidez."),
        ],
    },
    "la_pildora_roja_verdades_sobre_las_mujeres_y_la_atraccion": {
        "attraction": [
            ("Realismo emocional", "atraccion mujeres realidad deseo", "No idealices: conversa desde realidad y observacion, no desde fantasia sobre quien quieres que ella sea."),
            ("Valor antes de demanda", "valor hombre demanda atencion mujer", "Antes de pedir atencion, muestra valor contextual: humor, presencia, plan o lectura social."),
            ("No negociar deseo", "deseo atraccion no negociar mujer", "El deseo no se convence con argumentos largos; se cultiva con energia, contexto y reciprocidad."),
            ("Marco propio", "marco hombre mujer atraccion", "Mantener tu marco significa no abandonar tus gustos, tiempo o limites para comprar interes."),
            ("Seleccion mutua", "seleccion mutua pareja mujer hombre", "Evalua tambien si ella encaja contigo; eso cambia el tono de necesidad por curiosidad."),
            ("Claridad sin rudeza", "hombre directo claro mujer atraccion", "Ser claro ayuda, pero la claridad no necesita sonar dura: mejor directo, breve y humano."),
            ("Evitar pedestal", "pedestal mujer aprobacion atraccion", "No la pongas en pedestal por apariencia; trata su atencion como valiosa, pero no como inalcanzable."),
            ("Cierre oportuno", "momento cita numero whatsapp mujer", "Pide WhatsApp o cita cuando haya senales; pedirlo sin energia parece atajo ansioso."),
            ("Gestion del rechazo", "rechazo mujer hombre compostura", "Si no hay interes, retirarte bien conserva dignidad y abre aprendizaje."),
            ("Coherencia masculina", "coherencia hombre deseo mujer", "La coherencia entre intencion, tono y accion pesa mas que frases perfectas."),
        ],
        "psychology": [
            ("Atraccion no es justicia", "atraccion no justicia deseo mujeres", "El libro remarca que la atraccion no siempre sigue reglas de merecimiento; conviene observar patrones, no quejarse."),
            ("Filtros", "filtros mujer pareja atractivo", "Muchas mujeres filtran por seguridad, estatus contextual, energia y consistencia."),
            ("Deseo implicito", "deseo implicito mujeres atraccion", "El deseo suele comunicarse por senales indirectas; hay que leer ritmo, energia y disponibilidad."),
            ("No dependencia", "dependencia emocional hombre mujer", "La dependencia emocional reduce atractivo porque desplaza la relacion hacia necesidad."),
            ("Lectura social", "lectura social mujer hombre", "Entender contexto social evita mensajes que tecnicamente son buenos pero llegan en mal momento."),
        ],
    },
    "speed_seduction_book": {
        "attraction": [
            ("Lenguaje sensorial", "lenguaje sensorial emocion mujer seduccion", "Usa lenguaje que evoque experiencias, no solo informacion; una imagen concreta suele activar mas emocion que una explicacion."),
            ("Estado emocional", "estado emocional seduccion conversacion", "La conversacion funciona mejor si cambia el estado emocional: curiosidad, juego, comodidad o anticipacion."),
            ("Preguntas evocadoras", "preguntas evocadoras imaginacion mujer", "Pregunta de forma que ella imagine una escena o sensacion, en vez de responder si/no."),
            ("Ritmo verbal", "ritmo pausa conversacion seduccion", "Alterna frases cortas, pausas y detalles; no satures con monologos."),
            ("Asociacion positiva", "asociacion emociones positivas contigo", "Vincula tu presencia con emociones agradables, pero sin manipular ni presionar."),
            ("Calibracion consciente", "calibracion senales respuesta mujer", "Si ella se abre, profundiza; si se cierra, vuelve a comodidad o cambia de tema."),
            ("Cierre emocional", "cierre cita emocion anticipacion", "Cierra cuando la emocion esta arriba, no cuando el chat ya se agoto."),
            ("Evitar tecnicismo visible", "tecnica visible seduccion natural", "La tecnica debe quedarse invisible; si ella siente guion, baja la autenticidad."),
            ("Consentimiento verbal", "consentimiento respeto seduccion", "Todo avance debe mantener agencia; lenguaje adulto no justifica presion."),
            ("Curiosidad hipnotica segura", "curiosidad imaginacion seduccion segura", "Puedes crear intriga con imaginacion y humor, manteniendo respeto y claridad."),
        ],
        "psychology": [
            ("Asociaciones", "asociaciones emocionales atraccion", "El libro se centra en como las asociaciones emocionales influyen en el deseo."),
            ("Imaginacion", "imaginacion deseo mujer lenguaje", "La imaginacion puede intensificar interes cuando se usa con juego y comodidad."),
            ("Estado antes que logica", "estado emocional logica atraccion", "La respuesta emocional pesa mas que la argumentacion racional."),
            ("Calibracion", "calibracion respuesta no verbal mujer", "Observar microcambios en respuesta ayuda a ajustar ritmo."),
            ("Etica del lenguaje", "lenguaje manipulacion consentimiento seduccion", "Por su enfoque persuasivo, Maximus debe usarlo con filtro de consentimiento y no como manipulacion."),
        ],
    },
    "el_cerebro_femenino": {
        "attraction": [
            ("Seguridad biologica", "cerebro femenino seguridad confianza estres", "La seguridad emocional reduce friccion: si tu tono genera estres, la atraccion pierde terreno."),
            ("Escucha empatica", "cerebro femenino escucha empatia comunicacion", "La conexion mejora cuando ella siente que registras matices emocionales, no solo datos."),
            ("Contexto hormonal", "hormonas mujer estado emocional relacion", "El estado emocional y corporal cambia la receptividad; no interpretes todo como rechazo personal."),
            ("Vinculo progresivo", "vinculo oxitocina confianza mujer", "Construye confianza por consistencia y pequenas experiencias positivas, no por intensidad brusca."),
            ("Comunicacion clara", "comunicacion femenina claridad emocional", "Mensajes claros y sensibles al contexto funcionan mejor que ambiguedad fria."),
            ("No activar amenaza", "amenaza estres mujer cerebro", "Evita presion, burla pesada o insistencia: activan defensa en vez de curiosidad."),
            ("Validar sin someterse", "validacion emocional mujer pareja", "Reconocer emociones no significa perder marco; significa entender antes de responder."),
            ("Ritmo relacional", "ritmo relacion mujer cerebro", "El avance gradual da tiempo a que se forme confianza."),
            ("Memoria emocional", "memoria emocional mujer relacion", "Los detalles importan: recordar algo que dijo comunica atencion real."),
            ("Calma masculina", "calma hombre estres mujer atraccion", "La calma estable hace que el contacto se sienta mas seguro y atractivo."),
        ],
        "psychology": [
            ("Empatia", "cerebro femenino empatia comunicacion", "El libro enfatiza sistemas de comunicacion y empatia como parte central de la experiencia femenina."),
            ("Estres", "estres cortisol mujer cerebro", "El estres afecta receptividad y deseo; conviene leer carga emocional antes de avanzar."),
            ("Vinculo", "oxitocina vinculo mujer cerebro", "La confianza se fortalece con consistencia y experiencias positivas repetidas."),
            ("Cambios vitales", "cerebro femenino etapas vida", "La psicologia femenina cambia por etapas, contexto y biologia; no hay una sola regla universal."),
            ("Lenguaje emocional", "lenguaje emocional mujer cerebro", "La conversacion significativa suele integrar emocion, contexto y detalle."),
        ],
    },
    "la_evolucion_del_deseo": {
        "attraction": [
            ("Senales de valor", "evolucion deseo valor pareja mujer", "Comunica valor de forma observable: estabilidad, criterio, competencia social y confiabilidad."),
            ("Preferencias evolucionadas", "preferencias mujeres pareja evolucion", "El atractivo se entiende mejor como combinacion de senales: recursos, seguridad, salud, estatus y trato."),
            ("Competencia sin fanfarronear", "estatus competencia atraccion mujer", "Mostrar competencia funciona mejor cuando es natural, no presumida."),
            ("Compromiso creible", "compromiso pareja mujer deseo", "Si buscas algo mas que chat, la consistencia hace creible tu intencion."),
            ("Diferenciacion sexual", "diferencias sexuales deseo hombres mujeres", "Entender diferencias de preferencias evita mensajes que solo apelan a lo que atrae a hombres."),
            ("Cita con valor contextual", "cita plan valor contexto pareja", "Propón planes que muestren criterio y cuidado por contexto, no solo disponibilidad."),
            ("Humor como inteligencia", "humor inteligencia atractivo pareja", "El humor puede operar como senal de inteligencia social si no humilla ni fuerza."),
            ("Evitar celos forzados", "celos pareja evolucion deseo", "El libro analiza celos y competencia, pero en apps conviene no manipular con inseguridad."),
            ("Fiabilidad", "fiabilidad pareja mujer deseo", "Ser confiable pesa: prometer poco y cumplir sube valor relacional."),
            ("Seleccion reciproca", "seleccion pareja evolucion deseo mujer", "No solo busques gustar; evalua compatibilidad real."),
        ],
        "psychology": [
            ("Preferencias", "mujeres preferencias pareja evolucion", "El libro muestra patrones de preferencia femenina ligados a seguridad, recursos, compromiso y compatibilidad."),
            ("Estrategias", "estrategias apareamiento mujeres hombres", "Hay estrategias de corto y largo plazo; confundirlas causa errores de comunicacion."),
            ("Celos", "celos evolucion pareja mujer", "Los celos aparecen como mecanismo de proteccion del vinculo, no como herramienta para provocar."),
            ("Compromiso", "compromiso mujer pareja evolucion", "La percepcion de compromiso cambia el significado de las acciones."),
            ("Contexto cultural", "cultura deseo pareja evolucion", "La biologia importa, pero cultura y contexto modulan las decisiones."),
        ],
    },
    "la_psicologia_oscura_detras_de_la_atraccion": {
        "attraction": [
            ("Leer influencia", "psicologia oscura influencia atraccion", "Aprende a detectar dinamicas de influencia para no caer ni hacer caer en juegos daninos."),
            ("Persuasion etica", "persuasion etica atraccion consentimiento", "Si usas persuasion, que sea para claridad y comodidad, no para anular decision."),
            ("Marco firme", "marco firme manipulacion atraccion", "Un marco firme te protege de manipulacion y evita que intentes controlar."),
            ("No explotar vulnerabilidad", "vulnerabilidad manipular mujer atraccion", "Nunca conviertas una vulnerabilidad emocional en palanca; eso destruye confianza."),
            ("Lenguaje claro", "lenguaje persuasion comunicacion atraccion", "La claridad persuasiva debe ayudar a decidir, no confundir."),
            ("Detectar dependencia", "dependencia emocional psicologia oscura", "Si la dinamica se vuelve dependencia, baja intensidad y vuelve a respeto/autonomia."),
            ("Fronteras", "limites fronteras psicologia oscura", "Define limites propios y respeta los de ella; sin limites, la atraccion se contamina."),
            ("Desactivar juegos", "juegos mentales atraccion manipular", "Si aparecen juegos mentales, no escales: vuelve a comunicacion directa."),
            ("Intensidad responsable", "intensidad emocional atraccion responsabilidad", "Lo intenso puede atraer, pero sin responsabilidad se vuelve presion."),
            ("Cierre transparente", "cierre whatsapp cita transparencia", "Pedir WhatsApp o cita debe ser transparente: motivo claro, opcion libre y cero culpa."),
        ],
        "psychology": [
            ("Manipulacion", "manipulacion psicologia oscura relacion", "El libro ayuda a reconocer herramientas manipulativas; Maximus debe explicarlas como riesgos, no como instrucciones de abuso."),
            ("Vulnerabilidad", "vulnerabilidad emocional atraccion", "La vulnerabilidad puede crear intimidad, pero explotarla es una linea roja."),
            ("Control", "control relacion psicologia oscura", "El deseo de controlar revela inseguridad; la conexion sana conserva agencia."),
            ("Persuasion", "persuasion atraccion lenguaje", "Persuasion no es obligar: bien usada ordena una propuesta y reduce friccion."),
            ("Autonomia", "autonomia mujer consentimiento", "La psicologia femenina no debe leerse como manual de control, sino como mapa para entender y respetar decisiones."),
        ],
    },
}


@dataclass(frozen=True)
class Book:
    id: int
    slug: str
    title: str
    author: str
    category: str
    total_chunks: int


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(BOOKS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def clean_display(value: Any) -> str:
    text = str(value or "")
    if ftfy_fix_text is not None:
        for _ in range(2):
            fixed = ftfy_fix_text(text)
            if fixed == text:
                break
            text = fixed
    text = re.sub(r"\s+", " ", text).strip()
    return text


REPORT_STOPWORDS = {
    "para",
    "pero",
    "como",
    "cuando",
    "donde",
    "porque",
    "tambien",
    "también",
    "desde",
    "hasta",
    "este",
    "esta",
    "estos",
    "estas",
    "ellas",
    "ellos",
    "hacia",
    "sobre",
    "entre",
    "tiene",
    "tienes",
    "puede",
    "pueden",
    "hacer",
    "debe",
    "debes",
    "con",
    "los",
    "las",
    "una",
    "uno",
    "del",
    "que",
}


def report_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-záéíóúñü0-9]{4,}", clean_display(text).lower())
        if token not in REPORT_STOPWORDS
    }


def parse_concept_tags(raw: Any) -> dict[str, list[str]]:
    try:
        data = json.loads(str(raw or "{}"))
    except Exception:
        data = []
    if isinstance(data, dict):
        tags = data.get("tags") if isinstance(data.get("tags"), list) else []
        super_tags = data.get("super_tags") if isinstance(data.get("super_tags"), list) else []
        return {
            "tags": [clean_display(item) for item in tags if clean_display(item)],
            "super_tags": [clean_display(item) for item in super_tags if clean_display(item)],
        }
    if isinstance(data, list):
        return {"tags": [clean_display(item) for item in data if clean_display(item)], "super_tags": []}
    return {"tags": [], "super_tags": []}


def resolve_books(conn: sqlite3.Connection, selectors: list[str]) -> tuple[list[Book], list[str]]:
    books: list[Book] = []
    missing: list[str] = []
    seen: set[int] = set()
    for selector in selectors:
        row = conn.execute("SELECT * FROM books WHERE slug = ?", (selector,)).fetchone()
        if row is None:
            needle = f"%{normalize(selector).replace(' ', '%')}%"
            row = conn.execute(
                """
                SELECT * FROM books
                WHERE lower(replace(replace(titulo, '_', ' '), '-', ' ')) LIKE ?
                   OR lower(replace(replace(slug, '_', ' '), '-', ' ')) LIKE ?
                ORDER BY id
                LIMIT 1
                """,
                (needle, needle),
            ).fetchone()
        if row is None:
            missing.append(selector)
            continue
        if int(row["id"]) in seen:
            continue
        seen.add(int(row["id"]))
        books.append(
            Book(
                id=int(row["id"]),
                slug=str(row["slug"]),
                title=str(row["titulo"]),
                author=str(row["autor"]),
                category=str(row["categoria"] or ""),
                total_chunks=int(row["total_chunks"] or 0),
            )
        )
    return books, missing


def chunk_row(conn: sqlite3.Connection, book: Book, chunk_index: int | None) -> sqlite3.Row | None:
    if chunk_index is None:
        return None
    return conn.execute(
        "SELECT * FROM chunks WHERE book_id = ? AND chunk_index = ?",
        (book.id, int(chunk_index)),
    ).fetchone()


def coalesce(*values: Any) -> str:
    for value in values:
        if value is not None and str(value).strip() not in {"", "None"}:
            return str(value)
    return ""


def source_from_hit(conn: sqlite3.Connection, book: Book, meta: dict[str, Any]) -> dict[str, str]:
    raw_chunk = meta.get("chunk_index")
    try:
        chunk_index = int(raw_chunk) if raw_chunk is not None else None
    except (TypeError, ValueError):
        chunk_index = None
    chunk = chunk_row(conn, book, chunk_index)
    section = coalesce(
        meta.get("section_title"),
        chunk["section_title"] if chunk and "section_title" in chunk.keys() else None,
        chunk["capitulo"] if chunk and "capitulo" in chunk.keys() else None,
        "Sin seccion",
    )
    page = coalesce(
        meta.get("page_estimate"),
        chunk["page_estimate"] if chunk and "page_estimate" in chunk.keys() else None,
        chunk["pagina_inicio"] if chunk and "pagina_inicio" in chunk.keys() else None,
        "s/d",
    )
    return {
        "book": clean_display(book.title),
        "author": clean_display(book.author),
        "section_title": clean_display(section),
        "page_estimate": clean_display(page),
        "chunk_index": str(chunk_index if chunk_index is not None else "s/d"),
    }


def query_book(
    conn: sqlite3.Connection,
    collection: Any,
    book: Book,
    query: str,
    n_results: int = 4,
) -> dict[str, Any]:
    result = collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"book_slug": book.slug},
        include=["metadatas", "distances"],
    )
    metas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    if not metas:
        return {"source": source_from_hit(conn, book, {}), "distance": None, "hit_count": 0}
    best = metas[0] or {}
    return {
        "source": source_from_hit(conn, book, best),
        "distance": round(float(distances[0]), 4) if distances else None,
        "hit_count": len(metas),
    }


def build_items(
    conn: sqlite3.Connection,
    collection: Any,
    book: Book,
    templates: list[dict[str, str]],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, template in enumerate(templates, start=1):
        hit = query_book(conn, collection, book, template["query"])
        items.append(
            {
                "index": index,
                "label": template["label"],
                "tip": template["tip"],
                "source": hit["source"],
                "distance": hit["distance"],
                "hit_count": hit["hit_count"],
            }
        )
    return items


def query_structured_principle(
    conn: sqlite3.Connection,
    book: Book,
    query: str,
    label: str,
    tip: str,
) -> dict[str, Any]:
    try:
        rows = conn.execute(
            """
            SELECT id, principle, category, concept_tags, risk_level, voice_policy,
                   natalia_use, maximus_use, source_reference
            FROM book_principles
            WHERE book_id = ?
            """,
            (book.id,),
        ).fetchall()
    except sqlite3.Error:
        return {"hit_count": 0, "principle": "", "category": "", "risk_level": "", "source_reference": "", "link": None}

    query_tokens = report_tokens(f"{query} {label} {tip}")
    scored: list[tuple[int, sqlite3.Row, dict[str, list[str]]]] = []
    for row in rows:
        concept_meta = parse_concept_tags(row["concept_tags"])
        haystack = " ".join(
            [
                str(row["principle"] or ""),
                str(row["category"] or ""),
                " ".join(concept_meta["tags"]),
                " ".join(concept_meta["super_tags"]),
                str(row["source_reference"] or ""),
            ]
        )
        common = len(query_tokens & report_tokens(haystack))
        if common <= 0:
            continue
        score = common
        if row["risk_level"] == "low":
            score += 2
        elif row["risk_level"] == "medium":
            score += 1
        if row["category"] and normalize(str(row["category"])) in normalize(f"{query} {label}"):
            score += 2
        scored.append((score, row, concept_meta))
    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored:
        return {"hit_count": 0, "principle": "", "category": "", "risk_level": "", "source_reference": "", "link": None}

    score, row, concept_meta = scored[0]
    link = conn.execute(
        """
        SELECT post_id, objective, link_score, confidence, evidence_summary
        FROM principle_case_links
        WHERE principle_id = ?
        ORDER BY link_score DESC
        LIMIT 1
        """,
        (row["id"],),
    ).fetchone()
    return {
        "hit_count": len(scored),
        "match_score": score,
        "principle_id": row["id"],
        "principle": clean_display(row["principle"]),
        "category": clean_display(row["category"]),
        "concepts": ", ".join(concept_meta["super_tags"] + concept_meta["tags"]),
        "risk_level": clean_display(row["risk_level"]),
        "voice_policy": clean_display(row["voice_policy"]),
        "natalia_use": clean_display(row["natalia_use"]),
        "maximus_use": clean_display(row["maximus_use"]),
        "source_reference": clean_display(row["source_reference"]),
        "link": dict(link) if link is not None else None,
    }


def build_v2_comparison_items(
    conn: sqlite3.Connection,
    book: Book,
    templates: list[dict[str, str]],
) -> list[dict[str, Any]]:
    items = []
    for index, template in enumerate(templates, start=1):
        principle = query_structured_principle(conn, book, template["query"], template["label"], template["tip"])
        items.append(
            {
                "index": index,
                "label": template["label"],
                "v1_tip": template["tip"],
                "v2_principle": principle,
            }
        )
    return items


def specific_templates(book: Book, group: str) -> list[dict[str, str]]:
    payload = BOOK_SPECIFIC.get(book.slug, {})
    rows = payload.get(group, [])
    if not rows:
        return ATTRACTION_TEMPLATES if group == "attraction" else PSYCHOLOGY_TEMPLATES
    return [{"label": label, "query": query, "tip": tip} for label, query, tip in rows]


def td(value: Any) -> str:
    return f"<td>{html.escape(clean_display(value))}</td>"


FRIENDLY_CATEGORIES = {
    "psicologia_femenina_preferencias": "Psicologia femenina y preferencias",
    "humor_tension_sana": "Humor y tension sana",
    "lectura_contexto_timing": "Lectura de contexto y timing",
    "cierre_transparente": "Cierre transparente",
    "presentacion_perfil": "Presentacion y perfil",
    "valor_congruencia": "Valor y congruencia",
    "agencia_limites": "Agencia, consentimiento y limites",
    "fuente_teoria_vs_caso": "Teoria aplicada a casos",
    "comunicacion_escucha": "Comunicacion y escucha",
    "reciprocidad_inversion": "Reciprocidad e inversion",
    "influencia_riesgo_manipulacion": "Influencia de alto riesgo",
}


FRIENDLY_RISK = {
    "low": "bajo",
    "medium": "medio",
    "high": "alto",
}


FRIENDLY_POLICY = {
    "silent_strategy": "uso silencioso para Natalia",
    "silent_strategy_guarded": "uso silencioso con cuidado",
    "maximus_only_review": "solo revision de Maximus",
}


def friendly_category(value: Any) -> str:
    raw = clean_display(value)
    return FRIENDLY_CATEGORIES.get(raw, raw.replace("_", " ").strip())


def friendly_risk_policy(risk: Any, policy: Any) -> str:
    risk_text = FRIENDLY_RISK.get(clean_display(risk), clean_display(risk) or "s/d")
    policy_text = FRIENDLY_POLICY.get(clean_display(policy), clean_display(policy) or "s/d")
    return f"riesgo {risk_text}; {policy_text}"


def human_source_reference(value: Any) -> str:
    text = clean_display(value)
    text = re.sub(r"\s*\|\s*pag_estimada=", " | pagina estimada ", text)
    text = re.sub(r"\s*\|\s*chunk=", " | segmento ", text)
    text = text.replace("sin seccion", "sin seccion registrada")
    text = text.replace("n/d", "sin dato")
    return text


def human_case_link(link: dict[str, Any]) -> str:
    if not link:
        return "Sin caso real enlazado"
    parts = [
        f"Post {clean_display(link.get('post_id'))}",
        f"objetivo: {clean_display(link.get('objective')) or 's/d'}",
        f"confianza: {clean_display(link.get('confidence')) or 's/d'}",
        f"score enlace: {clean_display(link.get('link_score')) or 's/d'}",
    ]
    return "; ".join(parts)


def render_tip_table(items: list[dict[str, Any]]) -> str:
    rows = []
    for item in items:
        source = item["source"]
        rows.append(
            "<tr>"
            + td(item["index"])
            + td(item["label"])
            + td(item["tip"])
            + td(f"{source['book']} - {source['author']}")
            + td(source["section_title"])
            + td(source["page_estimate"])
            + td(source["chunk_index"])
            + "</tr>"
        )
    return "\n".join(rows)


def render_v2_comparison_table(items: list[dict[str, Any]]) -> str:
    rows = []
    for item in items:
        principle = item["v2_principle"]
        link = principle.get("link") or {}
        rows.append(
            "<tr>"
            + td(item["index"])
            + td(item["label"])
            + td(item["v1_tip"])
            + td(principle.get("principle") or "Sin principio estructurado")
            + td(friendly_category(principle.get("category") or ""))
            + td(friendly_risk_policy(principle.get("risk_level"), principle.get("voice_policy")))
            + td(human_source_reference(principle.get("source_reference") or ""))
            + td(human_case_link(link))
            + "</tr>"
        )
    return "\n".join(rows)


def render_book_section(book_payload: dict[str, Any]) -> str:
    book = book_payload["book"]
    attraction_rows = render_tip_table(book_payload["attraction_tips"])
    psychology_rows = render_tip_table(book_payload["psychology_tips"])
    v2_html = ""
    if book_payload.get("attraction_v2") or book_payload.get("psychology_v2"):
        attraction_v2_rows = render_v2_comparison_table(book_payload.get("attraction_v2", []))
        psychology_v2_rows = render_v2_comparison_table(book_payload.get("psychology_v2", []))
        v2_html = f"""
  <h3>Comparacion v1 vs v2: principios estructurados enlazados a casos reales</h3>
  <p class="note">V1 es la sintesis anterior del reporte. V2 muestra el principio estructurado recuperado de los libros y su enlace a caso real cuando existe. Natalia debe usarlo en silencio; Maximus puede explicarlo.</p>
  <h4>10 tips de atraccion: v1 vs v2</h4>
  <table>
    <thead><tr><th>#</th><th>Tema</th><th>Respuesta v1</th><th>Principio v2 estructurado</th><th>Categoria v2</th><th>Uso recomendado</th><th>Fuente v2</th><th>Caso real enlazado</th></tr></thead>
    <tbody>{attraction_v2_rows}</tbody>
  </table>
  <h4>5 tips de psicologia femenina: v1 vs v2</h4>
  <table>
    <thead><tr><th>#</th><th>Tema</th><th>Respuesta v1</th><th>Principio v2 estructurado</th><th>Categoria v2</th><th>Uso recomendado</th><th>Fuente v2</th><th>Caso real enlazado</th></tr></thead>
    <tbody>{psychology_v2_rows}</tbody>
  </table>
"""
    return f"""
<section class="book">
  <h2>{html.escape(book.title)}</h2>
  <p class="meta"><b>Autor:</b> {html.escape(book.author)} &middot; <b>Slug:</b> {html.escape(book.slug)} &middot; <b>Categoria:</b> {html.escape(book.category)} &middot; <b>Chunks:</b> {book.total_chunks}</p>
  <p class="note">Nota: los tips son sintesis operativas basadas en recuperacion local; no son citas literales ni reemplazan el contexto completo del libro.</p>
  <h3>10 tips de seduccion/atraccion</h3>
  <table>
    <thead><tr><th>#</th><th>Principio</th><th>Sintesis</th><th>Libro + autor</th><th>Seccion</th><th>Pagina estimada</th><th>Segmento</th></tr></thead>
    <tbody>{attraction_rows}</tbody>
  </table>
  <h3>5 tips para entender psicologia femenina</h3>
  <table>
    <thead><tr><th>#</th><th>Principio</th><th>Sintesis</th><th>Libro + autor</th><th>Seccion</th><th>Pagina estimada</th><th>Segmento</th></tr></thead>
    <tbody>{psychology_rows}</tbody>
  </table>
  {v2_html}
</section>
"""


def source_badges(payloads: list[dict[str, Any]]) -> str:
    seen: dict[str, dict[str, str]] = {}
    for payload in payloads:
        for group in ("attraction_tips", "psychology_tips"):
            for item in payload[group]:
                source = item["source"]
                key = "|".join(
                    [
                        source["book"],
                        source["author"],
                        source["section_title"],
                        source["page_estimate"],
                        source["chunk_index"],
                    ]
                )
                seen[key] = source
    badges = []
    for idx, source in enumerate(list(seen.values())[:18], start=1):
        badges.append(
            f"<li>S{idx}: {html.escape(source['book'])} - {html.escape(source['author'])}; "
            f"{html.escape(source['section_title'])}; pag. {html.escape(source['page_estimate'])}; "
            f"segmento {html.escape(source['chunk_index'])}</li>"
        )
    return "\n".join(badges)


def render_final_framework(payloads: list[dict[str, Any]]) -> str:
    sources = source_badges(payloads)
    return f"""
<section class="final">
  <h2>Formula practica para apps de citas</h2>
  <p class="note">Sintesis transversal, no cita literal. En contenido adulto o manipulador, se conserva solo el analisis util bajo consentimiento, respeto y agencia mutua.</p>
  <ol>
    <li><b>Perfil legible:</b> fotos claras, senal de vida real y bio breve con una puerta conversacional.</li>
    <li><b>Abridor situado:</b> comenta algo especifico de su perfil o una eleccion divertida, sin sexualizar de entrada.</li>
    <li><b>Intercambio con reciprocidad:</b> alterna humor, curiosidad y pequenas revelaciones propias; no conviertas el chat en entrevista.</li>
    <li><b>Calibracion:</b> si ella amplia y pregunta, sube un poco la intencion; si responde corto, baja energia o cierra con elegancia.</li>
    <li><b>Cierre concreto:</b> cuando hay energia, propone plan simple, lugar/tipo de actividad y opcion de decir no sin drama.</li>
  </ol>
  <h3>Roleplay hombre/mujer basado en los principios recuperados</h3>
  <div class="chat">
    <p><b>Hombre 1:</b> Vi que tienes una foto en una libreria. Pregunta seria: cafe para leer o cafe para sobrevivir?</p>
    <p><b>Mujer 1:</b> Jajaja, ambas. Pero si el libro esta bueno, el cafe es secundario.</p>
    <p><b>Hombre 2:</b> Buena respuesta. Entonces eres de las que desaparece dos horas si el capitulo pega fuerte.</p>
    <p><b>Mujer 2:</b> Totalmente. Aunque tambien salgo al mundo real, prometo.</p>
    <p><b>Hombre 3:</b> Eso tranquiliza a la sociedad. Que plan del mundo real te recarga mas: caminar, musica o comida rica?</p>
    <p><b>Mujer 3:</b> Caminar y comida rica. Musica depende del dia.</p>
    <p><b>Hombre 4:</b> Buen combo. Yo soy de caminar para elegir lugar y luego fingir que fue planeado.</p>
    <p><b>Mujer 4:</b> Jajaja, estrategia aceptable si el lugar esta bueno.</p>
    <p><b>Hombre 5:</b> Entonces tengo una hipotesis: paseo corto + algo rico gana a entrevista eterna por chat.</p>
    <p><b>Mujer 5:</b> Puede ser. Depende de la compania.</p>
    <p><b>Hombre 6:</b> Justo. Si te late, esta semana probamos una version simple: cafe y caminata, sin ceremonia.</p>
    <p><b>Mujer 6:</b> Me gusta. Que dia pensabas?</p>
    <p><b>Hombre 7:</b> Jueves tarde o sabado a media manana. Si alguno te encaja, lo armamos; si no, cero presion.</p>
    <p><b>Mujer 7:</b> Sabado a media manana suena bien :)</p>
  </div>
  <h3>Fuentes usadas en la sintesis transversal</h3>
  <ul class="sources">{sources}</ul>
</section>
"""


def v2_stats(payload: dict[str, Any]) -> dict[str, int]:
    total = 0
    hits = 0
    linked = 0
    high_risk = 0
    categories: set[str] = set()
    for book_payload in payload["books"]:
        for group in ("attraction_v2", "psychology_v2"):
            for item in book_payload.get(group, []):
                total += 1
                principle = item["v2_principle"]
                if principle.get("hit_count"):
                    hits += 1
                if principle.get("link"):
                    linked += 1
                if principle.get("risk_level") == "high":
                    high_risk += 1
                if principle.get("category"):
                    categories.add(str(principle["category"]))
    return {
        "total": total,
        "hits": hits,
        "linked": linked,
        "high_risk": high_risk,
        "categories": len(categories),
    }


def render_v2_overview(payload: dict[str, Any]) -> str:
    if not payload.get("include_v2"):
        return ""
    stats = v2_stats(payload)
    original_size = OUTPUT_HTML.stat().st_size if OUTPUT_HTML.exists() else 0
    return f"""
<section class="final">
  <h2>Comparacion global v1 vs v2</h2>
  <p class="note">La v2 conserva la estructura del reporte original, pero agrega una capa de principios estructurados creada despues de integrar los 6 libros. La comparacion no inventa texto: contrasta la sintesis v1 contra principios guardados en la base local y enlaces a casos reales.</p>
  <table>
    <thead><tr><th>Metrica</th><th>Resultado</th></tr></thead>
    <tbody>
      <tr><td>Archivo original comparado</td><td>{html.escape(str(OUTPUT_HTML))}</td></tr>
      <tr><td>Tamano HTML original</td><td>{original_size} bytes</td></tr>
      <tr><td>Respuestas evaluadas en v2</td><td>{stats['total']}</td></tr>
      <tr><td>Principios estructurados encontrados</td><td>{stats['hits']}/{stats['total']}</td></tr>
      <tr><td>Principios con caso real enlazado</td><td>{stats['linked']}/{stats['total']}</td></tr>
      <tr><td>Categorias superiores usadas</td><td>{stats['categories']}</td></tr>
      <tr><td>Principios de riesgo alto visibles en comparacion</td><td>{stats['high_risk']} (solo para revision/Maximus; Natalia no debe imitarlos)</td></tr>
    </tbody>
  </table>
</section>
"""


def render_html(payload: dict[str, Any]) -> str:
    book_sections = "\n".join(render_book_section(book_payload) for book_payload in payload["books"])
    missing = payload["missing"]
    missing_html = ""
    if missing:
        missing_items = "".join(f"<li>{html.escape(item)}</li>" for item in missing)
        missing_html = f"""
<section class="warning">
  <h2>Libros faltantes</h2>
  <p>El script no encontro estos slugs/titulos en SQLite, por eso no se incluyeron en el reporte:</p>
  <ul>{missing_items}</ul>
</section>
"""
    final_framework = render_final_framework(payload["books"])
    v2_overview = render_v2_overview(payload)
    generated_at = html.escape(payload["generated_at"])
    suffix = " v2" if payload.get("include_v2") else ""
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Resumen 6 libros psicologia femenina</title>
  <style>
    :root {{ color-scheme: light; --ink:#172026; --muted:#5b6770; --line:#d8dee4; --soft:#f4f7f8; --accent:#0f766e; --warn:#9a3412; }}
    body {{ margin:0; font-family: Arial, Helvetica, sans-serif; color:var(--ink); background:#fff; line-height:1.48; }}
    header {{ background:#e8f3f1; border-bottom:1px solid var(--line); padding:28px max(24px, calc((100vw - 1180px) / 2)); }}
    main {{ max-width:1180px; margin:0 auto; padding:24px; }}
    h1 {{ margin:0 0 8px; font-size:30px; }}
    h2 {{ margin:0 0 10px; font-size:24px; }}
    h3 {{ margin:22px 0 8px; font-size:18px; }}
    section {{ margin:0 0 30px; }}
    .book, .final, .warning {{ border:1px solid var(--line); border-radius:8px; padding:18px; background:#fff; }}
    .meta, .note {{ color:var(--muted); margin:6px 0 12px; }}
    .note {{ border-left:4px solid var(--accent); padding-left:10px; }}
    .warning {{ border-color:#fed7aa; background:#fff7ed; }}
    .warning h2 {{ color:var(--warn); }}
    table {{ width:100%; border-collapse:collapse; margin:8px 0 16px; font-size:13px; }}
    th, td {{ border:1px solid var(--line); padding:8px; vertical-align:top; }}
    th {{ background:var(--soft); text-align:left; }}
    td:nth-child(1), th:nth-child(1) {{ width:38px; text-align:center; }}
    td:nth-child(5), td:nth-child(6), td:nth-child(7) {{ color:var(--muted); }}
    .chat {{ display:grid; grid-template-columns:1fr; gap:6px; background:var(--soft); border:1px solid var(--line); border-radius:8px; padding:12px; }}
    .chat p {{ margin:0; }}
    .sources {{ columns:2; color:var(--muted); }}
    @media (max-width: 760px) {{
      main {{ padding:14px; }}
      table {{ display:block; overflow-x:auto; white-space:nowrap; }}
      .sources {{ columns:1; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Resumen de 6 libros: psicologia femenina, seduccion y atraccion{suffix}</h1>
    <p class="meta">Generado: {generated_at}. Fuente: base local de libros y recuperacion semantica. No contiene texto completo de libros ni citas literales.</p>
  </header>
  <main>
    {missing_html}
    {v2_overview}
    {book_sections}
    {final_framework}
  </main>
</body>
</html>
"""


def build_report(selectors: list[str], include_v2: bool = False) -> dict[str, Any]:
    with connect() as conn:
        books, missing = resolve_books(conn, selectors)
        client = chromadb.PersistentClient(path=str(BOOKS_CHROMA))
        collection = client.get_collection(COLLECTION_NAME)
        payload_books = []
        for book in books:
            attraction_templates = specific_templates(book, "attraction")
            psychology_templates = specific_templates(book, "psychology")
            book_payload = {
                "book": book,
                "attraction_tips": build_items(conn, collection, book, attraction_templates),
                "psychology_tips": build_items(conn, collection, book, psychology_templates),
            }
            if include_v2:
                book_payload["attraction_v2"] = build_v2_comparison_items(conn, book, attraction_templates)
                book_payload["psychology_v2"] = build_v2_comparison_items(conn, book, psychology_templates)
            payload_books.append(
                book_payload
            )
    return {
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "selectors": selectors,
        "missing": missing,
        "books": payload_books,
        "include_v2": include_v2,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--book",
        action="append",
        dest="books",
        help="Slug or title to include. Repeat up to 6 times. Defaults to the built-in six-book list.",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_HTML),
        help="HTML output path. Defaults to the original report path.",
    )
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Include the v1 vs v2 comparison against structured book_principles and linked cases.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selectors = (args.books or DEFAULT_BOOKS)[:6]
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = build_report(selectors, include_v2=args.v2)
    output.write_text(render_html(payload), encoding="utf-8")

    status = {
        "html": str(output),
        "v2": bool(args.v2),
        "requested_books": len(selectors),
        "included_books": len(payload["books"]),
        "missing": payload["missing"],
        "sources_found": sum(
            1
            for book_payload in payload["books"]
            for group in ("attraction_tips", "psychology_tips")
            for item in book_payload[group]
            if item["hit_count"]
        ),
        "expected_sources": len(payload["books"]) * 15,
        "v2_principles_found": sum(
            1
            for book_payload in payload["books"]
            for group in ("attraction_v2", "psychology_v2")
            for item in book_payload.get(group, [])
            if item["v2_principle"].get("hit_count")
        ),
        "v2_expected_principles": len(payload["books"]) * 15 if args.v2 else 0,
        "note": "Sintesis, no citas literales. Contenido adulto/manipulador tratado con consentimiento y respeto.",
    }
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
