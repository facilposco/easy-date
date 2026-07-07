# Informe Natalia Doble Agente - Nivel 1

Fecha: 2026-06-28

## Objetivo

Corregir el simulador para que Natalia no avance por plantilla fija y para que el Coach evalue el mensaje real del usuario contra el contexto visible de la conversacion.

## Cambios realizados

- Se mantiene el endpoint dinamico `POST /api/simulate-turn`.
- El frontend envia cada turno al backend con nivel, paso, vidas, atraccion, historial, mensaje del usuario y tiempo elegido.
- Natalia-Persona genera la respuesta de chat; Natalia-Coach genera feedback separado.
- El backend recupera casos desde ChromaDB (`natalia_conversations`) y turnos desde SQLite para orientar la evaluacion.
- Se amplio el retrieval para cubrir mas de la base completa:
  - ChromaDB `natalia_conversations`.
  - SQLite `reddit_conversations`.
  - SQLite `transcripts` de YouTube.
  - SQLite `chat_turns`.
- El fallback de Natalia ahora recibe senales de los casos recuperados, para no quedar como respuesta generica cuando Gemini entra en cuota.
- Se elimino la dependencia de `nextStep.her_message` para avanzar la conversacion.
- Se agrego timeout con `AbortController` en frontend para evitar que el usuario quede bloqueado si Gemini tarda o entra en cuota.
- Se agrego fallback local conversacional en frontend para mantener la sesion viva si el backend no responde a tiempo.
- Se corrigio la persistencia de `locked`: ya no se guarda como estado permanente en `localStorage`.
- Si una recarga encuentra una sesion bloqueada con un mensaje pendiente, retira ese ultimo turno pendiente y deja el simulador usable.
- Se corrigio la restauracion del historial para evitar `Tardo: Tardo: 15 min`.
- Se elimino restauracion con `innerHTML` para mensajes de usuario; ahora usa nodos de texto.
- Se mejoro el fallback backend de Natalia para no responder con temas antiguos fuera de contexto, especialmente el caso Bogota/Miami.
- Se fuerza consistencia: si `score < 6`, la respuesta incorrecta quita vida.

## Verificacion en Chrome

URL usada: `http://127.0.0.1:8000/simulador_v1.2.html`

Resultado de prueba manual automatizada:

- Nivel 1 completado con 10 de 10 turnos.
- Aparecio Level Up al finalizar.
- No aparecio Game Over.
- El modal Coach abrio y cerro en cada turno.
- El boton `ENTENDIDO` funciono.
- El input quedo habilitado despues de cada cierre del Coach.
- En el Level Up el input queda bloqueado, que es el comportamiento esperado.
- Un turno uso fallback local por timeout/cuota; la sesion continuo sin quedarse congelada.

## Verificacion tecnica

- `pytest -q tests/test_simulator_level1.py -rs`: 2 passed.
- `python -m py_compile backend/server.py build_simulator.py`: OK.
- `node --check scratch/simulator_embedded.js`: OK.
- `/health`: OK, Chroma conectado, coleccion `natalia_conversations` con 169 documentos.
- Prueba HTTP de `/api/simulate-turn`: OK, recupero fuentes `chroma`, `sqlite_reddit`, `sqlite_youtube` y `sqlite_chat_turns`.
- Checks del HTML:
  - `/api/simulate-turn`: presente.
  - `AbortController`: presente.
  - `localEmergencySimulationTurn`: presente.
  - `locked` no se persiste: presente.
  - `nextStep.her_message`: ausente.
  - restauracion antigua con `innerHTML`: ausente.

## Pendiente recomendado

Para llegar a una sensacion mas humana todavia:

- Reducir respuestas repetidas del fallback usando una memoria corta de ultimas frases de Natalia.
- Etiquetar mejor exito/fracaso por conversacion en SQLite/Chroma.
- Crear metricas por turno: humor, sobreinversion, congruencia, avance a cita/numero.
- Agregar resumen final pedagogico al Level Up y Game Over.
- Evitar depender de Gemini free tier para sesiones largas, porque los 429 activan fallback.
