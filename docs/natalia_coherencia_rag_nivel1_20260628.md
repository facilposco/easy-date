# Informe Natalia/Coach - Coherencia RAG Nivel 1

Fecha: 2026-06-28

## Objetivo

Corregir la desalineacion donde el usuario respondia una cosa, Natalia contestaba otra y el Coach evaluaba como si siguiera un guion oculto.

## Cambios aplicados

- `backend/server.py`
  - `SimulateTurnRequest` ahora acepta `evaluated_step_id` y `visible_context`.
  - Coach y Natalia reciben un `CONTEXTO VISIBLE AUTORITATIVO` con ultimo mensaje visible de Natalia, respuesta actual del hombre y snapshot resumido.
  - `chat_turns` ya no trae los ultimos turnos por perfil; ahora rankea por similitud con el contexto visible.
  - Nivel 3 ya no busca `alta_selectividad` como perfil RAG inexistente; usa `desinteresada` como perfil recuperable y conserva `alta_selectividad` como etiqueta pedagogica.
  - Fallback de Natalia reconoce si el hombre ignora una pregunta visible.
  - Fallback de Natalia escala el cierre del nivel: curiosidad, plan, dia y WhatsApp segun avance/atraccion.
  - Fallback del Coach penaliza explicitamente ignorar la pregunta visible.
  - Natalia-Persona recibe el dictamen completo del Coach, no solo el score.
  - Se agrego validacion ligera para rechazar respuestas de Natalia que mencionen coach, score, reglas o contradigan el veredicto.
  - Se agrego recuperacion de pares reales `Hombre -> Mujer` desde `chat_turns` y `reddit_conversations.transcription_json`.
  - Los pares reales se insertan en `retrieve_cases` como `sqlite_chat_pair` y `sqlite_reddit_pair`.
  - Si Gemini cae por cuota, el fallback puede reutilizar una respuesta real corta de mujer cuando el par recuperado es similar y seguro.
  - Los pares reales ahora se etiquetan al vuelo con `intent`, `woman_signal` y `success_score`.
  - Se agrego `/api/training-status` para auditar el volumen de entrenamiento sin exponer secretos.

- `build_simulator.py`
  - El frontend envia `visible_context` al backend.
  - El tiempo por defecto ahora es `15m`, no `Ahora mismo`.
  - El fallback local del navegador ya no dice que fallo la IA.
  - El fallback local responde segun la ultima pregunta visible de Natalia y escala hacia plan/WhatsApp.

- `simulador_v1.2.html`
  - Regenerado desde `build_simulator.py`.

## Verificacion ejecutada

- `python -m py_compile backend\server.py build_simulator.py`
- `python -m py_compile backend\server.py build_simulator.py tests\test_backend.py`
- `python build_simulator.py`
- `pytest -q tests\test_simulator_level1.py -rs`
- `pytest -q tests\test_backend.py tests\test_simulator_level1.py -rs`
- Ultima corrida: `8 passed`.
- `node` syntax check del JavaScript embebido.
- Backend reiniciado en `http://127.0.0.1:8000`.
- `/health` OK:
  - `gemini_keys_loaded`: 3
  - `chroma_connected`: true
  - `chroma_documents`: 169

## Smoke test de coherencia

Caso:

- Natalia visible: `me gusta eso, perfecto donde vives? yo en brickell y tu?`
- Hombre: `hola`

Resultado actual:

- Natalia: `jaja respondiste, pero me dejaste la pregunta en el aire.`
- Coach: penaliza que ignoro la pregunta visible de Natalia.
- Pierde vida: true.

Esto corrige el fallo anterior donde el Coach podia hablar de vino, ubicacion o cita sin coincidir con el mensaje real.

## Smoke test RAG real

Caso:

- Hombre: `Tengo datos curiosos sobre trenes.`

Resultado API/UI:

- Natalia: `Dime tu dato de trenes mas cochino jajaja`
- Fuente recuperada: `sqlite_chat_pair` y `sqlite_reddit_pair` desde el post Reddit `epxvl5`.
- Metadata del par principal: `intent=conversacion`, `woman_signal=risa`, `success_score=9`.

Esto prueba que, incluso con Gemini en 429, Natalia puede apoyarse en respuestas reales de la base y no solo en plantillas locales.

## Ajuste anti-repeticion y modo escribir

Ronda adicional:

- Natalia ahora registra respuestas previas de ella en el historial y evita reutilizar la misma frase local o recuperada.
- La seleccion de frases reales prioriza senales de mujer segun la intencion del hombre: contacto, cierre de plan, humor, pregunta contextual o conversacion general.
- En pasos tardios del nivel o con atraccion alta, el fallback progresa hacia WhatsApp/plan en vez de quedarse dando vueltas en frases genericas.
- Para intenciones de cierre/contacto/logistica, Natalia prioriza el contexto local del plan y no una frase RAG que pueda venir cruzada de otro tema.
- Se filtran respuestas reales vacias tipo `Jajajajajaja` para que funcionen como senal, pero no como respuesta principal.
- Al restaurar una partida guardada, el simulador fuerza `replyMode = free` para que el usuario vea el campo de escritura como experiencia principal tipo Tinder.
- El campo de texto se enfoca al restaurar una conversacion para reducir la sensacion de que "no deja escribir".
- El campo de mensaje queda siempre visible; el modo `Sugerencias` ahora rellena el textarea en vez de reemplazarlo.
- El boton falso de `GIF` se cambio a reaccion `😂`, porque por ahora inserta emoji y no un GIF real.
- El panel inferior tiene `max-height` y scroll interno para reducir overflow en pantallas bajas.

Pruebas agregadas:

- `test_fallback_natalia_avoids_repeated_plan_reply`
- `test_fallback_natalia_progresses_to_contact_late_level`
- `test_reusable_real_reply_skips_empty_laughter`
- `test_fallback_plan_intent_ignores_unrelated_real_pair`

Verificacion:

- `python -m py_compile backend\server.py tests\test_backend.py`
- `pytest -q tests\test_backend.py tests\test_simulator_level1.py -rs`
- Resultado: `12 passed, 1 warning`.

Smoke test adicional:

- Entrada: `Tengo un plan con vino y buena musica`
- Natalia: `Ok, ahora si estas vendiendo mejor el plan. Sigue.`
- Resultado esperado: ya no responde con frases cruzadas de otro caso real, como trenes.

## Ronda de coherencia contra capturas del usuario

Problema observado:

- El usuario respondia `yo vivo en bogota y en que trabajas?`.
- Natalia podia saltar a un tema de guion como vino, sin responder la pregunta real.
- El Coach podia evaluar contra el paso oculto en vez de contra el mensaje visible.

Cambios:

