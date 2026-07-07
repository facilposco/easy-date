# Revisión senior RAG + Router Natalia/Maximus — instrucciones de implementación para Codex

**Fecha:** 2026-07-06 · **Base revisada:** `arquitectura.html` (886 líneas) + código real de `backend/server.py` (~3.770 líneas, revisado en vivo), `simulador_v1.2.html`, `AGENTS.md`, estructura de carpeta.
**Metodología:** revisión multi-agente con verificación adversarial contra el documento + lectura directa del código. Todo lo citado abajo existe en el código/documento; lo no verificable está marcado como **BRECHA**.

> ⚠️ **Regla de AGENTS.md que aplica a todo este documento:** al implementar cualquier cambio de aquí, documentarlo en `AGENTS.md` **y** `arquitectura.html`. El HTML del simulador se edita vía `build_simulator.py`, no a mano.

---

## 0. Respuesta a la pregunta central: ¿Natalia y Maximus deben ser 1 agente o 2?

**Deben ser 2 agentes (2 prompts, 2 retrievals separados) + 1 router determinista que decide quién habla. Nunca 1 solo agente.**

Razones concretas, ancladas al código actual:

1. **Ya son 2 agentes y esa separación es el activo principal del sistema.** `build_natalia_prompt()` ("Eres Natalia-Persona… no como coach, no expliques teoría") y `build_coach_prompt()` (evaluador JSON con score/suggestions) tienen contratos incompatibles: una debe sonar humana y breve; el otro debe ser pedagógico y estructurado. Un solo prompt que haga ambos roles produce exactamente la contaminación de voz que `natalia_response_is_invalid()` ya castiga (palabras prohibidas: `coach`, `score`, `puntaje`, `rag`, `regla`…). Fusionarlos obligaría a quitar ese guardrail.
2. **Los retrievals son distintos por diseño:** `retrieve_persona_cases()` = pares reales H→M + success cases (sin negativos); `retrieve_coach_cases()` = success + legacy + libros + YouTube + `natalia_negative_cases`. Un agente único con un contexto único mezclaría negativos y teoría en la voz de la chica — violación directa de la "Regla de seguridad RAG" documentada.
3. **La confusión que se observa hoy NO es por tener 2 agentes: es porque el router v0 decide mal y porque, cuando decide "maximus", nadie responde de verdad la pregunta** (ver sección 2). El problema es de orquestación, no de número de agentes.

**Arquitectura correcta (3 piezas):**

```
mensaje del usuario
      │
      ▼
[1] route_turn_request()  ← determinista, local, sin LLM, <1 ms
      │
      ├── route = "natalia"  → [2] Natalia-Persona responde (retrieve_persona_cases)
      │                          + Maximus evalúa el turno EN PARALELO como hoy
      │                          (turn_metrics + modal). Esto no cambia.
      │
      └── route = "maximus"  → [3] Maximus RESPONDE LA PREGUNTA (nuevo prompt Q&A
                                 con retrieve_coach_cases). NO se llama a Natalia,
                                 NO se evalúa el mensaje como flirteo, NO se pierde
                                 vida, NO cambia attraction.
```

**Principio rector: el router decide QUIÉN HABLA, no quién evalúa.** En ruta natalia, el Coach sigue evaluando cada turno (eso no es una fuga: la prohibición real es que la voz del coach jamás se pinte en la burbuja de chat de Natalia).

---

## 1. Estado actual del router v0 (código real, `backend/server.py` ~líneas 3425–3486)

Esto es lo que existe hoy:

```python
MAXIMUS_ROUTE_PATTERNS = [
    r"^\s*maximus\b",
    r"\bcoach\b",
    r"\bque respondo\b",
    r"\bque le respondo\b",
    r"\bque digo\b",
    r"\bque le digo\b",
    r"\bcomo le respondo\b",
    r"\bcomo respondo\b",
    r"\baconsej",
    r"\bconsejo\b",
    r"\bestrategia\b",
    r"\btecnica\b",
    r"\bexplicame\b",
    r"\bexplicacion\b",
    r"\bopener\b",
    r"\babridor\b",
    r"\bprimera cita\b",
    r"\bfotos?\b",
    r"\bperfil\b.*\bfoto",
]

MAXIMUS_STAGE_HINTS = {
    "coach", "study", "estudiar", "game_over", "gameover",
    "summary", "resumen", "free_advice", "maximus",
}

def route_turn_request(request: SimulateTurnRequest) -> Dict[str, Any]:
    message = normalize_route_text(request.user_message)
    context = request.visible_context or {}
    stage = normalize_route_text(str(context.get("mode") or context.get("stage") or context.get("route") or ""))
    reasons: List[str] = []
    if stage in MAXIMUS_STAGE_HINTS:
        reasons.append(f"stage:{stage}")
    for pattern in MAXIMUS_ROUTE_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            reasons.append(f"pattern:{pattern}")
            break
    route = "maximus" if reasons else "natalia"
    return {"route": route, "reasons": reasons, "stage": stage or "chat"}
```

