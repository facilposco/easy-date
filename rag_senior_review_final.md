# Revisión Senior de Arquitectura RAG — Easy Date / Natalia
> Rol: Arquitecto Senior de RAG, LLMOps, Sistemas Conversacionales y Evaluación de Agentes  
> Documento base: `C:\desarrollos\Codex\Easy Date\arquitectura.html` (revisado 2026-07-07)

---

## 1. Diagnóstico Breve de la Arquitectura Actual

### Lo que ya está bien (fortalezas reales)

| Área | Estado |
|------|--------|
| Separación Chroma como índice / SQLite como fuente de verdad | ✅ Bien planteado. Parent-document real, no chunks sueltos. |
| Aislamiento de colecciones por rol | ✅ `natalia_success_cases`, `natalia_negative_cases`, `natalia_conversations`, `natalia_books_kb` ya separadas. |
| Regla de no cruce: Natalia-Persona no consume negativos | ✅ Documentada y activa en `retrieve_persona_cases()`. |
| Reranker local `success_case_rank()` | ✅ Reordena por objetivo, score, confidence, app, timestamps, similitud textual. |
| Catálogo de 120 preguntas etiquetadas con criterio de fallo | ✅ 120/120 OK. Automatizado en daily maintenance. |
| Compuerta anti-alucinación RAG: si no hay evidencia → declarar falta | ✅ Documentada en QA 20 preguntas. |
| Índice incremental sin reconstrucción completa | ✅ `--incremental` activo. |
| Fallback auditable (api vs guardrail) | ✅ `natalia_fallback_category` y `natalia_fallback_reason` en `retrieval_summary`. |

### Brechas detectadas (documentadas honestamente)

| # | Brecha | Severidad |
|---|--------|-----------|
| B1 | El router Natalia/Maximus es por **etapa del juego**, no por **intención del mensaje**. Un mensaje de teoría dentro del chat de Natalia lo responde Natalia-Persona si el juego está en mid-conversation. | 🔴 Alta |
| B2 | No existe un clasificador de intención separado. El backend decide la ruta por endpoint y etapa, no por el texto del turno actual. | 🔴 Alta |
| B3 | Los libros (`books_kb/chroma_books`) no están integrados en el Chroma operativo (`chroma_db`). Están en una base separada sin unificación de retrieval. | 🟡 Media |
| B4 | El catálogo de 120 preguntas **no tiene preguntas de routing** (¿debe responder Natalia o Maximus?), ni preguntas de persona-voice (¿suena humana?), ni de regresión de emojis. | 🟡 Media |
| B5 | `natalia_conversations_plus` (46 docs legacy) está sin sincronizar con `chroma_db` principal. Puede producir retrieval inconsistente si se activa en el futuro. | 🟡 Media |
| B6 | Metadata en Chroma no incluye: `etapa_conversacional`, `ocr_quality_score`, `tiempo_respuesta_turno`, `idioma_original`, `app_source`, `evidencia_tipo` como campos atómicos filtrables. Solo existen como texto libre. | 🟡 Media |
| B7 | El reranker local es heurístico. No hay reranker neural para medir si el texto recuperado es semánticamente relevante al turno actual. | 🟡 Media |
| B8 | No hay pruebas automatizadas de **routing** (¿este mensaje va a Natalia o Maximus?), ni de **persona-voice** (¿suena como mujer real?). | 🟡 Media |
| B9 | Cuando el usuario escribe "Maximus..." dentro del chat libre de Natalia, no está definido si se intercepta. No está documentado como regla activa. | 🟡 Media |
| B10 | El catálogo de preguntas no diferencia **dificultad por nivel** (nivel 1 vs nivel 4 necesitan retrieval distinto). | 🟢 Baja |

---

## 2. Top 10 Mejoras Priorizadas

### 🔴 Prioridad Alta

---

**Mejora 1: Clasificador de Intención de Turno (Intent Router)**

**Problema:** El routing actual usa etapa de juego, no contenido del mensaje. Un usuario que escribe "¿Qué técnica funciona aquí?" dentro del chat no llega a Maximus.

