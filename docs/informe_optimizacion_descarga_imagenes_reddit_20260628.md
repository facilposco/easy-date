# Informe: optimizacion de descarga de imagenes Reddit

Fecha local: 2026-06-28

## Cambios aplicados

- Se detuvo la corrida anterior para evitar gasto de proxy mientras se optimizaba.
- Se actualizo `scratch/descargar_imagenes_reddit.py`.
- Se mantiene la carpeta destino unica: `imagenes`.
- Se agrego manifiesto persistente: `docs/imagenes_reddit_manifest.json`.

## Optimizaciones de proxy

- Reutilizacion local: si una imagen ya existe en `imagenes` y PIL la valida, no se consulta red ni proxy.
- Manifiesto por URL: si la misma URL ya fue descargada y validada, se copia localmente en lugar de descargar otra vez.
- Descarga directa primero: el script intenta bajar desde `i.redd.it` o `i.imgur.com` sin proxy.
- Fallback a DataImpulse: solo usa proxy si la descarga directa falla.
- Consumo proxy auditable: el CSV separa `source` y `proxy_estimated_mb`.
- Limite maximo por imagen: `--max-mb 12` corta imagenes demasiado grandes antes de seguir gastando.
- Reintentos limitados: los reintentos se mantienen controlados para no multiplicar trafico.

## Prueba de optimizacion

Prueba ejecutada con 20 imagenes:

- 18 imagenes ya existentes: `skipped_existing_verified`.
- 2 imagenes nuevas: `downloaded_verified`.
- Source de nuevas imagenes: `direct`.
- Consumo proxy estimado: `0.000 MB`.
- Ahorro estimado por descarga directa: `0.312 MB`.
- Targets faltantes: `0`.

## Sobre descargar en formato mas liviano

Convertir la imagen despues de descargarla no ahorra proxy, porque el proxy ya transfirio la imagen original.

Opciones reales:

- Usar thumbnails/previews del origen: puede ahorrar proxy, pero baja la calidad y puede danar OCR.
- Usar original para OCR y crear preview local comprimida para HTML: no ahorra proxy, pero si ahorra disco/carga visual.
- Usar `--prefer-imgur-thumbnail`: queda disponible solo para Imgur y desactivado por defecto, porque puede perder texto legible.

Decision recomendada:

- Para OCR y auditoria: mantener imagen original.
- Para visualizacion HTML: generar previews locales despues de descargar, si hace falta.

## Corrida completa optimizada activa

- PID: `15036`
- Script: `scratch/descargar_imagenes_reddit.py`
- Carpeta: `imagenes`
- CSV: `docs/imagenes_reddit_full_opt_20260628_092803.csv`
- Resumen: `docs/imagenes_reddit_full_opt_20260628_092803_summary.md`
- stdout: `docs/imagenes_reddit_full_opt_20260628_092803.stdout.log`
- stderr: `docs/imagenes_reddit_full_opt_20260628_092803.stderr.log`
- Manifiesto: `docs/imagenes_reddit_manifest.json`

La automatizacion de status cada 10 minutos fue actualizada para monitorear esta corrida.