- Natalia-Persona ahora tiene instruccion explicita de no avanzar a un tema oculto cuando el hombre da un dato o pregunta algo directo.
- Si el hombre responde ubicacion y pregunta trabajo, Natalia reconoce ubicacion y responde trabajo antes de devolver otra pregunta.
- El fallback local del frontend replica esa misma logica si la API no responde.
- El mock de pruebas ya no evalua por similitud literal contra la opcion correcta; usa el simulador local contextual.
- El retrieval RAG ahora prioriza pares reales `Hombre -> Mujer` antes de Chroma/Reddit largo/YouTube, para que Natalia imite turnos reales y no teoria.
- El prompt de Natalia aclara que los casos reales son inspiracion de tono, no texto para copiar si contradicen el contexto visible.

Smoke test de captura:

- Contexto visible: `me gusta eso, perfecto donde vives? yo en brickell y tu?`
- Hombre: `yo vivo en bogota y en que trabajas?`
- Coach fallback: reconoce que respondio la ubicacion y senala como pulible la pregunta logistica extra.
- Natalia fallback: `Jaja Bogota me queda claro. Trabajo en algo creativo, pero me interesa mas saber que haces cuando sales del modo serio.`
- Pierde vida: `false`.

Verificacion adicional:

- `pytest -q tests\test_backend.py tests\test_simulator_level1.py -rs`
- Resultado: `14 passed, 1 warning`.

Chrome:

- Chrome esta instalado y corriendo.
- La extension Codex Chrome aparece instalada y habilitada.
- El diagnostico del native host reporto registry key faltante: `HKCU\Software\Google\Chrome\NativeMessagingHosts\com.openai.codexextension`.
- Por esa razon no se pudo controlar Chrome para una prueba visual completa desde Codex. La guia del plugin indica no reparar esto manualmente; requiere reinstalar/rehabilitar el plugin desde la UI de Codex.

## Ronda de analizador compartido Coach/Natalia

Objetivo:

- Reducir respuestas tipo plantilla cuando el usuario escribe libremente.
- Hacer que Natalia-Persona y Natalia-Coach se basen en el mismo analisis del turno visible.

Cambios:

- Se agrego `analyze_visible_turn`, una capa compartida que detecta:
  - intencion del mensaje,
  - temas del ultimo mensaje de Natalia,
  - temas del mensaje del hombre,
  - si el hombre respondio la pregunta visible,
  - si agrego una pregunta nueva,
  - si ignoro la pregunta.
- `heuristic_score` ahora usa esa capa comun, en vez de inferir todo con reglas separadas.
- `fallback_natalia_message` tambien usa esa capa para responder preguntas directas antes de usar RAG o frases de avance.
- Natalia ahora contesta directamente preguntas sobre trabajo, ejercicio, vino o ubicacion antes de cambiar de tema.
- `infer_turn_intent` ya no mezcla de forma ingenua el mensaje anterior con el mensaje del hombre; esto evitaba clasificar `como va tu dia?` como cierre de plan.

Smoke test adicional:

- Contexto visible: `esa soy yo totalmente jaja como va tu dia?`
- Hombre: `bien en el gimnasio y a ti te gusta hacer ejercicio?`
- Natalia: `Si, me gusta moverme, pero sin volverme intensa con el gym jaja. Tu que entrenas?`
- Coach: `Calidad del mensaje: conecta con el contexto visible.`
- Pierde vida: `false`.

Verificacion:

- `python -m py_compile backend\server.py tests\test_backend.py`
- `pytest -q tests\test_backend.py tests\test_simulator_level1.py -rs`
- Resultado: `16 passed, 1 warning`.

## Ronda de calidad RAG y resumen de entrenamiento

Objetivo:

- Evitar que una respuesta real de la base se reutilice cuando pertenece a otro tema.
- Hacer visible cuanto entrenamiento utilizable hay por perfil, intencion y senal de mujer.

Cambios:

- `reusable_real_woman_reply` ahora acepta `topic_guard`.
- Cuando el turno actual tiene temas claros, un caso real solo puede reutilizarse si su mensaje de hombre comparte tema.
- Si el caso real no tiene tema detectable y el turno actual si lo tiene, no se usa como respuesta directa.
- `/api/training-status` ahora incluye `profile_training`.
- `profile_training` desglosa por perfil:
  - pares derivados,
  - promedio de exito,
  - intenciones,
  - senales de la mujer.

Ejemplo vivo de `profile_training.coqueta`:

- Pares: 182
- Success average: 5.35
- Intenciones principales: `conversacion=125`, `pregunta_contextual=31`, `abridor=12`
- Senales principales: `neutral=109`, `pregunta_de_vuelta=35`, `fria=17`, `receptiva=12`

Verificacion:

- `python -m py_compile backend\server.py tests\test_backend.py`
- `pytest -q tests\test_backend.py tests\test_simulator_level1.py -rs`
- Resultado: `17 passed, 1 warning`.

## Ronda frontend contra salto de guion

Auditoria:

- El frontend ya no inyecta `step.her_message` como respuesta fija de Natalia.
- La respuesta visible de Natalia sale de `simulation.natalia_message`.
- Los pasos siguen existiendo como estructura pedagogica/progreso, no como dialogo obligatorio.

Riesgo detectado:

- El fallback local del HTML todavia necesitaba una prueba automatica que reprodujera mensajes libres fuera del guion.

Cambios:

- Se agrego `window.easyDateTest.runContextCoherenceSmoke`.
- El smoke prueba dos divergencias similares a las capturas:
  - Hombre pregunta por ejercicio despues de `como va tu dia`.
  - Hombre responde ubicacion y pregunta trabajo despues de `donde vives`.
- Se agrego `test_frontend_fallback_context_coherence_with_playwright`.

Verificacion:

- `python build_simulator.py`

## Ronda multiagente y verificacion Chrome real

Fecha/hora: 2026-06-28, tarde.

Objetivo:

- Acercar el simulador a una conversacion humana real.
- Separar mejor Natalia-Persona de Natalia-Coach.
- Evitar que el Coach y Natalia respondan desde plantillas o pasos ocultos.
- Validar Nivel 1 en Chrome real.

Subagentes usados:

- Auditor backend/RAG-Coach: detecto mojibake real, fallos con tildes y mezcla de teoria YouTube dentro del prompt de Natalia-Persona.
- Auditor frontend/UX: detecto mezcla entre modo `Mensaje` y `Sugerencias`, boton GIF falso y ambiguedad del modal Coach.
- Auditor pruebas: confirmo la suite minima para Nivel 1 y huecos de cobertura.

Cambios aplicados:

- `backend/server.py`
  - Se agrego `clean_ui_text` con `ftfy` para limpiar mojibake antes de devolver mensajes, feedback, sugerencias y tiempos.
  - `topic_set`, `asks_question`, `infer_turn_intent` y `direct_question_topics` ahora normalizan texto antes de detectar intenciones.
  - `direct_question_topics` ahora reconoce espanol normal con tilde: `¿en qué trabajas?`, `¿dónde vives?`, `¿qué tal tu día?`.
  - Se agrego `persona_cases_to_prompt`: Natalia-Persona recibe solo pares reales `Hombre -> Mujer`; YouTube/teoria quedan para Coach/RAG, no como voz que Natalia deba imitar.
  - `/api/evaluate` limpia mojibake y ya no agrega el placeholder viejo `[Simulacion] El NPC recibe el mensaje...`.
  - El feedback fallback cambio `Objetivo del paso` por `Objetivo del turno`.