**Propuesta accionable:**
```python
# Antes de llamar retrieve_persona_cases() o retrieve_coach_cases()
# en /api/simulate-turn, ejecutar:

def classify_turn_intent(user_message: str, game_stage: str) -> str:
    """
    Retorna: 'natalia' | 'maximus' | 'hybrid'
    """
    MAXIMUS_TRIGGERS = [
        r'\bMaximus\b', r'\bcoach\b', r'qu[eé] respondo', r'qu[eé] digo',
        r'c[oó]mo le\b', r'estrategia', r'teor[ií]a', r'consejo',
        r'explicame', r'explicación', r'opener', r'primera cita',
        r'whatsapp', r'instagram', r'foto[s]?', r'\bpide\b.*\bfoto\b'
    ]
    FORCE_NATALIA = ['game_active', 'mid_conversation']
    
    for pattern in MAXIMUS_TRIGGERS:
        if re.search(pattern, user_message, re.IGNORECASE):
            return 'maximus'
    
    return 'natalia'  # default cuando está en conversación activa
```

**Componentes afectados:** `backend/server.py` → función `simulate_turn()`  
**Esfuerzo:** 2-3 días  
**Riesgo:** Bajo si se implementa antes del retrieve, no reemplaza la lógica de etapa.

---

**Mejora 2: Metadata Atómica Estándar en Chroma**

**Problema:** Sin campos atómicos en metadata, los filtros `$contains` y `$and` de Chroma no funcionan correctamente. El reranker opera solo sobre texto, no sobre campos estructurados.

**Campos que FALTAN como atómicos:**

```python
metadata_schema = {
    "post_id": str,           # YA existe
    "objetivo": str,          # YA existe (pero como texto libre)
    "confidence": str,        # YA existe
    "app": str,               # YA existe
    "fuente": str,            # YA existe
    # FALTAN:
    "etapa_conversacional": str,  # 'apertura' | 'medio' | 'cierre' | 'contacto'
    "ocr_quality": str,           # 'alta' | 'media' | 'baja'
    "idioma_original": str,       # 'en' | 'es' | 'de' | 'pt' | 'fr' | 'it'
    "evidencia_tipo": str,        # 'numero' | 'whatsapp' | 'cita' | 'instagram' | 'conexion'
    "nivel_dificultad": int,      # 1-4 (para retrieval calibrado por nivel)
    "n_turnos": int,              # longitud de conversación
}
```

**Script de migración:** `scratch/migrate_chroma_metadata_v2.py`  
**Esfuerzo:** 3-4 días (migración + QA)  
**Riesgo:** Medio. Requiere re-indexación incremental con los nuevos campos. No destruye datos existentes.

---

**Mejora 3: Reglas Explícitas del Router (Documento de Contrato)**

Las reglas que defines en el prompt deben existir como código ejecutable, no solo como documentación:

```python
ROUTER_RULES = {
    "natalia_persona": {
        "trigger": "usuario habla como si fuera con la chica",
        "colecciones": ["natalia_success_cases"],  # NO negativos, NO libros de teoría
        "prohibido": ["natalia_negative_cases", "natalia_books_kb (teoría)"],
        "modo": "respuesta breve, humana, emocional"
    },
    "maximus_coach": {
        "trigger": [
            "pide consejo/estrategia/teoría",
            "escribe 'Maximus...' en chat",
            "solicita opener, foto, WhatsApp, Instagram",
            "está en sección Estudiar, Game Over, resumen final",
            "pregunta '¿qué respondo?'"
        ],
        "colecciones": ["natalia_success_cases", "natalia_negative_cases", 
                        "natalia_books_kb", "natalia_conversations"],
        "modo": "análisis pedagógico, 3 opciones, citar fuente"
    }
}
```

**Componentes:** `backend/server.py` + nueva función `route_turn_request()`

---

### 🟡 Prioridad Media

---

**Mejora 4: Ampliar Catálogo de 120 → 200+ Preguntas**

Las 120 preguntas actuales cubren retrieval pero les faltan estas categorías críticas:

| Categoría nueva | Cantidad propuesta | Descripción |
|---|---|---|
| **Routing Intent** | 20 | "¿Este mensaje activa Natalia o Maximus?" — verificar que el clasificador no confunda |
| **Persona Voice** | 20 | "¿La respuesta suena como mujer real LATAM casual?" — evaluar tono, no solo retrieval |
| **Nivel de Dificultad** | 15 | Las preguntas de nivel 4 deben traer casos de mujer selectiva/defensiva |
| **Groundedness** | 15 | "¿La respuesta cita datos que SÍ están en el contexto recuperado?" |
| **Emoji Regression** | 10 | Detectar que emojis degradados (🟡🟡) no activan reglas falsas |
| **Negative Isolation** | 10 | "El caso recuperado para Natalia-Persona ¿viene de `natalia_negative_cases`?" → debe ser NO |
| **Timing** | 10 | Latencia < 3s para 90% de turnos bajo carga de 5 usuarios simultáneos |

**Total propuesto:** 120 + 100 = **220 preguntas** organizadas por dimensión.

**Formato a añadir al catálogo:**
```json
{
  "id": "ROUTING-001",
  "categoria": "routing",
  "pregunta": "el usuario escribe 'qué técnica uso aquí?' durante una conversación activa",
  "respuesta_esperada_ruta": "maximus",
  "colecciones_esperadas": ["natalia_negative_cases", "natalia_books_kb"],
  "criterio_fallo": "si responde Natalia-Persona con voz de mujer sin análisis pedagógico"
}
```

---

**Mejora 5: Reranker Semántico Ligero (sin subir costo)**

**Propuesta sin costo adicional:**

```python
# Usar sentence-transformers local (modelo pequeño ~80MB)
from sentence_transformers import CrossEncoder

cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank_with_cross_encoder(query: str, candidates: list[dict], top_k=5) -> list[dict]:
    """Solo reranking, no embedding. Opera sobre los top-15 que ya devuelve Chroma."""
    pairs = [(query, c['conversation_text'][:500]) for c in candidates]
    scores = cross_encoder.predict(pairs)
    ranked = sorted(zip(scores, candidates), reverse=True)
    return [c for _, c in ranked[:top_k]]
```

**Ventaja:** Costo cero en API (modelo local), latencia ~150ms extra por turno.  
**Riesgo:** Bajo. Solo opera sobre candidatos ya recuperados por Chroma. El reranker heurístico existente se mantiene como fallback.  
**Comparación requerida:** Agregar al catálogo QA 10 preguntas de "¿el reranker neural mejora sobre el heurístico?" antes de activarlo en producción.

---

**Mejora 6: Reducir Alucinaciones — Guardrails de Grounding**

**Reglas que deben existir como código, no solo como documentación:**

```python
GROUNDING_RULES = {
    "no_inventar_numeros": {
        "descripcion": "Natalia no puede dar un número de teléfono si no está en el contexto visible",
        "check": lambda response, context: not re.search(r'\d{7,}', response) or
                  any(re.search(r'\d{7,}', c) for c in context),
        "accion_si_falla": "activar abstención y señalar falta de evidencia"
    },
    "no_inventar_citas": {
        "descripcion": "Natalia no puede confirmar una cita si no ocurrió en el historial visible",
        "check": lambda response, visible_history: 'cita' not in response.lower() or
                  any('cita' in h.lower() for h in visible_history),
    },
    "citar_fuente_coach": {
        "descripcion": "Maximus debe indicar de qué caso o libro viene la sugerencia",
        "formato": "[Caso #{post_id} — {objetivo}]" 
    }
}
```

**Patrón de abstención activo (ya documentado, falta como código explícito):**
```
Si no_evidencia_suficiente:
    → Natalia: "Hmm, no sé qué decirte en este punto."  (voz persona, no break 4th wall)
    → Maximus: "No tengo un caso exacto para este escenario. Te sugiero..."
```

---

**Mejora 7: Integración Controlada del RAG de Libros**

**Estado actual:** `books_kb/chroma_books` está separado del `chroma_db` operativo. No se consulta en runtime.

**Propuesta en 3 pasos:**

