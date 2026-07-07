# Auditoria de bases y scoring de mensajes - Easy Date

Fecha: 2026-06-30 18:12:41

## Resumen ejecutivo

- SQLite fuente: `C:\desarrollos\Codex\Easy Date\textgame.db`.
- ChromaDB vectorial: `C:\desarrollos\Codex\Easy Date\chroma_db\chroma.sqlite3`.
- Conversaciones Reddit en SQLite: 213.
- Conversaciones Reddit con mensajes OCR/JSON no vacios: 169; sin mensajes parseables: 44.
- Mensajes conversacionales parseables en SQLite, sin YouTube: 880 = 806 de Reddit OCR + 74 de `chat_turns`.
- Transcripciones YouTube: 46 videos, 217,379 palabras, aproximadamente 12098 segmentos equivalentes de mensaje/idea.
- Total fuente aproximado si se incluyen segmentos YouTube: 12978 unidades de mensaje/contexto.
- ChromaDB indexa 243 vectores: chat_turns_collection=74, natalia_conversations=169.
- Score promedio de conversaciones Reddit con scoring JSON: 8.35/10.
- Score promedio de mensajes hombre/usuario detectados: 5.68/10.

Nota: ChromaDB no se suma como mensajes nuevos porque es indice vectorial de contenido derivado de SQLite.

## Tabla por fuente

| Base | Coleccion/tabla | Registros | Mensajes/unidades | Hombre/usuario | Mujer/contexto | Desconocido | Score promedio | Mediana |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SQLite | reddit_conversations | 213 | 806 | 396 | 191 | 219 | 5.55 | 6.0 |
| SQLite | chat_turns | 37 | 74 | 37 | 37 | 0 | 6.0 | 6.0 |
| SQLite | transcripts YouTube | 46 | ~12098 segmentos | - | - | - | - | - |
| ChromaDB | natalia_conversations | 169 | 169 | 169 | contexto no separado | - | 5.05 | 5 |
| ChromaDB | chat_turns_collection | 74 | 74 | 74 | metadata girl_response | - | 6.32 | 7.0 |

## Distribucion de scoring 1-10

| Conjunto | N | Promedio | Mediana | Distribucion |
| --- | --- | --- | --- | --- |
| Reddit conversaciones: scoring JSON | 20 | 8.35 | 8.5 | 3:1, 6:1, 7:2, 8:6, 9:4, 10:6 |
| Mensajes hombre/usuario calificables | 433 | 5.68 | 6 | 1:1, 3:57, 4:15, 5:18, 6:269, 7:61, 8:12 |
| Mensajes mujer/contexto | 228 | 5.57 | 6.0 | 2:2, 3:38, 4:8, 5:15, 6:121, 7:32, 8:12 |
| Mensajes OCR autor desconocido | 219 | 5.43 | 6 | 1:2, 2:2, 3:30, 4:6, 5:24, 6:135, 7:20 |
| Todos mensajes OCR+chat_turns | 880 | 5.59 | 6.0 | 1:3, 2:4, 3:125, 4:29, 5:57, 6:525, 7:113, 8:24 |
| Chroma docs hombre: natalia_conversations | 169 | 5.05 | 5 | 1:2, 2:3, 3:10, 4:46, 5:26, 6:72, 7:10 |
| Chroma docs hombre: chat_turns_collection | 74 | 6.32 | 7.0 | 3:4, 4:4, 6:28, 7:32, 8:6 |

## Reddit por perfil

| Perfil | Conversaciones | Mensajes OCR | Hombre | Mujer | Desconocido | Score conv. prom. | Score msg. prom. | Distribucion scoring conv. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MILF | 2 | 2 | 0 | 2 | 0 | 9.0 | 7.0 | 8:1, 10:1 |
| coqueta | 67 | 372 | 188 | 97 | 87 | 8.89 | 5.45 | 7:1, 8:2, 9:3, 10:3 |
| defensiva | 27 | 173 | 88 | 37 | 48 | 7.0 | 5.53 | 6:1, 8:1 |
| desconocida | 2 | 0 | 0 | 0 | 0 | None | None | - |
| desinteresada | 11 | 58 | 34 | 19 | 5 | 5.0 | 5.71 | 3:1, 7:1 |
| indecisa | 96 | 160 | 70 | 19 | 71 | 9.0 | 5.68 | 8:1, 10:1 |
| stripper/sugar | 8 | 41 | 16 | 17 | 8 | 9.0 | 5.85 | 8:1, 9:1, 10:1 |

## Estado de imagenes y OCR Reddit

| Metrica | Valor |
| --- | --- |
| Filas Reddit totales | 213 |
| Filas con image_urls | 211 |
| URLs de imagen registradas | 243 |
| Rutas locales registradas | 243 |
| JSON/OCR con mensajes parseables | 169 |
| JSON/OCR vacio o no parseable | 44 |

## Criterio de scoring heuristico de mensajes

El scoring individual de mensajes se calcula localmente sin IA externa. Suma puntos por longitud calibrada, una pregunta clara, humor/emojis suaves, respuesta contextual y avance hacia plan/contacto. Penaliza mensajes demasiado cortos/largos, demasiadas preguntas, intensidad sexual temprana, necesidad, exceso de emojis y cumplidos genericos intensos. Para conversaciones Reddit se respeta el `scoring` ya presente en `transcription_json` cuando existe.
