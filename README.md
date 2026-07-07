# Easy Date

Servidor local del simulador `simulador_v1.2.html`.

## Arranque local

```powershell
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000
```

URLs principales:

- `http://localhost:8000/`
- `http://localhost:8000/simulador_v1.2.html`
- `http://localhost:8000/health`
- `http://localhost:8000/api/evaluate`

## Verificacion reproducible

Con el servidor corriendo en `http://localhost:8000`:

```powershell
python tests\verify_local_server.py
```

La verificacion comprueba:

- `/health` por HTTP real contra el servidor local.
- `simulador_v1.2.html` como simulador principal.
- Cantidad de llaves Gemini cargadas, solo por conteo.
- Conexion a ChromaDB, coleccion `natalia_conversations` y conteo de documentos cuando el servidor lo expone.
- Flujo de `/api/evaluate` sin consumir cuota: se ejecuta en proceso con Gemini y Chroma reemplazados por fakes.

El script no imprime secretos y no conecta el RAC/RAG de libros. Si el servidor usa otra URL:

```powershell
python tests\verify_local_server.py --base-url http://localhost:8000
```