1. **QA previo:** Correr el catálogo de 120 preguntas solo contra `natalia_books_kb` para medir si hay solapamiento útil o ruido.
2. **Merge por colección:** Añadir `natalia_books_kb` como colección adicional en el Chroma operativo, con metadata `fuente_tipo: "libro"` para poder filtrarla.
3. **Regla de uso:** Maximus puede consultar libros + casos reales. Natalia-Persona consulta casos reales exclusivamente, y libros **solo** si no hay casos con `confidence: alta` para esa etapa.

**Riesgo:** Medio. Los libros pueden contaminar el tono de Natalia con frases teóricas. Necesita guardrail de filtro: si la fuente es libro, no usar como ejemplo directo de cómo habla una mujer.

---

**Mejora 8: Entrenamiento de Natalia más Humano y Calibrado**

**Problema actual:** El fallback local responde con plantillas por nivel. Cuando Gemini falla, la voz puede sonar robótica.

**Propuesta:**
```python
# Para el fallback local, crear banco de respuestas reales por:
# - etapa_conversacional × nivel_dificultad × tema

REAL_RESPONSE_BANK = {
    ("apertura", 1, "trabajo"): [
        "Jaja eso suena interesante, ¿y qué haces exactamente?",
        "Ah sí? No me lo imaginaba, cuéntame",
    ],
    ("cierre", 3, "contacto"): [
        "Veré si tengo tiempo...",
        "Mmm depende, ¿de qué estarías hablando?",
    ]
}
```

Esto no es fine-tuning. Es un banco local extraído directamente de casos `candidate_qa` aprobados y organizados por etapa + nivel + tema.

**Por qué NO recomendar fine-tuning como primer paso:**
- Los 1.895 casos son suficientes para RAG pero **insuficientes** para fine-tuning de alta calidad (mínimo recomendado: 5.000-10.000 pares de alta calidad para un modelo conversacional).
- El RAG con reranker semántico y metadata atómica va a resolver el 80% del problema de coherencia sin riesgo de contaminar el modelo base.
- **Si en el futuro se considera fine-tuning:** usar solo casos `confidence: alta` + `etapa_conversacional: cierre o contacto` + `evidencia_tipo: numero o cita verificable`. Excluir casos con `ocr_quality: baja`, conversaciones < 6 turnos y cualquier caso con señal negativa en OCR.

---

**Mejora 9: Pruebas Automatizadas Faltantes**

| Suite | Herramienta propuesta | Qué verifica |
|---|---|---|
| `test_routing_intent.py` | pytest | Input → ruta correcta (Natalia/Maximus). 50+ casos. |
| `test_retrieval_precision.py` | pytest + catálogo | Colección recuperada = colección esperada. |
| `test_groundedness.py` | pytest | Respuesta no inventa datos fuera del contexto. |
| `test_persona_voice.py` | LLM-as-judge (Gemini Flash) | ¿La respuesta suena como mujer LATAM real? Score 1-5. |
| `test_coach_pedagogy.py` | pytest | ¿Maximus da 3 sugerencias y cita fuente? |
| `test_emoji_regression.py` | pytest | Emojis degradados (🟡🟡) no activan reglas falsas. |
| `test_ui_regression.py` | Playwright headless | Nav tabs, modales, Game Over, Level Up sin errores JS. |
| `test_timing_p95.py` | locust o pytest + asyncio | P95 < 3s en 5 usuarios simultáneos. |
| `test_negative_isolation.py` | pytest | Natalia-Persona nunca recupera de `natalia_negative_cases`. |

---

**Mejora 10: Integración de los 5.000 Casos sin Contaminar**

**Protocolo de integración segura:**

```
1. QA pre-indexación:
   - Correr catálogo 220 preguntas contra lote ANTES de indexar.
   - Si alguna categoría baja > 5% vs baseline, STOP y audit.

2. Staging:
   - Crear colección temporal `natalia_success_cases_v2` en Chroma.
   - Shadow-run: 10% de tráfico real va a v2, registrar retrieval_summary.
   - Comparar confidence scores y match_quality vs v1.

3. Merge:
   - Si staging pasa QA (95% ≥ baseline), merge a `natalia_success_cases`.
   - Reconstruir grafo de objetivos.
   - Correr daily_maintenance completo.

4. Post-merge monitoring:
   - Alertar si `persona_rejected_pairs` sube > 10% del total nuevo.
   - Alertar si fallback_category="guardrail" sube > 15%.
```