Y en `simulate_turn()` (~líneas 3663–3706), la ruta maximus solo hace esto:

```python
    if route_info["route"] == "maximus":
        lose_life = False
        attraction_delta = 0
    ...
    if route_info["route"] == "maximus":
        natalia_message = maximus_intercept_message()   # texto fijo
        natalia_time = "Maximus"
        natalia_live_used = False
```

---

## 2. Los 6 defectos del router v0 (la causa exacta de la "confusión")

### D1 — Keywords sin destinatario roban mensajes legítimos del juego (el defecto más grave)

El patrón matchea por keyword en cualquier parte del mensaje, sin distinguir si el usuario le habla **a ella** (juego) o **sobre ella** (consulta). Mensajes de juego que hoy se roban:

| Mensaje del usuario (dirigido a Natalia) | Patrón que lo roba | Debería ser |
|---|---|---|
| "qué linda tu **foto** 😍" | `\bfotos?\b` | natalia |
| "me mandas una **foto**?" | `\bfotos?\b` | natalia |
| "¿esta sería nuestra **primera cita**? jaja" | `\bprimera cita\b` | natalia (¡es el objetivo del nivel!) |
| "mi **estrategia** para conquistarte va bien jaja" | `\bestrategia\b` | natalia |
| "no sé **qué digo** cuando te veo" | `\bque digo\b` | natalia |
| "mi **coach** del gym me tiene muerto hoy" | `\bcoach\b` (matchea en cualquier posición) | natalia |
| "tu **perfil** tiene una **foto** en la playa, ¿dónde es?" | `\bperfil\b.*\bfoto` | natalia |

Cada robo = el usuario escribe un mensaje de flirteo válido y en vez de responder Natalia recibe "Te contesta Maximus abajo…". Rompe la inmersión y bloquea el objetivo del nivel (proponer la cita dispara `primera cita` → maximus). **La regla correcta: ninguna keyword enruta sola; enruta el DESTINATARIO** (2ª persona hacia ella = juego; 3ª persona sobre ella / instruccional = coach).

### D2 — Cuando la ruta es maximus, Maximus NO responde la pregunta

El flujo actual en ruta maximus: (a) el Coach **evalúa la meta-pregunta como si fuera un mensaje de flirteo** (`build_coach_prompt` es un evaluador, no un Q&A) → score y feedback sin sentido ("Evalúa mejor el contexto visible antes de responder" ante "¿cómo pido el WhatsApp?"); (b) `natalia_message` se reemplaza por un texto fijo. **El usuario pregunta algo y nadie se lo contesta.** Falta un prompt de respuesta directa del Coach usando `retrieve_coach_cases()`.

### D3 — Se desperdician 2 llamadas Gemini por turno maximus

En ruta maximus igual se ejecutan: la llamada live del Coach (evaluación inútil) y la llamada live de Natalia (cuya respuesta se genera y se descarta en la línea `natalia_message = maximus_intercept_message()`). Con la contingencia 429 y rotación de 3 keys documentada, es cuota quemada en el peor lugar.

### D4 — El interceptor sale en la burbuja de Natalia (contaminación de voz en UI)

`simulador_v1.2.html` **no tiene ningún manejo de `route`** (verificado: cero ocurrencias de "route"/"maximus" en el HTML). El texto "Te contesta Maximus abajo; no voy a mezclar esto con el chat" se renderiza como mensaje de Natalia → Natalia rompe personaje mencionando a Maximus, y ese texto **entra al historial** (`gameState.history`) que luego se manda como `chat_snapshot`/`last_natalia_message` en `visible_context`, contaminando los turnos siguientes de Persona.

### D5 — `MAXIMUS_STAGE_HINTS` nunca dispara desde el frontend real

`buildVisibleContext()` en el HTML solo envía `evaluated_step_id`, `evaluated_step_index`, `last_natalia_message`, `last_user_message`, `chat_snapshot`. Nunca envía `mode`/`stage`/`route`, así que la señal de UI (la más confiable de todas) está muerta.

### D6 — `turn_metrics` y score se calculan sobre la meta-pregunta

En ruta maximus, `turn_metrics_for_message()` analiza "¿qué le respondo?" como si fuera flirteo (sobreinversión, emojis, etc.) y ese ruido va a la telemetría.

---

## 3. Implementación correcta — código completo

### 3.1 Router v1 con lógica de destinatario (reemplaza patrones y `route_turn_request`)

Reemplazar el bloque `MAXIMUS_ROUTE_PATTERNS` / `route_turn_request()` por:

```python
# ---------------------------------------------------------------------------
# Router Natalia/Maximus v1 — determinista, local, sin LLM.
# Regla central: enruta el DESTINATARIO, no la keyword.
#   - 2a persona dirigida a ella  -> juego (natalia)
#   - 3a persona sobre ella / instruccional -> consulta (maximus)
# Precedencia: UI stage > prefijo explicito > señal fuerte > 2 señales débiles > default natalia.
# Ante la duda gana natalia: un falso "juego" se corrige con un toque;
# un falso "maximus" roba un turno legítimo y rompe la inmersión.
# ---------------------------------------------------------------------------

MAXIMUS_STAGE_HINTS = {
    "coach", "study", "estudiar", "game_over", "gameover",
    "summary", "resumen", "free_advice", "maximus",
}

# Prefijo explícito SOLO al inicio del mensaje.
MAXIMUS_PREFIX_RE = re.compile(r"^\s*(?:maximus|coach)\b[\s,:.!¡¿?-]*", re.IGNORECASE)

# Señales FUERTES (1 basta, salvo veto): 3a persona hacia ella + verbo instruccional.
MAXIMUS_STRONG_RES = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bque le (?:digo|respondo|contesto|escribo|mando|pongo)\b",
        r"\bcomo le (?:respondo|contesto|escribo|pido|digo)\b",
        r"\bque (?:respondo|contesto)\b",          # sin contenido dirigido a ella
        r"\bcomo (?:respondo|contesto)\b",
        r"\bcomo (?:pido|consigo|saco) (?:el|su|un)\b",  # "como pido el whatsapp/numero"
        r"\bella me (?:dijo|dejo|respondio|escribio)\b",
        r"\besta bien (?:mi|este) mensaje\b",
        r"\bsirve este (?:mensaje|opener|abridor)\b",
        r"\bdame (?:un|una|tres|3)? ?(?:consejo|tip|ejemplo|opener|abridor|estrategia)\b",
        r"\bexplicame\b",
        r"\bvoy bien o\b",
        r"\bla estoy (?:cagando|regando|embarrando)\b",
    ]
]

# Señales DÉBILES (se necesitan >= 2): vocabulario meta sin destinatario claro.
MAXIMUS_WEAK_RES = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bconsejo\b", r"\baconsej", r"\bestrategia\b", r"\btecnica\b",
        r"\bopener\b", r"\babridor\b", r"\bteoria\b", r"\btips?\b",
        r"\beste mensaje\b", r"\bmi mensaje\b", r"\bel juego\b", r"\bel nivel\b",
        r"\bque opinas\b", r"\bayudame\b", r"\bmis fotos de perfil\b",
    ]
]
# NOTA: se eliminan deliberadamente \bfotos?\b, \bprimera cita\b, \bque digo\b y
# \bcoach\b-en-cualquier-posicion: son vocabulario legítimo del JUEGO.

# Señales de JUEGO (veto): el mensaje se dirige a ELLA en 2a persona.
GAME_SIGNAL_RES = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bte\b", r"\btu\b", r"\btus\b", r"\bcontigo\b", r"\btuyo\b", r"\btuya\b",
        r"\bme (?:pasas|das|dices|cuentas|mandas|envias|regalas)\b",
        r"\beres\b", r"\bestas\b", r"\bquieres\b", r"\bvamos\b", r"\bsalimos\b",
    ]
]


def route_turn_request(request: SimulateTurnRequest) -> Dict[str, Any]:
    raw = request.user_message or ""
    message = normalize_route_text(raw)  # ya normaliza acentos degradados (qu?, m?sica)
    context = request.visible_context or {}
    stage = normalize_route_text(str(context.get("mode") or context.get("stage") or context.get("route") or ""))

    def result(route: str, rule: str, reasons: List[str], clean_message: str = "") -> Dict[str, Any]:
        return {
            "route": route,
            "rule": rule,
            "reasons": reasons,
            "stage": stage or "chat",
            "coach_question": clean_message or raw.strip(),
        }

    # R0 — señal dura de UI: el usuario está físicamente en una pantalla de coaching.
    if stage in MAXIMUS_STAGE_HINTS:
        return result("maximus", "R0", [f"stage:{stage}"])

    # R1 — prefijo explícito "Maximus…"/"Coach…" al inicio (declaración del usuario).
    prefix_match = MAXIMUS_PREFIX_RE.match(message)
    if prefix_match:
        question = raw.strip()[prefix_match.end():].strip() or raw.strip()
        return result("maximus", "R1", ["prefix"], question)

    game_signals = [r.pattern for r in GAME_SIGNAL_RES if r.search(message)]
    strong = [r.pattern for r in MAXIMUS_STRONG_RES if r.search(message)]
    weak = [r.pattern for r in MAXIMUS_WEAK_RES if r.search(message)]

    # R2 — señal fuerte de meta-consulta, sin veto de 2a persona.
    #      "como le pido el whatsapp?" -> maximus. "me pasas tu whatsapp?" -> veto -> natalia.
    if strong and not game_signals:
        return result("maximus", "R2", [f"strong:{strong[0]}"])

    # R2b — dos señales débiles sin veto ("dame tips con el opener de este nivel").
    if len(weak) >= 2 and not game_signals:
        return result("maximus", "R2b", [f"weak:{w}" for w in weak[:3]])

    # R3 — default: juego. Incluye los cierres de nivel ("me pasas tu whatsapp?",
    #      "quieres que tengamos nuestra primera cita?") que JAMÁS deben ir al coach.
    return result("natalia", "R3", game_signals[:2] if game_signals else ["default"])
```

