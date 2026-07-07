# Prompt para Claude: revision senior del RAG de Natalia

Actua como arquitecto senior de RAG, LLMOps, sistemas conversacionales y evaluacion de agentes.

Necesito que revises este archivo del proyecto Easy Date:

`C:\desarrollos\Codex\Easy Date\arquitectura.html`

Objetivo del sistema:

Natalia es una IA que simula a una mujer real en una app de citas tipo Tinder/Bumble/Hinge. Maximus es el coach que evalua al usuario. El sistema usa RAG con conversaciones reales exitosas, casos negativos, libros, OCR de imagenes y SQLite como fuente de verdad. No queremos que Natalia invente resultados, telefonos, citas, intenciones ni hechos que no esten en el contexto recuperado.

Revisa especificamente:

1. Si la arquitectura RAG separa bien Natalia-persona, Maximus-Coach, casos exitosos, casos negativos, libros y conversaciones legacy.
2. Si el patron "Chroma como indice, SQLite como fuente de verdad / parent document" esta bien planteado para recuperar conversaciones completas.
3. Si el catalogo de 120 preguntas etiquetadas es suficiente como base de evaluacion o que ampliarias para llegar a 200+ preguntas.
4. Que metadata faltaria para mejorar retrieval: objetivo, perfil, app, idioma, evidencia de exito, confidence, OCR quality, tiempos de respuesta, etapa conversacional, etc.
5. Como mejorarias el reranking despues de Chroma sin aumentar demasiado costo ni latencia.
6. Como reducir alucinaciones: reglas de grounding, abstencion, citas de evidencia, guardrails, trazabilidad de fuentes.
7. Como mejorar el entrenamiento de Natalia para sonar mas humana, calibrada por nivel de dificultad y coherente con el ultimo mensaje visible.
8. Como integrar mejor los 1.895 casos exitosos actuales, los 1.000 negativos, los libros y futuros 5.000 casos sin contaminar la voz de Natalia.
9. Como debe funcionar el enrutador de intencion entre Natalia y Maximus. Situacion actual documentada: cuando el usuario juega en el chat, `/api/simulate-turn` prepara `retrieve_persona_cases()` para Natalia-persona y `retrieve_coach_cases()` para Maximus-Coach; no es el RAG quien decide solo, sino el flujo backend. Necesitamos saber si conviene mantener enrutamiento por etapa del juego, agregar clasificador de intencion, crear endpoint separado "Preguntale a Maximus", o usar una arquitectura hibrida.
10. Que reglas exactas debe seguir el router:
    - Si el usuario escribe como si hablara con la chica, debe responder Natalia-persona.
    - Si el usuario pide consejo, teoria, estrategia, explicacion, fotos, primera cita, opener, WhatsApp o "que respondo", debe responder Maximus.
    - Si el mensaje ocurre dentro de una evaluacion, resumen final, Game Over o seccion estudiar, debe responder Maximus.
    - Si el usuario escribe "Maximus..." dentro del chat de Natalia, definir si se intercepta y se manda al Coach o si se mantiene como mensaje del juego.
    - Evitar que Natalia-persona consulte negativos, YouTube o teoria de libros directamente si eso la hace sonar como coach.
11. Que pruebas automaticas faltan: routing Natalia/Maximus, retrieval, groundedness, persona, coach, regresion de UI, timing, emojis, cierre de cita/contacto.
12. Que cambios priorizarias en corto plazo, mediano plazo y largo plazo.

Condiciones:

- No inventes datos de la base. Si algo no esta documentado en `arquitectura.html`, dilo como brecha o pregunta.
- Da sugerencias accionables, con prioridad Alta/Media/Baja.
- Incluye riesgos si una mejora puede contaminar el RAG o aumentar costo.
- Propone una tabla final con: mejora, motivo, archivo/componente afectado, esfuerzo estimado, riesgo y prueba de verificacion.
- No recomiendes fine-tuning como primer paso si el problema se resuelve mejor con RAG, metadata, reranking, evaluacion o mejores prompts.
- Si recomiendas fine-tuning, explica exactamente que dataset usarias, que no incluirias y como validarias que no empeora el sistema.

Entrega esperada:

1. Diagnostico breve de la arquitectura actual.
2. Top 10 mejoras priorizadas.
3. Recomendaciones para ampliar el catalogo de preguntas de 120 a 200+.
4. Mejoras para evitar alucinaciones y conservar conversaciones completas.
5. Propuesta de arquitectura del router Natalia vs Maximus, con ejemplos de mensajes y fuentes permitidas por cada ruta.
6. Plan de implementacion en fases con pruebas.
