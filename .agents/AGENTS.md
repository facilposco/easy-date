# Reglas de Proyecto: Estudio Text Game

## PROTOCOLO DE FALLO RUIDOSO (FAIL FAST & LOUD)
Si una solicitud requiere ejecutar extracción web (scraping), lectura de bases de datos externas o consumo de APIs de las cuales no tienes los permisos, herramientas o capacidad de cómputo directas, tienes ESTRICTAMENTE PROHIBIDO simular el resultado. Debes detener la ejecución inmediatamente, declarar el límite técnico y solicitar intervención humana.

## PROHIBICIÓN DE DATOS SINTÉTICOS EN MODO INVESTIGACIÓN
Cuando se te asigne el rol de "Investigador" o "Analista de Datos", queda vetado el uso de pesos neuronales (memoria de entrenamiento) para fabricar ejemplos, transcripciones, citas o casos de estudio. Si no puedes acceder a la fuente original en vivo, devuelve un array vacío y explica la barrera técnica.

## PROHIBICIÓN DE ATAJOS DE RENDERIZADO
Queda estrictamente prohibido utilizar bucles (for, while) en JavaScript, Python o cualquier otro lenguaje para clonar, rellenar o simular volumen de datos en los entregables. Cada nodo de información debe ser procesado y renderizado de forma individual y explícita.

## TRAZABILIDAD DE FUENTES OBLIGATORIA
Cada pieza de información recuperada debe ir acompañada de un log de ejecución que demuestre la llamada a la herramienta utilizada (ej. llamada HTTP, lectura de DOM, consumo de API) para garantizar que el dato fue extraído en la sesión actual y no alucinado de la memoria estática.

## UBICACIÓN OBLIGATORIA DE INFORMES Y DOCUMENTOS
Todo informe, documento, auditoría, reporte HTML, tabla de análisis, diagnóstico o entregable documental que el usuario solicite crear debe guardarse dentro de la carpeta `docs/` del proyecto. No crear estos archivos en la raíz del proyecto salvo que el usuario lo pida explícitamente.

## PROTOCOLO CODEX QA Y CENTER FIRST
1. **Center First obligatorio:** Toda función nueva debe implementarse primero en el centro lógico del sistema antes de tocar pantallas finales, HTML compilado o archivos generados.
   - Backend/API: `backend/`.
   - Lógica reutilizable: módulos Python/JS testeables.
   - DB, RAG, ChromaDB, OCR y vectorización: módulos o scripts controlados.
   - Reportes y documentos: `docs/`.
   - Experimentos temporales: `scratch/`.
2. **Prohibición de lógica crítica en HTML final:** No implementar lógica crítica directamente en `simulador_v*.html`, HTML compilado, pantallas generadas o blobs grandes si existe o puede crearse una función central testeable. Si existe un generador, modificar el generador y regenerar.
3. **Desarrollo verificable:** Para toda función nueva, leer el código existente, identificar el centro lógico, definir éxito verificable, implementar el cambio mínimo, agregar o actualizar prueba/verificación, integrar en UI/API y validar antes de entregar.
4. **Corrección de bugs con regresión:** Para bugs reportados, reproducir primero con test, fixture, script diagnóstico o checklist verificable; corregir con cambio quirúrgico; ejecutar el test nuevo y pruebas relacionadas.
5. **Cambios quirúrgicos:** No refactorizar código no relacionado, no reescribir módulos completos si basta una función, no revertir cambios de usuario y no cambiar formato masivo sin necesidad.
6. **Matriz mínima de pruebas:** Lógica pura requiere unit test; DB requiere schema/conteos/fixture real; API requiere endpoint o fake local; RAG/Chroma requiere conteos SQLite vs Chroma y búsqueda pequeña; UI requiere prueba visual o Playwright cuando aplique; scraping/descarga requiere dry-run con límite, delays y log.
7. **Validación obligatoria:** Antes de cerrar cambios de código, ejecutar la prueba enfocada correspondiente. Si toca backend/core, ejecutar suite completa cuando sea razonable. Si una prueba no puede ejecutarse, documentar motivo y riesgo.
8. **Cierre estándar:** La respuesta final debe incluir archivos modificados, pruebas ejecutadas, resultado y riesgos o pendientes.

## SEGURIDAD DE SECRETOS
1. Nunca imprimir ni exponer `.env`.
2. Nunca mostrar claves Gemini, OpenAI, Decodo, DataImpulse, passwords ni strings completos de proxy.
3. Si se detecta un secreto hardcodeado, reportarlo y recomendar rotación/migración a `.env`.