- `build_simulator.py`
  - Modo `Sugerencias` ahora se separa del modo `Mensaje`: oculta el textarea libre y no copia opciones al campo de texto.
  - Al volver a `Mensaje`, se limpian opciones seleccionadas para evitar enviar algo distinto a lo visible.
  - Insercion de emoji respeta cursor en posicion 0.
  - Boton `GIF` inserta `[GIF: risa]`, para que el Coach pueda evaluar el recurso como parte del mensaje.
  - Modal del Coach muestra `Natalia-Coach`, no `Maximus Coach`.
  - Feedback local ya no habla de `Paso X`; usa objetivo visible/turno.
  - Boton `ENTENDIDO` reforzado con `click`, `pointerdown` y teclado.
  - Timeout frontend contra `/api/simulate-turn` bajado de 45s a 18s para no congelar la UI si Gemini/API tarda.

- `simulador_v1.2.html`
  - Regenerado desde `build_simulator.py`.

Pruebas ejecutadas:

- `python -m py_compile backend\server.py tests\test_backend.py build_simulator.py`
- `python build_simulator.py`
- `pytest -q tests\test_backend.py tests\test_simulator_level1.py tests\test_simulator_mobile_layout.py -rs`
- Resultado final completo: `35 passed, 1 warning`.
- Verificacion UI especifica despues del timeout: `pytest -q tests\test_simulator_level1.py tests\test_simulator_mobile_layout.py -rs`
- Resultado UI: `6 passed`.

Chrome real:

- URL probada: `http://127.0.0.1:8000/simulador_v1.2.html`.
- Se completo Nivel 1 hasta `¡Cita Lograda!`.
- Progreso final observado: `Nivel 1 · Paso 10 de 10`.
- Vidas finales observadas: `❤️❤️❤️❤️`.
- Atraccion final observada: `100%`.
- El modal ya mostro `Natalia-Coach`, sin `Maximus Coach`.
- En los pasos verificados no aparecio `Objetivo del paso`.
- Caso critico corregido:
  - Hombre: `Vivo en Bogotá. ¿Y tú en qué trabajas?`
  - Natalia: `Jaja Bogotá me queda claro. Trabajo en algo creativo, pero me interesa más saber qué haces cuando sales del modo serio.`
  - No salto a vino.

Riesgo pendiente:

- Gemini sigue respondiendo `429` en las 3 keys. El servidor rota claves correctamente y cae a fallback, pero la naturalidad 100% humana todavia no puede declararse completada con modelo real activo.
- Mientras Gemini este en 429, la experiencia depende del fallback contextual + RAG local. Ya no se rompe el flujo, pero la voz puede sentirse menos variada que con Natalia-Persona funcionando con modelo.

## Ronda anti-plantilla para fallback 429

Motivo:

- En Chrome real, con Gemini en `429`, el fallback podia sonar generico en pasos de logistica.
- Ejemplo observado: cuando el usuario hablaba de zona/lugar, Natalia podia caer en `cuentame un poco mas`, que no responde la logistica visible.
- El Coach tambien podia traer sugerencias aprendidas de DB sin tema claro, por ejemplo frases de vacaciones que no correspondian al turno actual.

Cambios:

- `case_based_suggestions` ahora exige que haya un tema claro en el turno antes de proponer frases aprendidas de la DB.
- `topic_set` y `direct_question_topics` ahora entienden `zona`, `lugar`, `que zona`, `que lugar` como logistica de ubicacion/plan.
- `fallback_natalia_message` prioriza dia/copa antes de `lugar`, para no perder mensajes como `jueves una copa corta`.
- Natalia fallback contesta logistica:
  - Si preguntan zona: responde Brickell/zona y pide lugar concreto.
  - Si proponen lugar: reconoce el lugar y pide concrecion.
  - Si proponen dia+copa: reconoce jueves/copa.
- El fallback local del navegador replica ese orden para no depender del backend cuando hay timeout.
- Texto local corregido: `Podrías decir algo como:`.

Pruebas nuevas:

- `test_case_based_suggestions_requires_clear_topic`
- `test_fallback_answers_zone_logistics_without_generic_curiosity`
- `test_fallback_answers_place_logistics_without_generic_curiosity`

Verificacion:

- `pytest -q tests\test_backend.py -q`
- Resultado: `32 passed`.
- `python build_simulator.py`
- `pytest -q tests\test_backend.py tests\test_simulator_level1.py tests\test_simulator_mobile_layout.py -rs`
- Resultado final: `38 passed, 1 warning`.

## Ronda de cobertura RAG cross-profile

Motivo:

- `/api/training-status` mostro 389 pares reales derivados, pero con baja cobertura en intenciones criticas:
  - `cerrar_plan`: 7 pares.
  - `logistica_ligera`: 6 pares.
  - `humor`: 5 pares.
  - `pedir_contacto`: 0 pares directos en varios perfiles y solo 2 senales de contacto en total.
- Si Natalia restringe siempre por perfil exacto, niveles con pocos datos quedan demasiado dependientes de fallback manual.

Cambios:

- Se agrego `SCARCE_REPLY_INTENTS`.
- `retrieve_real_reply_pairs` ahora abre busqueda cross-profile solo para intenciones escasas: `cerrar_plan`, `pedir_contacto`, `logistica_ligera`, `humor`.
- El perfil exacto conserva prioridad con `profile_rank_bonus`, asi que no se pierde la personalidad del nivel cuando hay pares suficientes.
- Para intenciones comunes como `conversacion`, la busqueda sigue estricta por perfil para evitar contaminacion de tono.
- `/api/training-status` ahora reporta `profile_intent_gaps` para ver brechas por perfil/intencion.

Verificacion de endpoint:

- `derived_training_pairs`: 389.
- `chroma_documents`: 169.
- Brechas actuales detectadas:
  - `coqueta`: `pedir_contacto=0`.
  - `defensiva`: `cerrar_plan=0`, `humor=0`, `logistica_ligera=0`, `pedir_contacto=0`.
  - `desinteresada`: `cerrar_plan=0`, `humor=0`, `logistica_ligera=2`, `pedir_contacto=0`.
  - `indecisa`: `cerrar_plan=2`, `humor=0`, `logistica_ligera=0`, `pedir_contacto=0`.

Pruebas nuevas:

- `test_retrieve_real_reply_pairs_broadens_profiles_for_scarce_plan_intent`
- `test_retrieve_real_reply_pairs_keeps_profile_strict_for_common_intent`

Verificacion:

- `pytest -q tests\test_backend.py -q`
- Resultado: `34 passed`.
- `pytest -q tests\test_backend.py tests\test_simulator_level1.py tests\test_simulator_mobile_layout.py -rs`
- Resultado final: `40 passed, 1 warning`.

## Ronda de limpieza de señales mujer

Motivo:

