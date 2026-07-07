# QA: optimizacion del scraper Reddit / Decodo

Fecha local: 2026-07-01 17:29:55

Alcance:
- Revisar `scratch/reddit_success_parallel_pipeline.py`
- Revisar `scratch/reddit_success_image_pipeline.py`
- Proponer una optimizacion segura para acelerar discovery cerca de 10 req/s sin disparar gasto premium innecesario
- No tocar credenciales, no borrar datos, no interrumpir procesos activos

Estado:
- No aplique cambios de codigo. Hay procesos Python activos en la maquina y preferi dejar el worktree intacto.
- El hallazgo principal es claro: el cuello de botella no esta en OCR ni en descarga de imagenes, sino en discovery secuencial y en la consulta extra de score por post.

## Hallazgos

1. `reddit_success_image_pipeline.py` ya esta orientado a Decodo "standard" para discovery, no a un flujo JS/premium.
   - `fetch_decodo_api()` envia `proxy_pool: standard` y no agrega flags de render JS.
   - `fetch_rss()` solo usa Decodo primero si `DECODO_API_MODE` lo pide; si no, intenta directo/proxy antes de caer a Decodo.
   - Esto significa que el gasto premium no viene de un endpoint especial de Reddit, sino de cuantas llamadas haces y de si activas fallback innecesario.
   - Referencias: `scratch/reddit_success_image_pipeline.py:278-290`, `scratch/reddit_success_image_pipeline.py:391-418`.

2. `reddit_success_parallel_pipeline.py` hace una llamada extra por post con `fetch_post_score()`.
   - El `min-reddit-score` por defecto es `10`, asi que en discovery masivo se consulta `comments/<id>.json` para cada candidato.
   - Si esa llamada falla, puede caer a Decodo otra vez con `--score-decodo-fallback`.
   - Ese es el punto mas caro y el menos rentable para un barrido amplio.
   - Referencias: `scratch/reddit_success_parallel_pipeline.py:319-320`, `scratch/reddit_success_parallel_pipeline.py:402-406`, `scratch/reddit_success_image_pipeline.py:423-443`.

3. El modo actual de discovery es secuencial y con pausas amplias.
   - El loop va `subreddit -> query -> sort/time_window` en serie.
   - Entre rondas mete `sleep_min=1.5` y `sleep_max=4.0`, asi que el techo real queda muy por debajo de 10 req/s.
   - Hoy hay paralelismo solo despues del discovery, en el procesamiento de batch, no en la busqueda.
   - Referencias: `scratch/reddit_success_parallel_pipeline.py:288-292`, `scratch/reddit_success_parallel_pipeline.py:323-324`, `scratch/reddit_success_parallel_pipeline.py:362-419`.

4. La heuristica de likes/engagement se puede aproximar mejor con `sort=top` y ventanas temporales, no con score por post.
   - Ya existe `SEARCH_MODES` con `top/all`, `top/year`, `new/all`, `relevance/all`, `comments/all`.
   - Para un barrido masivo, `top` sobre varias ventanas es un proxy bastante bueno de engagement.
   - `relevance` y `comments` amplian costo con poco valor para esta tarea.
   - `self:no` ya esta aplicado por `media_first_query()`, asi que el barrido ya apunta a posts que no son self-posts.
   - Referencias: `scratch/reddit_success_parallel_pipeline.py:51-57`, `scratch/reddit_success_image_pipeline.py:139-142`.

## Recomendacion tecnica

La optimizacion mas segura es separar discovery de scoring y tratar el score de Reddit como enriquecimiento opcional, no como filtro obligatorio en el barrido.

### Fase 1: discovery barato y rapido
- Mantener `Decodo standard` y no activar JS/render premium.
- Usar solo discovery RSS con `sort=top` y ventanas `day/week/month/year` como proxy de likes.
- Eliminar `fetch_post_score()` del camino caliente.
- Dejar `--min-reddit-score` en `0` por defecto para discovery masivo.
- Si se necesita score, hacerlo luego sobre un subconjunto pequeno de candidatos.

### Fase 2: enriquecimiento selectivo
- Para los top N ya encontrados, ejecutar un pase aparte que si consulte score.
- Ese pase puede ser serial o con baja concurrencia, porque ya no afecta el throughput del descubrimiento.
- Si se quiere conservar el filtro, que sea opt-in con un flag explicito, no por defecto.

### Fase 3: paralelismo con rate limiter
- Introducir discovery concurrente con un `ThreadPoolExecutor` o cola de tareas para `(subreddit, query, sort, window)`.
- Usar un rate limiter global de aproximadamente 8-9 req/s para acercarse al limite de 10 req/s sin cruzarlo.
- Limitar inflight requests con un burst pequeno y reusar sesiones por hilo.
- Mantener reintentos cortos solo para 429 y errores transitorios.

## Cambios sugeridos, con write-set minimo

No hice patch de codigo, pero si se decide tocarlo, lo mas limpio seria:

1. Agregar flags no disruptivos a `scratch/reddit_success_parallel_pipeline.py`
   - `--skip-reddit-score`
   - `--discovery-workers`
   - `--discovery-rps`
   - `--discovery-burst`
   - `--discovery-modes top,top/year,top/month,top/week`

2. Cambiar el default de barrido masivo
   - `--min-reddit-score 0`
   - `--score-decodo-fallback` desactivado salvo pase de enriquecimiento

3. Si hace falta un cambio aun mas conservador
   - Crear un wrapper nuevo, por ejemplo `scratch/reddit_success_parallel_pipeline_fast.py`
   - Ese wrapper solo ajusta flags y la politica de discovery, sin tocar el pipeline original

## Riesgo y seguridad

- No hay riesgo de borrado de datos si se mantiene el write-set acotado a flags o a un wrapper nuevo.
- El cambio con mas retorno es quitar la llamada por post a `fetch_post_score()` del camino caliente.
- El segundo mayor retorno es paralelizar discovery con limite global, no procesar mas imagenes.
- No recomendaria activar nada "premium" para barrido masivo: el valor viene del volumen de discovery, no del render extra.

## Rollout recomendado

1. Ensayo corto con flags solamente
   - `--min-reddit-score 0`
   - `--score-decodo-fallback` apagado
   - `sort=top` prioritario
   - medir requests/seg y tasa de 429

2. Habilitar discovery concurrente limitado
   - subir workers gradualmente
   - fijar rate limiter en 8 req/s
   - validar que la calidad de candidatos no caiga

3. Si el rendimiento es estable, separar oficialmente discovery y enrichment
   - discovery rapido
   - score solo para candidatos finales

## Rutas

- [scratch/reddit_success_parallel_pipeline.py](<C:\desarrollos\Codex\Easy Date\scratch\reddit_success_parallel_pipeline.py>)
- [scratch/reddit_success_image_pipeline.py](<C:\desarrollos\Codex\Easy Date\scratch\reddit_success_image_pipeline.py>)
- [docs/qa_decodo_scraper_optimization_20260701_172955.md](<C:\desarrollos\Codex\Easy Date\docs\qa_decodo_scraper_optimization_20260701_172955.md>)
