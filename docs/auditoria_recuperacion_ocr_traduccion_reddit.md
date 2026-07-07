# Auditoria de recuperacion, OCR y traduccion Reddit

Fecha: 2026-06-28

## Resultado ejecutivo

La auditoria NO aprueba todavia la recuperacion completa de imagenes en el workspace principal.

Aunque `docs/reddit_image_recovery_dataimpulse.csv` y `docs/reddit_image_recovery_dataimpulse_summary.md` registran descargas exitosas, la carpeta fisica `downloaded_files/` no existe actualmente en `C:\desarrollos\Codex\Easy Date`.

Esto significa que el reporte de descarga y la realidad del filesystem no coinciden.

## 1. Donde se guardaron

Segun el script y el CSV, las imagenes debian guardarse en:

```text
C:\desarrollos\Codex\Easy Date\downloaded_files\post_<post_id>\img_N.jpg
```

Evidencia documental:

- `docs/reddit_image_recovery_dataimpulse.csv`
- `docs/reddit_image_recovery_dataimpulse_summary.md`

Estado fisico verificado:

| Ruta | Estado |
|---|---|
| `downloaded_files/` | No existe en el workspace principal |
| `docs/prueba_assets/` | Existe, 26 imagenes de muestra |
| `prueba_assets/` | Existe, 26 imagenes de muestra |

Conclusion: las imagenes completas no estan disponibles actualmente en el workspace principal, aunque el CSV diga que fueron descargadas.

## 2. Carruseles / posts con mas de una imagen

SQLite contiene 14 posts tipo `carousel`, con 46 imagenes esperadas.

| DB ID | post_id | perfil | imagenes esperadas | imagenes encontradas en `downloaded_files` |
|---:|---|---|---:|---:|
| 8 | ifdzv2 | indecisa | 6 | 0 |
| 14 | t7t11y | defensiva | 6 | 0 |
| 38 | pejv1m | defensiva | 2 | 0 |
| 41 | vqamjj | indecisa | 6 | 0 |
| 88 | ria49q | indecisa | 2 | 0 |
| 89 | u2iitz | indecisa | 3 | 0 |
| 90 | wcp9zp | defensiva | 2 | 0 |
| 93 | sb1orq | defensiva | 3 | 0 |
| 147 | wwdac2 | defensiva | 2 | 0 |
| 148 | sos3u8 | defensiva | 3 | 0 |
| 152 | qa677y | coqueta | 4 | 0 |
| 174 | qkq1d6 | desinteresada | 2 | 0 |
| 175 | s3f0w8 | indecisa | 2 | 0 |
| 181 | plvqb2 | indecisa | 3 | 0 |

Conclusion: no se puede aprobar que todos los carruseles esten recuperados hasta que `downloaded_files/` exista y contenga las 46 imagenes esperadas.

## 3. OCR vs transcripcion guardada en DB

Estado de SQLite:

| Metrica | Conteo |
|---|---:|
| Conversaciones con imagenes | 211 |
| Imagenes esperadas desde `image_urls` | 243 |
| Filas con `transcription_text` | 211 |
| Filas con `transcription_json` | 211 |
| Filas con mensajes estructurados utiles | 169 |
| Filas OCR no vectorizables / sin mensajes utiles | 42 |

El OCR guardado en DB existe para las 211 conversaciones con imagenes.

Limitacion de auditoria:

- No hay `downloaded_files/` fisico para comparar imagen por imagen.
- No hay motor OCR local instalado (`tesseract.exe`, `pytesseract` y `easyocr` no estan disponibles).

Conclusion: se puede afirmar que la DB conserva OCR/transcripcion, pero NO se puede certificar por re-OCR local que cada imagen recuperada coincide con la transcripcion hasta restaurar las imagenes y tener un motor OCR o una verificacion visual/LLM controlada.

## 4. Traduccion al espanol latino

La DB no esta completamente normalizada al espanol latino.

Heuristica sobre `transcription_json`:

| Categoria aproximada | Conteo |
|---|---:|
| Mayormente espanol | 23 |
| Mayormente ingles | 114 |
| Mixto o poco claro | 74 |

Observaciones:

- Muchos casos conservan labels o mensajes en ingles (`Girl`, `Guy`, `Him`, `Her`, etc.).
- Algunos textos estan traducidos al espanol, pero no todos tienen gramatica natural latinoamericana.
- Algunos casos tienen contenido mixto: titulo en ingles, mensajes parcialmente traducidos, o estructuras OCR pobres.

Estado del HTML de muestra `docs/prueba.html`:

| Metrica | Resultado |
|---|---:|
| Casos incluidos | 10 |
| Secciones traducidas | 10 |
| Carruseles incluidos | 5 |
| Imagenes locales de muestra | 26 |
| Marcas de codificacion rota visibles (`T?TULO`, `TRANSCRIPCI?N`) | presentes |

Conclusion: la muestra `docs/prueba.html` es util para inspeccion, pero no esta lista como entrega final pulida. Requiere normalizacion de encoding, titulos y espanol latino.

## 5. Riesgos

1. El CSV puede estar registrando descargas que ocurrieron en otro contexto/fork o que no quedaron en el filesystem actual.
2. `AGENTS.md` y `arquitectura.html` pueden haber quedado demasiado optimistas si dicen que la recuperacion fisica ya esta completa.
3. La DB tiene OCR, pero la trazabilidad visual completa necesita las imagenes.
4. La traduccion al espanol latino no esta normalizada en toda la base.

## 6. Recomendaciones

1. No dar por recuperadas las imagenes hasta que exista `downloaded_files/` en el workspace principal.
2. Relanzar el downloader en el workspace principal o recuperar los artefactos reales del subagente/fork.
3. Despues de recuperar imagenes, verificar:
   - 243 imagenes fisicas.
   - 14 carruseles completos.
   - 46 imagenes de carrusel presentes.
4. Instalar o habilitar un OCR local para auditoria:
   - Tesseract + `pytesseract`, o
   - EasyOCR, o
   - auditoria visual/LLM por muestra controlada.
5. Crear un proceso de normalizacion de traduccion:
   - labels: `Hombre`, `Mujer`, `Yo`, nombre propio.
   - espanol latino natural.
   - correccion de encoding.
   - conservar tiempos solo si existen.
6. Regenerar `docs/prueba.html` despues de normalizar traducciones.

## 7. Veredicto

| Area | Estado |
|---|---|
| Registro CSV de descarga | Aprobado documentalmente |
| Archivos fisicos completos | No aprobado |
| Carruseles completos | No aprobado |
| OCR existente en DB | Aprobado |
| OCR verificado contra imagen | No verificable aun |
| Traduccion espanol latino DB completa | No aprobado |
| HTML de muestra | Util, pero requiere limpieza |