**Casos canónicos que esta tabla resuelve** (van al dataset de tests, sección 5):

| Mensaje | Ruta | Regla |
|---|---|---|
| "me pasas tu whatsapp? 😏" | natalia | R3 (veto `me pasas`/`tu`) — objetivo del nivel |
| "¿cómo le pido el whatsapp?" | maximus | R2 (`como le pido`) |
| "¿qué le digo?" | maximus | R2 |
| "¿qué me dices?" | natalia | R3 (veto `me dices`) |
| "oye una pregunta, ¿te gusta el vino?" | natalia | R3 (veto `te`) |
| "Maximus, ¿sirve este opener?" | maximus | R1 |
| "mi amigo maximus dice que eres linda" | natalia | R3 (prefijo no inicial + veto `eres`) |
| "qué linda tu foto 😍" | natalia | R3 (ya no existe patrón `fotos?`) |
| "¿esta sería nuestra primera cita? jaja" | natalia | R3 |
| "mi coach del gym me tiene muerto" | natalia | R3 (prefijo no inicial) |
| "dame tips con el opener" | maximus | R2 (`dame...tip/opener`) |
| "qu? m?sica te gusta" | natalia | R3 (normalización degradada + veto `te`) |

### 3.2 Respuesta real de Maximus (nueva función + prompt Q&A)

Hoy no existe. Agregar después de `maximus_intercept_message()`:

```python
def build_maximus_answer_prompt(question: str, cases_prompt: str, behavior: Dict[str, Any]) -> str:
    profile = str(behavior.get("profile", "coqueta"))
    return f"""Eres Maximus, el coach de citas del simulador. El usuario NO esta hablando con la chica:
te esta preguntando a TI directamente. Responde su pregunta de forma practica y accionable.

PREGUNTA DEL USUARIO:
{question}

PERFIL DEL NIVEL ACTUAL: {profile}

CASOS Y TEORIA RECUPERADOS (tu unica evidencia; no inventes nada fuera de esto):
{cases_prompt}

REGLAS ESTRICTAS:
- Usa SOLO la evidencia recuperada y el estado visible del juego. Si la evidencia no alcanza,
  di explicitamente "No tengo casos suficientes para asegurarlo" y da un consejo conservador.
- NUNCA garantices resultados ("con esto seguro te da el numero" esta prohibido).
- NUNCA hables como si fueras la chica ni uses su voz.
- Maximo 5 frases + hasta 3 sugerencias concretas.

Devuelve SOLO JSON valido:
{{
  "answer": "respuesta directa en espanol latino",
  "suggestions": ["sugerencia A", "sugerencia B", "sugerencia C"],
  "cited_post_ids": ["post_id de los casos usados, si aplica"]
}}"""


def maximus_fallback_answer(question: str, coach_cases: List[Dict[str, str]]) -> Dict[str, Any]:
    """Respuesta local sin Gemini: resume la evidencia recuperada (patron fallback ya existente)."""
    top = [c for c in coach_cases if c.get("text")][:3]
    if not top:
        return {
            "answer": ("No tengo casos suficientes en la base para responder eso con evidencia. "
                       "Consejo conservador: manten el hilo del ultimo mensaje de ella y no fuerces el cierre."),
            "suggestions": [],
            "cited_post_ids": [],
        }
    lines = []
    cited = []
    for case in top:
        pid = str(case.get("post_id") or "")
        if pid:
            cited.append(pid)
        snippet = str(case.get("text", "")).strip().splitlines()
        resumen = next((l for l in snippet if l.lower().startswith("resumen")), snippet[0] if snippet else "")
        lines.append(f"- {resumen[:180]}")
    return {
        "answer": "Esto es lo que muestran los casos reales mas parecidos a tu situacion:\n" + "\n".join(lines),
        "suggestions": [],
        "cited_post_ids": cited,
    }
```

### 3.3 Cortocircuito en `simulate_turn()` (ahorra 2 llamadas Gemini y arregla D2/D3/D6)