---

## 3. Propuesta de Arquitectura del Router Natalia vs Maximus

```
Usuario envía mensaje
        │
        ▼
┌─────────────────────────────────────────────┐
│  classify_turn_intent(message, game_stage)  │
│                                             │
│  ¿Contiene trigger de Maximus?             │
│  → regex: consejo, qué digo, técnica,      │
│    estrategia, Maximus, foto, opener,       │
│    WhatsApp explícito como pregunta,        │
│    Instagram como pregunta, primera cita    │
│                                             │
│  ¿Etapa = Game Over / Estudiar / Resumen?  │
│  → Siempre Maximus                         │
│                                             │
│  Si ninguno → Natalia-Persona              │
└─────────────────────────────────────────────┘
        │                    │
        ▼                    ▼
  RUTA NATALIA          RUTA MAXIMUS
  ─────────────         ─────────────
  retrieve_persona      retrieve_coach
  _cases()              _cases()
       │                    │
  Solo colecciones:    Todas las colecciones:
  • natalia_success    • natalia_success_cases
    _cases             • natalia_negative_cases
  (NO negativos,       • natalia_books_kb
   NO libros teoría,   • natalia_conversations
   NO YouTube)         • YouTube/legacy
       │                    │
  Respuesta breve      Análisis pedagógico
  conversacional       + 3 opciones A/B/C
  humana LATAM         + cita de fuente
```

### Ejemplos de mensajes y su ruta

| Mensaje del usuario | Ruta | Colecciones |
|---|---|---|
| "Jaja sí, trabajo en marketing" | Natalia-Persona | natalia_success_cases |
| "¿Qué le respondo a esto?" | Maximus-Coach | todas |
| "Maximus, ¿cómo la cierro?" | Maximus-Coach | todas |
| "¿Cuál es tu película favorita?" | Natalia-Persona | natalia_success_cases |
| "Me puedes dar un opener" | Maximus-Coach | natalia_books_kb + success |
| "Quiero ver fotos de ella" | Maximus-Coach (educativo) | success + libros |
| "Lol qué gracioso" | Natalia-Persona | natalia_success_cases |
| (Game Over screen) cualquier texto | Maximus-Coach | todas |
| "Dame una estrategia para el nivel 3" | Maximus-Coach | success + negativos + libros |

### Regla para "Maximus..." dentro del chat de Natalia

**Recomendación:** Interceptar como trigger de Maximus y NO pasarlo como mensaje de conversación a Natalia-Persona.

```python
if re.match(r'^maximus[,:]?\s+', user_message, re.IGNORECASE):
    return route_to_maximus(user_message)
# Evita que Natalia reciba "Maximus, ayúdame" y responda como si el usuario le hablara a ella
```

---

## 4. Plan de Implementación por Fases

### Fase Corto Plazo (1-2 semanas)

| Tarea | Esfuerzo | Prioridad |
|---|---|---|
| Implementar `classify_turn_intent()` en `server.py` | 2d | 🔴 Alta |
| Interceptar "Maximus..." en chat de Natalia | 0.5d | 🔴 Alta |
| Añadir metadata atómica: `etapa_conversacional`, `evidencia_tipo`, `idioma_original` | 3d | 🔴 Alta |
| Ampliar catálogo a 200+ con preguntas de routing y persona-voice | 2d | 🟡 Media |
| Implementar `test_routing_intent.py` + `test_negative_isolation.py` | 1d | 🟡 Media |
| Hardcodear guardrails de grounding como código (no solo docs) | 1d | 🟡 Media |

### Fase Mediano Plazo (3-6 semanas)

| Tarea | Esfuerzo | Prioridad |
|---|---|---|
| Reranker semántico local (CrossEncoder) con A/B vs heurístico | 3d | 🟡 Media |
| Integración controlada de `natalia_books_kb` en Chroma operativo | 4d | 🟡 Media |
| Banco de respuestas reales para fallback local (por etapa × nivel × tema) | 5d | 🟡 Media |
| Suite completa de pruebas automáticas (timing, UI, emoji) | 4d | 🟡 Media |
| Sincronizar `natalia_conversations_plus` legacy | 1d | 🟢 Baja |

