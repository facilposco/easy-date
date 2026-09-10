# 📱 Easy Date: Text Game Simulator & RAG Architecture

> **Un simulador interactivo impulsado por IA para mejorar tus habilidades de Text Game y dinámicas sociales en aplicaciones de citas como Tinder, Bumble y Hinge.**

![Version](https://img.shields.io/badge/version-1.2-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688)
![Gemini](https://img.shields.io/badge/AI-Gemini_Pro_%26_Flash-orange)
![ChromaDB](https://img.shields.io/badge/Vector_DB-Chroma-purple)

## 🎯 Sobre el Proyecto

**Easy Date** es una plataforma dual que combina un **juego interactivo de simulación** y una **base de conocimiento (guías de estudio)** basada en miles de interacciones reales y fine tuneado con los mejores libros de de text game, tambien cuenta con agentes ia entrenados para ser un simulador humano. El objetivo es ayudar a los usuarios a practicar sus interacciones de texto en un entorno seguro antes de aplicarlas en el mundo real.

El núcleo del sistema es una arquitectura **RAG v2 Integral (Retrieval-Augmented Generation)** que separa cognitivamente dos agentes de Inteligencia Artificial:
1. **Natalia (Persona):** Simula a la chica en el chat, emulando respuestas de mujeres reales extraídas de casos de éxito comprobados.
2. **Maximus (Coach):** Analiza tus mensajes, ofrece métricas pedagógicas, advierte sobre errores y sugiere mejores caminos de acción basados en teoría y psicología femenina.

---

## 🚀 Características Principales

### 🎮 Simulador Interactivo (Frontend)
* **Entorno de Juego Realista:** Interfaz tipo app de citas (`simulador_v1.2.html`) donde debes elegir las mejores opciones de diálogo y manejar los tiempos de respuesta (sliders de timing).
* **Feedback en Tiempo Real:** Modal de retroalimentación del *Coach* que evalúa cada interacción (tono, métricas pedagógicas, riesgos).
* **Niveles de Dificultad:** Desde perfiles receptivos hasta chicas frías y defensivas con "shit-tests" rigurosos.
* **Sistema de Vidas y Progresión:** Completa los niveles sin perder todos los corazones para desbloquear la cita final (Level Up).
* **Casos Reales y Guías:** Pestaña de estudio para revisar diálogos verdaderos categorizados (Me gustaron / No me gustaron) y aprender teoría (abridores, cierres, humor).

### 🧠 Arquitectura de IA y RAG (Backend)
* **Enrutamiento Inteligente (Router):** El sistema detecta si el usuario está hablando con la chica (envía a Natalia) o pidiendo consejos de estudio (envía a Maximus).
* **Base Vectorial (ChromaDB) + SQLite:** Almacena casos reales ganadores de Reddit, libros de seducción/psicología femenina y conversaciones de ejemplo. SQLite actúa como fuente de verdad para rehidratar conversaciones completas, evitando alucinaciones de la IA.
* **Rotación y Resiliencia de APIs:** Soporte integrado para múltiples llaves de Gemini (Flash/Pro) rotativas para evadir errores de cuota (429) y garantizar alta disponibilidad, con *fallback* a modelos locales.
* **Evaluación Dual Estricta:** Un catálogo de QA semántico de 200+ preguntas y reglas estrictas que bloquean respuestas tóxicas, manipulación o coerción.

---

## ⚙️ Pipeline de Extracción de Datos (Scraping)

El motor de inteligencia se nutre de un pipeline automatizado, paralelo y auditable de datos empíricos:
* **Orígenes Reales:** Extracción de posts ganadores en comunidades de dating (Reddit) utilizando perfiles de búsqueda de alta precisión y evasión de bloqueos (DataImpulse, retrasos aleatorios, spoofing de cabeceras).
* **Procesamiento y OCR:** Descarga de imágenes y aplicación de OCR local para leer chats reales.
* **Traducción LATAM:** Traducción automática de conversaciones ganadoras al español latino casual manteniendo la jerga natural de las aplicaciones de citas.
* **Filtros de Calidad:** Los casos solo se indexan si demuestran una evidencia de éxito verificable (cierre de WhatsApp, Instagram, cita programada) y un OCR coherente.

---

## 🛠️ Stack Tecnológico

* **Backend:** Python, FastAPI
* **IA & Modelos:** Gemini Pro 1.5 (lógica compleja), Gemini Flash 3.5 (tareas repetitivas, RAG chat).
* **Bases de Datos:** ChromaDB (Búsqueda Vectorial Semántica), SQLite (Estado relacional, persistencia completa de chats, logs de auditoría por turno).
* **Scraping:** SeleniumBase UC, APIs Decodo/DataImpulse, OCR local.
* **Frontend:** HTML5, CSS3, Vanilla JS, Web Audio API (efectos de sonido sintetizados locales).
* **Despliegue de Producción:** VPS, Docker (contenedor `easy-date-rag`), Traefik, Red Docker `zeus-network`, Cloudflare Access.

---

## 📚 Estructura de Conocimiento (RAC)

El RAG de Easy Date se divide en colecciones especializadas:
1. `natalia_success_cases`: Ejemplos con resultados positivos y trazabilidad. (Usado por Natalia y Maximus).
2. `natalia_negative_cases`: Errores y contraejemplos. (Usado **solo** por Maximus).
3. `natalia_books`: Libros sobre teoría, psicología, relaciones y text game estructurados con trazabilidad `Libro -> Principio -> Caso Real`.
4. `natalia_book_conversations`: Ventanas de conversaciones extraídas de la literatura evaluada.

---

## 🔒 Privacidad y Ética (Guardrails)

* **Seguridad Emocional:** El sistema integra evaluadores semánticos que bloquean estereotipos universales, coerción, manipulación destructiva y comportamiento no sustentado. 
* **Aislamiento de Perfiles:** Natalia solo aprende de casos de éxito empíricos que encajan con su nivel de dificultad. No lee teoría cruda ni ejemplos negativos para evitar comportamientos robóticos.
* **Zero Datos Sintéticos:** Todas las respuestas emuladas parten de datos comprobables (cero invención de resultados que no estén en la base de datos).

---

## 👨‍💻 Autor y Contacto

Desarrollado y estructurado por **Omar Francisco Espinel Roncancio** bajo **Nueva Informática SAS / Fácil POS**.

Para dudas de arquitectura, integración o licencias, visita el código fuente o la documentación interna desplegada.