- La clasificacion de senales de la mujer (`contacto`, `risa`, `pregunta_de_vuelta`, `receptiva`, `fria`) alimenta el `success_score` de pares reales.
- Esa funcion todavia leia texto sin normalizar; OCR/mojibake podia ocultar `numero`, `teléfono`, emojis de risa o signos de pregunta.

Cambios:

- `infer_woman_signal` ahora aplica `clean_ui_text` antes de clasificar.
- Reconoce variantes limpias y mojibake de `número`, `teléfono`.
- Reconoce emojis reales `😂` y `🤣` ademas de mojibake viejo.
- Reconoce `¿` como pregunta de vuelta.

Prueba nueva:

- `test_infer_woman_signal_cleans_encoding_and_emojis`

Verificacion:

- `pytest -q tests\test_backend.py::test_infer_woman_signal_cleans_encoding_and_emojis -q`
- Resultado: `1 passed`.
- `pytest -q tests\test_backend.py -q`
- Resultado: `35 passed`.
- `pytest -q tests\test_backend.py tests\test_simulator_level1.py tests\test_simulator_mobile_layout.py -rs`
- Resultado final: `41 passed, 1 warning`.

## Ronda de limpieza iterativa de mojibake

Motivo:

- Algunos textos de DB/tests pueden llegar con doble mojibake, por ejemplo `TardÃƒÂ³` o `tendrÃƒÂ­amos`.
- Una sola pasada de limpieza puede reparar solo parcialmente y dejar texto raro dentro de prompts, feedback o sugerencias.

Cambios:

- `clean_ui_text` ahora aplica `ftfy` hasta 3 veces o hasta que el texto se estabilice.
- Esto mejora prompts, salida visible, deteccion de intenciones y senales de mujer porque todas esas rutas pasan por `clean_ui_text`.

Prueba nueva:

- `test_clean_ui_text_repairs_double_mojibake_with_ascii_escapes`

Verificacion:

- `pytest -q tests\test_backend.py::test_clean_ui_text_repairs_mojibake tests\test_backend.py::test_clean_ui_text_repairs_double_mojibake_with_ascii_escapes -q`
- Resultado: `2 passed`.
- `pytest -q tests\test_backend.py -q`
- Resultado: `36 passed`.
- `pytest -q tests\test_backend.py tests\test_simulator_level1.py tests\test_simulator_mobile_layout.py -rs`
- Resultado final: `42 passed, 1 warning`.

## Ronda ficha concreta de Natalia

Motivo:

- La respuesta fallback de trabajo usaba `algo creativo`, que sonaba plantilla.
- Para que Natalia se sienta humana, la identidad del nivel debe tener datos concretos y consistentes.

Cambios:

- `LEVEL_BEHAVIOR` ahora incluye por nivel:
  - `location_area`
  - `work_hint`
  - `off_mode`
- Nivel 1 queda con:
  - zona: `Brickell`
  - trabajo: `marketing visual para restaurantes`
  - fuera de rutina: `planes tranquilos y musica sin ponerse intensa`
- El prompt de Natalia-Persona recibe esa ficha.
- El fallback backend usa esa ficha al responder trabajo/ubicacion/logistica.
- El fallback local del navegador tambien responde con `marketing visual para restaurantes`, no `algo creativo`.
- Se evito meter `vino` dentro de la respuesta de trabajo para no reabrir el bug de salto de tema.

Pruebas:

- `test_level_behavior_has_concrete_persona_facts`
- Se actualizaron expectativas para exigir `marketing` en respuestas de trabajo.
- Smoke frontend actualizado para validar la misma ficha concreta.

Verificacion:

- `pytest -q tests\test_backend.py -q`
- Resultado: `37 passed`.
- `python build_simulator.py`
- `pytest -q tests\test_backend.py tests\test_simulator_level1.py tests\test_simulator_mobile_layout.py -rs`
- Resultado final: `43 passed, 1 warning`.
- `pytest -q tests\test_backend.py tests\test_simulator_level1.py -rs`
- Resultado: `18 passed, 1 warning`.

## Estado de entrenamiento derivado

Endpoint: `/api/training-status`

- Reddit total: 213
- Reddit con `transcription_json`: 211
- `chat_turns`: 37
- Pares derivados `Hombre -> Mujer`: 385
- Chroma: 169 documentos

Intenciones detectadas:

- `abridor`: 29
- `cerrar_plan`: 13
- `conversacion`: 244
- `humor`: 12
- `logistica_ligera`: 7
- `pregunta_contextual`: 80

Senales de mujer detectadas:

- `contacto`: 2
- `fria`: 56
- `neutral`: 209
- `pregunta_de_vuelta`: 64
- `receptiva`: 25
- `risa`: 29

## Prueba Chrome Nivel 1

Se ejecuto Nivel 1 completo en Chrome con respuestas libres.

Resultado:

- Llego a `Cita Lograda` / Level Up.
- No hubo bloqueo del modal Coach.
- El input se bloqueo durante evaluacion y se desbloqueo despues de `ENTENDIDO`.
- El progreso llego a `Nivel 1 - Paso 10 de 10`.
- El tiempo por defecto fue `15m`.

## Limitacion actual

Gemini devolvio 429 en las 3 claves para `gemini-2.5-flash`.

Por eso la prueba completa de Chrome valido flujo, contexto visible y fallback coherente, pero no prueba todavia la naturalidad maxima con Gemini activo. Mientras las claves sigan en 429, Natalia no puede sentirse 100% humana porque no esta generando con el modelo, sino con fallback local.

## Pendientes recomendados

1. Reprobar Nivel 1 cuando Gemini deje de responder 429.
2. Agregar un endpoint/debug opcional que devuelva `fallback_reason` sin exponer claves.
3. Etiquetar exito/fracaso por conversacion con mas precision manual o semi-automatica.
4. Reducir la UI visible de juego si se quiere maxima inmersion Tinder.

## Ronda UI mobile y trazabilidad compartida

Fecha/hora local: 2026-06-28 tarde.

Cambios backend:

- `/api/simulate-turn` ahora calcula `turn_analysis` una sola vez por turno.
- `turn_analysis` se inyecta tanto en el prompt de Natalia-Coach como en el de Natalia-Persona bajo `ANALISIS COMPARTIDO DEL TURNO`.
- La respuesta API devuelve `turn_analysis` para auditoria segura:
  - `intent`
  - `user_topics`
  - `last_topics`
  - `answered_topics`
  - `asked_question`
  - `ignored_question`
  - `chosen_time`

Cambios frontend:

- `simulador_v1.2.html` fue regenerado desde `build_simulator.py`.
- El footer se compacto para parecer mas composer de chat:
  - acciones `Reiniciar`, `Estudiar` y `Enviar` en una sola fila;
  - boton `Enviar` mas corto, sin `ENVIAR RESPUESTA`;
  - boton `GIF` con etiqueta accesible de GIF de risa;
  - `aria-pressed` en el selector `Mensaje/Sugerencias`;
  - media query para pantallas bajas;
  - `100dvh/100svh` para reducir problemas de viewport movil;
  - grilla de sugerencias a una columna en pantallas chicas.