Insertar **inmediatamente después** de `route_info = route_turn_request(request)`, antes de cualquier retrieval de persona:

```python
    if route_info["route"] == "maximus":
        # --- Ruta Maximus: el coach RESPONDE, nadie evalúa flirteo, no se toca el juego ---
        question = route_info.get("coach_question") or request.user_message
        coach_cases = retrieve_coach_cases(request, behavior, persona_cases=[])
        cases_prompt = cases_to_prompt(coach_cases, max_cases=6, max_text_chars=550)
        maximus_live_used = False
        try:
            if gemini_live_enabled():
                raw_answer = rotator.generate_content(
                    build_maximus_answer_prompt(question, cases_prompt, behavior)
                )
                payload = json_from_model(raw_answer)
                maximus_live_used = True
            else:
                payload = maximus_fallback_answer(question, coach_cases)
        except Exception as exc:
            print(f"WARNING: maximus fallback: {exc}")
            payload = maximus_fallback_answer(question, coach_cases)

        answer = clean_ui_text(payload.get("answer")) or maximus_fallback_answer(question, coach_cases)["answer"]
        suggestions = [clean_ui_text(s) for s in payload.get("suggestions", []) if clean_ui_text(s)][:3]

        retrieval_summary = retrieval_summary_for_cases(coach_cases, [])
        retrieval_summary.update({
            "route": "maximus",
            "route_rule": route_info["rule"],
            "route_reasons": route_info["reasons"],
            "route_stage": route_info["stage"],
            "maximus_live_used": maximus_live_used,
            "turn_consumed": False,
        })
        return SimulateTurnResponse(
            natalia_message="",                # el frontend NO pinta burbuja si viene vacío + route=maximus
            natalia_time="",
            coach_title="Maximus Coach",
            coach_feedback=answer,
            score=0,
            lose_life=False,
            attraction_delta=0,
            suggestions=suggestions,
            retrieved_cases=[{
                "source": c.get("source", ""), "post_id": c.get("post_id", ""),
                "profile": c.get("profile", ""), "intent": c.get("intent", ""),
                "woman_signal": c.get("woman_signal", ""), "success_score": c.get("success_score", ""),
            } for c in coach_cases[:10]],
            retrieval_summary=retrieval_summary,
            fallback=not maximus_live_used,
            turn_analysis={},
            turn_metrics={},
        )
```

Y **eliminar** los dos parches actuales (`if route_info["route"] == "maximus": lose_life = False...` y `natalia_message = maximus_intercept_message()`): con el cortocircuito quedan muertos. `maximus_intercept_message()` puede borrarse.

Verificar que `retrieve_coach_cases(request, behavior, persona_cases=[])` funciona con lista vacía (sí: solo hace `list(persona_cases[:2])` y `persona_cases[2:5]`, ambos seguros con `[]`).

### 3.4 Frontend (`build_simulator.py` → regenerar `simulador_v1.2.html`)

Tres cambios en el JS del simulador (editar el generador, no el HTML):

```javascript
// 1. En buildVisibleContext(): enviar el modo de UI para que R0 funcione.
//    (hoy MAXIMUS_STAGE_HINTS está muerto porque nunca llega stage/mode)
return {
    evaluated_step_id: step ? step.step_id : null,
    evaluated_step_index: gameState.step_index,
    last_natalia_message: lastNatalia ? lastNatalia.text : '',
    last_user_message: lastUser ? lastUser.text : '',
    chat_snapshot: snapshot,
    mode: gameState.uiMode || 'chat'   // 'chat' | 'coach' | 'gameover' | 'summary' | 'estudiar'
};

// 2. Al recibir la respuesta del API: si es ruta maximus, tarjeta de coach, no burbuja.
const isMaximus = (data.retrieval_summary && data.retrieval_summary.route === 'maximus');
if (isMaximus) {
    renderCoachCard(data.coach_feedback, data.suggestions);  // estilo "Lectura del Coach":
    // borde/color/avatar distintos a las burbujas, inline en el chat, SIN modal bloqueante.
    // CRÍTICO: no llamar a addMessage('her', ...) → el texto de Maximus NUNCA entra a
    // gameState.history, así no contamina chat_snapshot ni last_natalia_message.
    return;  // no descontar vidas, no avanzar paso, no tocar attraction.
}

// 3. renderCoachCard(text, suggestions): nueva función; reusar la estética del modal
//    del Coach pero como tarjeta inline (el modal bloqueante actual interrumpe el flujo).
```

**Regla de oro UI:** la respuesta de Maximus jamás se renderiza en la burbuja de Natalia, y el mensaje del usuario en ruta maximus jamás entra al historial que ve Persona.

---

## 4. Bug crítico independiente: mojibake DENTRO de los literales de `server.py`

