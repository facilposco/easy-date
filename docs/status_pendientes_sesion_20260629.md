# Status de pendientes de la sesion - 2026-06-29

Estado revisado en `C:\desarrollos\Codex\Easy Date`.

| Frente | Estado | Evidencia | Pendiente / riesgo |
|---|---|---|---|
| Backend estable | OK | `http://127.0.0.1:8000/health` responde `status=ok`, PID actual `17808`, `gemini_live_enabled=false`, `chroma_connected=true`, `chroma_documents=169`. | Usar para pruebas sin gastar Gemini. |
| Backend live experimental | OK parcial | `http://127.0.0.1:8003/health` responde `status=ok`, PID actual `17836`, `gemini_live_enabled=true`, `gemini_coach_enabled=false`, `gemini_keys_loaded=3`, modelos fallback configurados. | No todos los turnos usan Gemini live; algunos caen a fallback por calidad/cuota. |
| Simulador principal | OK | `simulador_v1.2.html` existe y abre en Chrome en `8003`. | Mantener cambios en `build_simulator.py` y regenerar HTML. |
| Nivel 1 en Chrome live | OK | Chrome quedo en `Nivel 1 · Paso 10 de 10`, `levelupActive=true`, `gameoverActive=false`, `inputDisabled=true`. | Hacer QA de niveles 2-4 despues. |
| Natalia-Persona live | OK parcial fuerte | Prueba API de 10 turnos en `8003`: 9/10 con `retrieval_summary.natalia_live_used=true`; 1/10 con fallback local por guardrail de coherencia; 0 vidas perdidas. | No declarar 100% live hasta eliminar el ultimo fallback sin permitir incoherencias. |
| Natalia-Coach | OK | En modo live experimental `gemini_coach_enabled=false`; Coach usa heuristica local para ahorrar tokens y evitar 429. | Si se reactiva Coach live, probar consumo y estabilidad. |
| Calidad de entrenamiento Natalia-Persona | OK | `retrieve_real_reply_pairs` ahora descarta pares OCR de perfiles/memes y contenido inseguro/absurdo antes de que Natalia pueda imitarlos. `/api/training-status`: `derived_training_pairs=389`, `persona_usable_pairs=320`, `persona_rejected_pairs=69`. | El Coach puede seguir usando contexto amplio; Natalia-Persona solo debe usar pares hombre-mujer compatibles. |
| Selectividad por nivel | OK | Backend usa `passing_score` segun selectividad: Nivel 1=6, Nivel 2=7, Nivel 3=8, Nivel 4=9. Runtime probado: en Nivel 3 un score 7 pierde vida y reporta `passing_score=8`. | Falta QA conversacional completo en niveles 2-4, pero ya no comparten el mismo umbral pedagogico. |
| Voz fallback en alta selectividad | OK | El fallback local ahora ajusta respuestas de Nivel 3-4: mas cortas, menos disponibles y mas selectivas en trabajo, dia, ejercicio, musica, comida, contacto y plan. Tests enfocados: `5 passed, 88 deselected, 1 warning`. Smoke API en `8000`: Nivel 3, score 7, `lose_life=true`, respuesta `Pilates y caminar. Pero nada de conversacion eterna de gym.` | Falta validar la experiencia completa de Nivel 3-4 en navegador con usuario real. |
| Auditoria fallback live | OK | `retrieval_summary` ahora incluye `natalia_fallback_category` y `natalia_fallback_reason`. Tests cubren `api` por cuota/cooldown y `guardrail` por respuesta incoherente. Runtime live probado: respuesta directa de deporte con `natalia_live_used=true` y categoria vacia. | Usar estos campos para no confundir cuota/API con mala coherencia de Natalia. |
| Metricas por turno | OK | `/api/simulate-turn` devuelve `turn_metrics` con calidad del mensaje, contexto, objetivo, tono/emojis y timing. El modal del Coach ahora muestra `Lectura del Coach` con contexto, objetivo, emojis y riesgos. Prueba Chrome: emoji real `😉` visible y calibrado. | Pendiente: convertirlo en panel grafico si se quiere dashboard pedagogico permanente. |
| Resumen final de nivel | OK | `levelup-summary` y `gameover-summary` muestran buenas, por mejorar, vidas perdidas, precision, mejor mensaje, mensaje a corregir y patron. Game Over agrega boton `ESTUDIAR CASOS REALES`. | Pendiente: sumar categorias de errores recurrentes cuando haya mas telemetria historica. |
| RAG / ChromaDB | OK | `/health`: `chroma_query_enabled=true`, `chroma_documents=169`. | La brecha SQLite/Chroma sigue explicada por OCR vacio/no vectorizable. |
| SQLite Reddit | OK | `reddit_conversations=213`; `image_urls=243`; `chat_turns=37`; `transcripts=46`. | Revisar perfiles "desconocida" porque la DB actual muestra 2 con `image_urls`, distinto al resumen previo. |
| Imagenes Reddit | OK | `imagenes/` contiene 243 archivos recursivos en subcarpetas `post_*`, 74,363,537 bytes; extensiones: 199 `.jpg`, 42 `.png`, 2 `.jpeg`. DB esperaba 243 URLs; no hay targets faltantes. | La raiz de `imagenes` no tiene archivos sueltos porque todo quedo por carpeta de post. No borrar; optimizar solo sobre copias derivadas. |
| Proxy / ahorro | OK | CSV final: `source=direct` para 221, `local` para 22; consumo proxy estimado `0.000 MB`; ahorro estimado `66.332 MB`. | Contrastar con dashboard DataImpulse solo si se requiere facturacion externa. |
| Tests | OK | `pytest -q tests -p no:cacheprovider -rs` -> `105 passed, 1 warning in 172.73s`. | Warning no bloqueante de `StarletteDeprecationWarning`. |
| Continuacion Nivel 1 humano | OK | Contrato automatico de 10 turnos + Chrome completo en `localhost:8000/simulador_v1.2.html?reset=1`, Paso 10/10, `Cita Lograda`, Game Over falso, Atraccion 100%, Coach con metricas en cada modal. | Ampliar esta misma auditoria a niveles 2-4. |
| Modal Coach / Level Up | OK | Chrome detecto bug real: `modal-overlay` quedaba transparente con `display:flex`. Corregido en `build_simulator.py`; al cerrar el ultimo Coach queda `coachActive=false`, `levelupActive=true`, overlay `display:none`, `pointer-events:none`. | Ninguno para Nivel 1; seguir observando en Game Over y niveles altos. |
| Documentacion | OK | Actualizados `docs/status_pendientes_sesion_20260629.md`, `docs/natalia_humano_nivel1_continuacion_20260629.md` y `arquitectura.html` con selectividad/fallback y tests actuales. | Mantener nuevos informes siempre dentro de `docs/`. |
| Git/versionado | Pendiente | `git status` falla porque la carpeta no es un repositorio Git. | Recomendado inicializar repo antes de seguir con cambios grandes. |

## Resumen operativo

- El simulador ya se puede usar en `http://127.0.0.1:8000/simulador_v1.2.html` en modo estable.
- Para empezar una partida limpia aunque exista estado guardado: `http://127.0.0.1:8000/simulador_v1.2.html?reset=1`.
- Chrome quedo probado en `http://localhost:8000/simulador_v1.2.html?reset=1` con Nivel 1 completado y modal `Cita Lograda`.
- Para pruebas con Natalia live, usar `http://127.0.0.1:8003/simulador_v1.2.html`.
- El modo live funciona mucho mejor: 9/10 turnos live en la ultima prueba API de Nivel 1, con fallback local aun necesario como red de seguridad.
- El fallback local ya refleja mejor la dificultad de perfiles selectivos en niveles 3-4.
- Natalia-Persona ya no imita pares OCR contaminados como perfiles/memes; esos datos quedan fuera de la voz de la chica.
- Reporte de continuacion: `docs/natalia_humano_nivel1_continuacion_20260629.md`.
