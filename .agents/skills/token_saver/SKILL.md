---
name: TokenSaver
description: Reglas y directrices de comportamiento para optimizar y reducir al máximo el consumo de tokens en la sesión.
---

# Guía de Optimización de Tokens (TokenSaver)

Esta skill se activa automáticamente para indicarle al agente cómo operar con la máxima eficiencia de tokens posible, protegiendo los límites de 5 horas y semanales del usuario.

## Directrices para el Agente

### 1. Concisión en las Respuestas
- **Sin preámbulos:** Evitar saludos repetitivos, introducciones largas o explicaciones redundantes de lo que hace el código. Ir directo al grano.
- **Formateo Directo:** Responder con la información exacta que solicitó el usuario, utilizando viñetas y tablas cortas.

### 2. Eficiencia en el Manejo de Código
- **Uso de Diffs:** Nunca reescribir un archivo completo en el chat si solo cambió una línea. Mostrar únicamente los fragmentos modificados en formato `diff`.
- **Modificación Quirúrgica:** Utilizar herramientas específicas de edición de archivos (`replace_file_content` o `multi_replace_file_content`) apuntando a líneas exactas, evitando lecturas o escrituras completas innecesarias.

### 3. Orquestación Inteligente de Modelos
- **Recomendación de Flash:** El agente debe detectar proactivamente cuándo el usuario solicita una tarea mecánica, repetitiva o de generación de plantillas (boilerplate) y sugerirle explícitamente cambiar a **Gemini 3.5 Flash** antes de proceder.
- **Reserva de Pro:** Reservar **Gemini 3.1 Pro** únicamente para fases de arquitectura, debugging complejo o análisis lógico abstracto.

### 4. Reducción de Contexto
- **Evitar lecturas redundantes:** No leer archivos del sistema múltiples veces en la misma sesión si el contenido no ha cambiado.
- **Mantener el contexto limpio:** Sugerir al usuario iniciar una nueva conversación cuando el hilo actual sea demasiado largo y la tarea anterior ya esté resuelta.
