# Auditoria del scraper de imagenes Reddit - 2026-06-28

## Objetivo

Revisar si el codigo del scraping puede borrar la carpeta de imagenes y preparar una prueba controlada de 10 imagenes en disco D.

## Resultado corto

No encontre una instruccion que borre `downloaded_files` ni en el proyecto principal (`C:\desarrollos\Codex\Easy Date`) ni en la copia de Anti-Gravity (`C:\desarrollos\antigravity\Easy Date`).

Si hay un riesgo real: el scraper original guarda imagenes usando rutas relativas. Eso puede hacer que las imagenes se descarguen en otro directorio de trabajo si el script se ejecuta desde otra terminal, agente, carpeta o sesion.

## Hallazgos

### 1. No hay borrado directo de `downloaded_files`

Busqueda realizada sobre ambos proyectos con patrones:

- `Remove-Item`
- `rm`
- `rmdir`
- `del`
- `delete`
- `unlink`
- `shutil.rmtree`
- `os.remove`
- `downloaded_files`

Coincidencia relevante encontrada:

- `reddit_bulk_scraper.py:64` ejecuta `os.remove("scraper_log.txt")`.

Eso solo borra el log del scraper, no la carpeta de imagenes.

### 2. Riesgo principal: rutas relativas

En `reddit_bulk_scraper.py`:

- `os.makedirs("downloaded_files", exist_ok=True)`
- `folder = f"downloaded_files/post_{post_id}"`
- `with urllib.request.urlopen(...), open(filepath, "wb") as f:`

Estas rutas dependen del directorio desde donde se lance Python. Si el proceso se ejecuta desde otra carpeta, la carpeta `downloaded_files` se crea alla, no necesariamente dentro de `C:\desarrollos\Codex\Easy Date`.

La copia de Anti-Gravity tiene el mismo patron.

### 3. El recuperador DataImpulse es mas seguro

En `scratch\recover_reddit_images_dataimpulse.py`:

- `ROOT = Path(__file__).resolve().parents[1]`
- `OUT_ROOT = ROOT / "downloaded_files"`
- `target.write_bytes(response.content)`

Este script si fija el destino al proyecto, independientemente del directorio desde donde se lance.

No encontre borrado de archivos en este script.

### 4. La carpeta existe ahora, pero esta vacia

Estado actual:

- `C:\desarrollos\Codex\Easy Date\downloaded_files`
- Archivos actuales: `0`

Nota: esta carpeta fue creada/asegurada al activar la auditoria de filesystem de Windows, por eso su existencia actual no prueba que contenga las imagenes recuperadas antes.

### 5. Disco D no esta montado

Windows reporta actualmente solo la unidad `C:\`.

Comprobacion:

- `Test-Path D:\` => `False`
- `Get-PSDrive -PSProvider FileSystem` => solo aparece `C:`

Por eso todavia no puedo ejecutar una prueba honesta de 10 imagenes en `D:\`.

## Hipotesis mas probable

La evidencia apunta mas a un problema de persistencia/ruta que a un borrado explicito:

1. El scraper original pudo guardar en un `downloaded_files` relativo a otra carpeta.
2. Un agente o sesion pudo ejecutar el script con un `cwd` distinto.
3. El CSV de descarga pudo quedar en el proyecto, pero las imagenes pudieron quedar en otro contexto de ejecucion.
4. Windows no tenia auditoria de filesystem activa antes, asi que no hay rastro historico confiable de creacion/borrado.

## Recomendacion senior

Antes de otro escaneo grande:

1. Convertir todo scraper a rutas absolutas basadas en `PROJECT_ROOT`.
2. Agregar parametro obligatorio `--output-root`, por ejemplo `D:\EasyDateRedditImages`.
3. Registrar por cada imagen: ruta absoluta, bytes, sha256, http_status y timestamp.
4. Al finalizar, hacer verificacion fisica: contar archivos reales en disco y comparar contra el CSV.
5. Bloquear ejecucion si el destino no existe o no esta en el disco esperado.

## Bloqueo actual

Inicialmente la prueba de 10 imagenes quedo pendiente porque `D:\` no existe/monta en este Windows en este momento.

El usuario confirmo que este equipo solo tiene una particion `C:\`. Por eso se ejecuto una prueba controlada en:

`C:\desarrollos\Codex\Easy Date\downloaded_files_test10`

## Actualizacion: prueba de 10 imagenes en C

Se ejecuto una descarga controlada de 10 imagenes con DataImpulse.

Resultado:

- Descargas reportadas por CSV: `10 downloaded`
- Archivos fisicos encontrados: `10`
- Imagenes legibles por Windows/.NET: `10`
- Archivos vacios: `0`
- Caso multi-imagen cubierto: `post_ifdzv2` con `img_1.jpg`, `img_2.jpg`, `img_3.jpg`

Rutas de revision:

- Imagenes: `C:\desarrollos\Codex\Easy Date\downloaded_files_test10`
- CSV de descarga: `docs\reddit_image_recovery_test10_forced_dataimpulse.csv`
- Resumen: `docs\reddit_image_recovery_test10_forced_dataimpulse_summary.md`
- Manifest con hashes SHA256: `docs\reddit_image_recovery_test10_manifest.csv`
- Verificacion de dimensiones/lectura: `docs\reddit_image_recovery_test10_image_check.csv`

## Bug confirmado y corregido

Durante la primera prueba, el parametro `--output-root` no fue suficiente porque el script priorizaba `local_image_paths` historicos de la DB. Eso hizo que las imagenes se guardaran en:

`C:\desarrollos\Codex\Easy Date\downloaded_files`

Aunque se habia pedido:

`C:\desarrollos\Codex\Easy Date\downloaded_files_test10`

Se corrigio `scratch\recover_reddit_images_dataimpulse.py` agregando el flag:

`--ignore-db-local-paths`

Con ese flag, el recuperador fuerza la carpeta indicada en `--output-root` y ya no usa las rutas historicas de la DB para esa corrida.