Pruebas agregadas:

- `tests/test_simulator_mobile_layout.py`
  - Verifica `390x844` y `360x640`.
  - Comprueba que `#free-reply-input` y `#btn-send` quedan visibles.
  - Comprueba que `.bottom-panel` no supera el 49% del viewport.
  - Comprueba que al enfocar el textarea el boton enviar sigue visible.

Verificacion:

- `python build_simulator.py`
- `python -m py_compile backend\server.py build_simulator.py tests\test_backend.py`
- `pytest -q tests\test_backend.py tests\test_simulator_level1.py tests\test_simulator_mobile_layout.py -rs`
- Resultado: `21 passed, 1 warning`.

Smoke API tras reiniciar backend:

- Backend reiniciado en `http://127.0.0.1:8000`.
- `/health` OK con Chroma conectado y 169 documentos.
- Caso: Natalia pregunta ubicacion y el hombre responde `yo vivo en bogota y en que trabajas?`.
- Resultado:
  - Natalia responde sobre Bogota y trabajo.
  - No pierde vida.
  - `turn_analysis.answered_topics = ["ubicacion"]`.
  - `turn_analysis.user_topics = ["trabajo", "ubicacion"]`.

## Ronda validador post-modelo y Chrome real

Objetivo:

- Evitar que Natalia-Persona, incluso cuando Gemini responda, salte a un tema no relacionado.
- Reproducir y bloquear los fallos observados en capturas: pregunta por trabajo -> respuesta de vino; pregunta por semana -> respuesta de ubicacion/visita; plan con `dia jueves` -> respuesta sobre semana.

Cambios backend:

- `turn_analysis` ahora incluye:
  - `direct_question_topics`
  - `response_directive`
- Los prompts de Natalia-Coach y Natalia-Persona reciben una `DIRECTIVA OBLIGATORIA` derivada del contexto visible.
- `natalia_response_is_invalid()` ahora valida coherencia tematica post-modelo:
  - rechaza respuestas que no contestan el tema directo preguntado;
  - rechaza respuestas que introducen un tema ajeno sin puente;
  - mantiene los filtros previos de coach/score/RAG/longitud/tono.
- `fallback_natalia_message()` prioriza preguntas directas antes de reutilizar pares reales:
  - trabajo
  - dia/semana
  - ejercicio
  - vino
  - ubicacion
- Se corrigio la deteccion de `dia`: mencionar `dia jueves` ya no se interpreta como pregunta sobre la semana.

Cambios frontend:

- `localEmergencySimulationTurn()` ahora contesta preguntas de semana/dia sin saltar a ubicacion.
- `closeCoachModal()` es idempotente: si existe callback pendiente, lo ejecuta aunque la clase `active` se haya desincronizado.
- `setInputLocked(false)` restaura el texto del boton `Enviar` si habia quedado en `Natalia esta pensando...`.

Pruebas agregadas:

- `test_simulate_turn_rejects_model_reply_that_jumps_to_unrelated_topic`
- `test_simulate_turn_rejects_visit_reply_when_user_asks_about_week`
- `test_fallback_does_not_treat_date_plan_as_week_question`
- Smoke frontend ampliado para pregunta de semana.

Verificacion automatica:

- `python build_simulator.py`
- `python -m py_compile backend\server.py build_simulator.py tests\test_backend.py tests\test_simulator_level1.py`
- `pytest -q tests\test_backend.py tests\test_simulator_level1.py tests\test_simulator_mobile_layout.py -rs`
- Resultado: `24 passed, 1 warning`.

Smokes API:

- `Hola Natalia, que lindo tu perfil. Que tal tu semana?`
  - Natalia: `Va tranquila mi semana, con trabajo y ganas de hacer algo distinto. La tuya si va entretenida?`
  - `direct_question_topics = ["dia"]`
  - No salta a ubicacion/visita.
- `Jaja va, entonces nombro lugar y dia: jueves una copa corta?`
  - Natalia responde sobre plan/copa.
  - `direct_question_topics = []`
  - No responde sobre semana.
- `yo vivo en bogota y en que trabajas?`
  - Natalia responde ubicacion + trabajo.
  - No salta a vino.

Chrome real:

- Se abrio `http://127.0.0.1:8765/simulador_v1.2.html` en Chrome.
- Se probo una partida limpia con escritura real y cierre de Coach por boton.
- Resultado final observado:
  - `Nivel 1 - Paso 10 de 10`
  - `levelUp = true`
  - `gameOver = false`
  - `Vidas = 4`
  - `Atraccion = 100%`
- Durante la prueba se detectaron y corrigieron:
  - pregunta de semana respondida como ubicacion;
  - cierre de Coach desincronizado que podia dejar input bloqueado;
  - `dia jueves` confundido con pregunta sobre semana.

Limitacion vigente:

- El endpoint sigue devolviendo `fallback: true` en los smokes porque Gemini esta cayendo por cuota/429.
- Por eso el flujo queda funcional y coherente, pero la meta de "100% humano" todavia no puede considerarse probada con modelo generativo activo.

## Ronda contexto autoritativo y Coach menos plantilla

Objetivo:

- Reducir otro origen de desalineacion: `visible_context` viejo o incorrecto enviado por el navegador.
- Hacer que las opciones A/B/C del Coach dependan del fallo real y no sean siempre iguales.
- Mejorar naturalidad cuando el usuario aterriza un plan concreto con dia/hora.

Cambios backend:

- Se agrego `authoritative_last_natalia(request)`.
- Si el historial trae un ultimo mensaje de Natalia, el backend lo usa como fuente autoritativa antes que `visible_context`.
- `visible_context_text()`, `retrieve_cases()`, `fallback_natalia_message()` y `simulate_turn()` usan ahora esa fuente autoritativa.
- `heuristic_score()` usa `coach_suggestions()` para crear sugerencias segun:
  - pregunta visible ignorada,
  - demasiadas preguntas,
  - pregunta logistica extra,
  - validacion temprana,
  - abridor generico,
  - sobreinversion,
  - contacto temprano,
  - cierre de plan,
  - emojis mal calibrados.
- `/api/evaluate` ya no se presenta como `Coach Maximus`; ahora usa `Natalia-Coach`, alineado con la arquitectura de doble agente.
- `fallback_natalia_message()` reconoce planes con dias concretos como `jueves` y responde sobre esa logistica.

Pruebas agregadas:

- `test_backend_uses_history_over_stale_visible_context`
- `test_heuristic_coach_suggestions_are_context_specific`
- `test_fallback_plan_with_day_gets_specific_logistics`

Verificacion automatica:

- `python -m py_compile backend\server.py tests\test_backend.py`
- `pytest -q tests\test_backend.py tests\test_simulator_level1.py tests\test_simulator_mobile_layout.py -rs`
- Resultado: `27 passed, 1 warning`.

Smokes API tras reiniciar backend:

- Contexto enviado por cliente decia `un vino suena bien`, pero historial real decia `donde vives`.
  - `turn_analysis.last_topics = ["ubicacion"]`
  - Natalia respondio Bogota + trabajo.
  - No salto a vino.
