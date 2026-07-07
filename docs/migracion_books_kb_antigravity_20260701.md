# Migracion RAC de libros AntiGravity a Codex - 2026-07-01

## Resumen

Se copio el modulo de conocimiento de libros desde AntiGravity hacia el workspace principal de Codex.

- Origen: `C:\desarrollos\antigravity\Easy Date\books_kb`
- Destino: `C:\desarrollos\Codex\Easy Date\books_kb`
- Copia realizada: 195 archivos, aproximadamente 260 MB
- Excluido intencionalmente: `.venv`, `__pycache__` y `*.pyc`

La exclusion evita mover entornos y cache regenerable. La informacion util de entrenamiento, auditoria y recuperacion quedo copiada.

Nota 2026-07-01: despues de esta migracion se agrego el EPUB `The Message Game A Guide to Dating at the Touch of a Button` como libro `id=23`. El estado actual del RAC de libros queda documentado en `C:\desarrollos\Codex\Easy Date\docs\ingesta_message_game_rag_20260701.md`.

## Verificacion en Codex

| Componente | Conteo / estado |
|---|---:|
| EPUB fuente en `source_books` | 23 |
| Libros procesados en `books_index.sqlite` | 22 |
| Chunks en SQLite | 2.114 |
| Chunks con ventana de contexto | 2.114 |
| Embeddings reportados por `processing_quality` | 2.104 |
| Conversaciones de libros en SQLite | 46 |
| Registros OCR de imagen | 5 |
| Imagenes registradas por auditoria de procesamiento | 1.385 |
| Palabras totales procesadas | 340.912 |
| Duplicados omitidos | 1 |

## Chroma de libros copiado

Ruta: `C:\desarrollos\Codex\Easy Date\books_kb\chroma_books\chroma.sqlite3`

| Coleccion | Embeddings |
|---|---:|
| `natalia_books_kb` | 2.104 |
| `natalia_conversations` | 46 |
| `natalia_conversations_plus` | 46 |

## Estado operativo

El Chroma activo del backend de Codex sigue siendo:

`C:\desarrollos\Codex\Easy Date\chroma_db`

El RAC de libros copiado queda como modulo staged en:

`C:\desarrollos\Codex\Easy Date\books_kb`

No se fusiono con el Chroma operativo para evitar contaminar o romper el simulador durante el scraping masivo de conversaciones exitosas. La integracion final debe hacerse con backup, QA y una regla clara de retrieval para Natalia y Maximus.

## Recomendacion de integracion

1. Mantener SQLite como fuente completa de verdad para libros y conversaciones largas.
2. Usar Chroma solo como indice de recuperacion semantica, guardando `book_id`, `chunk_id`, `conv_id` y ventana de contexto.
3. Cuando Natalia o Maximus recuperen un fragmento, rehidratar desde SQLite la conversacion completa o la ventana padre para que el RAC no entregue respuestas cortadas.
4. Fusionar al RAG final solo despues de validar que `natalia_conversations` de libros no choque con la coleccion operativa de Reddit/chat.