Verificado a nivel de bytes: el archivo contiene strings doble-codificados (UTF-8 → Latin-1 → UTF-8).

```
>>> raw = open('backend/server.py','rb').read()
>>> b'\xf0\x9f\x8d\x86' in raw       # 🍆 real (UTF-8 correcto)
False
>>> b'\xc3\x83\xc2\xb3' in raw       # "Ã³" = 'ó' doble-codificada
True
>>> raw[raw.find(b'risky = {'):][:60]
b'risky = {"\xc3\xb0\xc5\xb8\xc2\x8d\xe2\x80\xa0", ...'   # mojibake, no emojis
```

**Consecuencias funcionales reales:**

- En `emoji_profile()` (~línea 2172): los sets `risky`/`warm`/`romantic` contienen mojibake, así que con emojis reales del usuario `risky_count`/`warm_count`/`romantic_count` **siempre son 0** → la calibración "riesgo sexual temprano" y "demasiado romanticos" **nunca dispara**. (El conteo total sí funciona porque el regex usa escapes `\U0001F300`.)
- `natalia_time` default `"TardÃ³: 15 min"` (línea ~250) llega corrupto al UI en algunos paths.
- `cases_signal()` (~2161) busca `"nÃºmero"`/`"telÃ©fono"` que nunca matchean texto real (mitigado a medias por las variantes sin acento).
- `natalia_response_is_invalid()` (~3605) tiene `"mÃ©trica"` en la lista de palabras prohibidas → la variante con acento real "métrica" **no se detecta**.

**Fix (una sola vez):**

```bash
python - <<'PY'
p = 'backend/server.py'
raw = open(p, 'rb').read().decode('utf-8')
fixed = raw.encode('latin-1', errors='strict').decode('utf-8')  # deshace la doble codificación
open(p + '.fixed', 'w', encoding='utf-8', newline='').write(fixed)
PY
# revisar diff, correr tests, y reemplazar. Hacer backup primero (patrón .bak_<fecha> ya usado en el repo).
```

Si `encode('latin-1')` falla en algún tramo es porque el archivo está MEZCLADO (partes sanas y partes dobles — probable, dado que líneas nuevas como 3573 `"sábado"` se ven correctas). En ese caso aplicar `ftfy.fix_text()` línea por línea solo donde haya marcadores `Ã`/`ð` y revisar el diff a mano.

**Test de regresión obligatorio tras el fix:**

```python
def test_emoji_sets_are_real_unicode():
    from backend.server import emoji_profile
    assert emoji_profile("🍆💦")["risky_count"] == 2
    assert emoji_profile("😊🙂")["warm_count"] == 2
    assert emoji_profile("hola 😍😘❤️")["romantic_count"] == 3
```

---

## 5. Suite de pruebas de routing (nueva: `tests/test_routing_contract.py`)

Sin servidor ni Gemini (el router es función pura). Gates duros: **un solo mensaje de cierre robado rompe el build.**

```python
import pytest
from backend.server import route_turn_request, SimulateTurnRequest

def req(msg, mode=None):
    ctx = {"last_natalia_message": "jaja si, me encanta salir los viernes"}
    if mode:
        ctx["mode"] = mode
    return SimulateTurnRequest(user_message=msg, chosen_time="15m", level=1,
                               history=[], visible_context=ctx)

# GATE DURO 1: cierres/objetivo del nivel dirigidos a ELLA -> siempre natalia.
CIERRES_JUEGO = [
    "me pasas tu whatsapp? 😏", "dame tu numero y seguimos por alla",
    "¿cual es tu insta?", "¿quieres que tengamos nuestra primera cita?",
    "te invito una copa el jueves, ¿quedamos?", "¿salimos este finde?",
]
@pytest.mark.parametrize("msg", CIERRES_JUEGO)
def test_gate1_cierres_nunca_van_al_coach(msg):
    assert route_turn_request(req(msg))["route"] == "natalia"

# GATE DURO 2: consultas claras -> siempre maximus.
CONSULTAS = [
    "Maximus, ¿sirve este opener?", "coach ayudame con esto",
    "¿como le pido el whatsapp?", "¿que le digo ahora?",
    "¿que respondo aqui?", "dame tips con el opener",
    "explicame la regla de los emojis", "¿esta bien mi mensaje?",
]
@pytest.mark.parametrize("msg", CONSULTAS)
def test_gate2_consultas_van_al_coach(msg):
    assert route_turn_request(req(msg))["route"] == "maximus"

# Adversariales: vocabulario meta EN contexto de juego -> natalia.
ADVERSARIALES = [
    "que linda tu foto 😍", "me mandas una foto?",
    "mi coach del gym me tiene muerto hoy",
    "mi amigo maximus dice que eres linda",
    "no se que digo cuando te veo jaja",
    "mi estrategia para conquistarte va bien 😏",
    "qu? m?sica te gusta",   # acentos degradados Windows
]
@pytest.mark.parametrize("msg", ADVERSARIALES)
def test_adversariales_no_roban_juego(msg):
    assert route_turn_request(req(msg))["route"] == "natalia"

# R0: señal de UI gana a todo.
def test_stage_ui_manda():
    assert route_turn_request(req("hola linda", mode="gameover"))["route"] == "maximus"

# R1: el prefijo extrae la pregunta limpia para el prompt de Maximus.
def test_prefijo_extrae_pregunta():
    info = route_turn_request(req("Maximus: ¿sirve este opener?"))
    assert info["rule"] == "R1"
    assert "sirve este opener" in info["coach_question"].lower()
```

