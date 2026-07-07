# Informe de mejoras del simulador Nivel 1 - 2026-06-28

## Cambios aplicados

- Se corrigio el cierre del modal del Coach:
  - El boton `ENTENDIDO` ahora cierra de forma robusta.
  - Tambien cierra con `Enter`, `Espacio` o `Escape`.
  - El callback se protege contra doble ejecucion.

- Se bloqueo la UI detras del modal:
  - Mientras el Coach esta abierto, opciones, slider, enviar y reiniciar quedan deshabilitados.
  - Al cerrar el Coach, el flujo desbloquea controles solo si no hay modal de Game Over o Level Up.

- Se sincronizo la evaluacion con el paso actual:
  - Cada evaluacion captura `level_index`, `step_index` y `step_id`.
  - Si el estado cambia antes del cierre del Coach, no se avanza un paso incorrecto.

- Se decidio el modo actual del simulador:
  - Queda como `modo guiado`.
  - La ayuda del juego ahora aclara que se elige la mejor respuesta para el paso visible.

- Se cambio el progreso visible:
  - Antes: `Natalia (7/10)`.
  - Ahora: `Nivel 1 · Paso 7 de 10`.

- Se corrigio encoding/mojibake al compilar:
  - El compilador repara textos tipo `dÃ­a`, `nÃºmero`, `quÃ©`, `Â¿`, `Â¡` y emojis mojibake.
  - La reparacion se aplica al JSON de juego y al HTML final generado.

- Se hizo mas accionable el feedback del Coach:
  - Calidad del mensaje.
  - Contexto de la conversacion/timing.
  - Objetivo del paso.

- Se agrego modo de prueba de Nivel 1:
  - `window.easyDateTest.runLevel1HappyPath()`.
  - Recorre automaticamente los 10 pasos con respuestas correctas.
  - Verifica que el Coach abra/cierre y que aparezca Level Up.

## Archivos modificados

- `build_simulator.py`
- `simulador_v1.2.html`
- `tests/test_simulator_level1.py`

## Verificacion

- `python -m py_compile build_simulator.py tests\test_simulator_level1.py`
- `node --check scratch\simulator_embedded.js`
- `pytest -q tests\test_simulator_level1.py -rs`
- `pytest -q`

Resultado final:

- `6 passed`
- `3 warnings` preexistentes/no bloqueantes

## Nota de descarga en paralelo

La descarga completa de imagenes Reddit sigue corriendo en segundo plano con DataImpulse. En el ultimo status observado:

- Proceso activo: `PID 3076`
- CSV activo: `docs\reddit_image_recovery_full_20260628_084038.csv`
- Estados: `150 downloaded`, `10 skipped_existing`
- Total esperado: `243`

