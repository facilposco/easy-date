# Skill: epubsfacilpos

Ruta activa local:

`C:\Users\New\.codex\skills\epubsfacilpos`

Uso:

Se activa cuando se procesan nuevos libros, EPUBs, PDFs o lotes de libros para entrenar el RAG de Natalia/Maximus.

Flujo obligatorio:

1. Crear manifiesto con `scratch\build_book_batch_manifest.py`.
2. Revisar duplicados, idioma, categoria y accion recomendada.
3. Ingerir solo despues de revisar el manifiesto.
4. No traducir libros que ya esten en espanol.
5. Traducir libros no espanoles a espanol latino corregido.
6. Preservar original, traduccion, referencias EPUB, chunks y politicas de voz.
7. Generar `book_principles` y `principle_case_links`.
8. Ejecutar QA por libro/lote.
9. Generar reporte HTML/JSON v2 cuando exista comparacion.
10. Actualizar siempre `AGENTS.md` y `arquitectura.html`.

Criterio para afirmar que Natalia/Maximus quedaron entrenados:

- Libro en SQLite.
- Embeddings en Chroma.
- Texto limpio/traducido si aplica.
- Principios y politicas de voz creados.
- Casos reales enlazados cuando sea posible.
- QA aprobada.
- Reporte generado.
- Arquitectura documentada.

Nota:

La copia operativa del skill esta fuera del repositorio para que Codex lo descubra automaticamente. Este archivo es respaldo versionado del procedimiento.