## REGLAS DE EVASIÓN DE BLOQUEOS EN SCRAPING
1. **Obligatoriedad de Proxy Residencial:** Es una regla estricta e inquebrantable utilizar SIEMPRE el proxy residencial (`gw.dataimpulse.com` u otro aprovisionado en `.env`) para CUALQUIER tarea de web scraping, sin excepciones.
2. **Intervalos de Tiempo Estrictos:** Es obligatorio colocar intervalos de tiempo largos (`random.uniform(5, 10)` segundos) entre cada solicitud HTTP/descarga para evitar bloqueos inmediatos en Reddit y otras redes.
3. **Rotación de Puertos y Sesiones:** Si se usan proxies rotativos, se debe forzar una nueva dirección IP para cada solicitud modificando el ID de sesión del proxy en las credenciales.
4. **TLS Fingerprint & Headers:** Simular huellas de navegador reales. Nunca enviar solicitudes crudas sin cabeceras completas (`User-Agent`, `Accept-Language`, `sec-ch-ua`).
5. **Plan de Contingencia (Whisper local):** Si la API de transcripciones de YouTube está bloqueada permanentemente, el agente debe proponer descargar el audio usando `yt-dlp` y transcribirlo offline con `Whisper` de forma local.


## ROTACION DE IP (DATAIMPULSE)
Para evadir bloqueos de WAF como Cloudflare en Reddit, modificar el parametro de sesion en el usuario del proxy agregando _session-stringaleatorio al nombre de usuario. Esto fuerza a DataImpulse a asignar un nodo residencial nuevo y limpio.

## OBLIGATORIEDAD DE DESARROLLO DIRECTO Y MULTIAGENTE (SIN PLANES PREVIOS)
1. **Desarrollo Directo:** Queda estrictamente prohibido presentar planes de implementación (Planning Mode) o solicitar confirmaciones previas para programar, a menos que el usuario incluya un signo de interrogación ("?") en su petición. En su ausencia, el agente debe proceder de inmediato al desarrollo, ejecución y compilación directa.
2. **Uso de Multiagentes:** Para cualquier tarea de desarrollo o rediseño complejo, se debe coordinar de inmediato el flujo con subagentes paralelos (ej. game_developer, translator, UXUIAgent) para resolver concurrentemente.

## OPTIMIZACIÓN DE TOKENS Y SESIÓN (AHORRO DE RECURSOS)
1. **Optimización de Scraping (Contexto Mínimo):** Se prohíbe la recarga y lectura constante del DOM completo de Reddit/YouTube en bucles de monitoreo automáticos durante las pruebas. Se debe utilizar un pre-filtro local (offline) en Python para descartar conversaciones sin valor, y enviar únicamente fragmentos pequeños (chunks) a los modelos.
   - **Regla Estricta de Escaneo:** A partir de ahora, cuando lancemos el escaneo, aplicaré un pre-filtro local en Python (sin IA) para recortar las imágenes/textos de Reddit y le enviaré los fragmentos pequeños (chunks) exclusivamente a Gemini Flash 3.5 (low). Esto evitará que se vuelva a consumir tu cuota.
2. **Uso Eficiente de Modelos (Orquestación):**
   - **Enrutamiento Pro:** Reservar exclusivamente `Gemini Pro` para lógica de programación avanzada, algoritmos de juego complejos y análisis lógico abstracto.
   - **Enrutamiento Flash (Low):** Para cualquier tarea repetitiva, maquetación CSS/diseño, traducciones, generación de boilerplate y transcripciones OCR de scraping, se DEBE forzar el uso de `Gemini Flash 3.5 (low)` para lograr un ahorro de tokens masivo.

## ACTUALIZACIÓN DE ARQUITECTURA
1. **Actualización Obligatoria:** Es una regla estricta que el documento `arquitectura.html` debe ser actualizado inmediatamente después de realizar cualquier cambio arquitectónico, modificación en el esquema de las bases de datos o incorporación de nuevos módulos al proyecto.

## RECUPERACIÓN DE IMÁGENES REDDIT
1. **DataImpulse obligatorio:** La recuperación de imágenes guardadas en `reddit_conversations.image_urls` se ejecuta con DataImpulse como proxy residencial.
2. **Ritmo de descarga:** El script debe mantener pausas de `random.uniform(5, 10)` segundos entre descargas.
3. **Trazabilidad documental:** El resultado se registra en `docs/reddit_image_recovery_dataimpulse.csv` y se resume en `docs/reddit_image_recovery_dataimpulse_summary.md`.
4. **Sin IA/modelos:** Esta tarea no usa modelos de IA; es una descarga y validación documental offline.
 
## REGISTRO DE INFORMES
- `docs/natalia_coherencia_rag_nivel1_20260628.md`: auditoria y cambios de coherencia Natalia/Coach/RAG para Nivel 1.
