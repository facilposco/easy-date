# Informe: modo escritura del simulador

Fecha local: 2026-06-28

## Problema observado

En `simulador_v1.2.html` el usuario no podia escribir una respuesta libre. La pantalla mostraba solo opciones A/B/C/D.

## Causa

La version anterior habia dejado el Nivel 1 en modo guiado para evitar incoherencias entre texto libre y guion fijo.

## Cambio aplicado

- Se agrego `replyMode` al estado del juego.
- El modo predeterminado ahora es `free`.
- La pantalla principal muestra un textarea para escribir como en Tinder.
- Se agrego conmutador:
  - `Escribir`
  - `Opciones`
- El modo de opciones sigue disponible para practica guiada y depuracion.
- El textarea se bloquea cuando abre el modal del Coach.
- Se puede enviar desde el textarea con `Ctrl+Enter`.

## Archivos modificados

- `build_simulator.py`
- `simulador_v1.2.html`
- `tests/test_simulator_level1.py`

## Verificacion

- `python build_simulator.py`
- `python -m py_compile build_simulator.py tests/test_simulator_level1.py`
- `node --check scratch/simulator_embedded.js`
- `pytest -q tests/test_simulator_level1.py -rs`
- Prueba en navegador via `http://127.0.0.1:8765/simulador_v1.2.html`

Resultado:

- Textarea visible.
- Modo `Escribir` activo.
- Modo `Opciones` oculto por defecto.
- Happy path Nivel 1 completo escribiendo respuestas: 10/10 pasos, Level Up visible, Coach cerrado.