Y el **test de aislamiento de fuentes** (integración, con `GEMINI_LIVE_ENABLED=0`):

```python
def test_persona_nunca_recibe_negativos_ni_libros():
    # sobre retrieve_persona_cases directamente: ninguna fuente prohibida.
    from backend.server import retrieve_persona_cases, level_behavior
    cases = retrieve_persona_cases(req("hola, ¿que tal tu semana?"), level_behavior(1))
    prohibidas = {"negative_chroma", "books_chroma", "youtube_theory"}
    assert not [c for c in cases if c.get("source") in prohibidas]
```

Integrar la corrida a `scratch/daily_natalia_rag_maintenance.py` junto a QA 20 y QA catálogo 120.

---

## 6. Otros hallazgos del código real (fuera del router, ordenados por riesgo)

### 6.1 `retrieve_cases()` legacy (línea 2047) mezcla TODO — deprecarla ya

Confirmado en código: incluye `retrieve_books_chroma_cases`, `retrieve_negative_chroma_cases` y `retrieve_youtube_theory`. `simulate_turn` no la usa, pero sigue invocable. Es la vía más probable de fuga de negativos hacia Persona si alguien la reconecta. Fix mínimo:

```python
def retrieve_cases(request, behavior):
    raise RuntimeError(
        "retrieve_cases() esta deprecada: mezcla negativos/libros/YouTube. "
        "Usar retrieve_persona_cases() o retrieve_coach_cases() segun el consumidor."
    )
```

(Si algún endpoint viejo la llama, el error lo dirá de inmediato en vez de contaminar en silencio.)

### 6.2 Colisión de nombres confirmada en código: `natalia_conversations` ×2

`server.py` líneas 498 y 511: la misma string de colección se abre en `chroma_db` (169 legacy de perfiles) y en `books_kb/chroma_books` (74 conversaciones de libros). Además se usa `get_or_create_collection`, que **crea una colección vacía en silencio** si el path está mal — un typo en el path degradaría el retrieval a 0 resultados sin ningún error. Fix: renombrar la colección de libros (p. ej. `natalia_book_conversations`) por copia (crear→verificar conteo 74→borrar vieja) y cambiar a `get_collection()` + reporte de error en `/health` para las colecciones que deben existir.

### 6.3 En `retrieve_persona_cases()`, los success cases se saltan el filtro de tema

Línea ~2091–2096: cuando hay `direct_topics`, los pares reales se filtran por tema (`filtered_pairs`) pero los `success_cases` se agregan **sin pasar por ese filtro** (`return filtered_pairs + success_cases`). Si el usuario pregunta por música, puede entrar un caso de cierre de cita como "inspiración de tono" incompatible con el turno. Fix: aplicar el mismo `pair_topics(...)∩direct_topics` (o al menos compatibilidad de `objectives` vs `infer_query_objectives`) a los success cases antes de anexarlos.

### 6.4 `success_case_rank()` sin umbral de corte

El reranker (línea 996) ordena pero nunca descarta: un top-k irrelevante entra igual al contexto y empuja al modelo a extrapolar. Agregar corte mínimo (p. ej. `rank >= 8` o `retrieval_score > 0`) y, si nada sobrevive, devolver lista vacía para que el prompt diga "sin casos aplicables" (abstención) en vez de inspirarse en ruido.

### 6.5 `retrieval_summary` no se persiste

Se devuelve por HTTP y se pierde. Sin log no se puede auditar ninguna alucinación reportada ni medir tasas reales de guardrail/api/routing. Crear tabla `turn_audit_log` en `textgame.db` (turno, route, rule, fuentes, fallback_category, score, timestamp; purga a 90 días) y escribirla al final de `simulate_turn` (~1-2 ms).

### 6.6 Ciclo de vida del índice solo aditivo

