# Natalia humana Nivel 1 - continuacion 2026-06-29

## Evidencia revisada

- Texto de arquitectura recomendado: RAG estructurado, evaluacion por metricas y doble agente.
- Capturas del fallo: Natalia saltaba de gimnasio/trabajo a ubicacion/vino y el Coach evaluaba un paso que no correspondia al chat visible.
- Estado actual del backend estable: `http://127.0.0.1:8000`, `GEMINI_LIVE_ENABLED=0`, `GEMINI_COACH_ENABLED=0`, `CHROMA_QUERY_ENABLED=1`.

## Cambios aplicados

| Area | Cambio | Motivo |
|---|---|---|
| Natalia-Persona | `que deporte te gusta` ahora se detecta como tema `ejercicio`. | Evitar que Natalia responda como si fuera una pregunta generica. |
| Natalia-Persona | Para deporte, el fallback responde con gusto concreto: pilates/caminar/gym/aire libre. | Hacer la respuesta menos plantilla y mas humana. |
| Natalia-Coach | Un abridor que menciona `planes` ya no se penaliza por "sumar otra pregunta" si no habia hilo anterior. | Evitar feedback falso en el primer mensaje. |
| Natalia-Persona | Mensajes que contienen solo un telefono numerico ahora se detectan como `pedir_contacto`. | Evitar que el RAG reutilice una respuesta real incompatible cuando el usuario ya paso el numero. |
| RAG/Fallback | En contacto numerico/logistico, se prioriza una respuesta contextual segura antes de imitar pares reales. | Mantener coherencia humana sobre imitacion ciega de la DB. |
| Natalia-Persona | `interrogatorio` ya no puede activar mascotas por contener `gato`. | Evitar que una frase sobre no hacer entrevista salte absurdamente a perros/gatos. |
| Natalia-Persona | Preguntas directas de contacto tienen prioridad sobre otros temas detectados. | Si el usuario pregunta por WhatsApp, Natalia responde a contacto antes de cualquier tema secundario. |
| Calidad de datos Persona | Natalia-Persona ahora rechaza pares OCR que son perfiles/memes, respuestas no conversacionales o contenido inseguro/absurdo. | Evitar que el RAG ponga en boca de Natalia frases que no vienen de una conversacion mujer-hombre real. |
| Natalia-Persona live | Se aceptan respuestas Gemini en texto plano cuando son cortas, en espanol y coherentes con el tema activo. | Reducir fallbacks innecesarios cuando Gemini no devuelve JSON perfecto. |
| Natalia-Persona | Las respuestas con `dia`/`dia` ahora satisfacen preguntas directas sobre el dia. | Evitar que una respuesta humana como "Mi dia va bien" sea rechazada por no repetir "semana". |
| Natalia-Coach | `/api/simulate-turn` devuelve `turn_metrics` separados por calidad, contexto, objetivo, tono/emojis y timing. | Hacer auditable la evaluacion pedagogica y preparar UI de metricas sin mezclarla con Natalia-Persona. |
| Natalia-Coach UI | El modal del Coach agrega `Lectura del Coach` cuando la API devuelve metricas. | Mostrar al usuario evaluacion de contexto, objetivo, emojis y riesgos sin invadir el chat de Natalia. |
| Auditoria live | `retrieval_summary` diferencia `natalia_fallback_category=api` de `guardrail`. | Saber si un fallback fue cuota/API o una respuesta incoherente rechazada por seguridad. |
| Resumen final | Level Up y Game Over muestran resumen de buenas, por mejorar, vidas perdidas, precision, mejor mensaje, mensaje a corregir y patron. | Cerrar el nivel con feedback pedagogico; si pierde, enviarlo a estudiar casos reales. |
| Progresion de dificultad | El backend calcula `passing_score` por selectividad: Nivel 1=6, Nivel 2=7, Nivel 3=8, Nivel 4=9. | La misma respuesta ya no vale igual para una chica receptiva que para una de alta selectividad. |
| Voz de alta selectividad | El fallback local de Natalia responde mas corto y exigente en niveles 3-4 para trabajo, dia, ejercicio, musica, comida, contacto y plan. | Evitar que la dificultad viva solo en el Coach cuando Gemini cae a fallback. |
| QA | Se agrego un contrato automatico de Nivel 1 completo. | Verificar la conversacion entera, no solo bugs aislados. |

## Verificaciones