- Usuario: `Jaja va, entonces nombro lugar y dia: jueves una copa corta?`
  - `direct_question_topics = []`
  - Directiva: continuar hilo de plan.
  - Natalia: `Jueves puede funcionar. Me gusta que lo aterrices sin hacerlo intenso.`

## Ronda multiagente: aislamiento Persona/Coach, cooldown 429 y Chrome real

Objetivo:

- Cerrar brechas detectadas por auditoria paralela: input activo detras de modales, Persona condicionada con texto libre del Coach, preguntas fuera del mapa fijo y reintentos excesivos de Gemini cuando las 3 claves estan en cuota 429.

Cambios backend:

- `GeminiRotator` ahora tiene cooldown de cuota configurable con `GEMINI_QUOTA_COOLDOWN_SECONDS` (default 120s).
- Si todas las claves fallan por `429`, el siguiente turno cae rapido a fallback/RAG local sin gastar otra ronda completa de claves.
- Natalia-Persona ya no recibe `Razon Coach` ni feedback libre del Coach; recibe solo `Calidad estimada` y `Postura normalizada`.
- `direct_question_topics()` devuelve `pregunta_contextual` cuando el usuario hace una pregunta directa no cubierta por temas conocidos.
- Para `pregunta_contextual`, `natalia_response_is_invalid()` rechaza saltos oportunistas a vino, cita, contacto o ubicacion, pero permite respuestas humanas normales.

Cambios frontend:

- `showHelpModal()` y `showFinalWinModal()` bloquean input/botones del chat mientras el modal esta abierto.
- `closeHelpModal()` desbloquea controles solo si no queda otro modal bloqueante activo.
- El HTML fue regenerado desde `build_simulator.py`.

Pruebas agregadas:

- `test_gemini_rotator_uses_quota_cooldown_after_all_keys_429`
- `test_contextual_question_rejects_opportunistic_topic_jump`
- `test_blocking_modals_disable_chat_controls`

Verificacion automatica:

- `python -m py_compile backend\server.py build_simulator.py tests\test_backend.py tests\test_simulator_level1.py`
- `pytest -q tests -p no:cacheprovider -rs`
- Resultado final de esta ronda: `52 passed, 1 warning`.

Prueba Chrome real contra backend:

- URL: `http://127.0.0.1:8000/simulador_v1.2.html`
- Se reinicio la sesion desde UI y se completo Nivel 1 con mensajes escritos en modo libre.
- Resultado final observado:
  - `¡Cita Lograda!`
  - `Nivel 1 · Paso 10 de 10`
  - `Vidas: ❤️❤️❤️❤️`
  - `Atraccion: 90%`
- Muestras de coherencia observadas:
  - Pregunta semana: Natalia respondio sobre semana, no salto a ubicacion.
  - Pregunta trabajo despues de Bogota: Natalia respondio `marketing visual para restaurantes`, no salto a vino.
  - Pregunta zona: Natalia respondio `Por Brickell puede ser`.
  - Lugar/WhatsApp: Natalia siguio logistica y contacto sin romper el hilo.

Limitacion vigente:

- La prueba Chrome valido flujo completo, RAG/fallback contextual y UI real servida por backend.
- No prueba naturalidad maxima con Gemini activo si las claves siguen devolviendo `429`; esa validacion queda pendiente cuando la cuota se recupere.

Hardening operativo posterior:

- Se agrego `GEMINI_LIVE_ENABLED=0` en `.env` para que el servidor actual no inicialice el cliente Gemini mientras las claves esten colgadas/429.
- Se agrego `CHROMA_QUERY_ENABLED=0` en `.env` para evitar el bloqueo de ONNX al consultar Chroma en runtime. SQLite/RAG de pares reales sigue activo.
- `GeminiRotator` ya no inicializa el cliente si Gemini live esta apagado.
- Se corrigio un bucle infinito en `coach_suggestions()` cuando las sugerencias de relleno quedaban duplicadas.
- Se filtro contenido oscuro/raro de sugerencias aprendidas desde casos reales, por ejemplo frases tipo `enterrar vivo`.
- Smoke final real contra `http://127.0.0.1:8000/api/simulate-turn`:
  - Natalia: `Jaja bien, asi si. Me gusta cuando el plan queda claro sin tanta vuelta.`
  - `score=6`
  - `lose_life=false`
  - `fallback=true`
  - Sin sugerencias raras y sin timeout.

Para reactivar Gemini/Chroma en una prueba controlada:

- Cambiar `GEMINI_LIVE_ENABLED=1`.
- Cambiar `CHROMA_QUERY_ENABLED=1` solo cuando el embedding ONNX de Chroma este precargado o no bloquee el runtime.

## Ronda anti-falsos positivos por emojis y endpoints offline

Problema detectado:

- En Windows/PowerShell algunos emojis como `😉` pueden llegar al backend como `??`.
- El Coach interpretaba esos `??` como dos preguntas reales y penalizaba con `demasiadas preguntas`.
- `/api/evaluate` seguia pudiendo tocar Chroma/Gemini aunque el modo operativo estuviera apagado.

Cambios:

- Se agrego `meaningful_question_mark_count()` para diferenciar preguntas reales de marcas de reemplazo de emoji al final.
- `asks_question()`, `direct_question_topics()`, `infer_turn_intent()` y `heuristic_score()` usan ahora ese contador.
- `/api/evaluate` respeta `CHROMA_QUERY_ENABLED=0` y cae a feedback heuristico si `GEMINI_LIVE_ENABLED=0`.
- `/health` reporta `gemini_live_enabled` y `chroma_query_enabled` para que el estado operativo sea transparente.

Verificacion:

- `pytest -q tests -p no:cacheprovider -rs`
- Resultado: `56 passed, 1 warning`.
- Smoke real `/health`:
  - `gemini_live_enabled=false`
  - `chroma_query_enabled=false`
  - `chroma_documents=169`
- Smoke real `/api/simulate-turn` con `??` final:
  - `asked_question=false`
  - `direct_question_topics=[]`
  - feedback: `Calidad del mensaje: conecta con el contexto visible.`
  - Natalia: `Jaja bien, asi si. Me gusta cuando el plan queda claro sin tanta vuelta.`

## Ronda temas humanos fuera del guion

Problema detectado:

- El backend ya evitaba saltos a vino/cita/contacto cuando el usuario hacia una pregunta desconocida, pero preguntas comunes como musica, comida, viajes, mascotas o familia podian quedar demasiado genericas.
- La palabra `dia` se estaba clasificando como plan incluso en frases humanas como `depende del dia`.

Cambios:

- `topic_set()` y `direct_question_topics()` reconocen ahora `musica`, `comida`, `viajes`, `mascotas` y `familia`.
- `fallback_natalia_message()` responde esos temas con frases concretas y naturales, sin avanzar a cita/contacto si no corresponde.
- `topic_set()` ya no marca `dia` generico como plan; plan queda reservado para senales fuertes como `cita`, `salir`, `lugar`, `jueves`, etc.
- La validacion rechaza respuestas de modelo que salten a vino ante una pregunta de musica.