`index_success_candidates_chroma.py --incremental` solo agrega. Cuando un caso se demueve de `candidate_qa` (caso documentado: `dmoeoi`), su embedding queda huérfano en `natalia_success_cases` — `fetch_success_candidate_rows()` lo filtra al rehidratar (`WHERE status='candidate_qa'`), lo que **enmascara** el problema desperdiciando slots del top-k. Agregar: (a) check diario de huérfanos en `daily_natalia_rag_maintenance.py`; (b) flag `--sync-deletes` con dry-run por defecto (mismo patrón que `cleanup_reddit_images_after_scrape.py --apply`).

---

## 7. Backlog priorizado (de la revisión completa de arquitectura — resumen ejecutivo)

| # | Tarea | Prioridad | Esfuerzo | Archivos | Verificación |
|---|---|---|---|---|---|
| 1 | Router v1 + respuesta real de Maximus + frontend (secciones 3.1–3.4) | **Alta** | Medio | backend/server.py, build_simulator.py | Suite sección 5 en verde; gates duros 100% |
| 2 | Fix mojibake en server.py + test de emojis (sección 4) | **Alta** | Bajo | backend/server.py | `test_emoji_sets_are_real_unicode` pasa |
| 3 | Deprecar `retrieve_cases()` legacy (6.1) | **Alta** | Bajo | backend/server.py | Llamarla lanza RuntimeError; grep sin usos |
| 4 | Filtro de tema para success cases en Persona (6.3) | **Alta** | Bajo | backend/server.py | 20 turnos: `retrieval_summary` sin casos de tema incompatible |
| 5 | `turn_audit_log` persistente (6.5) | **Alta** | Bajo | backend/server.py, textgame.db | 10 turnos → 10 filas con route y fuentes |
| 6 | Umbral de corte + abstención en reranker (6.4) | **Alta** | Medio | backend/server.py | Preguntas fuera-de-corpus → 0 casos inyectados |
| 7 | Renombrar colección de libros + `get_collection` estricto (6.2) | Media | Bajo | server.py, books_kb | Ningún nombre repetido; /health reporta faltantes |
| 8 | Check integridad Chroma↔SQLite + `--sync-deletes` (6.6) | Media | Medio | scratch/daily..., scratch/index... | Demover caso de prueba → detectado → purgado |
| 9 | Catálogo QA v2: +40 preguntas adversariales que deben dar FALTA_EVIDENCIA + recall@5/MRR | Media | Medio | scratch/generate/qa_natalia_rag_catalog.py | 120 OK + 40/40 abstención correcta |
| 10 | Metadata atómica (objetivo/app/idioma/etapa/ocr_quality) + filtros `where=` pre-query | Media | Medio | scratch/index..., server.py | Censo de cobertura + A/B sin regresión |
| 11 | Derivar pares H→M desde los 1.895 success (hoy Persona vive de ~320 pares) | Media | Medio | nuevo script scratch/ | `persona_usable_pairs` ≥1.000, muestreo ≥90% OK |
| 12 | Validadores post-generación (claims de resultado + entidades fuera de ficha), modo solo-log primero | Media | Medio | backend/server.py | 30 turnos adversariales → 0 claims sin respaldo |

**Reglas transversales que no se negocian** (ya establecidas en AGENTS.md/arquitectura.html):
- Negativos, YouTube y teoría de libros JAMÁS en la voz de Natalia-Persona (solo Coach).
- Nada de fine-tuning: todo lo anterior se resuelve con router, RAG, metadata y evaluación.
- Ningún lote nuevo entra a Chroma sin QA (compuerta ya establecida).
- El router jamás usa LLM: reglas locales, cero costo, inmune a la contingencia 429.
- Al cerrar cada tarea: actualizar `AGENTS.md` + `arquitectura.html` y guardar reportes en `docs/`.

---

## 8. Brechas — preguntas que Codex debe confirmar en el código antes de implementar

1. ¿Algún endpoint además de los revisados llama a `retrieve_cases()` legacy? (grep antes del RuntimeError).
2. ¿`/api/evaluate` lo usa el frontend v1.2 o quedó muerto? (si está muerto, no reusarlo para Maximus: la ruta maximus de la sección 3.3 vive dentro de `simulate-turn` y es suficiente).
3. ¿Qué texto exacto se embebe en `natalia_success_cases` (OCR bruto vs `translation_es`)? Determina si el bug de OCR pegado (`let'sgetbrunch`) afecta el recall del índice.
4. ¿El `chat_snapshot` de `visible_context` puede ya contener mensajes del interceptor v0 en sesiones guardadas? Si sí, limpiar `localStorage` con `?reset=1` en las pruebas.
5. Cobertura real de `has_time_markers` en los 1.895 docs (condiciona usar timing en el reranker).

---

*Generado por revisión Claude (arquitecto RAG/LLMOps) el 2026-07-06. Fuente de verdad del análisis: código en `backend/server.py` leído en vivo + `arquitectura.html`. Los números de línea pueden desplazarse: buscar por nombre de función/constante.*