| Prueba | Resultado |
|---|---|
| Casos de las capturas por API | OK: gimnasio responde ejercicio; Bogota + trabajo responde ubicacion/trabajo; sin perdida de vida. |
| Matriz API de Nivel 1 | OK: deporte, trabajo, musica, comida, plan, WhatsApp y cierre quedan conectados. |
| Telefono numerico por API | OK: intent `pedir_contacto`, topic `contacto`, Natalia responde `Listo, si el plan queda claro te respondo por ahi.` |
| Tests completos | `95 passed, 1 warning in 155.30s` |
| Tests completos tras metricas | `97 passed, 1 warning in 152.45s` |
| Contrato humano Nivel 1 | OK: 10 turnos por API, sin vidas perdidas, sin respuestas repetidas, sin saltos a temas prohibidos. |
| Chrome Nivel 1 | OK: origen limpio `http://127.0.0.2:8000`, `Nivel 1 · Paso 10 de 10`, `levelup=true`, `gameover=false`, modal Coach no queda abierto. |
| API live Nivel 1 | OK parcial fuerte: 9/10 turnos con `retrieval_summary.natalia_live_used=true`, 1/10 fallback por guardrail de coherencia, 0 vidas perdidas. |
| API metricas/emojis | OK: emoji real `U+1F609` llega como `emoji_count=1`, `emoji_calibration=calibrados`; mensajes saturados/intensos quedan marcados en `turn_metrics`. |
| Chrome Nivel 1 con metricas visibles | OK: `http://127.0.0.3:8000/simulador_v1.2.html`, Paso 10/10, `Cita Lograda`, Game Over falso, Atraccion 100%, Coach mostro `Lectura del Coach` y emoji `😉` calibrado. |
| Auditoria fallback live | OK: tests cubren categoria `api` por cuota/cooldown y `guardrail` por incoherencia; runtime live de deporte respondio con `natalia_live_used=true` y sin fallback. |
| Resumen final/Game Over | OK: Playwright valida `Resumen: 10 buenas, 0 por mejorar`, `Mejor mensaje` y `Mensaje a corregir` en Level Up, y `ESTUDIAR CASOS REALES` en Game Over. |
| Selectividad por nivel | OK: tests validan umbrales 6/7/8/9 y runtime confirma que Nivel 3 con score 7 pierde vida (`passing_score=8`). |
| Voz fallback alta selectividad | OK: pruebas enfocadas validan que Nivel 3 no responde igual que Nivel 1 en ejercicio y que Nivel 4 exige plan claro para contacto. |
| Filtro de entrenamiento Persona | OK: `/api/training-status` reporta 389 pares derivados, 320 usables para Natalia-Persona y 69 rechazados por calidad/seguridad. |
| Flujo de capturas originales | OK: test API reproduce gimnasio/trabajo; Natalia responde ejercicio/trabajo y el Coach queda sincronizado con contexto visible. |
| Chrome Nivel 1 limpio | OK: `http://localhost:8000/simulador_v1.2.html?reset=1`, Paso 10/10, `Cita Lograda`, Game Over falso, Atraccion 100%, 0 vidas perdidas. |
| Modal Coach/Level Up | OK: corregido overlay transparente del Coach; al cerrar ultimo Coach, Level Up queda activo y `modal-overlay` queda `display:none` + `pointer-events:none`. |
| Tests completos actuales | `105 passed, 1 warning in 172.73s` |

## Conversacion final observada en Chrome

- Deporte: Natalia respondio `Me gusta pilates y caminar, pero sin volverlo tema eterno jaja. Tu eres mas gym o aire libre?`
- Trabajo: Natalia respondio `Hago marketing visual para restaurantes. Y tu, que haces cuando no estas en modo trabajo?`
- Musica: Natalia respondio sobre musica/energia.
- Comida: Natalia respondio sobre comida/lugar.
- Plan: Natalia acepto jueves/Brickell sin saltar de tema.
- Numero: Natalia respondio `Listo, si el plan queda claro te respondo por ahi.`
- Cierre: Natalia respondio `Jaja bien, asi si. Me gusta cuando el plan queda claro sin tanta vuelta.`

## Nuevo contrato automatico

Se agrego `test_level1_human_coherence_contract_across_full_session` en `tests/test_backend.py`.

La prueba juega 10 turnos acumulando historial real, fuerza fallback local como si Gemini estuviera en cuota agotada y valida:

- no perder vidas con mensajes buenos,
- responder preguntas directas de dia, deporte, trabajo, musica, comida y contacto,
- no saltar a vino, WhatsApp, mascotas o ubicacion cuando no corresponde,
- no repetir respuestas,
- mantener feedback del Coach con contexto y objetivo del turno.

## Pendiente real

- Esta verificacion cubre Nivel 1 en modo estable con RAG/SQLite/fallback local.
- Falta llevar el mismo nivel de prueba a niveles 2, 3 y 4.
- El tono local de niveles 3-4 ya fue ajustado, pero falta QA navegando esos niveles completos.
- El modo Gemini live mejoro a 9/10 turnos con Natalia live y 1/10 fallback local por guardrail de coherencia. No declarar `100% live` hasta eliminar ese ultimo fallback sin bajar calidad.
