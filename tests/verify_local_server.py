"""Smoke verification for the local Easy Date server.

Default behavior avoids live Gemini calls: /health is checked over HTTP, and
evaluate is exercised in-process with fake Gemini and Chroma dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class VerificationError(RuntimeError):
    pass


def load_json_url(url: str, timeout: float) -> dict[str, Any]:
    try:
        with urlopen(url, timeout=timeout) as response:
            status = getattr(response, "status", response.getcode())
            if status != 200:
                raise VerificationError(f"{url} returned HTTP {status}")
            raw = response.read().decode("utf-8")
    except URLError as exc:
        raise VerificationError(f"Cannot reach {url}: {exc}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise VerificationError(f"{url} did not return valid JSON: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def verify_health(base_url: str, timeout: float, min_keys: int) -> dict[str, Any]:
    health = load_json_url(f"{base_url}/health", timeout)

    require(health.get("status") == "ok", "/health status is not ok")
    require(health.get("simulator") == "simulador_v1.2.html", "/health reports the wrong simulator")
    require(health.get("simulator_exists") is True, "simulador_v1.2.html is not visible to the server")
    require(isinstance(health.get("gemini_keys_loaded"), int), "/health did not report a key count")
    require(
        health["gemini_keys_loaded"] >= min_keys,
        f"/health reports {health['gemini_keys_loaded']} Gemini keys, expected at least {min_keys}",
    )
    require(health.get("chroma_connected") is True, "ChromaDB is not connected")
    require(health.get("chroma_collection") == "natalia_conversations", "Unexpected Chroma collection")
    chroma_documents = health.get("chroma_documents")
    require(
        chroma_documents is None or isinstance(chroma_documents, int),
        "Chroma document count has an unexpected type",
    )

    return health


def verify_evaluate_without_quota() -> dict[str, Any]:
    from backend import server

    original_rotator = server.rotator
    original_chroma_collection = server.chroma_collection

    class FakeRotator:
        def generate_content(self, prompt: str) -> str:
            require("MENSAJE DEL USUARIO" in prompt, "Prompt did not include the user message block")
            require("caso local de prueba" in prompt, "Prompt did not include fake Chroma context")
            return json.dumps(
                {
                    "score": 8,
                    "feedback": "Claro y con buena energia.",
                    "suggestions": ["Sube un poco la curiosidad."],
                }
            )

    class FakeChromaCollection:
        name = "natalia_conversations"

        def query(self, query_texts: list[str], n_results: int) -> dict[str, list[list[str]]]:
            require(query_texts == ["Hola, me gusto hablar contigo."], "Unexpected Chroma query text")
            require(n_results == 3, "Unexpected Chroma result count")
            return {"documents": [["caso local de prueba"]]}

    try:
        server.rotator = FakeRotator()
        server.chroma_collection = FakeChromaCollection()
        response = server.evaluate(
            server.EvaluateRequest(
                level=1,
                history=[{"role": "assistant", "content": "Hola, como estas?"}],
                user_message="Hola, me gusto hablar contigo.",
            )
        )
    finally:
        server.rotator = original_rotator
        server.chroma_collection = original_chroma_collection

    require(response.score == 8, "Offline evaluate returned the wrong score")
    require(response.next_state == "WAITING_USER", "Offline evaluate returned the wrong next state")
    require(len(response.new_history) == 3, "Offline evaluate did not append the expected history")
    require("8/10" in response.evaluation, "Offline evaluate did not format the score")

    return {"score": response.score, "history_items": len(response.new_history)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the local Easy Date server without printing secrets.")
    parser.add_argument("--base-url", default=os.getenv("EASY_DATE_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--min-keys", type=int, default=int(os.getenv("EASY_DATE_MIN_KEYS", "1")))
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    try:
        health = verify_health(base_url, args.timeout, args.min_keys)
        evaluate = verify_evaluate_without_quota()
    except VerificationError as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 1

    print(
        "[ok] /health "
        f"simulator={health['simulator']} "
        f"keys_loaded={health['gemini_keys_loaded']} "
        f"chroma_connected={health['chroma_connected']} "
        f"chroma_documents={health['chroma_documents'] if health['chroma_documents'] is not None else 'unknown'}"
    )
    print(
        "[ok] /api/evaluate offline "
        f"score={evaluate['score']} "
        f"history_items={evaluate['history_items']} "
        "quota_used=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
