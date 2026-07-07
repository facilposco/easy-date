# Ingesta EPUB The Message Game al RAC de libros - 2026-07-01

## Resultado

Se agrego el EPUB `The Message Game A Guide to Dating at the Touch of a Button` al RAC de libros staged en Codex.

| Campo | Resultado |
|---|---:|
| Book ID | 23 |
| Autor | Ice White |
| Texto nativo extraido | 36.893 palabras |
| OCR de imagenes | 11.186 palabras |
| Total indexado | 48.082 palabras |
| Imagenes guardadas | 204 |
| Filas OCR del libro | 204 |
| Imagenes candidatas conversacionales por OCR | 195 |
| Imagenes que requieren revision manual | 9 |
| Chunks SQLite | 233 |
| Ventanas de contexto | 233 |
| Conversaciones detectadas | 28 |
| Score de calidad | 100 |

## Rutas

- EPUB copiado: `C:\desarrollos\Codex\Easy Date\books_kb\source_books\The Message Game A Guide to Dating at the Touch of a Button (White, Ice) (z-library.sk, 1lib.sk, z-lib.sk).epub`
- Texto completo: `C:\desarrollos\Codex\Easy Date\books_kb\raw_texts\libro_23_raw.txt`
- Texto nativo: `C:\desarrollos\Codex\Easy Date\books_kb\raw_texts\libro_23_native_text.txt`
- OCR consolidado: `C:\desarrollos\Codex\Easy Date\books_kb\raw_texts\libro_23_ocr_text.txt`
- Imagenes: `C:\desarrollos\Codex\Easy Date\books_kb\book_images\libro_23_the_message_game_a_guide_to_dating_at_the_touch_of_a_button`
- Chunks: `C:\desarrollos\Codex\Easy Date\books_kb\chunks\libro_23_chunks.json`
- Conversaciones: `C:\desarrollos\Codex\Easy Date\books_kb\conversations\libro_23_conversations.json`
- Reporte JSON de ingesta: `C:\desarrollos\Codex\Easy Date\books_kb\docs\ingesta_epub_the_message_game_a_guide_to_dating_at_the_touch_of_a_button_20260701_162703.json`
- HTML Top 100 de estudio: `C:\desarrollos\Codex\Easy Date\docs\message_game_top100_20260701_163617.html`
- HTML Top 100 estricto OCR + texto nativo: `C:\desarrollos\Codex\Easy Date\docs\message_game_top100_ocr_strict_20260701_165455.html`
- Cache layout OCR de las 204 imagenes: `C:\desarrollos\Codex\Easy Date\books_kb\docs\message_game_ocr_layout_cache.json`

## Estado del RAC de libros despues de la ingesta

| Componente | Total |
|---|---:|
| Libros procesados unicos | 23 |
| EPUB fuente guardados | 24 |
| Duplicados omitidos | 1 |
| Chunks SQLite | 2.347 |
| Chunks vectorizables | 2.335 |
| Conversaciones de libros | 74 |
| Chroma `natalia_books_kb` | 2.335 |
| Chroma `natalia_conversations` | 74 |
| Chroma `natalia_conversations_plus` | 46 |

## Ajustes realizados

- Se creo `books_kb\ingest_single_epub.py` para agregar EPUBs nuevos sin reordenar IDs antiguos.
- Se guardaron imagenes originales del EPUB en disco.
- Se ejecuto OCR local con `rapidocr_onnxruntime` y se guardo cache por hash.
- Se separo texto nativo, OCR consolidado y raw completo.
- Se indexaron chunks y conversaciones en SQLite/FTS y Chroma.
- Se crearon ventanas de contexto en `chunk_context_windows` para rehidratar contexto completo.

## Observaciones de calidad

El texto nativo del EPUB es limpio y debe ser la fuente principal para el RAC. El OCR local recupera texto de las capturas, pero en varias imagenes une palabras; por eso las 204 filas OCR quedan auditables y 9 requieren revision manual. La version estricta del HTML Top 100 se genero solo desde texto nativo real y OCR real: 27 casos de texto nativo y 73 casos OCR, con coordenadas/lados inferidos desde RapidOCR cuando hay imagen. Para entrenamiento fino de Natalia, conviene pasar un QA posterior de OCR y traduccion LATAM antes de usar capturas como ejemplos conversacionales directos.

## Recomendacion para los proximos libros Text Game

1. Ingerir cada EPUB con `ingest_single_epub.py`, no con `process_books.py --resume`, para evitar cambios de ID por orden alfabetico.
2. Mantener siempre tres capas: original completo, OCR bruto y version normalizada/traducida.
3. Usar SQLite como fuente completa y Chroma solo como indice semantico.
4. Para conversaciones largas, Chroma debe devolver IDs; la app debe rehidratar desde SQLite la conversacion completa o la ventana padre.
5. Agregar una cola de QA que clasifique cada conversacion por objetivo: numero, WhatsApp, Instagram, Snapchat, cita, reenganche, humor, timing, objecion, shit-test o cierre fallido.
6. Antes de mezclar con Natalia Persona, traducir a espanol latino y marcar tono/riesgo para que Maximus pueda enseñar sin que Natalia imite texto toxico o demasiado agresivo.
