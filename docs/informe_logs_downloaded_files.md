# Informe de logs: `downloaded_files`

Fecha: 2026-06-28

## Pregunta

Determinar si Windows o los logs del scraper muestran que la carpeta `downloaded_files/` se creo o se borro.

## Estado actual

Ruta revisada:

```text
C:\desarrollos\Codex\Easy Date\downloaded_files
```

Resultado actual:

```text
No existe
```

## Logs propios del downloader

Archivos revisados:

- `docs/reddit_image_recovery_dataimpulse.csv`
- `docs/reddit_image_recovery_dataimpulse_summary.md`

Resumen del CSV:

| Metrica | Valor |
|---|---:|
| Filas CSV | 245 |
| `downloaded` | 243 |
| `skipped_existing` | 2 |
| Primera descarga registrada | 2026-06-28T11:29:52.374560+00:00 |
| Ultima descarga registrada | 2026-06-28T12:03:37.075049+00:00 |

Primera fila:

```text
post_id: epxvl5
target: downloaded_files/post_epxvl5/img_1.jpg
status: downloaded
bytes: 120898
```

Ultima fila:

```text
post_id: un92gc
target: downloaded_files/post_un92gc/img_1.jpg
status: downloaded
bytes: 83234
```

Interpretacion: el script registro `downloaded` despues de escribir bytes en disco. Por log interno, la descarga se considero exitosa.

## Evidencia intermedia observada durante la ejecucion

Durante la ejecucion se hizo un corte de estado y se observo:

```text
rows CSV: 198
downloaded_files_exists: True
files: 196
```

Interpretacion: en algun momento de la corrida la carpeta si existio fisicamente en el entorno donde se ejecuto ese conteo.

## Windows Event Log

Se revisaron eventos de Windows alrededor de la ventana de descarga:

- Security: eventos 4663, 4660, 4656, 4662
- Security: proceso 4688
- Microsoft-Windows-PowerShell/Operational
- Papelera de reciclaje
- Historial PSReadLine

Resultado:

| Fuente | Resultado |
|---|---|
| Security 4663/4660/4656/4662 | Sin eventos coincidentes |
| Security 4688 | Sin eventos coincidentes |
| PowerShell Operational | No muestra un comando de borrado de `downloaded_files`; solo aparecen consultas posteriores de auditoria |
| PSReadLine history | No aparece `Remove-Item downloaded_files`, `rmdir downloaded_files` ni equivalente |
| Papelera de reciclaje | No se encontro `downloaded_files` |

Limitacion: Windows solo registra creacion/borrado de archivos en Security si la auditoria de objetos estaba activada previamente. En este equipo no aparecieron eventos de auditoria de archivo para esa ruta.

## Conclusion

No hay evidencia en los logs de Windows ni en el historial visible de PowerShell de que alguien haya borrado explicitamente `downloaded_files`.

Si hay evidencia de que:

1. El script registro descargas exitosas.
2. En un corte intermedio la carpeta existia y tenia archivos.
3. Actualmente la carpeta no existe en el workspace principal.

Hipotesis mas probables:

1. La descarga o parte de la ejecucion ocurrio en un contexto/fork/sesion no persistente.
2. Los archivos binarios no se sincronizaron al workspace principal aunque los reportes de texto si quedaron.
3. Hubo limpieza externa no registrada por Windows Event Log, por falta de auditoria de filesystem.

## Recomendacion

Relanzar la recuperacion directamente en el workspace principal y agregar una verificacion fisica final obligatoria:

```text
downloaded_files existe
243 archivos fisicos
14 carruseles completos
46 imagenes de carrusel presentes
```

Adicionalmente, el nuevo script/reporte debe escribir un resumen post-descarga que cuente archivos fisicos desde disco, no solo filas del CSV.