### Fase Largo Plazo (al llegar a 5.000 casos)

| Tarea | Esfuerzo | Prioridad |
|---|---|---|
| Protocolo de integración staging v2 de los 5.000 casos | 5d | 🔴 Alta cuando llegue |
| Grafo de conocimiento completo con 5.000 casos aprobados | 3d | 🔴 Alta cuando llegue |
| Evaluar fine-tuning (solo si RAG+reranker no alcanza 90% persona-voice) | 15d+ | 🟢 Baja por ahora |
| Ampliar catálogo a 500+ preguntas por dificultad y perfil femenino | 5d | 🟢 Baja |

---

## 5. Tabla Final de Mejoras

| # | Mejora | Motivo | Componente | Esfuerzo | Riesgo | Prueba de Verificación |
|---|---|---|---|---|---|---|
| 1 | Intent Router `classify_turn_intent()` | Routing actual es por etapa, no por intención | `backend/server.py` | 2d | Bajo | `test_routing_intent.py` 50 casos |
| 2 | Metadata atómica en Chroma | Sin campos atómicos, filtros `$and/$contains` no funcionan | `index_success_candidates_chroma.py` | 3d | Medio | Re-run catálogo 120 preguntas |
| 3 | Reglas de router como código | Reglas solo en docs no se verifican automáticamente | `server.py` + nuevo `router_rules.py` | 1d | Bajo | `test_routing_intent.py` |
| 4 | Ampliar catálogo 120→220 | Faltan dimensiones críticas: routing, voice, nivel, emoji | `generate_natalia_rag_eval_catalog.py` | 2d | Bajo | Correr `qa_natalia_rag_catalog.py` |
| 5 | Reranker semántico CrossEncoder | Reranker heurístico no mide relevancia semántica real | `server.py` + nuevo `reranker.py` | 3d | Bajo | A/B con catálogo 220 preguntas |
| 6 | Guardrails de grounding como código | Reglas de no-inventar solo documentadas, no ejecutadas | `server.py` + nuevo `guardrails.py` | 1d | Bajo | `test_groundedness.py` |
| 7 | Integración `natalia_books_kb` en chroma_db | Libros no se consultan en runtime | `daily_natalia_rag_maintenance.py` | 4d | Medio | QA catálogo solo contra libros primero |
| 8 | Banco real de respuestas para fallback | Fallback local puede sonar robótico | `server.py` local fallback | 5d | Bajo | `test_persona_voice.py` score ≥ 4/5 |
| 9 | Suite de pruebas automatizadas completa | Faltan 8 suites críticas (routing, timing, emoji, UI) | `tests/` nuevo directorio | 4d | Bajo | CI pre-deploy |
| 10 | Protocolo staging para 5.000 casos | Integración sin staging puede contaminar RAG activo | `index_success_candidates_chroma.py` v2 | 5d | Alto si se omite | Shadow-run 10% tráfico |

---

## 6. Brechas que No Están Documentadas en `arquitectura.html`

> Declaro honestamente lo que NO puedo asumir de la documentación:

- **B-DOC-1:** No está documentado qué sucede cuando Gemini devuelve respuesta incoherente (sin `400`, sin `429`). ¿Existe un guardrail de coherencia de idioma activo en producción?
- **B-DOC-2:** No está claro si `natalia_conversations_plus` (46 docs) se consulta activamente o está dormida.
- **B-DOC-3:** No está documentado el tiempo de latencia P95 real del sistema bajo carga. Solo hay pruebas funcionales, no de rendimiento.
- **B-DOC-4:** No se documenta qué ocurre si `retrieve_persona_cases()` devuelve 0 resultados. ¿Cae a fallback local inmediatamente o intenta otra colección?
- **B-DOC-5:** No está documentada la política de retención de conversaciones en `localStorage` del usuario. Si hay estado corrupto, `?reset=1` no se activa automáticamente.