Verificacion:

- `pytest -q tests -p no:cacheprovider -rs`
- Resultado: `62 passed, 1 warning`.
- Smoke real `/api/simulate-turn`:
  - Usuario: `Y a ti que musica te gusta?`
  - `direct_question_topics=["musica"]`
  - Natalia: `Me gusta la musica con buena energia, pero depende del mood. Tu eres mas de bailar o de escuchar tranquilo?`
  - Feedback: `Calidad del mensaje: conecta con el contexto visible.`

Sincronizacion frontend:

- `build_simulator.py` ahora replica esos temas en `buildEmergencyNataliaReply()` para que el fallback local del navegador tambien responda musica, comida, viajes, mascotas y familia sin sonar generico.
- `simulador_v1.2.html` fue regenerado desde el builder.
- Smoke del HTML servido por FastAPI: `GET /simulador_v1.2.html -> 200`.
- Verificacion frontend: `test_frontend_fallback_context_coherence_with_playwright` valida esos temas en el fallback local.

## Ronda pregunta activa, acentos degradados y Coach limpio

Problema detectado:

- Mensajes degradados por encoding como `qu? m?sica`, `?C?mo`, `c?moda` podian hacer que el backend detectara una pregunta generica o contara demasiados signos `?`.
- Si el usuario mencionaba un tema y preguntaba otro, por ejemplo `me gusta bailar... que comida te gusta?`, Natalia podia responder al tema anterior.
- El Coach mezclaba opciones aprendidas de casos reales superficialmente parecidos, como vacaciones o Brasil, aunque la pregunta activa fuera semana o trabajo.

Cambios:

- `analysis_text()` normaliza variantes degradadas frecuentes antes de clasificar intencion, temas y preguntas.
- `direct_question_topics()` ahora identifica el segmento activo de pregunta con signos reales, signos degradados y frases tipo `que musica`, `que comida`, `en que trabajas`.
- `meaningful_question_mark_count()` evita penalizar como `demasiadas preguntas` cuando los `?` vienen de acentos/emojis degradados.
- `fallback_natalia_message()` prioriza respuestas explicitas para pregunta directa antes de reutilizar pares reales.
- `case_based_suggestions()` solo usa ejemplos aprendidos del RAG cuando el caso coincide con la pregunta directa; para aperturas de semana/dia usa sugerencias pedagogicas locales.
- Se agregaron pruebas de interaccion real: escribir, enviar, bloquear input durante IA, cerrar Coach y continuar.

Verificacion:

- `pytest -q tests -p no:cacheprovider -rs`
- Resultado: `70 passed, 1 warning`.
- Smoke real `/api/simulate-turn`:
  - `Hola Natalia... ?C?mo va tu semana?` -> `direct_question_topics=["dia"]`, sin `demasiadas preguntas`.
  - `Y a ti qu? m?sica te gusta?` -> Natalia responde musica.
  - `?Qu? comida te gusta?` despues de mencionar bailar/lugar -> Natalia responde comida.
  - Propuesta de lugar -> Natalia responde lugar, no pregunta otra cosa fuera de hilo.
- Chrome real contra `http://127.0.0.1:8000/simulador_v1.2.html`:
  - Se completo Nivel 1 en modo libre.
  - Resultado observado: `levelupOpen=true`, `gameoverOpen=false`.
  - La conversacion visible siguio semana -> trabajo -> musica -> comida -> zona -> lugar -> WhatsApp sin saltos a temas incompatibles.

Limitacion vigente:

- `GEMINI_LIVE_ENABLED=false` y `CHROMA_QUERY_ENABLED=false` en `/health`.
- Por tanto, esta ronda valida la experiencia estable con SQLite/RAG local y fallback contextual, no la naturalidad maxima con Gemini/Chroma live.

## Ronda separacion runtime Persona/Coach y cobertura real DB

Problema detectado:

- La base completa existe, pero con Gemini y Chroma live apagados no todo el material influye igual en la respuesta.
- Antes se recuperaba una mezcla unica de pares, Reddit completo y YouTube; luego Persona y fallback solo podian usar una parte de eso.
- Eso hacia dificil auditar si Natalia estaba realmente usando pares humanos o solo reglas locales.

Cambios:

- Se separo la recuperacion por consumidor:
  - `retrieve_persona_cases()` recupera solo pares reales `sqlite_chat_pair` y `sqlite_reddit_pair` para Natalia-Persona.
  - `retrieve_coach_cases()` recibe pares reales mas contexto amplio: Reddit completo, YouTube y Chroma si esta habilitado.
- `simulate_turn()` ahora:
  - construye el prompt de Natalia-Persona solo con pares hombre-mujer compatibles;
  - construye el prompt de Natalia-Coach con contexto amplio;
  - usa pares de Persona para sugerencias deterministas y fallback local.
- La respuesta de `/api/simulate-turn` incluye `retrieval_summary` con fuentes reales usadas por Persona y Coach.
- `/api/training-status` reporta:
  - Reddit total y con JSON;
  - filas Reddit con pares hombre->mujer;
  - filas Reddit sin pares;
  - transcripciones YouTube por estado;
  - pares derivados por perfil.

Verificacion real:

- `/api/training-status`:
  - `reddit_conversations=213`
  - `reddit_with_transcription_json=211`
  - `reddit_rows_with_pairs=126`
  - `reddit_rows_without_pairs=85`
  - `chat_turns=37`
  - `transcripts.success.total=44`
  - `transcripts.success.chars=1039521`
  - `derived_training_pairs=389`
  - `coqueta.pairs=186`
- Smoke real `/api/simulate-turn` con `Y a ti que musica te gusta?`:
  - `intent=pregunta_contextual`
  - `direct_question_topics=["musica"]`
  - `persona_pair_cases=8`
  - `persona_sources={"sqlite_chat_pair": 4, "sqlite_reddit_pair": 4}`
  - `coach_context_cases=9`
  - `coach_sources` incluyo pares, `sqlite_reddit` y `sqlite_youtube`
  - Natalia respondio sobre musica, no sobre plan/vino/contacto.
- `pytest -q tests -p no:cacheprovider -rs`
- Resultado: `71 passed, 1 warning`.

Lectura arquitectonica:

- En modo offline estable, Natalia no esta "fine-tuneada"; opera como agente con memoria experta local:
  - pares reales para imitar respuesta femenina;
  - heuristica de Coach para evaluar;
  - contexto teorico recuperado y listo para Coach cuando Gemini se reactive.
- El objetivo siguiente para naturalidad maxima es reactivar `GEMINI_LIVE_ENABLED=1` y despues `CHROMA_QUERY_ENABLED=1` en prueba controlada, verificando que el resumen muestre uso live sin bloquear.

## Ronda anti-contaminacion Persona y cierre de status

Problema detectado:

- En un smoke real, Natalia respondia bien a `Y a ti que musica te gusta?`, pero `retrieve_persona_cases()` todavia recuperaba pares reales de otros temas. Eso no siempre contaminaba la respuesta por el fallback contextual, pero era un riesgo: la Persona podia imitar ejemplos de lugar, visita o comida cuando la pregunta visible era musica/trabajo.

Cambio aplicado:

- `retrieve_persona_cases()` ahora analiza la pregunta visible con `analyze_visible_turn()`.
- Si existe una pregunta directa (`musica`, `trabajo`, `comida`, etc.), Persona solo conserva pares Hombre -> Mujer cuyo mensaje del hombre comparte ese tema.
- Si no hay pregunta directa, se mantiene la recuperacion amplia anterior para no perder cobertura conversacional.
- El Coach ya tenia filtro equivalente en `case_based_suggestions()`; ahora Persona y Coach quedan alineados.

Verificacion:

- `python -m py_compile backend\server.py tests\test_backend.py`
- Pruebas enfocadas:
  - `test_retrieve_persona_cases_filters_unrelated_direct_question_pairs`
  - `test_case_based_suggestions_must_match_direct_question_topic`
  - `test_contextual_question_rejects_opportunistic_topic_jump`
  - Resultado: `3 passed, 1 warning`.
- Suite completa: `pytest -q tests -p no:cacheprovider -rs`
- Resultado: `73 passed, 1 warning`.

Estado operativo:

- El modo estable offline/RAG SQLite queda validado por tests.
- La verificacion live maxima con Gemini/Chroma sigue pendiente hasta activar `GEMINI_LIVE_ENABLED=1` y `CHROMA_QUERY_ENABLED=1` en una prueba controlada con cuota disponible.
## Ronda Chrome anti-saltos de tema y cierre natural

Problemas reproducidos en Chrome:

- Paso 4: el usuario preguntaba `¿Qué música te gusta?`, pero Natalia respondía otra vez sobre trabajo/marketing.
- Paso 7: el usuario proponía jueves/copa/Brickell, pero Natalia reutilizaba una respuesta real incompatible: `¿De dónde vienes de visita?`.
- Paso 10: al cerrar el plan, Natalia podía volver a pedir WhatsApp aunque el usuario ya estaba cerrando la logística.

Cambios aplicados:

- `analysis_text()` normaliza acentos para análisis interno; así `música`, `qué`, `Bogotá` y variantes acentuadas se detectan igual que `musica`, `que`, `Bogota`.
- En cierre de plan, los pares reales solo se aceptan si la respuesta recuperada contiene señales concretas de coordinación: día, lugar, copa, plan, WhatsApp o cuadrar. Esto evita respuestas genéricas de Tinder o visitas fuera de contexto.
- El cierre `trato hecho / te escribo / listo` ahora tiene prioridad sobre pedir contacto de nuevo.

Verificación:

- Pruebas nuevas:
  - `test_accented_active_music_question_overrides_earlier_work_topic`
  - `test_plan_proposal_does_not_reuse_unrelated_visit_reply`
- Suite completa: `pytest -q tests -p no:cacheprovider -rs`
- Resultado: `75 passed, 1 warning`.
- Chrome Nivel 1 completo:
  - Paso 4 respondió música: `Me gusta la musica con buena energia...`
  - Paso 7 respondió plan/jueves: `Jueves puede funcionar...`
  - Llegó a Level Up sin Game Over ni bloqueo de modal.
- Smoke API posterior al último ajuste de cierre:
  - `Trato hecho, te escribo con lugar y hora...` -> `Jaja bien, asi si. Me gusta cuando el plan queda claro sin tanta vuelta.`

Estado:

- La experiencia offline/RAG SQLite del Nivel 1 queda mucho más coherente y ya no reproduce los saltos de tema de las capturas originales.
- Sigue pendiente la validación de naturalidad máxima con `GEMINI_LIVE_ENABLED=1` y `CHROMA_QUERY_ENABLED=1`, porque el estado operativo actual reporta ambos apagados.
## Ronda Gemini live, Chroma runtime y manejo de cuota

Problema detectado:

- Al activar temporalmente `GEMINI_LIVE_ENABLED=1` y `CHROMA_QUERY_ENABLED=1`, `/health` confirmo Gemini live y Chroma runtime activos.
- La primera prueba no fallaba por el prompt ni por RAG, sino por configuracion: `google-genai` devolvia `400 INVALID_ARGUMENT` porque el deadline HTTP estaba en 8s y Gemini exige minimo 10s.
- Despues de corregir el deadline, las llamadas live llegaron a Gemini, pero las llaves entraron en errores retryables, principalmente `429 RESOURCE_EXHAUSTED` de free tier. El backend cayo a fallback local/RAG sin romper el chat.

Cambios aplicados:

- `GEMINI_CALL_TIMEOUT_MS` ahora usa minimo 10000 ms y default 12000 ms.
- `GEMINI_HARD_TIMEOUT_SECONDS` ahora siempre queda por encima del timeout HTTP real, evitando cortar localmente antes de que el SDK devuelva 429/5xx.
- El rotador entra en cooldown si cualquier llave devuelve 429 durante la ronda, incluso si otra llave dio timeout/5xx. Esto evita retries lentos repetidos cuando la cuota esta agotada.

Verificacion:

- `pytest -q tests -p no:cacheprovider -rs`
- Resultado: `77 passed, 1 warning`.
- `/health` temporal live: `gemini_live_enabled=true`, `chroma_query_enabled=true`, `chroma_documents=169`.
- Logs live: errores retryables 429 y cooldown, no el 400 de deadline invalido.
- Estado final operativo para uso: Gemini live apagado y Chroma runtime encendido para evitar esperas de cuota y mantener contexto vectorial disponible.
## Ronda curaduria de sugerencias del Coach

Problema detectado:

- En la prueba Chrome, Natalia-Persona ya respondia mejor, pero Natalia-Coach podia mostrar opciones A/B/C aprendidas desde casos reales que no servian como pedagogia: frases como `¿Dónde estoy ahora? ¿Estoy despierto?`, vacaciones/visita fuera de contexto o sugerencias demasiado vagas para un cierre de plan.

Cambios aplicados:

- `unsafe_chat_suggestion()` ahora normaliza texto para analisis y bloquea ruido absurdo de scraping.
- Nuevo filtro `incompatible_coach_case_suggestion()`:
  - bloquea vacaciones/visita si el turno no trata de viajes;
  - en cierre de plan exige señales concretas de coordinacion: dia, lugar, copa, plan, WhatsApp, hora, cuadrar, sin discurso o sin entrevista;
  - evita que `salir/vernos` solos se consideren suficiente entrenamiento para un paso de logistica.

Verificacion:

- Pruebas nuevas:
  - `test_case_based_suggestions_filters_absurd_location_noise_in_plan`
  - `test_case_based_suggestions_filters_vacation_case_outside_travel_context`
- Suite completa: `79 passed, 1 warning`.
- Smoke API de Paso 7: Natalia responde `Jueves puede funcionar...` y Coach ofrece opciones coherentes, sin frases absurdas ni vacaciones fuera de contexto.