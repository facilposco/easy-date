# Verificacion Natalia humana - Nivel 1 - 2026-06-29

## Objetivo verificado

Revisar que Natalia-Persona responda al mensaje real visible del hombre, que Natalia-Coach evalue el mismo contexto sin mezclarse con la mujer del chat, y que el Nivel 1 funcione completo en Chrome.

## Evidencia revisada

- Texto adjunto de arquitectura: recomienda RAG estructurado, evaluacion por metricas y agente doble.
- Capturas originales: Natalia saltaba de gimnasio/trabajo a vino, y el Coach evaluaba objetivos de paso que no correspondian al chat visible.
- Backend actual: `backend/server.py`.
- Tests actuales: `tests/test_backend.py`.
- Runtime local: `http://127.0.0.1:8000/simulador_v1.2.html`.

## Cambios aplicados

| Area | Cambio | Motivo |
|---|---|---|
| Natalia-Coach | Dejo de penalizar cuando el hombre responde una pregunta visible y luego hace una pregunta natural. | Evitar feedback injusto tipo "metio pregunta logistica extra" cuando el usuario si siguio el hilo. |
| Sugerencias A/B/C | Las sugerencias aprendidas ahora deben cubrir tambien el tema respondido cuando hay una nueva pregunta. | Evitar opciones incompletas como preguntar trabajo sin contestar primero ubicacion. |
| Detector de temas | `soy de salsa` ya no se marca como ubicacion. | Evitar falsos positivos por substring. |
| Detector de temas | `interrogatorio` ya no se marca como mascotas por contener `gato`. | Evitar falsos positivos por substring. |
| Coach cierre | `copa/vino` se trata como parte del plan cuando el usuario esta cerrando logistica/contacto. | Evitar penalizar un cierre natural de cita como tema extra. |

## Tests

Comando:

```powershell
pytest -q tests -p no:cacheprovider -rs
```

Resultado:

```text
88 passed, 1 warning in 131.60s
```

Warning no bloqueante: `StarletteDeprecationWarning` por `httpx` en `TestClient`.

## Prueba Chrome Nivel 1

Servidor:

```text
http://127.0.0.1:8000/simulador_v1.2.html
```

Estado backend:

| Campo | Valor |
|---|---|
| `status` | `ok` |
| `gemini_live_enabled` | `false` |
| `gemini_keys_loaded` | `3` |
| `chroma_connected` | `true` |
| `chroma_query_enabled` | `true` |
| `chroma_documents` | `169` |

Mensajes usados en Chrome:

1. Hola Natalia, tu perfil se ve con buena vibra. Como va tu dia?
2. Bien, vengo saliendo del gimnasio. A ti te gusta hacer ejercicio? :)
3. Hago pesas y algo de cardio, sin volverme fanatico. Y tu en que trabajas?
4. Marketing visual suena creativo. Cuando no estas trabajando, que musica te gusta?
5. Soy de salsa y musica con energia. Tambien me gusta probar comida rica, que comida disfrutas?
6. Entonces te debo un lugar rico, buena musica y cero entrevista.
7. Si te late, el jueves podemos tomar una copa tranquila por Brickell y vemos si mi gusto pasa tu filtro.
8. Prometo plan simple: una copa, buena conversacion y sin interrogatorio eterno. Te paso mi WhatsApp?
9. Te lo paso: +1 305 555 0188. Lo usamos solo para cuadrar bien.
10. Trato hecho, te escribo con lugar y hora, sin discurso intenso.

Resultado Chrome:

| Check | Resultado |
|---|---|
| Avance 10 pasos | OK |
| Level Up / cita lograda | OK |
| Game Over | No |
| Modal Coach en cada paso | OK |
| Input deshabilitado con modal abierto | OK |
| Boton Enviar deshabilitado con modal abierto | OK |
| Paso gimnasio | Natalia responde sobre ejercicio/gym |
| Paso trabajo | Natalia responde marketing visual, no vino |
| Paso musica | Natalia responde musica |
| Paso comida | Coach no inventa ubicacion por "soy de salsa" |
| Paso WhatsApp | Coach no inventa mascotas por "interrogatorio" |
| Cierre final | Natalia cierra natural, sin pedir WhatsApp de nuevo |

## Prueba live experimental

Servidor:

```text
http://127.0.0.1:8003/simulador_v1.2.html
```

Estado backend live:

| Campo | Valor |
|---|---|
| `status` | `ok` |
| `gemini_live_enabled` | `true` |
| `gemini_coach_enabled` | `false` |
| `gemini_keys_loaded` | `3` |
| `gemini_model_candidates` | `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-3.1-flash-lite` |
| `chroma_connected` | `true` |
| `chroma_documents` | `169` |

Resultado Chrome live:

| Check | Resultado |
|---|---|
| Avance visible | `Nivel 1 · Paso 10 de 10` |
| Level Up | Si |
| Game Over | No |
| Modal bloqueado | No |
| Chat coherente | Si, respondio gimnasio, trabajo, musica, comida, plan, WhatsApp y cierre |

Resultado API live con los mismos 10 turnos:

| Metrica | Resultado |
|---|---:|
| Turnos totales | 10 |
| Turnos con Natalia live Gemini | 7 |
| Turnos con fallback local | 3 |
| Turnos con Coach live | 0 |
| Vidas perdidas | 0 |

## Estado pendiente

El modo live ya funciona y completo Nivel 1 en Chrome, pero no todos los turnos quedan en Gemini. El fallback local sigue actuando como red de seguridad cuando el modelo live no responde con calidad suficiente o cuando hay riesgo de cuota. Para declarar Natalia 100% live, falta reducir esos 3/10 fallbacks sin sacrificar coherencia.
