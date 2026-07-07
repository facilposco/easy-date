# Reporte de mejoras RAG Natalia - 2026-07-07

## Resultado

Se implemento y probo el catalogo de evaluacion extendida para Natalia. El sistema queda con evaluacion base de 20 preguntas y benchmark etiquetado de 120 preguntas para validar retrieval, colecciones esperadas y evidencia antes de afirmar que Natalia puede usar una fuente.

## Tabla de resultados

| Item | Resultado | Evidencia |
|---|---:|---|
| Catalogo RAG v1 generado | 120 preguntas | `docs/natalia_rag_eval_catalog_v1.csv`, `.json`, `.html` |
| Perfiles cubiertos | 5 | coqueta, indecisa, defensiva, desinteresada, alta_selectividad |
| Intenciones cubiertas | 24 | contacto, cita, opener, humor, emojis, timing, recuperacion, pruebas, no inventar |
| QA catalogo | 120/120 OK | `docs/natalia_rag_eval_catalog_run_20260706_210358.*` |
| Faltas de evidencia | 0 | `summary.falta_evidencia=0` |
| QA base | 20/20 OK | `docs/natalia_rag_qa_20_20260706_210207.*` |
| Traducciones pendientes | 0 | `docs/natalia_rag_daily_maintenance_20260706_210023.json` |
| Chroma exitos Reddit | 1.895 docs | `/health` y reporte diario |
| Chroma negativos Coach | 1.000 docs | `/health` y reporte diario |
| Libros RAG | 2.335 docs | `/health` |
| Conversaciones libros | 74 docs | `/health` |
| Gemini live | Activo | `/health`: `gemini_live_enabled=true`, `gemini_keys_loaded=3` |
| Chroma query runtime | Activo | `/health`: `chroma_query_enabled=true` |
| Mantenimiento diario | OK | `docs/natalia_rag_daily_maintenance_20260706_210023.json` |

## Archivos creados o actualizados

| Archivo | Funcion |
|---|---|
| `scratch/generate_natalia_rag_eval_catalog.py` | Genera el catalogo deterministico de 120 preguntas etiquetadas. |
| `scratch/qa_natalia_rag_catalog.py` | Ejecuta QA del catalogo contra las colecciones reales del RAG. |
| `scratch/daily_natalia_rag_maintenance.py` | Agrega generacion y QA del catalogo al mantenimiento diario. |
| `AGENTS.md` | Documenta regla y estado RAG actualizado. |
| `arquitectura.html` | Documenta arquitectura RAG implementada y verificacion extendida. |
| `docs/prompt_claude_revision_rag_natalia_20260707.md` | Prompt para que Claude revise `arquitectura.html` y sugiera mejoras. |

## Regla operativa

Las 120 preguntas no son respuestas prefabricadas para Natalia. Son un set de evaluacion y enrutamiento: sirven para detectar si el RAG encuentra evidencia correcta, si consulta la coleccion adecuada y si debe abstenerse cuando no hay datos suficientes.
