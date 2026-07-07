import itertools
import json
import os
import queue
import re
import sqlite3
import threading
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

try:
    from google import genai as google_genai
    from google.genai import types as google_genai_types
except Exception:
    google_genai = None
    google_genai_types = None

if google_genai is None:
    try:
        import google.generativeai as legacy_genai
    except Exception:
        legacy_genai = None
else:
    legacy_genai = None

try:
    from google.api_core import exceptions as google_api_exceptions
except Exception:
    google_api_exceptions = None

try:
    from ftfy import fix_text as ftfy_fix_text
except Exception:
    ftfy_fix_text = None


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
SIMULATOR_PATH = ROOT_DIR / "simulador_v1.2.html"
LEVELS_PATH = ROOT_DIR / "backend" / "levels_config.json"
CHROMA_PATH = ROOT_DIR / "chroma_db"
BOOKS_CHROMA_PATH = ROOT_DIR / "books_kb" / "chroma_books"
DB_PATH = ROOT_DIR / "textgame.db"
SUCCESS_COLLECTION_NAME = "natalia_success_cases"
NEGATIVE_COLLECTION_NAME = "natalia_negative_cases"
BOOKS_COLLECTION_NAME = "natalia_books_kb"
BOOK_CONVERSATIONS_COLLECTION_NAME = "natalia_conversations"
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
DEFAULT_GEMINI_MODEL_FALLBACKS = "gemini-2.5-flash-lite,gemini-3.1-flash-lite"
try:
    GEMINI_CALL_TIMEOUT_MS = max(10000, int(os.getenv("GEMINI_CALL_TIMEOUT_MS", "12000")))
except ValueError:
    GEMINI_CALL_TIMEOUT_MS = 12000
try:
    GEMINI_HARD_TIMEOUT_SECONDS = max(1, int(os.getenv("GEMINI_HARD_TIMEOUT_SECONDS", "10")))
except ValueError:
    GEMINI_HARD_TIMEOUT_SECONDS = 10
GEMINI_HARD_TIMEOUT_SECONDS = max(
    GEMINI_HARD_TIMEOUT_SECONDS,
    (GEMINI_CALL_TIMEOUT_MS + 999) // 1000 + 5,
)


def clean_ui_text(value: Any) -> str:
    text = str(value or "").strip()
    if ftfy_fix_text:
        for _ in range(3):
            try:
                fixed = ftfy_fix_text(text)
            except Exception:
                break
            if fixed == text:
                break
            text = fixed
    return text.strip()


def analysis_text(value: Any) -> str:
    text = clean_ui_text(value).lower()
    text = "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )
    replacements = {
        "qu?": "que",
        "c?mo": "como",
        "d?nde": "donde",
        "cu?ndo": "cuando",
        "m?sica": "musica",
        "canci?n": "cancion",
        "bogot?": "bogota",
        "presi?n": "presion",
        "qu?mica": "quimica",
        "t?": "tu",
        "m?s": "mas",
        "tambi?n": "tambien",
        "entren?": "entrene",
        "p?same": "pasame",
        "c?moda": "comoda",
    }
    for broken, fixed in replacements.items():
        text = text.replace(broken, fixed)
    return text


PHONE_NUMBER_RE = re.compile(r"(?:\+\d{1,3}[\s.-]*)?(?:\(?\d{2,4}\)?[\s.-]*){2,}\d{2,4}")


def contains_phone_number(text: Any) -> bool:
    return bool(PHONE_NUMBER_RE.search(str(text or "")))


def gemini_live_enabled() -> bool:
    value = os.getenv("GEMINI_LIVE_ENABLED", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def gemini_coach_enabled() -> bool:
    value = os.getenv("GEMINI_COACH_ENABLED", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def chroma_query_enabled() -> bool:
    value = os.getenv("CHROMA_QUERY_ENABLED", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}

LEVEL_BEHAVIOR = {
    1: {
        "name": "Natalia",
        "profile": "coqueta",
        "difficulty": "facil",
        "lives": 4,
        "receptivity": 0.78,
        "selectivity": 0.25,
        "style": "calida, juguetona, curiosa, frases cortas, tolera errores leves",
        "reply_length": "1 frase corta o 2 mensajes cortos",
        "location_area": "Brickell",
        "work_hint": "marketing visual para restaurantes",
        "off_mode": "planes tranquilos y musica sin ponerse intensa",
    },
    2: {
        "name": "Sofia",
        "profile": "indecisa",
        "difficulty": "media",
        "lives": 3,
        "receptivity": 0.55,
        "selectivity": 0.50,
        "style": "coqueta si hay chispa, pero pierde interes con mensajes genericos",
        "reply_length": "1-2 frases",
        "location_area": "Downtown",
        "work_hint": "eventos y redes sociales",
        "off_mode": "cafes buenos y planes sin demasiado ruido",
    },
    3: {
        "name": "Valentina",
        "profile": "alta_selectividad",
        "difficulty": "dificil",
        "lives": 2,
        "receptivity": 0.35,
        "selectivity": 0.78,
        "style": "selectiva, breve, con muchos matches, lanza pruebas suaves",
        "reply_length": "muy breve",
        "location_area": "zona centro",
        "work_hint": "marca personal y contenido",
        "off_mode": "planes bien elegidos, sin improvisacion torpe",
    },
    4: {
        "name": "Isabella",
        "profile": "defensiva",
        "difficulty": "muy dificil",
        "lives": 1,
        "receptivity": 0.18,
        "selectivity": 0.92,
        "style": "muy selectiva, defensiva, poco paciente, prueba el marco del usuario",
        "reply_length": "seca y breve",
        "location_area": "zona privada",
        "work_hint": "moda y produccion",
        "off_mode": "planes seguros, discretos y bien pensados",
    },
}


def load_env_lenient(path: Path) -> None:
    """Load KEY=value lines and ignore malformed legacy notes in .env."""
    if not path.exists():
        return

    key_pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key_pattern.match(key):
            continue

        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_env_lenient(ENV_PATH)

app = FastAPI(title="Easy Date Simulator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EvaluateRequest(BaseModel):
    level: Any
    history: List[Dict[str, str]]
    user_message: str


class EvaluateResponse(BaseModel):
    evaluation: str
    score: int = 5
    next_state: str
    new_history: List[Dict[str, str]]


class SimulateTurnRequest(BaseModel):
    level: int = 1
    step_index: int = 0
    evaluated_step_id: Optional[Any] = None
    lives: int = 4
    attraction: int = 50
    history: List[Dict[str, Any]] = []
    user_message: str
    chosen_time: str = ""
    visible_context: Dict[str, Any] = {}


class SimulateTurnResponse(BaseModel):
    natalia_message: str
    natalia_time: str = "TardÃ³: 15 min"
    coach_title: str
    coach_feedback: str
    score: int
    lose_life: bool
    attraction_delta: int
    suggestions: List[str] = []
    retrieved_cases: List[Dict[str, str]] = []
    retrieval_summary: Dict[str, Any] = {}
    fallback: bool = False
    turn_analysis: Dict[str, Any] = {}
    turn_metrics: Dict[str, Any] = {}


def collect_gemini_keys() -> List[str]:
    keys: List[str] = []
    seen = set()

    for idx in range(1, 10):
        value = os.getenv(f"GEMINI_API_KEY_{idx}", "").strip()
        if value and value not in seen:
            keys.append(value)
            seen.add(value)

    value = os.getenv("GEMINI_API_KEY", "").strip()
    if value and value not in seen:
        keys.append(value)

    return keys


def gemini_model_candidates() -> List[str]:
    values = [MODEL_NAME]
    raw_fallbacks = os.getenv("GEMINI_MODEL_FALLBACKS", DEFAULT_GEMINI_MODEL_FALLBACKS)
    values.extend(part.strip() for part in raw_fallbacks.split(",") if part.strip())
    candidates: List[str] = []
    seen = set()
    for value in values:
        if value and value not in seen:
            candidates.append(value)
            seen.add(value)
    return candidates


class GeminiRotator:
    def __init__(self) -> None:
        self.api_keys = collect_gemini_keys()
        self.keys_cycle = itertools.cycle(self.api_keys) if self.api_keys else None
        self.current_key = None
        self.client = None
        self.model = None
        self.active_model_name = MODEL_NAME
        self.quota_cooldown_until = 0.0
        try:
            self.quota_cooldown_seconds = max(
                0,
                int(os.getenv("GEMINI_QUOTA_COOLDOWN_SECONDS", "120")),
            )
        except ValueError:
            self.quota_cooldown_seconds = 120
        self.sdk_name = self._select_sdk()

        if not self.sdk_name:
            print("WARNING: No Gemini SDK is installed. Install google-genai.")
        elif not gemini_live_enabled():
            print("WARNING: Gemini live calls are disabled; using local fallback.")
        elif self.api_keys:
            self.rotate_key(log=False)
        else:
            print("WARNING: No Gemini API keys were loaded from .env")

    def _select_sdk(self) -> Optional[str]:
        if google_genai is not None:
            return "google-genai"
        if legacy_genai is not None:
            return "google-generativeai"
        return None

    def rotate_key(self, log: bool = True) -> None:
        if not self.keys_cycle:
            raise HTTPException(status_code=503, detail="No Gemini API keys configured.")
        if not self.sdk_name:
            raise HTTPException(status_code=503, detail="No Gemini SDK installed.")

        self.current_key = next(self.keys_cycle)
        if self.sdk_name == "google-genai":
            http_options = (
                google_genai_types.HttpOptions(timeout=GEMINI_CALL_TIMEOUT_MS)
                if google_genai_types is not None
                else {"timeout": GEMINI_CALL_TIMEOUT_MS}
            )
            self.client = google_genai.Client(api_key=self.current_key, http_options=http_options)
            self.model = None
        else:
            legacy_genai.configure(api_key=self.current_key)
            self.model = legacy_genai.GenerativeModel(self.active_model_name)
            self.client = None
        if log:
            print("[Rotator] Switched to next Gemini API key.")

    def _status_code(self, exc: Exception) -> Optional[int]:
        if google_api_exceptions is not None and isinstance(
            exc, google_api_exceptions.ResourceExhausted
        ):
            return 429

        for attr in ("code", "status_code", "status"):
            value = getattr(exc, attr, None)
            if callable(value):
                try:
                    value = value()
                except Exception:
                    value = None
            if isinstance(value, int):
                return value
            if hasattr(value, "value"):
                value = value.value
                if isinstance(value, tuple) and value:
                    return int(value[0])
                if isinstance(value, int):
                    return value
            if isinstance(value, str) and value.isdigit():
                return int(value)

        match = re.search(r"\b(429|5\d{2})\b", str(exc))
        return int(match.group(1)) if match else None

    def _is_retryable(self, exc: Exception) -> bool:
        status_code = self._status_code(exc)
        return status_code == 429 or (status_code is not None and 500 <= status_code <= 599)

    def _quota_cooldown_remaining(self) -> float:
        return max(0.0, self.quota_cooldown_until - time.monotonic())

    def _start_quota_cooldown(self) -> None:
        if self.quota_cooldown_seconds <= 0:
            return
        self.quota_cooldown_until = time.monotonic() + self.quota_cooldown_seconds
        print(f"[Rotator] Gemini cooldown active for {self.quota_cooldown_seconds}s.")

    def _generate_content_once(self, prompt: str, model_name: str) -> str:
        if self.client is None and self.model is None:
            self.rotate_key(log=False)
        self.active_model_name = model_name

        if self.sdk_name == "google-genai":
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
        else:
            self.model = legacy_genai.GenerativeModel(model_name)
            response = self.model.generate_content(prompt)

        text = getattr(response, "text", None)
        if text is None:
            raise HTTPException(status_code=502, detail="Gemini API returned no text.")
        return text

    def _generate_content_with_timeout(self, prompt: str, model_name: str) -> str:
        result_queue: "queue.Queue[tuple[bool, Any]]" = queue.Queue(maxsize=1)

        def run_request() -> None:
            try:
                result_queue.put((True, self._generate_content_once(prompt, model_name)))
            except Exception as exc:
                result_queue.put((False, exc))

        worker = threading.Thread(target=run_request, daemon=True)
        worker.start()
        worker.join(GEMINI_HARD_TIMEOUT_SECONDS)
        if worker.is_alive():
            raise TimeoutError(f"Gemini call timed out after {GEMINI_HARD_TIMEOUT_SECONDS}s.")

        ok, value = result_queue.get_nowait()
        if ok:
            return str(value)
        raise value

    def generate_content(self, prompt: str) -> str:
        if not self.api_keys:
            raise HTTPException(status_code=503, detail="No Gemini API keys configured.")
        if not self.sdk_name:
            raise HTTPException(status_code=503, detail="No Gemini SDK installed.")
        if not gemini_live_enabled():
            raise HTTPException(status_code=503, detail="Gemini live calls disabled; using local fallback.")
        cooldown_remaining = self._quota_cooldown_remaining()
        if cooldown_remaining > 0:
            raise HTTPException(
                status_code=429,
                detail=f"Gemini quota cooldown active for {int(cooldown_remaining)}s.",
            )

        all_retry_statuses: List[int] = []
        candidates = gemini_model_candidates()
        for model_index, model_name in enumerate(candidates):
            retry_statuses: List[int] = []
            self.active_model_name = model_name
            for attempt in range(len(self.api_keys)):
                try:
                    return self._generate_content_with_timeout(prompt, model_name)
                except Exception as exc:
                    if isinstance(exc, HTTPException):
                        raise
                    if isinstance(exc, TimeoutError):
                        self._start_quota_cooldown()
                        raise HTTPException(status_code=504, detail=str(exc))

                    status_code = self._status_code(exc)
                    if self._is_retryable(exc):
                        retry_statuses.append(status_code or 0)
                        status_label = status_code if status_code is not None else "unknown"
                        print(
                            f"[Rotator] Gemini retryable error {status_label} "
                            f"on model {model_name} key {attempt + 1}/{len(self.api_keys)}."
                        )
                        if attempt < len(self.api_keys) - 1:
                            self.rotate_key()
                            continue
                        break

                    detail = "Gemini API error."
                    if status_code is not None:
                        detail = f"Gemini API error with status {status_code}."
                    raise HTTPException(status_code=502, detail=detail)

            all_retry_statuses.extend(retry_statuses)
            if model_index < len(candidates) - 1:
                print(f"[Rotator] Trying fallback Gemini model {candidates[model_index + 1]}.")

        if all_retry_statuses and any(code == 429 for code in all_retry_statuses):
            status_code = 429
        elif all_retry_statuses and all(code == 504 for code in all_retry_statuses):
            status_code = 504
        else:
            status_code = 502
        if status_code in {429, 504}:
            self._start_quota_cooldown()
        raise HTTPException(
            status_code=status_code,
            detail=f"All Gemini API keys/models failed with retryable errors for models {', '.join(candidates)}.",
        )


rotator = GeminiRotator()

try:
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    chroma_collection = chroma_client.get_or_create_collection("natalia_conversations")
    success_collection = chroma_client.get_or_create_collection(SUCCESS_COLLECTION_NAME)
    negative_collection = chroma_client.get_or_create_collection(NEGATIVE_COLLECTION_NAME)
except Exception as exc:
    print(f"WARNING: Could not connect to ChromaDB at {CHROMA_PATH}: {exc}")
    chroma_client = None
    chroma_collection = None
    success_collection = None
    negative_collection = None

try:
    books_chroma_client = chromadb.PersistentClient(path=str(BOOKS_CHROMA_PATH))
    books_collection = books_chroma_client.get_or_create_collection(BOOKS_COLLECTION_NAME)
    book_conversations_collection = books_chroma_client.get_or_create_collection(
        BOOK_CONVERSATIONS_COLLECTION_NAME
    )
except Exception as exc:
    print(f"WARNING: Could not connect to books ChromaDB at {BOOKS_CHROMA_PATH}: {exc}")
    books_chroma_client = None
    books_collection = None
    book_conversations_collection = None


@app.get("/")
async def index():
    if not SIMULATOR_PATH.exists():
        raise HTTPException(status_code=404, detail="simulador_v1.2.html not found.")
    return FileResponse(SIMULATOR_PATH, media_type="text/html; charset=utf-8")


@app.get("/simulador_v1.2.html")
async def simulator():
    return await index()


@app.get("/health")
async def health():
    collection_count = None
    if chroma_collection is not None:
        try:
            collection_count = chroma_collection.count()
        except Exception:
            collection_count = None
    success_collection_count = None
    if success_collection is not None:
        try:
            success_collection_count = success_collection.count()
        except Exception:
            success_collection_count = None
    books_collection_count = None
    if books_collection is not None:
        try:
            books_collection_count = books_collection.count()
        except Exception:
            books_collection_count = None
    book_conversations_count = None
    if book_conversations_collection is not None:
        try:
            book_conversations_count = book_conversations_collection.count()
        except Exception:
            book_conversations_count = None
    negative_collection_count = None
    if negative_collection is not None:
        try:
            negative_collection_count = negative_collection.count()
        except Exception:
            negative_collection_count = None

    return {
        "status": "ok",
        "simulator": SIMULATOR_PATH.name,
        "simulator_exists": SIMULATOR_PATH.exists(),
        "gemini_model": MODEL_NAME,
        "gemini_model_candidates": gemini_model_candidates(),
        "gemini_sdk": rotator.sdk_name,
        "gemini_live_enabled": gemini_live_enabled(),
        "gemini_coach_enabled": gemini_coach_enabled(),
        "gemini_keys_loaded": len(rotator.api_keys),
        "chroma_connected": chroma_collection is not None,
        "chroma_query_enabled": chroma_query_enabled(),
        "chroma_collection": getattr(chroma_collection, "name", None),
        "chroma_documents": collection_count,
        "success_chroma_collection": getattr(success_collection, "name", None),
        "success_chroma_documents": success_collection_count,
        "books_chroma_collection": getattr(books_collection, "name", None),
        "books_chroma_documents": books_collection_count,
        "book_conversations_chroma_collection": getattr(book_conversations_collection, "name", None),
        "book_conversations_chroma_documents": book_conversations_count,
        "negative_chroma_collection": getattr(negative_collection, "name", None),
        "negative_chroma_documents": negative_collection_count,
    }


@app.get("/api/training-status")
async def training_status():
    if not DB_PATH.exists():
        raise HTTPException(status_code=404, detail="textgame.db not found.")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        reddit_total = conn.execute("SELECT COUNT(*) FROM reddit_conversations").fetchone()[0]
        reddit_json = conn.execute(
            "SELECT COUNT(*) FROM reddit_conversations WHERE transcription_json IS NOT NULL AND transcription_json != ''"
        ).fetchone()[0]
        chat_total = conn.execute("SELECT COUNT(*) FROM chat_turns").fetchone()[0]
        success_total = conn.execute(
            "SELECT COUNT(*) FROM reddit_success_scrape_candidates WHERE status = 'candidate_qa'"
        ).fetchone()[0]
        success_translated = conn.execute(
            """
            SELECT COUNT(*)
            FROM reddit_success_scrape_candidates
            WHERE status = 'candidate_qa'
              AND translation_es IS NOT NULL
              AND translation_es != ''
            """
        ).fetchone()[0]
        transcript_rows = conn.execute(
            """
            SELECT status, COUNT(*) AS total, SUM(LENGTH(COALESCE(raw_text, ''))) AS chars
            FROM transcripts
            GROUP BY status
            """
        ).fetchall()
        profile_rows = conn.execute(
            """
            SELECT girl_profile_type AS profile, COUNT(*) AS total
            FROM reddit_conversations
            GROUP BY girl_profile_type
            ORDER BY total DESC
            """
        ).fetchall()
        chat_rows = conn.execute(
            "SELECT user_message, girl_response, outcome, girl_profile_type FROM chat_turns"
        ).fetchall()
        reddit_rows = conn.execute(
            """
            SELECT transcription_json, girl_profile_type
            FROM reddit_conversations
            WHERE transcription_json IS NOT NULL AND transcription_json != ''
            """
        ).fetchall()
    finally:
        conn.close()

    intents: Dict[str, int] = {}
    signals: Dict[str, int] = {}
    by_profile: Dict[str, Dict[str, Any]] = {}
    pair_count = 0
    persona_usable_pair_count = 0
    persona_rejected_pair_count = 0
    reddit_rows_with_pairs = 0
    reddit_rows_without_pairs = 0

    def add_pair(man: str, woman: str, profile: str = "", outcome: str = "") -> None:
        nonlocal pair_count, persona_usable_pair_count, persona_rejected_pair_count
        pair_count += 1
        if valid_persona_pair(man, woman):
            persona_usable_pair_count += 1
        else:
            persona_rejected_pair_count += 1
        intent = infer_turn_intent(man)
        signal = infer_woman_signal(woman)
        success = score_pair_success(woman, outcome)
        profile_key = profile or "desconocida"
        intents[intent] = intents.get(intent, 0) + 1
        signals[signal] = signals.get(signal, 0) + 1
        profile_stats = by_profile.setdefault(
            profile_key,
            {"pairs": 0, "intents": {}, "woman_signals": {}, "success_total": 0},
        )
        profile_stats["pairs"] += 1
        profile_stats["success_total"] += success
        profile_stats["intents"][intent] = profile_stats["intents"].get(intent, 0) + 1
        profile_stats["woman_signals"][signal] = profile_stats["woman_signals"].get(signal, 0) + 1

    for row in chat_rows:
        add_pair(
            str(row["user_message"] or ""),
            str(row["girl_response"] or ""),
            str(row["girl_profile_type"] or "desconocida"),
            str(row["outcome"] or ""),
        )

    for row in reddit_rows:
        messages = parse_reddit_messages(row["transcription_json"] or "")
        row_pairs = 0
        for index, msg in enumerate(messages):
            if msg["role"] != "her":
                continue
            previous_user = ""
            for prev in reversed(messages[:index]):
                if prev["role"] == "user":
                    previous_user = prev["text"]
                    break
            if previous_user:
                add_pair(previous_user, msg["text"], str(row["girl_profile_type"] or "desconocida"), "OCR real")
                row_pairs += 1
        if row_pairs:
            reddit_rows_with_pairs += 1
        else:
            reddit_rows_without_pairs += 1

    profile_training = {}
    profile_intent_gaps = {}
    for profile, stats in by_profile.items():
        pairs = int(stats["pairs"] or 0)
        scarce = {
            intent: int(stats["intents"].get(intent, 0))
            for intent in sorted(SCARCE_REPLY_INTENTS)
            if int(stats["intents"].get(intent, 0)) < 3
        }
        if scarce:
            profile_intent_gaps[profile] = scarce
        profile_training[profile] = {
            "pairs": pairs,
            "success_average": round(float(stats["success_total"]) / pairs, 2) if pairs else 0,
            "intents": dict(sorted(stats["intents"].items(), key=lambda item: item[0])),
            "woman_signals": dict(sorted(stats["woman_signals"].items(), key=lambda item: item[0])),
        }

    return {
        "sqlite": {
            "reddit_conversations": reddit_total,
            "reddit_with_transcription_json": reddit_json,
            "reddit_rows_with_pairs": reddit_rows_with_pairs,
            "reddit_rows_without_pairs": reddit_rows_without_pairs,
            "chat_turns": chat_total,
            "reddit_success_candidate_qa": success_total,
            "reddit_success_translated": success_translated,
            "transcripts": {
                str(row["status"] or "desconocido"): {
                    "total": int(row["total"] or 0),
                    "chars": int(row["chars"] or 0),
                }
                for row in transcript_rows
            },
            "profiles": {str(row["profile"] or "desconocida"): int(row["total"]) for row in profile_rows},
        },
        "derived_training_pairs": pair_count,
        "persona_usable_pairs": persona_usable_pair_count,
        "persona_rejected_pairs": persona_rejected_pair_count,
        "pair_intents": dict(sorted(intents.items(), key=lambda item: item[0])),
        "woman_signals": dict(sorted(signals.items(), key=lambda item: item[0])),
        "profile_training": dict(sorted(profile_training.items(), key=lambda item: item[0])),
        "profile_intent_gaps": dict(sorted(profile_intent_gaps.items(), key=lambda item: item[0])),
        "chroma_documents": chroma_collection.count() if chroma_collection is not None else None,
        "success_chroma_documents": success_collection.count() if success_collection is not None else None,
        "books_chroma_documents": books_collection.count() if books_collection is not None else None,
        "book_conversations_chroma_documents": (
            book_conversations_collection.count() if book_conversations_collection is not None else None
        ),
        "negative_chroma_documents": negative_collection.count() if negative_collection is not None else None,
    }


def level_context_for(level_id: Any) -> str:
    try:
        if not LEVELS_PATH.exists():
            return ""
        levels_cfg = json.loads(LEVELS_PATH.read_text(encoding="utf-8"))
        level = levels_cfg.get(f"L{level_id}")
        if not level:
            return ""
        return (
            f"Perfil de la chica: {level.get('profile', 'desconocido')}. "
            f"Situacion: {level.get('title', '')}."
        )
    except Exception:
        return ""


def level_behavior(level_id: int) -> Dict[str, Any]:
    behavior = dict(LEVEL_BEHAVIOR.get(int(level_id or 1), LEVEL_BEHAVIOR[1]))
    profile = str(behavior.get("profile") or "")
    if profile == "alta_selectividad":
        behavior["profile_label"] = profile
        behavior["profile"] = "desinteresada"
    else:
        behavior["profile_label"] = profile
    return behavior


def passing_score_for_behavior(behavior: Dict[str, Any]) -> int:
    selectivity = float(behavior.get("selectivity") or 0)
    if selectivity >= 0.9:
        return 9
    if selectivity >= 0.7:
        return 8
    if selectivity >= 0.45:
        return 7
    return 6


def message_role(msg: Dict[str, Any]) -> str:
    sender = str(msg.get("sender") or msg.get("role") or "").lower()
    if sender in {"user", "me", "usuario", "man", "hombre"}:
        return "user"
    if sender in {"her", "assistant", "npc", "girl", "woman", "natalia"}:
        return "her"
    return sender


def latest_turn_text(history: List[Dict[str, Any]], role: str) -> str:
    for turn in reversed(history or []):
        if message_role(turn) == role:
            return str(turn.get("text") or turn.get("content") or turn.get("message") or "").strip()
    return ""


def authoritative_last_natalia(request: SimulateTurnRequest) -> str:
    from_history = latest_turn_text(request.history, "her")
    if from_history:
        return from_history
    context = request.visible_context or {}
    return str(context.get("last_natalia_message") or "").strip()


def authoritative_last_user(request: SimulateTurnRequest) -> str:
    current = (request.user_message or "").strip()
    if current:
        return current
    context = request.visible_context or {}
    return str(context.get("last_user_message") or "").strip() or latest_turn_text(request.history, "user")


def visible_context_text(request: SimulateTurnRequest) -> str:
    context = request.visible_context or {}
    last_her = authoritative_last_natalia(request)
    last_user = authoritative_last_user(request)
    snapshot = str(context.get("chat_snapshot") or "").strip()
    step_id = context.get("evaluated_step_id", request.evaluated_step_id)
    parts = [
        f"Paso visible: {step_id if step_id is not None else request.step_index + 1}",
        f"Ultimo mensaje visible de Natalia: {last_her or 'Sin mensaje previo de Natalia.'}",
        f"Respuesta actual del hombre: {last_user}",
    ]
    if snapshot:
        parts.append(f"Snapshot visible resumido:\n{snapshot[:1200]}")
    return "\n".join(parts)


def compact_history(history: List[Dict[str, Any]], limit: int = 10) -> str:
    lines: List[str] = []
    for msg in history[-limit:]:
        sender = message_role(msg)
        if sender == "user":
            role = "Hombre"
        elif sender == "her":
            role = "Natalia"
        else:
            role = sender or "Chat"
        text = str(msg.get("text") or msg.get("content") or "").strip()
        time_text = str(msg.get("timeText") or msg.get("time") or "").strip()
        if text:
            suffix = f" ({time_text})" if time_text else ""
            lines.append(f"{role}: {text}{suffix}")
    return "\n".join(lines) if lines else "Sin historial previo."


def json_from_model(raw: str) -> Dict[str, Any]:
    match = re.search(r"\{.*\}", raw or "", re.DOTALL)
    if not match:
        raise ValueError("No JSON object found.")
    return json.loads(match.group())


def natalia_payload_from_model(raw: str) -> Dict[str, str]:
    try:
        data = json_from_model(raw)
        return {
            "message": str(data.get("message") or "").strip(),
            "reply_time": str(data.get("reply_time") or "Tardó: 15 min").strip(),
        }
    except Exception:
        text = clean_ui_text(raw or "")
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"^(Natalia|Mujer|Respuesta)\s*:\s*", "", text, flags=re.IGNORECASE).strip()
        text = text.strip('"').strip("'").strip()
        if not text:
            raise ValueError("No usable Natalia text found.")
        if len(text.split()) > 28 or "\n" in text:
            raise ValueError("Natalia plain text reply is too long or multi-line.")
        return {"message": text, "reply_time": "Tardó: 15 min"}


def retrieve_chroma_cases(query: str, profile: str, limit: int = 4) -> List[Dict[str, str]]:
    if not chroma_query_enabled():
        return []
    if chroma_collection is None:
        return []
    try:
        try:
            result = chroma_collection.query(
                query_texts=[f"PROFILE {profile}. {query}"],
                n_results=limit,
                where={"profile": profile},
            )
        except Exception:
            result = chroma_collection.query(
                query_texts=[f"PROFILE {profile}. {query}"],
                n_results=limit,
            )
    except Exception as exc:
        print(f"Error querying ChromaDB: {exc}")
        return []

    docs = result.get("documents", [[]])[0] if result else []
    metadatas = result.get("metadatas", [[]])[0] if result else []
    cases: List[Dict[str, str]] = []
    for index, doc in enumerate(docs):
        meta = metadatas[index] if index < len(metadatas) else {}
        cases.append(
            {
                "source": "chroma",
                "post_id": str(meta.get("post_id", "")),
                "profile": str(meta.get("profile", "")),
                "text": str(doc)[:1800],
            }
        )
    return cases


def parse_json_list(raw: Any) -> List[str]:
    try:
        data = json.loads(str(raw or "[]"))
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [clean_ui_text(item) for item in data if clean_ui_text(item)]


def success_time_markers(text: str) -> List[str]:
    patterns = [
        r"\b\d{1,2}:\d{2}\s?(?:AM|PM|a\.m\.|p\.m\.)?\b",
        r"\b(?:today|yesterday|ayer|hoy|lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)\b",
        r"\b\d+\s?(?:min|mins|minutes|hour|hours|hora|horas|h)\b",
    ]
    markers: List[str] = []
    for pattern in patterns:
        markers.extend(re.findall(pattern, text or "", flags=re.IGNORECASE))
    return [clean_ui_text(item) for item in markers if clean_ui_text(item)]


def success_confidence(row: sqlite3.Row) -> tuple[str, List[str]]:
    objectives = parse_json_list(row["objectives_json"])
    score = int(row["score"] or 0)
    text = clean_ui_text(row["translation_es"] or row["ocr_text"] or "")
    local_paths = clean_ui_text(row["local_paths_json"] or "")
    reasons: List[str] = []
    if objectives:
        reasons.append("objetivo_detectado")
    if score >= 8:
        reasons.append("score_alto")
    elif score >= 6:
        reasons.append("score_medio")
    if len(text.split()) >= 35:
        reasons.append("conversacion_suficiente")
    if local_paths and local_paths != "[]":
        reasons.append("imagen_local")
    if success_time_markers(text):
        reasons.append("marcas_tiempo")
    strength = sum(
        1
        for item in [
            bool(objectives),
            score >= 8,
            len(text.split()) >= 35,
            local_paths and local_paths != "[]",
            bool(success_time_markers(text)),
        ]
        if item
    )
    if strength >= 4:
        return "alta", reasons
    if strength >= 2:
        return "media", reasons
    return "baja", reasons


def infer_query_objectives(query: str) -> set[str]:
    text = analysis_text(query)
    objectives: set[str] = set()
    if any(token in text for token in ["whatsapp", "numero", "telefono", "contacto"]):
        objectives.update({"whatsapp", "telefono"})
    if "instagram" in text or "insta" in text:
        objectives.add("instagram")
    if "snap" in text or "snapchat" in text:
        objectives.add("snapchat")
    if any(token in text for token in ["cita", "salir", "vernos", "cafe", "vino", "plan"]):
        objectives.add("cita")
    if any(token in text for token in ["abridor", "humor", "gracioso", "jaja", "risa"]):
        objectives.update({"humor", "abridor"})
    return objectives


def success_case_rank(query: str, case: Dict[str, str]) -> int:
    text = case.get("text", "")
    objectives = set(str(case.get("objectives", "")).split(", "))
    query_objectives = infer_query_objectives(query)
    try:
        score = int(str(case.get("success_score") or "0"))
    except ValueError:
        score = 0
    confidence = str(case.get("confidence") or "")
    rank = retrieval_score(query, text) * 4
    rank += score * 2
    rank += len(query_objectives.intersection(objectives)) * 8
    if confidence == "alta":
        rank += 6
    elif confidence == "media":
        rank += 3
    if str(case.get("has_time_markers", "")).lower() in {"true", "1", "yes"}:
        rank += 2
    return rank


def success_candidate_case_text(row: sqlite3.Row, max_chars: int = 2600) -> str:
    objectives = parse_json_list(row["objectives_json"])
    confidence, confidence_reasons = success_confidence(row)
    markers = success_time_markers(row["translation_es"] or row["ocr_text"] or "")
    title = clean_ui_text(row["title_es"] or row["title"] or "")
    summary = clean_ui_text(row["summary_es"] or "")
    translation = clean_ui_text(row["translation_es"] or "")
    source_url = clean_ui_text(row["source_url"] or "")
    lines = [
        "CASO REAL EXITOSO REDDIT",
        f"Post ID: {row['post_id']}",
        f"Titulo: {title}",
        f"Score QA: {row['score'] or ''}/10",
        f"Objetivos: {', '.join(objectives) if objectives else 'sin objetivo etiquetado'}",
        f"Confidence: {confidence} ({', '.join(confidence_reasons)})",
        f"Marcas de tiempo: {', '.join(markers[:8]) if markers else 'sin marcas detectadas'}",
        f"Resumen: {summary}",
        f"Fuente: {source_url}",
        "Conversacion traducida LATAM:",
        translation,
    ]
    text = "\n".join(part for part in lines if str(part).strip())
    return text[:max_chars]


def fetch_success_candidate_rows(post_ids: List[str]) -> Dict[str, sqlite3.Row]:
    if not post_ids or not DB_PATH.exists():
        return {}
    placeholders = ",".join("?" for _ in post_ids)
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT post_id, source_url, title, title_es, translation_es, objectives_json,
                   score, summary_es, status, ocr_text, ocr_lines_json, local_paths_json,
                   subreddit
            FROM reddit_success_scrape_candidates
            WHERE status = 'candidate_qa'
              AND post_id IN ({placeholders})
            """,
            post_ids,
        ).fetchall()
        conn.close()
    except Exception as exc:
        print(f"Error fetching success candidates: {exc}")
        return {}
    return {str(row["post_id"]): row for row in rows}


def retrieve_success_chroma_cases(query: str, limit: int = 4) -> List[Dict[str, str]]:
    if not chroma_query_enabled() or success_collection is None:
        return []
    try:
        result = success_collection.query(query_texts=[query], n_results=limit)
    except Exception as exc:
        print(f"Error querying success ChromaDB: {exc}")
        return []

    metadatas = result.get("metadatas", [[]])[0] if result else []
    ids = result.get("ids", [[]])[0] if result else []
    post_ids: List[str] = []
    for index, meta in enumerate(metadatas):
        post_id = str((meta or {}).get("post_id") or "")
        if not post_id and index < len(ids):
            post_id = str(ids[index]).replace("success_", "", 1)
        if post_id:
            post_ids.append(post_id)

    rows_by_id = fetch_success_candidate_rows(post_ids)
    cases: List[Dict[str, str]] = []
    for post_id in post_ids:
        row = rows_by_id.get(post_id)
        if row is None:
            continue
        cases.append(
            {
                "source": "success_chroma",
                "post_id": post_id,
                "profile": "casos_exitosos",
                "success_score": str(row["score"] or ""),
                "objectives": ", ".join(parse_json_list(row["objectives_json"])),
                "confidence": success_confidence(row)[0],
                "confidence_reasons": ", ".join(success_confidence(row)[1]),
                "has_time_markers": str(bool(success_time_markers(row["translation_es"] or row["ocr_text"] or ""))).lower(),
                "text": success_candidate_case_text(row),
            }
        )
    cases.sort(key=lambda case: success_case_rank(query, case), reverse=True)
    return cases[:limit]


def retrieve_success_sqlite_cases(query: str, limit: int = 3) -> List[Dict[str, str]]:
    if not DB_PATH.exists():
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT post_id, source_url, title, title_es, translation_es, objectives_json,
                   score, summary_es, status, ocr_text, ocr_lines_json, local_paths_json,
                   subreddit
            FROM reddit_success_scrape_candidates
            WHERE status = 'candidate_qa'
              AND translation_es IS NOT NULL
              AND translation_es != ''
            """
        ).fetchall()
        conn.close()
    except Exception as exc:
        print(f"Error querying success candidates: {exc}")
        return []

    scored: List[tuple[int, sqlite3.Row]] = []
    for row in rows:
        text = f"{row['title']} {row['title_es']} {row['summary_es']} {row['translation_es']}"
        score = retrieval_score(query, text)
        if score > 0:
            try:
                score += int(row["score"] or 0)
            except Exception:
                pass
            scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "source": "success_sqlite",
            "post_id": str(row["post_id"] or ""),
            "profile": "casos_exitosos",
            "success_score": str(row["score"] or ""),
            "objectives": ", ".join(parse_json_list(row["objectives_json"])),
            "confidence": success_confidence(row)[0],
            "confidence_reasons": ", ".join(success_confidence(row)[1]),
            "has_time_markers": str(bool(success_time_markers(row["translation_es"] or row["ocr_text"] or ""))).lower(),
            "text": success_candidate_case_text(row),
        }
        for _, row in scored[:limit]
    ]


TEXTGAME_CONCEPT_PATTERNS = {
    "opener": ["opener", "abridor", "opening", "primer mensaje", "first message", "icebreaker"],
    "tension": ["tension", "tensión", "sexual", "flirt", "coqueteo", "banter", "tease"],
    "inversion": ["investment", "inversion", "inversión", "chase", "perseguir", "needy", "necesitado"],
    "cierre": ["number", "numero", "número", "whatsapp", "phone", "date", "cita", "meet", "cerrar"],
    "timing": ["timing", "tiempo", "wait", "espera", "reply", "responder", "demora"],
    "humor": ["humor", "funny", "gracioso", "joke", "broma", "jaja", "laugh"],
    "frame": ["frame", "marco", "liderazgo", "lead", "dominant", "calibrar", "calibration"],
}


def infer_textgame_concepts(text: str) -> List[str]:
    lowered = clean_ui_text(text).lower()
    return [
        concept
        for concept, tokens in TEXTGAME_CONCEPT_PATTERNS.items()
        if any(token in lowered for token in tokens)
    ][:5]


def retrieve_books_chroma_cases(query: str, limit: int = 2) -> List[Dict[str, str]]:
    if not chroma_query_enabled():
        return []
    collections = [
        ("books_chroma", books_collection),
        ("books_conversations_chroma", book_conversations_collection),
    ]
    cases: List[Dict[str, str]] = []
    for source, collection in collections:
        if collection is None:
            continue
        try:
            result = collection.query(query_texts=[query], n_results=limit)
        except Exception as exc:
            print(f"Error querying books ChromaDB: {exc}")
            continue
        docs = result.get("documents", [[]])[0] if result else []
        metadatas = result.get("metadatas", [[]])[0] if result else []
        for index, doc in enumerate(docs):
            meta = metadatas[index] if index < len(metadatas) else {}
            label = str(meta.get("titulo_libro") or meta.get("libro") or meta.get("book_slug") or "")
            text = clean_ui_text(doc)
            concepts = infer_textgame_concepts(text)
            cases.append(
                {
                    "source": source,
                    "post_id": str(meta.get("conversation_id") or meta.get("book_id") or ""),
                    "profile": "teoria_libros",
                    "concepts": ", ".join(concepts),
                    "text": f"Fuente libro: {label}\nConceptos: {', '.join(concepts) or 'general'}\n{text[:1800]}",
                }
            )
    return cases[:limit]


def retrieve_negative_chroma_cases(query: str, limit: int = 2) -> List[Dict[str, str]]:
    if not chroma_query_enabled() or negative_collection is None:
        return []
    try:
        result = negative_collection.query(query_texts=[query], n_results=limit)
    except Exception as exc:
        print(f"Error querying negative ChromaDB: {exc}")
        return []
    docs = result.get("documents", [[]])[0] if result else []
    metadatas = result.get("metadatas", [[]])[0] if result else []
    cases: List[Dict[str, str]] = []
    for index, doc in enumerate(docs):
        meta = metadatas[index] if index < len(metadatas) else {}
        cases.append(
            {
                "source": "negative_chroma",
                "post_id": str(meta.get("post_id", "")),
                "profile": "casos_negativos",
                "success_score": str(meta.get("score", "")),
                "text": f"Ejemplo negativo para explicar errores, no para imitar:\n{clean_ui_text(doc)[:1400]}",
            }
        )
    return cases


def retrieve_chat_turns(query: str, profile: str, limit: int = 6) -> List[Dict[str, str]]:
    if not DB_PATH.exists():
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT user_message, girl_response, outcome, girl_profile_type
            FROM chat_turns
            WHERE girl_profile_type = ?
            """,
            (profile,),
        ).fetchall()
        conn.close()
    except Exception as exc:
        print(f"Error querying chat_turns: {exc}")
        return []

    scored: List[tuple[int, sqlite3.Row]] = []
    for row in rows:
        text = f"{row['user_message']}\n{row['girl_response']}\n{row['outcome'] or ''}"
        score = retrieval_score(query, text)
        if score > 0:
            scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)

    return [
        {
            "source": "sqlite_chat_turns",
            "profile": str(row["girl_profile_type"] or ""),
            "text": (
                f"Hombre: {row['user_message']}\n"
                f"Mujer: {row['girl_response']}\n"
                f"Resultado: {row['outcome'] or ''}"
            ),
        }
        for _, row in scored[:limit]
    ]


def retrieval_tokens(text: str) -> set[str]:
    stopwords = {
        "para",
        "pero",
        "como",
        "con",
        "que",
        "una",
        "uno",
        "los",
        "las",
        "del",
        "por",
        "and",
        "the",
        "you",
        "she",
        "her",
        "his",
        "this",
        "that",
    }
    return {
        token
        for token in re.findall(r"[a-zÃ¡Ã©Ã­Ã³ÃºÃ±Ã¼]{4,}", (text or "").lower())
        if token not in stopwords
    }


def retrieval_score(query: str, text: str) -> int:
    query_tokens = retrieval_tokens(query)
    if not query_tokens:
        return 0
    text_tokens = retrieval_tokens(text)
    return len(query_tokens & text_tokens)


def reddit_json_to_case_text(row: sqlite3.Row) -> str:
    raw_json = row["transcription_json"] or ""
    title = row["title"] or ""
    body = row["body_text"] or ""
    try:
        data = json.loads(raw_json) if raw_json else {}
    except Exception:
        data = {}
    if isinstance(data, list):
        data = {"mensajes": data}
    if not isinstance(data, dict):
        data = {}

    summary = str(data.get("resumen_estrategico") or data.get("summary") or "").strip()
    scoring = data.get("scoring") or data.get("score") or {}
    messages = data.get("mensajes") or data.get("messages") or []
    message_lines: List[str] = []
    if isinstance(messages, list):
        for item in messages[:8]:
            if not isinstance(item, dict):
                continue
            speaker = (
                item.get("speaker")
                or item.get("emisor")
                or item.get("role")
                or item.get("autor")
                or "turno"
            )
            text = (
                item.get("text")
                or item.get("texto")
                or item.get("message")
                or item.get("contenido")
                or ""
            )
            if str(text).strip():
                message_lines.append(f"{speaker}: {str(text).strip()}")

    parts = [
        f"Titulo: {title or data.get('titulo') or ''}",
        f"Resumen: {summary}",
        f"Scoring: {json.dumps(scoring, ensure_ascii=False)[:500] if scoring else ''}",
        "Mensajes:\n" + "\n".join(message_lines),
        f"Texto OCR: {(row['transcription_text'] or body or '')[:700]}",
    ]
    return "\n".join(part for part in parts if part.strip())[:1800]


def parse_reddit_messages(raw_json: str) -> List[Dict[str, str]]:
    try:
        data = json.loads(raw_json) if raw_json else {}
    except Exception:
        return []
    if isinstance(data, list):
        messages = data
    elif isinstance(data, dict):
        messages = data.get("mensajes") or data.get("messages") or []
    else:
        messages = []
    parsed: List[Dict[str, str]] = []
    if not isinstance(messages, list):
        return parsed
    for item in messages:
        if not isinstance(item, dict):
            continue
        speaker_raw = str(
            item.get("speaker")
            or item.get("emisor")
            or item.get("role")
            or item.get("autor")
            or ""
        ).lower()
        text = str(
            item.get("text")
            or item.get("texto")
            or item.get("message")
            or item.get("contenido")
            or ""
        ).strip()
        if not text:
            continue
        if any(token in speaker_raw for token in ["ella", "woman", "girl", "her", "natalia"]):
            role = "her"
        elif any(token in speaker_raw for token in ["Ã©l", "el", "hombre", "man", "user", "him"]):
            role = "user"
        else:
            role = "her" if len(parsed) % 2 else "user"
        parsed.append({"role": role, "text": text, "time": str(item.get("tiempo") or item.get("time") or "")})
    return parsed


def reply_pair_case(
    source: str,
    profile: str,
    man_message: str,
    woman_response: str,
    post_id: str = "",
    outcome: str = "",
    intent: str = "",
    woman_signal: str = "",
    success_score: int = 0,
) -> Dict[str, str]:
    return {
        "source": source,
        "post_id": post_id,
        "profile": profile,
        "man_message": man_message,
        "woman_response": woman_response,
        "outcome": outcome,
        "intent": intent,
        "woman_signal": woman_signal,
        "success_score": str(success_score),
        "text": (
            "PAR REAL HOMBRE-MUJER\n"
            f"Intencion: {intent}\n"
            f"Senal mujer: {woman_signal}\n"
            f"Hombre: {man_message}\n"
            f"Mujer: {woman_response}\n"
            f"Resultado: {outcome}\n"
            f"Success score: {success_score}"
        )[:1000],
    }


def infer_turn_intent(man_message: str, previous_woman: str = "") -> str:
    text = analysis_text(man_message)
    previous = analysis_text(previous_woman)
    combined = f"{previous}\n{text}"
    direct_topics = direct_question_topics(man_message, topic_set(man_message))
    if direct_topics:
        if "contacto" in direct_topics:
            return "pedir_contacto"
        if "plan" in direct_topics:
            return "cerrar_plan"
        if any(topic in direct_topics for topic in ["trabajo", "ubicacion"]):
            return "logistica_ligera"
        return "pregunta_contextual"
    if any(word in text for word in ["whatsapp", "numero", "nÃºmero", "telefono", "telÃ©fono", "celular", "insta"]) or contains_phone_number(man_message):
        return "pedir_contacto"
    if any(word in text for word in ["cita", "salir", "vernos", "tomar", "copa", "vino", "cafe", "cafÃ©", "plan"]):
        return "cerrar_plan"
    if any(word in text for word in ["cuando", "cuÃ¡ndo", "que dia", "quÃ© dÃ­a", "dia dices", "dÃ­a dices"]):
        return "cerrar_plan"
    if any(word in combined for word in ["donde", "dÃ³nde", "vives", "trabaj", "estud", "eres de", "bogota", "bogotÃ¡"]):
        return "logistica_ligera"
    if any(word in text for word in ["jaja", "jajaja", "ðŸ˜‚", "ðŸ¤£", "broma", "gracioso", "humor"]):
        return "humor"
    if any(word in text for word in ["hola", "hey", "match", "perfil"]):
        return "abridor"
    if meaningful_question_mark_count(text) > 0 or question_cue_present(text):
        return "pregunta_contextual"
    return "conversacion"


def topic_set(text: str) -> set[str]:
    lowered = analysis_text(text)
    topics: set[str] = set()
    if any(token in lowered for token in ["donde", "dÃ³nde", "dónde", "vives", "eres de", "bogota", "bogotÃ¡", "bogotá", "brickell", "miami", "zona"]):
        topics.add("ubicacion")
    if any(token in lowered for token in ["trabaj", "dedicas", "estud", "oficina", "profesion", "profesiÃ³n"]):
        topics.add("trabajo")
    if any(token in lowered for token in ["vivo", "vivi", "medellin", "barranquilla", "colombia"]):
        topics.add("ubicacion")
    if re.search(r"\b(cali)\b", lowered):
        topics.add("ubicacion")
    if any(token in lowered for token in ["gym", "gimnasio", "entren", "ejercicio", "deporte", "mover", "pilates", "yoga", "caminar", "running", "correr"]):
        topics.add("ejercicio")
    if any(token in lowered for token in ["vino", "copa", "drink", "tomar"]):
        topics.add("vino")
    if any(token in lowered for token in ["plan", "cita", "salir", "vernos", "lugar", "cuando", "cuÃ¡ndo", "cuándo", "jueves", "viernes", "sabado", "sÃ¡bado", "sábado", "domingo", "lunes", "martes", "miercoles", "miÃ©rcoles", "miércoles"]):
        topics.add("plan")
    if any(token in lowered for token in ["whatsapp", "numero", "nÃºmero", "telefono", "telÃ©fono", "celular", "insta"]) or contains_phone_number(text):
        topics.add("contacto")
    if any(token in lowered for token in ["como va", "cÃ³mo va", "que tal", "quÃ© tal", "semana"]):
        topics.add("dia")
    if re.search(r"\b(dia|dÃ­a|dÃƒÂ­a)\b", lowered):
        topics.add("dia")
    if any(token in lowered for token in ["musica", "mÃºsica", "cancion", "canciÃ³n", "playlist", "bailar", "reggaeton", "salsa"]):
        topics.add("musica")
    if any(token in lowered for token in ["comida", "comer", "restaurante", "sushi", "pizza", "tacos", "postre"]):
        topics.add("comida")
    if any(token in lowered for token in ["viaje", "viajar", "playa", "montaÃ±a", "montaña", "vacaciones", "paris", "mexico", "mÃ©xico"]):
        topics.add("viajes")
    if re.search(r"\b(perro|perros|gato|gatos|mascota|mascotas)\b", lowered):
        topics.add("mascotas")
    if any(token in lowered for token in ["familia", "hermano", "hermana", "mamÃ¡", "mama", "papÃ¡", "papa"]):
        topics.add("familia")
    return topics


def question_cue_present(text: str) -> bool:
    lowered = re.sub(r"Â¿|[¿?]+", " ", f" {analysis_text(text)} ")
    return any(
        phrase in lowered
        for phrase in [
            " que tal",
            " quÃ© ",
            " qué ",
            " qu? ",
            " que zona",
            " que dia",
            " que plan",
            " que lugar",
            " donde ",
            " dÃ³nde ",
            " dónde ",
            " d?nde ",
            " cuando ",
            " cuÃ¡ndo ",
            " cuándo ",
            " cu?ndo ",
            " como va",
            " cÃ³mo ",
            " cómo ",
            " c?mo ",
            " te gusta ",
            " trabajas",
            " haces",
            " dedicas",
            " vives",
            " eres de",
        ]
    )


def question_cue_count(text: str) -> int:
    lowered = f" {analysis_text(text)} "
    fragments = [part.strip() for part in re.split(r"Â¿|[¿?]+", lowered) if part.strip()]
    cue_fragments = sum(1 for part in fragments if question_cue_present(part))
    if cue_fragments:
        return cue_fragments
    cue_patterns = [
        r"\bque\s+(tal|zona|dia|plan|lugar|musica|comida)\b",
        r"\b(quien|donde|cuando|como)\b",
        r"\bte gusta\b",
        r"\btrabajas\b",
        r"\bhaces\b",
        r"\bdedicas\b",
        r"\bvives\b",
        r"\beres de\b",
        r"\btienes\b",
    ]
    return sum(1 for pattern in cue_patterns if re.search(pattern, lowered))


def meaningful_question_mark_count(text: str) -> int:
    cleaned = analysis_text(text)
    if not cleaned:
        return 0
    if "¿" in cleaned or "Â¿" in cleaned:
        return max(1, cleaned.count("¿") + cleaned.count("Â¿"))
    if question_cue_present(cleaned):
        return max(1, question_cue_count(cleaned))
    stripped = cleaned.rstrip()
    if re.search(r"\s\?{1,3}$", stripped):
        return 0
    return len(re.findall(r"(?<![a-záéíóúñ])\?+|\?+(?![a-záéíóúñ])", cleaned, flags=re.IGNORECASE))


def asks_question(text: str) -> bool:
    return meaningful_question_mark_count(text) > 0 or question_cue_present(text)


def direct_question_topics(message: str, user_topics: set[str]) -> List[str]:
    if not asks_question(message):
        return []
    lowered = analysis_text(message)
    question_part = lowered
    markers = [
        match.end()
        for match in re.finditer(r"Â¿|[¿?]", lowered)
        if re.search(r"[a-záéíóúñ]", lowered[match.end() :])
    ]
    if markers:
        question_part = lowered[max(markers) :]
    else:
        topic_cue_starts = [
            match.start()
            for pattern in [
                r"\bque\s+(tal|zona|dia|plan|lugar|musica|comida)\b",
                r"\ben\s+que\s+trabaj",
                r"\bque\s+haces\b",
                r"\bte\s+gusta\s+(viajar|hacer\s+ejercicio|el\s+gym|el\s+vino|tomar)\b",
                r"\bte\s+gusta\s+(hacer\s+)?deporte\b",
                r"\bque\s+deporte\b",
                r"\bdeporte\s+te\s+gusta\b",
                r"\bque\s+entrenas\b",
                r"\btomas\s+vino\b",
                r"\btienes\s+(perro|gato|mascota)\b",
                r"\beres\s+(cercana|cercano|de)\b",
                r"\bdonde\s+vives\b",
                r"\bcomo\s+va\b",
            ]
            for match in re.finditer(pattern, lowered)
        ]
        generic_cue_starts = [
            match.start()
            for pattern in [
                r"\bte\s+gusta\b",
                r"\btienes\b",
                r"\beres\s+de\b",
            ]
            for match in re.finditer(pattern, lowered)
        ]
        cue_starts = topic_cue_starts or generic_cue_starts
        if cue_starts:
            question_part = lowered[max(cue_starts) :]
    topics: List[str] = []
    if any(token in question_part for token in ["trabajas", "dedicas", "en que trabaj", "en qué trabaj", "que haces", "qué haces"]):
        topics.append("trabajo")
    if any(token in question_part for token in ["te gusta hacer ejercicio", "te gusta el gym", "entrenas", "haces ejercicio", "te gusta hacer deporte", "que deporte", "deporte te gusta", "que entrenas"]):
        topics.append("ejercicio")
    if any(token in question_part for token in ["te gusta el vino", "tomas vino", "te gusta tomar", "vino?"]):
        topics.append("vino")
    if any(token in question_part for token in ["donde vives", "dónde vives", "eres de", "vives?", "que zona", "qué zona", "zona te queda"]):
        topics.append("ubicacion")
    if any(token in question_part for token in ["cuando", "cuándo", "que dia", "qué día", "que plan", "qué plan", "que lugar", "qué lugar"]):
        topics.append("plan")
    if any(token in question_part for token in ["whatsapp", "numero", "número", "telefono", "teléfono", "celular", "insta"]):
        topics.append("contacto")
    if any(token in question_part for token in ["como va", "cómo va", "que tal tu dia", "qué tal tu día", "que tal tu semana", "qué tal tu semana"]):
        topics.append("dia")
    if any(token in question_part for token in ["musica", "mÃºsica", "cancion", "canciÃ³n", "playlist", "bailar"]):
        topics.append("musica")
    if any(token in question_part for token in ["comida", "comer", "restaurante", "sushi", "pizza", "tacos", "postre"]):
        topics.append("comida")
    if any(token in question_part for token in ["viaje", "viajar", "playa", "montaÃ±a", "montaña", "vacaciones"]):
        topics.append("viajes")
    if re.search(r"\b(perro|perros|gato|gatos|mascota|mascotas)\b", question_part):
        topics.append("mascotas")
    if any(token in question_part for token in ["familia", "hermano", "hermana", "mamÃ¡", "mama", "papÃ¡", "papa"]):
        topics.append("familia")
    if topics:
        return [
            topic
            for topic in [
                "trabajo",
                "ejercicio",
                "vino",
                "ubicacion",
                "plan",
                "contacto",
                "dia",
                "musica",
                "comida",
                "viajes",
                "mascotas",
                "familia",
            ]
            if topic in topics
        ]
    if meaningful_question_mark_count(lowered) > 0:
        return ["pregunta_contextual"]
    return []


def response_directive_for_turn(
    message: str,
    user_topics: set[str],
    last_topics: set[str],
    answered_topics: List[str],
    asked_question: bool,
    ignored_question: bool,
) -> str:
    question_topics = direct_question_topics(message, user_topics) if asked_question else []
    if ignored_question:
        return "Natalia debe notar que el hombre dejo una pregunta visible sin responder y bajar interes."
    if answered_topics and question_topics:
        return (
            f"Natalia debe reconocer que el hombre respondio {', '.join(answered_topics)}; despues debe responder brevemente "
            f"la pregunta nueva sobre {', '.join(question_topics)}, sin saltar a otro tema."
        )
    if question_topics:
        if question_topics == ["pregunta_contextual"]:
            return "Natalia debe responder la pregunta directa del hombre sin saltar a vino, numero, cita o logistica si no hay puente claro."
        return f"Natalia debe responder primero la pregunta directa sobre {', '.join(question_topics)} y luego devolver una pregunta natural."
    if answered_topics:
        return f"Natalia debe reconocer la respuesta sobre {', '.join(answered_topics)} y continuar ese mismo hilo visible."
    if last_topics:
        return f"Natalia debe mantenerse conectada con el tema visible anterior: {', '.join(sorted(last_topics))}."
    return "Natalia debe responder al ultimo mensaje real del hombre con tono humano, corto y contextual."


def analyze_visible_turn(message: str, last_natalia_message: str = "", chosen_time: str = "") -> Dict[str, Any]:
    user_topics = topic_set(message)
    last_topics = topic_set(last_natalia_message)
    answered_topics = sorted(user_topics.intersection(last_topics))
    asked_question = asks_question(message)
    question_topics = direct_question_topics(message, user_topics)
    ignored_question = bool(last_natalia_message and "?" in last_natalia_message and not answered_topics and len((message or "").strip()) < 18)
    return {
        "intent": infer_turn_intent(message, last_natalia_message),
        "user_topics": sorted(user_topics),
        "last_topics": sorted(last_topics),
        "asked_question": asked_question,
        "direct_question_topics": question_topics,
        "answered_topics": answered_topics,
        "ignored_question": ignored_question,
        "response_directive": response_directive_for_turn(
            message,
            user_topics,
            last_topics,
            answered_topics,
            asked_question,
            ignored_question,
        ),
        "chosen_time": chosen_time,
    }


def turn_analysis_prompt(analysis: Dict[str, Any]) -> str:
    def joined(key: str) -> str:
        values = analysis.get(key) or []
        if isinstance(values, list):
            return ", ".join(str(value) for value in values) or "-"
        return str(values) or "-"

    return "\n".join(
        [
            f"- Intent: {analysis.get('intent', '-')}",
            f"- Temas del hombre: {joined('user_topics')}",
            f"- Temas del ultimo mensaje de Natalia: {joined('last_topics')}",
            f"- Temas respondidos al ultimo mensaje: {joined('answered_topics')}",
            f"- Temas de pregunta directa del hombre: {joined('direct_question_topics')}",
            f"- El hombre hizo pregunta nueva: {bool(analysis.get('asked_question'))}",
            f"- Ignoro pregunta visible: {bool(analysis.get('ignored_question'))}",
            f"- Directiva de respuesta: {analysis.get('response_directive') or '-'}",
            f"- Tiempo elegido: {analysis.get('chosen_time') or '-'}",
        ]
    )


def infer_woman_signal(woman_response: str) -> str:
    cleaned = clean_ui_text(woman_response)
    text = cleaned.lower()
    if any(word in text for word in ["whatsapp", "numero", "nÃºmero", "número", "telefono", "telÃ©fono", "teléfono", "insta"]):
        return "contacto"
    if any(word in text for word in ["jaja", "jajaja", "haha", "😂", "🤣", "ðŸ˜‚", "ðŸ¤£"]):
        return "risa"
    if "?" in cleaned or "¿" in cleaned:
        return "pregunta_de_vuelta"
    if any(word in text for word in ["ok", "va", "dale", "claro", "perfecto", "me gusta"]):
        return "receptiva"
    if any(word in text for word in ["noup", "nope", "no", "mmm", "umm", "aburrida"]):
        return "fria"
    return "neutral"


def score_pair_success(woman_response: str, outcome: str = "") -> int:
    signal = infer_woman_signal(woman_response)
    outcome_l = (outcome or "").lower()
    score = 5
    if any(word in outcome_l for word in ["positivo", "success", "cita", "telefono", "contacto"]):
        score += 2
    if signal in {"contacto", "pregunta_de_vuelta", "risa", "receptiva"}:
        score += 2
    if signal == "fria":
        score -= 2
    if len((woman_response or "").split()) <= 2 and signal not in {"risa", "contacto"}:
        score -= 1
    return max(1, min(10, score))


SCARCE_REPLY_INTENTS = {"cerrar_plan", "pedir_contacto", "logistica_ligera", "humor"}


def broaden_reply_profiles(intent: str) -> bool:
    return intent in SCARCE_REPLY_INTENTS


def profile_rank_bonus(target_profile: str, case_profile: str, intent: str) -> int:
    if target_profile == case_profile:
        return 6
    if broaden_reply_profiles(intent):
        return 1
    return 0


def looks_like_profile_or_meme_pair(man_message: str, woman_response: str) -> bool:
    combined_raw = f"{man_message}\n{woman_response}".lower()
    combined = analysis_text(combined_raw)
    profile_tokens = [
        "[perfil",
        "[profile",
        "desliza a la izquierda",
        "desliza a la derecha",
        "swipe left",
        "swipe right",
        "less than a mile",
        "milla away",
        "mile away",
        "ghosting",
        "getting boned",
        "loteria",
        "loter\u00eda",
        "probabilidad de conseguir una cena gratis",
    ]
    if any(token in combined_raw or token in combined for token in profile_tokens):
        return True
    if combined_raw.count("[") >= 2 and combined_raw.count("]") >= 2:
        return True
    return False


def valid_persona_pair(man_message: str, woman_response: str) -> bool:
    man = clean_ui_text(man_message)
    woman = clean_ui_text(woman_response)
    combined = analysis_text(f"{man}\n{woman}")
    unsafe_tokens = [
        "enterrar vivo",
        "enterrarme",
        "enterrarte",
        "matar",
        "morir",
        "muerto",
        "suicid",
        "cadaver",
        "cadaver",
        "donde estoy ahora",
        "estoy despierto",
        "sueno rarisimo",
        "sueño rarisimo",
        "rompieron los pantalones",
    ]
    third_party_tokens = [
        "amigo",
        "dile lo que sientes",
        "me dijo que le gusto",
        "me hace sentir mejor saber que los hombres",
    ]
    if not man or not woman:
        return False
    if len(man) > 260 or len(woman) > 220:
        return False
    if looks_like_profile_or_meme_pair(man, woman):
        return False
    if any(token in combined for token in unsafe_tokens):
        return False
    if any(token in combined for token in third_party_tokens):
        return False
    if looks_non_spanish_reply(woman):
        return False
    return True


def pair_topics(case: Dict[str, str]) -> set[str]:
    return topic_set(clean_ui_text(case.get("man_message"))) | topic_set(clean_ui_text(case.get("woman_response")))


def retrieve_real_reply_pairs(query: str, profile: str, intent: str = "", limit: int = 5) -> List[Dict[str, str]]:
    if not DB_PATH.exists():
        return []
    scored: List[tuple[int, Dict[str, str]]] = []
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        if broaden_reply_profiles(intent):
            chat_rows = conn.execute(
                """
                SELECT user_message, girl_response, outcome, girl_profile_type
                FROM chat_turns
                """
            ).fetchall()
        else:
            chat_rows = conn.execute(
                """
                SELECT user_message, girl_response, outcome, girl_profile_type
                FROM chat_turns
                WHERE girl_profile_type = ?
                """,
                (profile,),
            ).fetchall()
        for row in chat_rows:
            man = str(row["user_message"] or "")
            woman = str(row["girl_response"] or "")
            if not valid_persona_pair(man, woman):
                continue
            row_profile = str(row["girl_profile_type"] or profile)
            pair_intent = infer_turn_intent(man)
            woman_signal = infer_woman_signal(woman)
            success_score = score_pair_success(woman, str(row["outcome"] or ""))
            score = retrieval_score(query, f"{man}\n{woman}\n{row['outcome'] or ''}")
            if intent and pair_intent == intent:
                score += 3
            if score > 0:
                scored.append((
                    score + success_score + profile_rank_bonus(profile, row_profile, intent),
                    reply_pair_case(
                        "sqlite_chat_pair",
                        row_profile,
                        man,
                        woman,
                        outcome=str(row["outcome"] or ""),
                        intent=pair_intent,
                        woman_signal=woman_signal,
                        success_score=success_score,
                    ),
                ))

        if broaden_reply_profiles(intent):
            reddit_rows = conn.execute(
                """
                SELECT post_id, transcription_json, girl_profile_type
                FROM reddit_conversations
                WHERE transcription_json IS NOT NULL
                  AND transcription_json != ''
                """
            ).fetchall()
        else:
            reddit_rows = conn.execute(
                """
                SELECT post_id, transcription_json, girl_profile_type
                FROM reddit_conversations
                WHERE girl_profile_type = ?
                  AND transcription_json IS NOT NULL
                  AND transcription_json != ''
                """,
                (profile,),
            ).fetchall()
        conn.close()
    except Exception as exc:
        print(f"Error querying real reply pairs: {exc}")
        return []

    for row in reddit_rows:
        messages = parse_reddit_messages(row["transcription_json"] or "")
        for index, msg in enumerate(messages):
            if msg["role"] != "her":
                continue
            previous_user = ""
            for prev in reversed(messages[:index]):
                if prev["role"] == "user":
                    previous_user = prev["text"]
                    break
            if not previous_user:
                continue
            woman = msg["text"]
            if not valid_persona_pair(previous_user, woman):
                continue
            row_profile = str(row["girl_profile_type"] or profile)
            pair_intent = infer_turn_intent(previous_user)
            woman_signal = infer_woman_signal(woman)
            success_score = score_pair_success(woman, "OCR real")
            score = retrieval_score(query, f"{previous_user}\n{woman}")
            if intent and pair_intent == intent:
                score += 3
            if score > 0:
                scored.append((
                    score + success_score + profile_rank_bonus(profile, row_profile, intent),
                    reply_pair_case(
                        "sqlite_reddit_pair",
                        row_profile,
                        previous_user,
                        woman,
                        post_id=str(row["post_id"] or ""),
                        outcome="OCR real",
                        intent=pair_intent,
                        woman_signal=woman_signal,
                        success_score=success_score,
                    ),
                ))

    scored.sort(key=lambda item: item[0], reverse=True)
    deduped: List[Dict[str, str]] = []
    seen = set()
    for _, case in scored:
        key = (case["source"], case["post_id"], case["woman_response"][:80])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(case)
        if len(deduped) >= limit:
            break
    return deduped


def retrieve_sqlite_reddit_cases(query: str, profile: str, limit: int = 4) -> List[Dict[str, str]]:
    if not DB_PATH.exists():
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, post_id, title, body_text, transcription_text, transcription_json, girl_profile_type
            FROM reddit_conversations
            WHERE girl_profile_type = ?
              AND transcription_json IS NOT NULL
              AND transcription_json != ''
            """,
            (profile,),
        ).fetchall()
        conn.close()
    except Exception as exc:
        print(f"Error querying reddit_conversations: {exc}")
        return []

    scored: List[tuple[int, sqlite3.Row, str]] = []
    for row in rows:
        text = reddit_json_to_case_text(row)
        score = retrieval_score(query, f"{row['title']}\n{text}")
        if score > 0:
            scored.append((score, row, text))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "source": "sqlite_reddit",
            "post_id": str(row["post_id"] or ""),
            "profile": str(row["girl_profile_type"] or ""),
            "text": text,
        }
        for _, row, text in scored[:limit]
    ]


def retrieve_youtube_theory(query: str, limit: int = 2) -> List[Dict[str, str]]:
    if not DB_PATH.exists():
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT video_id, raw_text
            FROM transcripts
            WHERE status = 'success'
              AND raw_text IS NOT NULL
              AND raw_text != ''
            """
        ).fetchall()
        conn.close()
    except Exception as exc:
        print(f"Error querying transcripts: {exc}")
        return []

    scored: List[tuple[int, sqlite3.Row]] = []
    for row in rows:
        score = retrieval_score(query, row["raw_text"] or "")
        if score > 0:
            scored.append((score, row))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "source": "sqlite_youtube",
            "post_id": str(row["video_id"] or ""),
            "profile": "teoria_textgame",
            "text": f"Transcripcion YouTube sobre text game:\n{str(row['raw_text'] or '')[:1200]}",
        }
        for _, row in scored[:limit]
    ]


def retrieve_cases(request: SimulateTurnRequest, behavior: Dict[str, Any]) -> List[Dict[str, str]]:
    profile = str(behavior.get("profile", "coqueta"))
    query = f"{request.user_message}\n{visible_context_text(request)}\n{compact_history(request.history, limit=6)}"
    last_natalia = authoritative_last_natalia(request)
    intent = infer_turn_intent(request.user_message, last_natalia)
    cases = retrieve_real_reply_pairs(query, profile, intent=intent, limit=5)
    cases.extend(retrieve_success_chroma_cases(query, limit=3))
    if not any(case.get("source") == "success_chroma" for case in cases):
        cases.extend(retrieve_success_sqlite_cases(query, limit=2))
    cases.extend(retrieve_chroma_cases(query, profile, limit=2))
    cases.extend(retrieve_sqlite_reddit_cases(query, profile, limit=2))
    cases.extend(retrieve_books_chroma_cases(query, limit=2))
    cases.extend(retrieve_negative_chroma_cases(query, limit=2))
    cases.extend(retrieve_youtube_theory(query, limit=2))
    cases.extend(retrieve_chat_turns(query, profile, limit=2))

    deduped: List[Dict[str, str]] = []
    seen = set()
    for case in cases:
        key = (case.get("source", ""), case.get("post_id", ""), case.get("text", "")[:80])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(case)
    return deduped[:10]


def retrieve_persona_cases(request: SimulateTurnRequest, behavior: Dict[str, Any], limit: int = 8) -> List[Dict[str, str]]:
    profile = str(behavior.get("profile", "coqueta"))
    query = f"{request.user_message}\n{visible_context_text(request)}\n{compact_history(request.history, limit=6)}"
    last_natalia = authoritative_last_natalia(request)
    intent = infer_turn_intent(request.user_message, last_natalia)
    cases = retrieve_real_reply_pairs(query, profile, intent=intent, limit=limit)
    success_cases = retrieve_success_chroma_cases(query, limit=2)
    if not success_cases:
        success_cases = retrieve_success_sqlite_cases(query, limit=1)
    analysis = analyze_visible_turn(request.user_message, last_natalia, request.chosen_time)
    direct_topics = {
        str(topic)
        for topic in (analysis.get("direct_question_topics") or [])
        if str(topic) != "pregunta_contextual"
    }
    if not direct_topics:
        return cases + success_cases
    filtered_pairs = [
        case
        for case in cases
        if pair_topics(case).intersection(direct_topics)
    ]
    return filtered_pairs + success_cases


def retrieve_persona_strategy_cases(
    request: SimulateTurnRequest,
    behavior: Dict[str, Any],
    limit: int = 2,
) -> List[Dict[str, str]]:
    profile = str(behavior.get("profile", "coqueta"))
    query = (
        f"{request.user_message}\n"
        f"{visible_context_text(request)}\n"
        f"{compact_history(request.history, limit=6)}\n"
        f"perfil {profile} text game respuesta femenina natural timing inversion cierre humor"
    )
    return retrieve_books_chroma_cases(query, limit=limit)


def retrieve_coach_cases(
    request: SimulateTurnRequest,
    behavior: Dict[str, Any],
    persona_cases: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    profile = str(behavior.get("profile", "coqueta"))
    query = f"{request.user_message}\n{visible_context_text(request)}\n{compact_history(request.history, limit=6)}"
    cases: List[Dict[str, str]] = list(persona_cases[:2])
    success_cases = retrieve_success_chroma_cases(query, limit=3)
    cases.extend(success_cases[:2])
    if not success_cases:
        success_cases = retrieve_success_sqlite_cases(query, limit=2)
        cases.extend(success_cases[:2])
    cases.extend(retrieve_negative_chroma_cases(query, limit=2))
    cases.extend(success_cases[2:])
    cases.extend(persona_cases[2:5])
    cases.extend(retrieve_chroma_cases(query, profile, limit=2))
    cases.extend(retrieve_sqlite_reddit_cases(query, profile, limit=2))
    cases.extend(retrieve_books_chroma_cases(query, limit=2))
    cases.extend(retrieve_youtube_theory(query, limit=2))
    cases.extend(retrieve_chat_turns(query, profile, limit=2))

    deduped: List[Dict[str, str]] = []
    seen = set()
    for case in cases:
        key = (
            case.get("source", ""),
            case.get("post_id", ""),
            case.get("man_message", ""),
            case.get("woman_response", ""),
            case.get("text", "")[:80],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(case)
    return deduped[:10]


def retrieval_summary_for_cases(
    coach_cases: List[Dict[str, str]],
    persona_cases: List[Dict[str, str]],
    strategy_cases: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    def counts(cases: List[Dict[str, str]]) -> Dict[str, int]:
        result: Dict[str, int] = {}
        for case in cases:
            source = str(case.get("source") or "desconocida")
            result[source] = result.get(source, 0) + 1
        return dict(sorted(result.items(), key=lambda item: item[0]))

    persona_pair_cases = [
        case for case in persona_cases if case.get("source") in {"sqlite_chat_pair", "sqlite_reddit_pair"}
    ]
    persona_support_cases = [
        case for case in persona_cases if case.get("source") not in {"sqlite_chat_pair", "sqlite_reddit_pair"}
    ]

    return {
        "persona_pair_cases": len(persona_pair_cases),
        "persona_support_cases": len(persona_support_cases),
        "coach_context_cases": len(coach_cases),
        "strategy_context_cases": len(strategy_cases or []),
        "persona_sources": counts(persona_pair_cases),
        "persona_support_sources": counts(persona_support_cases),
        "coach_sources": counts(coach_cases),
        "strategy_sources": counts(strategy_cases or []),
        "gemini_live_enabled": gemini_live_enabled(),
        "chroma_query_enabled": chroma_query_enabled(),
    }


def cases_signal(cases: List[Dict[str, str]]) -> str:
    combined = "\n".join(case.get("text", "") for case in cases[:5]).lower()
    if any(word in combined for word in ["whatsapp", "phone", "nÃºmero", "numero", "telÃ©fono", "telefono"]):
        return "contacto"
    if any(word in combined for word in ["date", "cita", "meet", "salir", "bottle", "botella"]):
        return "cita"
    if any(word in combined for word in ["laugh", "jaja", "haha", "humor", "broma"]):
        return "humor"
    if any(word in combined for word in ["coffee", "cafÃ©", "cafe", "drink", "vino"]):
        return "plan_suave"
    return ""


def emoji_profile(text: str) -> Dict[str, Any]:
    emojis = re.findall("[\U0001F300-\U0001FAFF\u2600-\u27BF]", text or "")
    risky = {"ðŸ†", "ðŸ’¦", "ðŸ‘…", "ðŸ¥µ", "ðŸ˜ˆ"}
    warm = {"ðŸ˜‰", "ðŸ˜„", "ðŸ˜ƒ", "ðŸ˜‚", "ðŸ¤£", "ðŸ˜…", "ðŸ™‚", "ðŸ˜Š", "ðŸ˜Œ"}
    romantic = {"ðŸ˜", "ðŸ˜˜", "â¤ï¸", "ðŸ’•", "ðŸ’–", "ðŸ”¥"}
    unique = sorted(set(emojis))
    risky_count = sum(1 for emoji in emojis if emoji in risky)
    warm_count = sum(1 for emoji in emojis if emoji in warm)
    romantic_count = sum(1 for emoji in emojis if emoji in romantic)

    if not emojis:
        calibration = "sin emojis"
        note = "No uso emojis; esta bien si el texto tiene tono humano."
    elif len(emojis) <= 2 and risky_count == 0:
        calibration = "calibrados"
        note = "Uso pocos emojis y no invade el mensaje."
    elif risky_count:
        calibration = "riesgo sexual temprano"
        note = "Uso emojis sexuales o muy intensos para una conversacion inicial."
    elif len(emojis) >= 4:
        calibration = "excesivos"
        note = "Uso demasiados emojis y puede parecer necesitado o poco natural."
    elif romantic_count >= 2:
        calibration = "demasiado romanticos"
        note = "Usa demasiada validacion emocional para el momento."
    else:
        calibration = "neutros"
        note = "Los emojis no destruyen el mensaje, pero deben tener intencion."

    return {
        "count": len(emojis),
        "unique": unique,
        "risky_count": risky_count,
        "warm_count": warm_count,
        "romantic_count": romantic_count,
        "calibration": calibration,
        "note": note,
    }


def turn_metrics_for_message(
    message: str,
    last_natalia_message: str,
    chosen_time: str,
    analysis: Dict[str, Any],
) -> Dict[str, Any]:
    text = (message or "").strip()
    lowered = analysis_text(text)
    emojis = emoji_profile(text)
    word_count = len(text.split())
    question_count = meaningful_question_mark_count(text)
    direct_topics = list(analysis.get("direct_question_topics") or [])
    answered_topics = list(analysis.get("answered_topics") or [])
    intent = str(analysis.get("intent") or "conversacion")

    overinvestment = question_count
    if word_count > 28:
        overinvestment += int((word_count - 28) / 8) + 1
    overinvestment = max(0, min(10, overinvestment))

    context_congruence = 8
    if analysis.get("ignored_question"):
        context_congruence = 2
    elif direct_topics and not answered_topics and last_natalia_message:
        context_congruence = 5
    elif answered_topics:
        context_congruence = 9

    direction_score = 8 if intent in {"cerrar_plan", "pedir_contacto"} else 5
    if any(token in lowered for token in ["quedar", "cita", "plan", "whatsapp", "numero", "tel", "jueves", "hoy"]):
        direction_score = max(direction_score, 7)

    humor_score = 7 if any(token in lowered for token in ["jaja", "jeje", "risa", "broma"]) else 4
    generic_risk = 8 if lowered in {"hola", "hey", "ola", "buenas", "como estas", "como vas"} else 2
    neediness_risk = 7 if any(token in lowered for token in ["hermosa", "preciosa", "amor", "por favor", "contestame"]) else 2
    intensity_risk = 7 if emojis["risky_count"] or any(token in lowered for token in ["mi amor", "te amo", "casarnos"]) else 2

    return {
        "message_quality": {
            "word_count": word_count,
            "question_count": question_count,
            "overinvestment_risk": overinvestment,
            "generic_risk": generic_risk,
            "neediness_risk": neediness_risk,
            "intensity_risk": intensity_risk,
        },
        "context": {
            "context_congruence": context_congruence,
            "answered_topics": answered_topics,
            "direct_question_topics": direct_topics,
            "ignored_question": bool(analysis.get("ignored_question")),
        },
        "objective": {
            "intent": intent,
            "direction_score": direction_score,
            "moves_toward_contact_or_date": intent in {"cerrar_plan", "pedir_contacto"} or direction_score >= 7,
        },
        "tone": {
            "humor_score": humor_score,
            "emoji_calibration": emojis["calibration"],
            "emoji_count": emojis["count"],
            "emoji_risky_count": emojis["risky_count"],
            "emoji_note": emojis["note"],
        },
        "timing": {
            "chosen_time": chosen_time or "",
            "too_immediate": chosen_time.lower() in {"ahora", "ahora mismo"},
        },
    }


def fallback_reason_text(exc: Exception) -> str:
    detail = getattr(exc, "detail", None)
    if detail is None:
        detail = str(exc)
    return clean_ui_text(str(detail))[:180]


def fallback_category(exc: Exception) -> str:
    status_code = getattr(exc, "status_code", None)
    reason = fallback_reason_text(exc).lower()
    if status_code in {429, 502, 503, 504}:
        return "api"
    if any(token in reason for token in ["429", "quota", "gemini api", "retryable", "cooldown", "timeout"]):
        return "api"
    if any(token in reason for token in ["invalid", "incoherent", "plain text", "json", "coherente"]):
        return "guardrail"
    return "unknown"


def cases_to_prompt(
    cases: List[Dict[str, str]],
    max_cases: Optional[int] = None,
    max_text_chars: Optional[int] = None,
) -> str:
    if not cases:
        return "No hay casos reales recuperados."
    chunks: List[str] = []
    selected_cases = cases[:max_cases] if max_cases is not None else cases
    for index, case in enumerate(selected_cases, start=1):
        extra = ""
        if case.get("intent") or case.get("woman_signal"):
            extra = f" intent={case.get('intent','')} signal={case.get('woman_signal','')} success={case.get('success_score','')}"
        if case.get("concepts"):
            extra += f" concepts={case.get('concepts')}"
        label = f"CASO {index} [{case.get('source','')}/{case.get('profile','')}{extra}]"
        case_text = clean_ui_text(case.get("text", ""))
        if max_text_chars is not None and len(case_text) > max_text_chars:
            case_text = case_text[:max_text_chars].rstrip() + "..."
        chunks.append(f"{label}\n{case_text}")
    return "\n\n".join(chunks)


def persona_cases_to_prompt(
    cases: List[Dict[str, str]],
    limit: int = 6,
    max_text_chars: Optional[int] = None,
) -> str:
    human_pairs = [
        case
        for case in cases
        if case.get("source") in {"sqlite_chat_pair", "sqlite_reddit_pair"}
        and clean_ui_text(case.get("woman_response"))
    ][:limit]
    support_cases = [
        case
        for case in cases
        if case.get("source") in {"success_chroma", "success_sqlite"}
        and clean_ui_text(case.get("text"))
    ][:2]
    selected = human_pairs + support_cases
    if not selected:
        return "No hay pares hombre-mujer compatibles; responde solo al contexto visible."
    return cases_to_prompt(selected, max_text_chars=max_text_chars)


def normalized_reply_text(text: str) -> str:
    return re.sub(r"\s+", " ", clean_ui_text(text).lower())


def looks_non_spanish_reply(text: str) -> bool:
    lowered = f" {clean_ui_text(text).lower()} "
    english_tokens = {
        " i ",
        " you ",
        " your ",
        " the ",
        " also ",
        " like ",
        " called ",
        " father ",
        " would ",
        " could ",
        " should ",
        " with ",
        " from ",
    }
    spanish_tokens = {
        " que ",
        " pero ",
        " jaja",
        " si ",
        " no ",
        " me ",
        " te ",
        " el ",
        " la ",
        " una ",
        " un ",
        " lugar ",
        " plan ",
        " jueves ",
        " copa ",
        " trabajo ",
        " donde ",
        " hola ",
    }
    english_hits = sum(1 for token in english_tokens if token in lowered)
    spanish_hits = sum(1 for token in spanish_tokens if token in lowered)
    return english_hits >= 2 and spanish_hits == 0


def used_natalia_replies(history: List[Dict[str, Any]]) -> set[str]:
    used: set[str] = set()
    for turn in history or []:
        if message_role(turn) == "her":
            text = str(turn.get("text") or turn.get("content") or turn.get("message") or "")
            if text:
                used.add(normalized_reply_text(text))
    return used


def reusable_real_woman_reply(
    cases: List[Dict[str, str]],
    score: int,
    used_replies: Optional[set[str]] = None,
    preferred_signals: Optional[List[str]] = None,
    topic_guard: Optional[set[str]] = None,
) -> str:
    used_replies = used_replies or set()
    preferred_signals = preferred_signals or []
    topic_guard = topic_guard or set()
    candidates: List[tuple[int, str]] = []
    for case in cases:
        if case.get("source") not in {"sqlite_chat_pair", "sqlite_reddit_pair"}:
            continue
        if topic_guard:
            case_topics = topic_set(clean_ui_text(case.get("man_message")))
            if not case_topics or case_topics.isdisjoint(topic_guard):
                continue
        reply = clean_ui_text(case.get("woman_response"))
        lowered = reply.lower()
        if not reply or len(reply.split()) > 18:
            continue
        if looks_non_spanish_reply(reply):
            continue
        if topic_guard:
            reply_topics = topic_set(reply)
            if not reply_topics or reply_topics.isdisjoint(topic_guard):
                continue
        letters_only = re.sub(r"[^a-zÃ¡Ã©Ã­Ã³ÃºÃ±]+", "", lowered)
        if letters_only and re.fullmatch(r"(ja|ha)+", letters_only):
            continue
        if normalized_reply_text(reply) in used_replies:
            continue
        if any(token in lowered for token in ["bebe", "jesus", "matrimonio", "estacionamiento", "escocia", "arnold"]):
            continue
        if score < 6 and any(token in lowered for token in ["perfecto", "me encanta", "claro", "obvio"]):
            continue
        if score >= 6 and any(token in lowered for token in ["noup", "nope", "no me interesa"]):
            continue
        if "jaja" in lowered or "?" in reply or len(reply.split()) <= 8:
            rank = int(str(case.get("success_score") or "0") or 0)
            if case.get("woman_signal") in preferred_signals:
                rank += 5
            candidates.append((rank, reply))
    if not candidates:
        return ""
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def unsafe_chat_suggestion(text: str) -> bool:
    lowered = analysis_text(text)
    blocked = [
        "enterrar vivo",
        "enterrarme",
        "enterrarte",
        "matar",
        "morir",
        "muerto",
        "suicid",
        "cadaver",
        "donde estoy ahora",
        "estoy despierto",
        "cadáver",
    ]
    return any(token in lowered for token in blocked)


def incompatible_coach_case_suggestion(text: str, analysis: Dict[str, Any]) -> bool:
    lowered = analysis_text(text)
    topic_guard = set(str(topic) for topic in (analysis.get("user_topics") or []))
    topic_guard.update(str(topic) for topic in (analysis.get("last_topics") or []))
    intent = str(analysis.get("intent") or "")
    if any(token in lowered for token in ["vacaciones", "visita"]) and "viajes" not in topic_guard:
        return True
    if intent == "cerrar_plan" or "plan" in topic_guard:
        plan_tokens = [
            "jueves",
            "viernes",
            "sabado",
            "domingo",
            "lunes",
            "martes",
            "miercoles",
            "lugar",
            "copa",
            "plan",
            "whatsapp",
            "cuadr",
            "hora",
            "sin discurso",
            "sin entrevista",
        ]
        return not any(token in lowered for token in plan_tokens)
    return False


def case_based_suggestions(cases: List[Dict[str, str]], analysis: Dict[str, Any], limit: int = 3) -> List[str]:
    topic_guard = set(str(topic) for topic in (analysis.get("user_topics") or []))
    topic_guard.update(str(topic) for topic in (analysis.get("last_topics") or []))
    direct_topics = {
        str(topic)
        for topic in (analysis.get("direct_question_topics") or [])
        if str(topic) != "pregunta_contextual"
    }
    answered_topics = set(str(topic) for topic in (analysis.get("answered_topics") or []))
    if direct_topics and direct_topics.issubset({"dia"}):
        return []
    if not topic_guard:
        return []
    candidates: List[tuple[int, str]] = []
    for case in cases:
        if case.get("source") not in {"sqlite_chat_pair", "sqlite_reddit_pair"}:
            continue
        man_message = clean_ui_text(case.get("man_message"))
        if not man_message or len(man_message.split()) < 3 or len(man_message) > 160:
            continue
        if topic_guard:
            case_topics = topic_set(man_message)
            if not case_topics or case_topics.isdisjoint(topic_guard):
                continue
            if direct_topics and case_topics.isdisjoint(direct_topics):
                continue
            if answered_topics and direct_topics and case_topics.isdisjoint(answered_topics):
                continue
        lowered = man_message.lower()
        if any(token in lowered for token in ["bebe", "jesus", "matrimonio", "arnold"]):
            continue
        if unsafe_chat_suggestion(man_message):
            continue
        if incompatible_coach_case_suggestion(man_message, analysis):
            continue
        rank = int(str(case.get("success_score") or "0") or 0)
        if case.get("woman_signal") in {"pregunta_de_vuelta", "risa", "receptiva", "contacto"}:
            rank += 4
        candidates.append((rank, man_message))

    candidates.sort(key=lambda item: item[0], reverse=True)
    suggestions: List[str] = []
    seen = set()
    for _, suggestion in candidates:
        normalized = normalized_reply_text(suggestion)
        if normalized in seen:
            continue
        seen.add(normalized)
        suggestions.append(suggestion)
        if len(suggestions) >= limit:
            break
    return suggestions


def merge_suggestions(primary: List[str], learned: List[str], limit: int = 3) -> List[str]:
    merged: List[str] = []
    for suggestion in learned + primary:
        text = clean_ui_text(suggestion)
        if not text:
            continue
        if normalized_reply_text(text) in {normalized_reply_text(item) for item in merged}:
            continue
        merged.append(text)
        if len(merged) >= limit:
            break
    return merged


def learned_coach_note(cases: List[Dict[str, str]], analysis: Dict[str, Any]) -> str:
    topic_guard = set(str(topic) for topic in (analysis.get("user_topics") or []))
    topic_guard.update(str(topic) for topic in (analysis.get("last_topics") or []))
    direct_topics = {
        str(topic)
        for topic in (analysis.get("direct_question_topics") or [])
        if str(topic) != "pregunta_contextual"
    }
    compatible_pairs: List[Dict[str, str]] = []
    for case in cases or []:
        if case.get("source") not in {"sqlite_chat_pair", "sqlite_reddit_pair"}:
            continue
        man_message = clean_ui_text(case.get("man_message"))
        if not man_message:
            continue
        case_topics = topic_set(man_message)
        if topic_guard and (not case_topics or case_topics.isdisjoint(topic_guard)):
            continue
        if direct_topics and case_topics.isdisjoint(direct_topics):
            continue
        compatible_pairs.append(case)

    if not compatible_pairs:
        return ""

    signal_counts: Dict[str, int] = {}
    success_total = 0
    for case in compatible_pairs:
        signal = str(case.get("woman_signal") or "neutral")
        signal_counts[signal] = signal_counts.get(signal, 0) + 1
        try:
            success_total += int(str(case.get("success_score") or "0") or 0)
        except ValueError:
            pass

    top_signals = [
        signal
        for signal, _count in sorted(signal_counts.items(), key=lambda item: item[1], reverse=True)[:2]
        if signal and signal != "neutral"
    ]
    if not top_signals:
        top_signals = ["respuesta natural"]
    average = round(success_total / len(compatible_pairs), 1) if compatible_pairs else 0
    return (
        f"Patron aprendido de casos reales: {len(compatible_pairs)} pares compatibles "
        f"promedian {average}/10 y suelen generar {', '.join(top_signals)}. "
        "Usa eso como guia, sin copiar frases fuera de contexto."
    )


def first_fresh_reply(options: List[str], used_replies: set[str]) -> str:
    for option in options:
        if normalized_reply_text(option) not in used_replies:
            return option
    return options[-1] if options else ""


def coach_suggestions(tags: List[str], analysis: Dict[str, Any], emojis: Dict[str, Any], intent: str) -> List[str]:
    suggestions: List[str] = []

    def add(text: str) -> None:
        if text not in suggestions and len(suggestions) < 3:
            suggestions.append(text)

    if analysis.get("ignored_question"):
        last_topics = ", ".join(analysis.get("last_topics") or []) or "lo que ella pregunto"
        add(f"Responde primero {last_topics} en una frase corta y luego agrega una pregunta suave.")
    answered_topics = [str(topic) for topic in (analysis.get("answered_topics") or [])]
    direct_topics = [
        str(topic)
        for topic in (analysis.get("direct_question_topics") or [])
        if str(topic) != "pregunta_contextual"
    ]
    if answered_topics and direct_topics:
        add(
            "Primero responde "
            + ", ".join(answered_topics)
            + " y luego pregunta "
            + ", ".join(direct_topics)
            + " con una sola frase natural."
        )
    if "demasiadas preguntas" in tags or "sumo otra pregunta antes de cerrar el hilo anterior" in tags:
        add("Cierra una sola idea antes de preguntar otra cosa; evita que el chat parezca entrevista.")
    if "metio una pregunta logistica extra" in tags:
        add("Reconoce su pregunta y mete la tuya con puente, por ejemplo: 'Bogota, y tu mundo laboral que tal?'")
    if "validacion temprana" in tags:
        add("Baja la validacion fisica y usa curiosidad por su estilo o su energia.")
    if "abridor generico" in tags or "mensaje demasiado corto" in tags:
        add("Abre con algo especifico de su perfil o con una pregunta facil de responder.")
    if "sobreinversion" in tags:
        add("Recorta el mensaje a una idea clara; deja que ella tambien invierta.")
    if intent == "pedir_contacto":
        add("Pide contacto solo despues de aterrizar un plan concreto y una razon simple.")
    if intent == "cerrar_plan":
        add("Aterriza el plan con lugar o dia, pero mantenlo ligero y facil de aceptar.")
    if emojis.get("calibration") in {"excesivos", "riesgo sexual temprano", "demasiado romanticos"}:
        add("Usa maximo un emoji calido y evita emojis sexuales o demasiado romanticos al inicio.")
    if not suggestions:
        add("Toma un detalle visible de ella y responde con una frase natural, no una plantilla.")
        add("Haz una sola pregunta facil de contestar, con tono ligero.")
        add("Si hay buena energia, avanza suavemente hacia un plan concreto.")
    for fallback in [
        "Mantenlo corto, especifico y conectado al ultimo mensaje visible.",
        "Responde primero lo que ella dijo antes de abrir otro tema.",
        "Deja una sola idea clara para que ella pueda invertir tambien.",
    ]:
        if len(suggestions) >= 3:
            break
        add(fallback)
    return suggestions[:3]


def heuristic_score(
    message: str,
    chosen_time: str,
    last_natalia_message: str = "",
    cases: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    text = (message or "").strip()
    lowered = analysis_text(text)
    last_lower = analysis_text(last_natalia_message)
    emojis = emoji_profile(text)
    analysis = analyze_visible_turn(text, last_natalia_message, chosen_time)
    intent = str(analysis["intent"])
    score = 7
    tags: List[str] = []
    positives: List[str] = []

    if analysis["ignored_question"] or (last_natalia_message and "?" in last_natalia_message and (
        len(text) < 12 or lowered in {"hola", "hey", "ola", "buenas", "si", "no", "ok"}
    )):
        score -= 4
        tags.append("ignoro la pregunta visible de Natalia")
    if "ubicacion" in analysis["answered_topics"]:
        score += 1
        positives.append("respondio la ubicacion que Natalia pregunto")
    if "dia" in analysis["answered_topics"]:
        score += 1
        positives.append("respondio al estado del dia que Natalia pregunto")
    if "ejercicio" in analysis["answered_topics"]:
        score += 1
        positives.append("respondio al tema de ejercicio que Natalia abrio")
    if (
        "trabajo" in analysis["user_topics"]
        and "ubicacion" in analysis["last_topics"]
        and "ubicacion" not in analysis["answered_topics"]
    ):
        tags.append("metio una pregunta logistica extra")
    unresolved_topics = set(analysis["user_topics"]) - set(analysis["answered_topics"]) - set(analysis["direct_question_topics"])
    if "plan" in analysis["user_topics"]:
        unresolved_topics.discard("vino")
    if analysis["asked_question"] and analysis["last_topics"] and len(analysis["user_topics"]) >= 2 and unresolved_topics:
        tags.append("sumo otra pregunta antes de cerrar el hilo anterior")
    if intent in {"cerrar_plan", "pedir_contacto"}:
        positives.append("intenta avanzar hacia un objetivo concreto")
    if len(text) < 4:
        score -= 3
        tags.append("mensaje demasiado corto")
    if len(text) > 180:
        score -= 2
        tags.append("sobreinversion")
    if lowered in {"hola", "hey", "ola", "buenas"}:
        score -= 3
        tags.append("abridor generico")
    if (
        meaningful_question_mark_count(text) >= 2
        and not (analysis["answered_topics"] and analysis["direct_question_topics"])
    ):
        score -= 1
        tags.append("demasiadas preguntas")
    if any(word in lowered for word in ["hermosa", "preciosa", "bella", "amor"]):
        score -= 1
        tags.append("validacion temprana")
    if any(
        word in lowered
        for word in [
            "jaja",
            "vino",
            "cita",
            "plan",
            "quimica",
            "quÃ­mica",
            "cafe",
            "cafÃ©",
            "sonrisa",
            "espont",
            "conversacion",
            "conversaciÃ³n",
            "bogota",
            "bogotÃ¡",
            "entren",
        ]
    ):
        score += 1
        positives.append("usa tono social util")
    if chosen_time.lower() in {"ahora mismo", "ahora"}:
        score -= 1
        tags.append("respuesta muy inmediata")
    if emojis["calibration"] == "calibrados":
        score += 1
        positives.append("emojis calibrados")
    elif emojis["calibration"] in {"excesivos", "riesgo sexual temprano", "demasiado romanticos"}:
        score -= 2
        tags.append(f"emojis {emojis['calibration']}")

    score = max(1, min(10, score))
    if score < 6:
        quality = "falla porque " + ", ".join(tags) + "." if tags else "no conecta bien con el contexto visible."
    elif tags and positives:
        quality = "funciona en parte porque " + ", ".join(positives) + "; puede pulir " + ", ".join(tags) + "."
    elif tags:
        quality = "tiene base usable, pero conviene pulir " + ", ".join(tags) + "."
    elif positives:
        quality = "conecta bien porque " + ", ".join(positives) + "."
    else:
        quality = "conecta con el contexto visible."
    suggestions = coach_suggestions(tags, analysis, emojis, intent)
    learned_note = learned_coach_note(cases or [], analysis)
    feedback_parts = [
        "Calidad del mensaje: " + quality,
        (
            "Contexto de la conversacion: Natalia venia de decir "
            f'"{last_natalia_message[:120]}"; tu respuesta debe conectar con eso.'
            if last_natalia_message
            else f"Contexto de la conversacion: respondiste en {chosen_time or 'un tiempo no indicado'}, y Natalia debe reaccionar a lo ultimo que ella dijo."
        ),
    ]
    if learned_note:
        feedback_parts.append(learned_note)
    feedback_parts.extend(
        [
            f"Emojis: {emojis['count']} {''.join(emojis['unique']) or '-'}; calibracion: {emojis['calibration']}. {emojis['note']}",
            "Objetivo del turno: responder al contexto visible, mantener humor ligero y avanzar suave si hay buena energia.",
        ]
    )
    return {
        "score": score,
        "lose_life": score < 6,
        "attraction_delta": 10 if score >= 8 else 4 if score >= 6 else -15,
        "verdict": "good" if score >= 8 else "acceptable" if score >= 6 else "bad",
        "natalia_stance": "open" if score >= 8 else "neutral" if score >= 6 else "pull_back",
        "reason": ", ".join(positives + tags) if positives or tags else "conecta con el contexto visible",
        "feedback": "\n\n".join(feedback_parts),
        "suggestions": suggestions,
    }


def fallback_natalia_message(
    request: SimulateTurnRequest,
    score: int,
    behavior: Dict[str, Any],
    cases: Optional[List[Dict[str, str]]] = None,
) -> str:
    text = request.user_message.strip()
    lowered = analysis_text(text)
    signal = cases_signal(cases or [])
    last_natalia = authoritative_last_natalia(request)
    last_lower = analysis_text(last_natalia)
    used_replies = used_natalia_replies(request.history)
    analysis = analyze_visible_turn(text, last_natalia, request.chosen_time)
    intent = str(analysis["intent"])
    direct_topics = set(str(topic) for topic in (analysis.get("direct_question_topics") or []))
    location_area = str(behavior.get("location_area") or "Brickell")
    work_hint = str(behavior.get("work_hint") or "marketing visual")
    off_mode = str(behavior.get("off_mode") or "planes tranquilos")
    selectivity = float(behavior.get("selectivity") or 0)
    high_selectivity = selectivity >= 0.7
    extreme_selectivity = selectivity >= 0.9

    preferred_signals = ["pregunta_de_vuelta", "risa", "receptiva"]
    if score < 6:
        preferred_signals = ["fria", "neutral"]
    elif intent == "pedir_contacto":
        preferred_signals = ["contacto", "receptiva"]
    elif intent == "cerrar_plan":
        preferred_signals = ["pregunta_de_vuelta", "receptiva", "contacto"]
    elif intent in {"abridor", "humor", "pregunta_contextual"}:
        preferred_signals = ["risa", "pregunta_de_vuelta", "receptiva"]

    if last_natalia and "?" in last_natalia:
        if len(text) < 12 or lowered in {"hola", "hey", "ola", "buenas", "si", "no", "ok"}:
            return first_fresh_reply(
                [
                    "jaja respondiste, pero me dejaste la pregunta en el aire.",
                    "jaja ok, pero no me respondiste lo que te pregunte.",
                ],
                used_replies,
            )
        if any(word in lowered for word in ["no se", "nose", "lo que sea"]):
            return first_fresh_reply(
                [
                    "Mmm eso suena a que no quieres pensar mucho. Dame algo mas tuyo.",
                    "jaja esa respuesta fue muy comoda. Sorprendeme un poquito.",
                ],
                used_replies,
            )

    if high_selectivity:
        if "trabajo" in direct_topics:
            return first_fresh_reply(
                [
                    f"Hago {work_hint}. Y tu haces algo interesante o solo preguntas mucho?",
                    f"{work_hint}. Pero me interesa mas ver si tienes vida fuera del trabajo.",
                ],
                used_replies,
            )
        if "dia" in direct_topics:
            return first_fresh_reply(
                [
                    "Bien, ocupada. Tu dia si tuvo algo interesante?",
                    "Va bien, sin mucho drama. A ver si tu dia trae mejor historia.",
                ],
                used_replies,
            )
        if "ejercicio" in direct_topics:
            return first_fresh_reply(
                [
                    "Pilates y caminar. Pero nada de conversacion eterna de gym.",
                    "Me gusta moverme. Sorprendeme con algo mas que rutina y disciplina.",
                ],
                used_replies,
            )
        if "musica" in direct_topics:
            return first_fresh_reply(
                [
                    "Depende del mood. Sorprendeme con algo menos obvio.",
                    "Me gusta la musica con energia, pero no me vendas playlist generica.",
                ],
                used_replies,
            )
        if "comida" in direct_topics:
            return first_fresh_reply(
                [
                    "Me gusta comer bien, pero el lugar importa. Cual propones?",
                    "Buena comida suma. Ahora quiero ver si eliges con criterio.",
                ],
                used_replies,
            )
        if "contacto" in direct_topics:
            return first_fresh_reply(
                [
                    "Puede ser, si el plan esta claro. No me mandes novela.",
                    "Te lo paso si lo usas para concretar, no para hacer entrevista eterna.",
                ],
                used_replies,
            )
        if "plan" in direct_topics:
            if extreme_selectivity:
                return first_fresh_reply(
                    [
                        "Suena posible. Dame lugar y hora, y veo.",
                        "Puede ser, pero quiero una opcion concreta.",
                    ],
                    used_replies,
                )
            return first_fresh_reply(
                [
                    "Me puede sonar. Dame lugar y hora sin venderlo tanto.",
                    "Ok, pero aterrizalo: lugar, hora y cero discurso.",
                ],
                used_replies,
            )

    if "trabajo" in direct_topics:
        if "ubicacion" in analysis["answered_topics"]:
            return first_fresh_reply(
                [
                    f"Bogota, ok. Yo hago {work_hint}; fuera de eso me gustan {off_mode}.",
                    f"Ah bueno, Bogota. Yo hago {work_hint}; ahora dime que haces cuando no estas ocupado.",
                ],
                used_replies,
            )
        return first_fresh_reply(
            [
                f"Hago {work_hint}. Y tu, que haces cuando no estas en modo trabajo?",
                f"Hago {work_hint}. Pero me da mas curiosidad saber como es tu vida fuera del trabajo.",
            ],
            used_replies,
        )
    if "dia" in direct_topics:
        return first_fresh_reply(
            [
                "Va tranquila mi semana, con trabajo y ganas de hacer algo distinto. La tuya si va entretenida?",
                "Mi semana va bien, algo movida pero llevadera. Y la tuya que tal, mucho caos o todo bajo control?",
            ],
            used_replies,
        )
    if "ejercicio" in direct_topics:
        if "deporte" in lowered:
            return first_fresh_reply(
                [
                    "Me gusta pilates y caminar, pero sin volverlo tema eterno jaja. Tu eres mas gym o aire libre?",
                    "Me gusta moverme, pilates o algo al aire libre. Tu que deporte haces en serio?",
                ],
                used_replies,
            )
        return first_fresh_reply(
            [
                "Si, me gusta moverme, pero sin volverme intensa con el gym jaja. Tu que entrenas?",
                "Me gusta, aunque no soy de vivir hablando de rutina. Que haces tu?",
            ],
            used_replies,
        )
    if "vino" in direct_topics:
        return first_fresh_reply(
            [
                "Si, me gusta el vino. Pero no me salgas con clase tecnica de sommelier jaja.",
                "Me gusta, sobre todo si el plan no se siente armado a la fuerza.",
            ],
            used_replies,
        )
    if "ubicacion" in direct_topics:
        return first_fresh_reply(
            [
                f"{location_area} me queda bien si el lugar no es demasiado ruidoso. Que tenias en mente?",
                f"Por {location_area} me funciona. Pero quiero ver si eliges un lugar con buen criterio.",
            ],
            used_replies,
        )
    if "contacto" in direct_topics:
        return first_fresh_reply(
            [
                "Mmm va, pero usalo bien. Si el plan es bueno, te respondo.",
                "Ok, te lo paso si prometes no volver esto una entrevista eterna.",
            ],
            used_replies,
        )
    if "plan" in direct_topics:
        if any(day in lowered for day in ["jueves", "viernes", "sabado", "sÃ¡bado", "sábado", "domingo", "lunes", "martes", "miercoles", "miÃ©rcoles", "miércoles"]):
            return first_fresh_reply(
                [
                    "Jueves puede funcionar. Me gusta que lo aterrices sin hacerlo intenso.",
                    "Ok, jueves suena posible. Ahora dime que lugar tienes en mente.",
                ],
                used_replies,
            )
        return first_fresh_reply(
            [
                "Un lugar tranquilo me suena bien. Dame una opcion concreta y te digo si me convence.",
                "Me gusta que lo aterrices. Dime el lugar y vemos si pasa mi filtro jaja.",
            ],
            used_replies,
        )
    if "musica" in direct_topics:
        return first_fresh_reply(
            [
                "Me gusta la musica con buena energia, pero depende del mood. Tu eres mas de bailar o de escuchar tranquilo?",
                "Soy de playlists mezcladas: algo para moverme y algo mas tranquilo. Tu que pondrias?",
            ],
            used_replies,
        )
    if "comida" in direct_topics:
        return first_fresh_reply(
            [
                "Me gusta comer rico sin hacerlo complicado. Si eliges buen lugar, eso suma puntos jaja.",
                "Soy facil si el lugar tiene buena comida y buena vibra. Tu recomendacion cual seria?",
            ],
            used_replies,
        )
    if "viajes" in direct_topics:
        return first_fresh_reply(
            [
                "Me gustan los viajes con plan, pero dejando espacio para improvisar. Tu eres mas playa o ciudad?",
                "Viajar me encanta, sobre todo cuando no parece agenda militar jaja. Que lugar repetirias?",
            ],
            used_replies,
        )
    if "mascotas" in direct_topics:
        return first_fresh_reply(
            [
                "Me gustan, pero necesito ver si tu mascota aprueba mi filtro tambien jaja. Tienes perro o gato?",
                "Me dan ternura, aunque no prometo competir con una mascota por atencion jaja.",
            ],
            used_replies,
        )
    if "familia" in direct_topics:
        return first_fresh_reply(
            [
                "Soy cercana con mi gente, pero no soy de contar toda mi vida en el primer chat. Tu como eres con tu familia?",
                "Mi familia es importante, aunque prefiero hablarlo natural, no como entrevista jaja.",
            ],
            used_replies,
        )

    if (
        not direct_topics
        and "lugar" in lowered
        and request.step_index < 8
        and not any(phrase in lowered for phrase in ["trato hecho", "te escribo", "lo cuadramos", "listo"])
    ):
        return first_fresh_reply(
            [
                "Ok, lugar tranquilo suma. Ahora dime cual y veo si confio en tu gusto.",
                "Me gusta que lo concretes. Dime el lugar y te digo si pasa.",
            ],
            used_replies,
        )

    if not direct_topics and ("contacto" in analysis["user_topics"] or intent == "pedir_contacto"):
        return first_fresh_reply(
            [
                "Listo, si el plan queda claro te respondo por ahi.",
                "Va, pero que sea para cuadrar algo simple, no para volverlo eterno jaja.",
            ],
            used_replies,
        )

    topic_guard = set(analysis["user_topics"]) | set(analysis["last_topics"])
    if topic_guard:
        real_reply = reusable_real_woman_reply(
            cases or [],
            score,
            used_replies,
            preferred_signals,
            topic_guard,
        )
        if real_reply and (intent == "cerrar_plan" or "plan" in analysis["user_topics"]):
            real_lower = analysis_text(real_reply)
            plan_reply_tokens = [
                "jueves",
                "viernes",
                "sabado",
                "domingo",
                "lunes",
                "martes",
                "miercoles",
                "lugar",
                "copa",
                "plan",
                "whatsapp",
                "cuadr",
                "funcionar",
                "posible",
            ]
            if not any(token in real_lower for token in plan_reply_tokens):
                real_reply = ""
        if real_reply and not natalia_response_is_invalid(real_reply, score, analysis):
            return real_reply

    if not direct_topics and ("plan" in analysis["user_topics"] or intent == "cerrar_plan"):
        if any(phrase in lowered for phrase in ["trato hecho", "te escribo", "lo cuadramos", "listo"]):
            return first_fresh_reply(
                [
                    "Jaja bien, asi si. Me gusta cuando el plan queda claro sin tanta vuelta.",
                    "Listo, asi si suena simple. Me gusta cuando no lo vuelven intenso.",
                ],
                used_replies,
            )
        if request.step_index >= 8 and request.attraction >= 75:
            return first_fresh_reply(
                [
                    "Ok, eso ya suena a plan real. Te paso mi WhatsApp y lo cuadramos.",
                    "Me gusta que lo dejes claro. Pasame tu WhatsApp y lo cuadramos bien.",
                ],
                used_replies,
            )
        if any(day in lowered for day in ["jueves", "viernes", "sabado", "sÃƒÂ¡bado", "sÃ¡bado", "domingo", "lunes", "martes", "miercoles", "miÃƒÂ©rcoles", "miÃ©rcoles"]):
            return first_fresh_reply(
                [
                    "Jueves puede funcionar. Me gusta que lo aterrices sin hacerlo intenso.",
                    "Ok, jueves suena posible. Ahora dime que lugar tienes en mente.",
                ],
                used_replies,
            )
        return first_fresh_reply(
            [
                "Me gusta que lo aterrices como plan. Dime el lugar y vemos si pasa mi filtro jaja.",
                "Un plan tranquilo me suena bien. Dame una opcion concreta y lo miro.",
            ],
            used_replies,
        )

    if score <= 4:
        if "hola" == lowered:
            return first_fresh_reply(
                ["jaja hola... eso fue todo tu gran abridor?", "hola jaja, pense que venias con mas creatividad."],
                used_replies,
            )
        return first_fresh_reply(
            [
                "mmm no se, eso sono un poco intenso. Baja un cambio y habla normal.",
                "jaja no se, ahi te senti un poco forzado. Hablame mas normal.",
            ],
            used_replies,
        )
    if any(word in lowered for word in ["numero", "whatsapp", "telefono", "telÃ©fono", "celular"]):
        if request.attraction >= 65 or request.step_index >= 7:
            return first_fresh_reply(
                [
                    "Mmm va, pero usalo bien. Si el plan es bueno, te respondo.",
                    "Ok, te lo paso si prometes no volver esto una entrevista eterna.",
                ],
                used_replies,
            )
        return first_fresh_reply(
            [
                "jajaja vas rapido. Primero dime por que deberia confiar en tu plan.",
                "vas rapido jaja. Vendeme mejor el plan primero.",
            ],
            used_replies,
        )
    if "bogota" in lowered or "bogotÃ¡" in lowered:
        if "trabaj" in lowered:
            return first_fresh_reply(
                [
                    f"Jaja Bogota me queda claro. Yo hago {work_hint}, pero me interesa mas saber que haces fuera de rutina.",
                    f"Ah bueno, Bogota. Yo hago {work_hint}; ahora dime cual seria tu plan fuera de oficina.",
                ],
                used_replies,
            )
        if "donde" in last_lower or "vives" in last_lower or "eres de" in last_lower:
            return first_fresh_reply(
                [
                    "Ok, eso me ubica. Y cuando no estas trabajando, que plan te gusta?",
                    "Ah bueno, eso ya me ubica. Que haces cuando sales del modo serio?",
                ],
                used_replies,
            )
        return first_fresh_reply(
            [
                "Bogota tiene buenos planes, eso suma. Ahora quiero saber cual seria tu plan ganador.",
                "Bogota da para buenos planes. A ver, cual seria el tuyo?",
            ],
            used_replies,
        )
    if "trabaj" in lowered:
        return first_fresh_reply(
            [
                f"Hago {work_hint}, pero me interesa mas lo que haces cuando sales del modo serio.",
                f"Hago {work_hint}; me interesa mas tu plan fuera de oficina.",
            ],
            used_replies,
        )
    if "entrevista" in lowered:
        return first_fresh_reply(
            [
                "Eso me gusta. Odio cuando el chat parece formulario, prefiero algo con chispa.",
                "Bien, porque si esto parece entrevista me aburro rapidisimo jaja.",
            ],
            used_replies,
        )
    if "cafe" in lowered or "cafÃ©" in lowered:
        if "recomendaci" in last_lower or "cafÃ©" in last_lower or "cafe" in last_lower:
            return first_fresh_reply(
                [
                    "Jaja ok, entonces ya te puse tarea: quiero nombre del lugar y por que vale la pena.",
                    "Ok, pero con nombre real del lugar, no recomendacion generica jaja.",
                ],
                used_replies,
            )
        return first_fresh_reply(
            [
                "Ok, entonces tienes que probar que tu recomendacion de cafe no es puro cuento.",
                "Mmm cafe suena bien si el lugar tiene algo especial.",
            ],
            used_replies,
        )
    if any(phrase in lowered for phrase in ["trato hecho", "te escribo", "lo cuadramos", "sin discurso", "listo"]) and (
        "whatsapp" in last_lower or "usalo" in last_lower or request.step_index >= 8
    ):
        return first_fresh_reply(
            [
                "Jaja bien, asi si. Me gusta cuando el plan queda claro sin tanta vuelta.",
                "Ok, eso suena facil. Ahora si quiero ver si cumples ese plan.",
            ],
            used_replies,
        )
    if any(word in lowered for word in ["vino", "copa", "salir", "plan", "cita", "lugar", "zona"]):
        if any(day in lowered for day in ["jueves", "viernes", "sabado", "sÃ¡bado", "sábado", "domingo", "lunes", "martes", "miercoles", "miÃ©rcoles", "miércoles"]):
            return first_fresh_reply(
                [
                    "Jueves puede funcionar. Me gusta que lo aterrices sin hacerlo intenso.",
                    "Ok, jueves suena posible. Ahora dime que lugar tienes en mente.",
                ],
                used_replies,
            )
        if "zona" in lowered:
            return first_fresh_reply(
                [
                    f"{location_area} me queda bien si no eliges un sitio aburrido.",
                    f"Por {location_area} puede ser. Ahora dime que lugar tienes en mente.",
                ],
                used_replies,
            )
        if "lugar" in lowered:
            return first_fresh_reply(
                [
                    "Ok, lugar tranquilo suma. Ahora dime cual y veo si confio en tu gusto.",
                    "Me gusta que lo concretes. Dime el lugar y te digo si pasa.",
                ],
                used_replies,
            )
        if request.step_index >= 8 or request.attraction >= 80:
            return first_fresh_reply(
                [
                    "Ok, eso ya suena a plan real. Te paso mi WhatsApp y lo cuadramos.",
                    "Va, pasame tu WhatsApp y lo aterrizamos bien.",
                ],
                used_replies,
            )
        if request.step_index >= 6:
            return first_fresh_reply(
                ["Mmm me gusta. Y que dia dices tu?", "Ok, eso ya suena mas concreto. Cuando dices?"],
                used_replies,
            )
        if "vino" in last_lower or "plan" in last_lower:
            return first_fresh_reply(
                ["Jaja eso si suena mas interesante. Que tienes en mente?", "Ok, ahora si estas vendiendo mejor el plan. Sigue."],
                used_replies,
            )
        if "energia" in last_lower or "energÃ­a" in last_lower:
            return first_fresh_reply(
                ["Jaja vas vendiendo el plan poco a poco, eso me gusta.", "Mmm, eso ya suena menos a chat eterno y mas a plan."],
                used_replies,
            )
        return first_fresh_reply(
            [
                "Eso suena bien. Me gustan los planes simples cuando la conversacion tiene buena energia.",
                "Un plan simple gana si la conversacion se siente facil.",
            ],
            used_replies,
        )
    if any(word in lowered for word in ["gym", "gimnasio", "entren"]):
        return first_fresh_reply(
            [
                "Me gusta esa disciplina, aunque espero que no hables solo de rutina y proteina jaja.",
                "Bien por la disciplina, pero prometeme que tienes mas temas que gym jaja.",
            ],
            used_replies,
        )
    if signal == "contacto" and request.attraction >= 65:
        return first_fresh_reply(
            [
                "Vas bien, pero no te saltes la logistica: dime cuando y que plan tienes en mente.",
                "Ok, pero aterrizalo: cuando y que plan tienes en mente?",
            ],
            used_replies,
        )
    if signal == "cita":
        return first_fresh_reply(
            ["Me gusta cuando aterrizan el plan sin hacerlo intenso. Que idea tienes?", "Eso suena mejor. Cual seria el plan concreto?"],
            used_replies,
        )
    if signal == "humor":
        return first_fresh_reply(
            [
                "Jaja, ese tono me gusta mas. Sigue por ahi, pero no te pongas demasiado personaje.",
                "Jaja ok, ese humor si entra mejor. No lo quemes todavia.",
            ],
            used_replies,
        )
    if signal == "plan_suave":
        return first_fresh_reply(
            [
                "Un plan simple suena bien si la conversacion sigue asi de facil.",
                "Me gustan los planes simples cuando no se sienten forzados.",
            ],
            used_replies,
        )
    if score >= 8:
        return first_fresh_reply(
            [
                "jaja ok, eso estuvo mejor. Me gusta que no escribes como todos.",
                "jaja bien, ahi ya se siente mas natural.",
            ],
            used_replies,
        )
    if last_natalia:
        return first_fresh_reply(
            [
                "Jaja ok, eso me da curiosidad. Cuentame un poco mas, pero sin hacerlo entrevista.",
                "Mmm ok, me dio curiosidad. Desarrolla eso sin ponerte intenso.",
            ],
            used_replies,
        )
    return first_fresh_reply(
        [
            "Jaja, eso estuvo mejor. Sigue, quiero ver si de verdad tienes buena conversacion.",
            "Ok, arrancaste mejor. A ver si sostienes esa energia.",
        ],
        used_replies,
    )


def build_coach_prompt(
    request: SimulateTurnRequest,
    behavior: Dict[str, Any],
    cases_prompt: str,
    turn_analysis: Dict[str, Any],
) -> str:
    emojis = emoji_profile(request.user_message)
    return f"""Eres Natalia-Coach, un agente pedagogico separado de Natalia-Persona.
No eres la mujer del chat. Tu trabajo es evaluar el mensaje del hombre contra el contexto real visible.
No uses una plantilla fija ni penalices por no seguir un guion oculto.
Habla de la mujer como "Natalia" o "ella"; nunca digas "mi pregunta", "me dijiste" ni hables en primera persona como si fueras ella.

NIVEL:
- Nivel: {request.level}
- Perfil RAG: {behavior.get('profile')}
- Perfil pedagogico: {behavior.get('profile_label', behavior.get('profile'))}
- Receptividad: {behavior.get('receptivity')}
- Selectividad: {behavior.get('selectivity')}
- Estilo de ella: {behavior.get('style')}

CONTEXTO VISIBLE AUTORITATIVO:
{visible_context_text(request)}

ANALISIS COMPARTIDO DEL TURNO:
{turn_analysis_prompt(turn_analysis)}

DIRECTIVA OBLIGATORIA:
{turn_analysis.get('response_directive') or 'Responde al ultimo mensaje visible.'}

HISTORIAL VISIBLE:
{compact_history(request.history)}

MENSAJE DEL HOMBRE:
"{request.user_message}"

TIEMPO ELEGIDO:
{request.chosen_time}

EMOJIS DEL MENSAJE:
- Cantidad: {emojis['count']}
- Emojis unicos: {''.join(emojis['unique']) or '-'}
- Calibracion previa: {emojis['calibration']}
- Nota: {emojis['note']}

CASOS REALES RECUPERADOS:
{cases_prompt}

REGLA ANTI-ALUCINACION:
- Si una recomendacion no esta apoyada por el contexto visible o por casos recuperados, dilo como hipotesis suave o no la menciones.
- No inventes resultados, telefonos, citas ni intenciones de ella.
- Si el caso recuperado no coincide con el turno actual, ignora ese caso y prioriza el contexto visible.

METRICAS A EVALUAR:
- coherencia con el ultimo mensaje visible de Natalia
- naturalidad humana
- sobreinversion o necesidad
- humor/calibracion
- cantidad y calibracion de emojis (0-2 suele ser bien; exceso o sexualizacion temprana resta)
- si pregunta demasiado o ignora contexto
- si avanza hacia cita/numero cuando corresponde

Devuelve SOLO JSON valido:
{{
  "score": 1-10,
  "lose_life": true/false,
  "attraction_delta": -25..15,
  "feedback": "feedback en espanol latino, maximo 4 frases, accionable y especifico al mensaje real",
  "verdict": "good|acceptable|bad",
  "natalia_stance": "open|neutral|pull_back|challenge",
  "reason": "razon breve basada en el contexto visible",
  "suggestions": ["opcion A concreta", "opcion B concreta", "opcion C concreta"]
}}"""


MAXIMUS_ROUTE_PATTERNS = [
    r"^\s*maximus\b",
    r"\bcoach\b",
    r"\bqu[eé]\s+respondo\b",
    r"\bqu[eé]\s+le\s+respondo\b",
    r"\bqu[eé]\s+digo\b",
    r"\bqu[eé]\s+le\s+digo\b",
    r"\bc[oó]mo\s+le\s+respondo\b",
    r"\bc[oó]mo\s+respondo\b",
    r"\bc[oó]mo\s+la\s+cierro\b",
    r"\bc[oó]mo\s+pido\b",
    r"\baconsej",
    r"\bconsejo\b",
    r"\bestrategia\b",
    r"\btecnica\b",
    r"\bexplicame\b",
    r"\bexplicacion\b",
    r"\bopener\b",
    r"\babridor\b",
    r"\bprimera cita\b",
    r"\bfotos?\b",
    r"\bperfil\b.*\bfoto",
]


MAXIMUS_STAGE_HINTS = {
    "coach",
    "study",
    "estudiar",
    "game_over",
    "gameover",
    "summary",
    "resumen",
    "free_advice",
    "maximus",
}


def normalize_route_text(text: str) -> str:
    return clean_ui_text(text or "").lower()


def route_turn_request(request: SimulateTurnRequest) -> Dict[str, Any]:
    message = normalize_route_text(request.user_message)
    context = request.visible_context or {}
    stage = normalize_route_text(str(context.get("mode") or context.get("stage") or context.get("route") or ""))
    reasons: List[str] = []
    if stage in MAXIMUS_STAGE_HINTS:
        reasons.append(f"stage:{stage}")
    explicit_prefix = re.search(r"^\s*(maximus|coach)\b", message, re.IGNORECASE)
    if explicit_prefix:
        reasons.append("explicit_prefix")
    addressed_to_her = bool(
        re.search(
            r"\b(te|tu|tus|eres|estas|estás|vamos|salgamos|pasame|pásame|dame tu|te invito|nuestra\s+(primera\s+)?cita|me gustas|me encanta)\b",
            message,
            re.IGNORECASE,
        )
    )
    advice_patterns = [
        r"\bqu[eé]\s+(le\s+)?(respondo|digo)\b",
        r"\bc[oó]mo\s+(le\s+)?(respondo|digo|pido|cierro)\b",
        r"\b(dame|necesito|quiero)\s+(un\s+)?(consejo|tip|ejemplo|abridor|opener)\b",
        r"\b(aconsej|estrategia|tecnica|t[eé]cnica|explicame|expl[ií]came|analiza|evalua|eval[uú]a)\b",
        r"\b(foto|fotos|perfil)\b.*\b(recomiendas|mejorar|consejo|tip)\b",
        r"\b(primera cita|cita)\b.*\b(lugar|tema|consejo|recomiendas|tip|estrategia)\b",
    ]
    if not explicit_prefix and not addressed_to_her:
        for pattern in advice_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                reasons.append(f"advice:{pattern}")
                break
    route = "maximus" if reasons else "natalia"
    return {
        "route": route,
        "reasons": reasons,
        "stage": stage or "chat",
        "addressed_to_her": addressed_to_her,
    }


def maximus_intercept_message() -> str:
    return "Te contesta Maximus abajo; no voy a mezclar esto con el chat."


def build_maximus_prompt(request: SimulateTurnRequest, behavior: Dict[str, Any], cases_prompt: str) -> str:
    return f"""Eres Maximus, coach de text game del simulador Easy Date.
El usuario te esta pidiendo consejo; NO esta hablando con Natalia.
Responde en espanol latino, claro y accionable, sin inventar resultados no demostrados.

NIVEL ACTUAL:
- Perfil femenino: {behavior.get('profile_label', behavior.get('profile'))}
- Dificultad: {behavior.get('difficulty')}
- Estilo de Natalia: {behavior.get('style')}

CONTEXTO VISIBLE DEL CHAT:
{visible_context_text(request)}

HISTORIAL VISIBLE:
{compact_history(request.history)}

PREGUNTA DEL USUARIO:
"{request.user_message}"

EVIDENCIA RAG DISPONIBLE:
{cases_prompt}

REGLAS:
- Si no hay evidencia exacta, dilo con prudencia y da una recomendacion general.
- Separa: que pasa en el contexto, que conviene hacer, y 3 respuestas sugeridas.
- Puedes usar libros, Reddit, YouTube y casos negativos, pero no inventes citas, numeros ni WhatsApp.
- Maximo 7 frases antes de las opciones.

Devuelve SOLO JSON valido:
{{
  "answer": "respuesta breve de Maximus",
  "suggestions": ["opcion A concreta", "opcion B concreta", "opcion C concreta"]
}}"""


def fallback_maximus_answer(request: SimulateTurnRequest, coach_cases: List[Dict[str, str]]) -> Dict[str, Any]:
    suggestions = case_based_suggestions(coach_cases, analyze_visible_turn(request.user_message, authoritative_last_natalia(request), request.chosen_time))
    if not suggestions:
        suggestions = [
            "Jaja me gusta eso, pero tengo que ver si lo sostienes en persona.",
            "Eso suena peligroso... en el buen sentido.",
            "Me dio curiosidad, sigue.",
        ]
    return {
        "answer": (
            "Maximus: por el contexto, responde corto, con calma y sin explicar de mas. "
            "Mantén el tono juguetón y avanza solo si ella ya mostró receptividad."
        ),
        "suggestions": suggestions[:3],
    }


def build_natalia_prompt(
    request: SimulateTurnRequest,
    behavior: Dict[str, Any],
    cases_prompt: str,
    strategy_prompt: str,
    coach: Dict[str, Any],
    turn_analysis: Dict[str, Any],
) -> str:
    return f"""Eres Natalia-Persona, la mujer del chat de un simulador tipo Tinder.
Tu unica tarea es responder como una mujer real, no como coach, no expliques teoria.
Debes responder directamente al ultimo mensaje del hombre y mantener continuidad humana.
No avances a un tema oculto del nivel si el hombre hizo una pregunta o dio un dato concreto.
Si el hombre pregunta algo directo, contesta brevemente y luego puedes devolver una pregunta natural.
Si el hombre responde ubicacion y pregunta trabajo, reconoce la ubicacion y responde trabajo; no saltes a vino, numero o cita sin puente.

PERSONALIDAD DEL NIVEL:
- Nombre: {behavior.get('name')}
- Perfil RAG: {behavior.get('profile')}
- Perfil pedagogico: {behavior.get('profile_label', behavior.get('profile'))}
- Dificultad: {behavior.get('difficulty')}
- Estilo: {behavior.get('style')}
- Longitud: {behavior.get('reply_length')}
- Zona de Natalia: {behavior.get('location_area', 'zona por definir')}
- Trabajo de Natalia: {behavior.get('work_hint', 'trabajo creativo')}
- Fuera de rutina: {behavior.get('off_mode', 'planes tranquilos')}

ESTADO:
- Atraccion actual: {request.attraction}
- Vidas del usuario: {request.lives}
- Calidad estimada del mensaje: {coach.get('score')}
- Postura normalizada de Natalia: {coach.get('natalia_stance', 'neutral')}

CONTEXTO VISIBLE AUTORITATIVO:
{visible_context_text(request)}

ANALISIS COMPARTIDO DEL TURNO:
{turn_analysis_prompt(turn_analysis)}

DIRECTIVA OBLIGATORIA:
{turn_analysis.get('response_directive') or 'Responde al ultimo mensaje visible.'}

HISTORIAL VISIBLE:
{compact_history(request.history)}

ULTIMO MENSAJE DEL HOMBRE:
"{request.user_message}"

CASOS REALES PARA IMITAR NATURALIDAD:
{cases_prompt}

PRINCIPIOS TEXT GAME PARA RAZONAR EN SILENCIO:
{strategy_prompt}

USO DE PRINCIPIOS:
- Estos principios de libros solo ayudan a calibrar estrategia, timing, inversion, humor, tension y cierre.
- No los cites, no expliques teoria y no respondas como coach.
- La respuesta final debe sonar como una mujer real dentro del chat visible.

REGLAS:
- Responde en espanol latino natural.
- Usa los pares/casos reales solo como inspiracion de tono, longitud y patron conversacional.
- No copies un caso si el tema no coincide con el ultimo mensaje visible.
- Si los casos recuperados contradicen el contexto visible, ignoralos y responde al contexto visible.
- No inventes datos fuera del contexto visible: no inventes ubicacion, numero, cita, gustos ni historia personal.
- 1 mensaje corto, maximo 22 palabras.
- Puedes usar maximo 1 emoji si se siente natural; no satures.
- Si el mensaje del hombre ignora lo que dijiste, reacciona a eso.
- Si es generico, responde tibia o con una prueba suave.
- Si es bueno, abre un poco mas la conversacion.
- No entregues telefono/cita de inmediato salvo que el contexto ya lo justifique.
- No menciones score, coach, RAG, base de datos ni reglas.

Devuelve SOLO JSON valido:
{{"message": "respuesta de Natalia", "reply_time": "Tardó: 15 min"}}"""


def response_has_required_topic(message: str, required_topics: List[str]) -> bool:
    if not required_topics:
        return True
    if required_topics == ["pregunta_contextual"]:
        response_topics = topic_set(message)
        if response_topics.intersection({"vino", "contacto", "ubicacion"}):
            return False
        lowered = clean_ui_text(message).lower()
        strong_plan_tokens = [
            "salir",
            "cita",
            "vernos",
            "lugar",
            "copa",
            "tomar",
            "jueves",
            "viernes",
            "sabado",
            "sábado",
            "domingo",
            "whatsapp",
            "numero",
            "número",
            "telefono",
            "teléfono",
        ]
        return not any(token in lowered for token in strong_plan_tokens)
    response_topics = topic_set(message)
    return bool(response_topics.intersection(required_topics))


def response_introduces_unrelated_topic(message: str, allowed_topics: set[str]) -> bool:
    response_topics = topic_set(message)
    if not response_topics:
        return False
    bridge_topics = {"plan", "contacto"}
    unexpected = response_topics - allowed_topics
    if unexpected and not response_topics.intersection(allowed_topics):
        return True
    if unexpected.intersection(bridge_topics) and not allowed_topics.intersection(bridge_topics):
        return True
    return False


def natalia_response_is_invalid(message: str, score: int, turn_analysis: Optional[Dict[str, Any]] = None) -> bool:
    lowered = (message or "").lower()
    if not lowered.strip():
        return True
    if looks_non_spanish_reply(message):
        return True
    forbidden = ["coach", "score", "puntaje", "rag", "base de datos", "regla", "mÃ©trica", "metrica"]
    if any(word in lowered for word in forbidden):
        return True
    if len(message.split()) > 28:
        return True
    too_warm = ["me encanta", "perfecto", "genial", "suena super", "me gustas", "obvio"]
    too_cold = ["aburrido", "no me interesa", "paso", "next", "que flojera"]
    if score <= 4 and any(phrase in lowered for phrase in too_warm):
        return True
    if score >= 8 and any(phrase in lowered for phrase in too_cold):
        return True
    if turn_analysis:
        direct_topics = [str(topic) for topic in turn_analysis.get("direct_question_topics") or []]
        if direct_topics and not response_has_required_topic(message, direct_topics):
            return True
        allowed_topics = set(str(topic) for topic in (turn_analysis.get("user_topics") or []))
        allowed_topics.update(str(topic) for topic in (turn_analysis.get("last_topics") or []))
        allowed_topics.update(direct_topics)
        if direct_topics != ["pregunta_contextual"] and allowed_topics and response_introduces_unrelated_topic(message, allowed_topics):
            return True
    return False


@app.post("/api/simulate-turn", response_model=SimulateTurnResponse)
def simulate_turn(request: SimulateTurnRequest):
    behavior = level_behavior(request.level)
    route_info = route_turn_request(request)
    persona_cases = retrieve_persona_cases(request, behavior)
    strategy_cases = [] if route_info["route"] == "maximus" else retrieve_persona_strategy_cases(request, behavior)
    coach_cases = retrieve_coach_cases(request, behavior, persona_cases)
    cases_prompt = cases_to_prompt(coach_cases, max_cases=6, max_text_chars=550)
    natalia_cases_prompt = persona_cases_to_prompt(persona_cases, limit=5, max_text_chars=420)
    strategy_prompt = cases_to_prompt(strategy_cases, max_cases=2, max_text_chars=450)
    last_natalia = authoritative_last_natalia(request)
    turn_analysis = analyze_visible_turn(request.user_message, last_natalia, request.chosen_time)
    turn_metrics = turn_metrics_for_message(request.user_message, last_natalia, request.chosen_time, turn_analysis)
    fallback = False
    coach_live_used = False
    natalia_live_used = False
    natalia_fallback_category = ""
    natalia_fallback_reason = ""

    if route_info["route"] == "maximus":
        maximus_live_used = False
        maximus_fallback_category = ""
        try:
            if not gemini_live_enabled():
                raise RuntimeError("Gemini live disabled")
            maximus_raw = rotator.generate_content(build_maximus_prompt(request, behavior, cases_prompt))
            maximus = json_from_model(maximus_raw)
            maximus_live_used = True
        except Exception as exc:
            print(f"WARNING: maximus fallback: {exc}")
            maximus_fallback_category = fallback_category(exc)
            maximus = fallback_maximus_answer(request, coach_cases)
            fallback = True

        suggestions = [
            clean_ui_text(item)
            for item in maximus.get("suggestions", [])
            if clean_ui_text(item)
        ][:3]
        answer = clean_ui_text(maximus.get("answer")) or fallback_maximus_answer(request, coach_cases)["answer"]
        if suggestions:
            answer += "\n\nOpciones mejores:\n" + "\n".join(
                f"{chr(65 + index)}. {item}" for index, item in enumerate(suggestions)
            )
        returned_cases = [
            {
                "source": case.get("source", ""),
                "post_id": case.get("post_id", ""),
                "profile": case.get("profile", ""),
                "intent": case.get("intent", ""),
                "woman_signal": case.get("woman_signal", ""),
                "success_score": case.get("success_score", ""),
            }
            for case in coach_cases[:10]
        ]
        retrieval_summary = retrieval_summary_for_cases(coach_cases, persona_cases, strategy_cases)
        retrieval_summary.update(
            {
                "gemini_coach_enabled": gemini_coach_enabled(),
                "coach_live_used": maximus_live_used,
                "natalia_live_used": False,
                "maximus_live_used": maximus_live_used,
                "maximus_fallback_category": maximus_fallback_category,
                "passing_score": passing_score_for_behavior(behavior),
                "route": route_info["route"],
                "route_reasons": route_info["reasons"],
                "route_stage": route_info["stage"],
                "addressed_to_her": route_info.get("addressed_to_her", False),
            }
        )
        return SimulateTurnResponse(
            natalia_message="",
            natalia_time="Maximus",
            coach_title="Maximus Coach",
            coach_feedback=answer,
            score=10,
            lose_life=False,
            attraction_delta=0,
            suggestions=suggestions,
            retrieved_cases=returned_cases,
            retrieval_summary=retrieval_summary,
            fallback=fallback,
            turn_analysis=turn_analysis,
            turn_metrics=turn_metrics,
        )

    if gemini_live_enabled() and gemini_coach_enabled():
        try:
            coach_raw = rotator.generate_content(build_coach_prompt(request, behavior, cases_prompt, turn_analysis))
            coach = json_from_model(coach_raw)
            coach_live_used = True
        except Exception as exc:
            print(f"WARNING: coach fallback: {exc}")
            coach = heuristic_score(request.user_message, request.chosen_time, last_natalia, coach_cases)
            fallback = True
    else:
        coach = heuristic_score(request.user_message, request.chosen_time, last_natalia, coach_cases)
        if not gemini_live_enabled():
            fallback = True

    score = max(1, min(10, int(coach.get("score", 5))))
    passing_score = passing_score_for_behavior(behavior)
    lose_life = score < passing_score or bool(coach.get("lose_life", False))
    attraction_delta = int(coach.get("attraction_delta", 10 if score >= 8 else -10 if score < 6 else 3))
    if route_info["route"] == "maximus":
        lose_life = False
        attraction_delta = 0
    suggestions = [
        clean_ui_text(item)
        for item in coach.get("suggestions", [])
        if clean_ui_text(item)
    ][:3]
    suggestions = merge_suggestions(suggestions, case_based_suggestions(persona_cases, turn_analysis))
    feedback = clean_ui_text(coach.get("feedback")) or "Evalua mejor el contexto visible antes de responder."
    if score >= 6 and score < passing_score:
        feedback += (
            f"\n\nExigencia del nivel: este perfil es mas selectivo; aqui necesitas "
            f"{passing_score}/10 o mas para no perder vida."
        )

    try:
        natalia_raw = rotator.generate_content(
            build_natalia_prompt(
                request,
                behavior,
                natalia_cases_prompt,
                strategy_prompt,
                coach,
                turn_analysis,
            )
        )
        natalia = natalia_payload_from_model(natalia_raw)
        natalia_message = clean_ui_text(natalia.get("message"))
        natalia_time = clean_ui_text(natalia.get("reply_time", "Tardó: 15 min"))
        if natalia_response_is_invalid(natalia_message, score, turn_analysis):
            raise ValueError("Natalia returned invalid or incoherent message.")
        natalia_live_used = True
    except Exception as exc:
        print(f"WARNING: natalia fallback: {exc}")
        natalia_fallback_category = fallback_category(exc)
        natalia_fallback_reason = fallback_reason_text(exc)
        natalia_message = fallback_natalia_message(request, score, behavior, persona_cases)
        natalia_time = "Tardó: 15 min"
        fallback = True

    if route_info["route"] == "maximus":
        natalia_message = maximus_intercept_message()
        natalia_time = "Maximus"
        natalia_live_used = False

    title = "Maximus Coach" if route_info["route"] == "maximus" else "Buena respuesta" if score >= passing_score + 1 else "Respuesta aceptable" if not lose_life else "Respuesta incorrecta"
    coach_feedback = feedback
    if suggestions:
        coach_feedback += "\n\nOpciones mejores:\n" + "\n".join(
            f"{chr(65 + index)}. {item}" for index, item in enumerate(suggestions)
        )

    returned_cases = [
        {
            "source": case.get("source", ""),
            "post_id": case.get("post_id", ""),
            "profile": case.get("profile", ""),
            "intent": case.get("intent", ""),
            "woman_signal": case.get("woman_signal", ""),
            "success_score": case.get("success_score", ""),
        }
        for case in coach_cases[:10]
    ]
    retrieval_summary = retrieval_summary_for_cases(coach_cases, persona_cases, strategy_cases)
    retrieval_summary.update(
        {
            "gemini_coach_enabled": gemini_coach_enabled(),
            "coach_live_used": coach_live_used,
            "natalia_live_used": natalia_live_used,
            "natalia_fallback_category": natalia_fallback_category,
            "natalia_fallback_reason": natalia_fallback_reason,
            "passing_score": passing_score,
            "route": route_info["route"],
            "route_reasons": route_info["reasons"],
            "route_stage": route_info["stage"],
            "addressed_to_her": route_info.get("addressed_to_her", False),
        }
    )

    return SimulateTurnResponse(
        natalia_message=natalia_message,
        natalia_time=natalia_time or "Tardó: 15 min",
        coach_title=title,
        coach_feedback=coach_feedback,
        score=score,
        lose_life=lose_life,
        attraction_delta=attraction_delta,
        suggestions=suggestions,
        retrieved_cases=returned_cases,
        retrieval_summary=retrieval_summary,
        fallback=fallback,
        turn_analysis=turn_analysis,
        turn_metrics=turn_metrics,
    )


@app.post("/api/evaluate", response_model=EvaluateResponse)
def evaluate(request: EvaluateRequest):
    context_texts: List[str] = []

    if chroma_collection and chroma_query_enabled():
        try:
            results = chroma_collection.query(query_texts=[request.user_message], n_results=3)
            if results and results.get("documents"):
                context_texts = results["documents"][0]
        except Exception as exc:
            print(f"Error querying ChromaDB: {exc}")

    context_str = "\n".join(context_texts) if context_texts else "No hay casos similares disponibles."
    history_str = ""
    for msg in request.history:
        role = "Usuario" if msg.get("role") == "user" else "NPC"
        history_str += f"{role}: {msg.get('content')}\n"

    prompt = f"""Eres Natalia-Coach, el agente pedagogico separado de Natalia-Persona.
Evalua mensajes de texto en un simulador tipo Tinder. Se corto, directo y usa espanol simple.
No eres la mujer del chat y no debes hablar como si fueras ella.

CONTEXTO DEL NIVEL:
{level_context_for(request.level) or f"Nivel {request.level} - App de citas."}

CASOS REALES SIMILARES:
{context_str}

HISTORIAL:
{history_str}

MENSAJE DEL USUARIO:
"{request.user_message}"

INSTRUCCIONES:
1. Califica del 1 al 10.
2. Da feedback en maximo 2 frases cortas.
3. Sugiere 1-2 alternativas concretas si el mensaje puede mejorar.

Responde SOLO con este JSON:
{{"score": <1-10>, "feedback": "<2 frases max>", "suggestions": ["<alternativa1>", "<alternativa2>"]}}"""

    try:
        raw = rotator.generate_content(prompt)
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            score = 5
            feedback_text = clean_ui_text(raw)
            suggestions = []
        else:
            try:
                parsed = json.loads(json_match.group())
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=502, detail=f"Gemini returned invalid JSON: {exc}")
            score = max(1, min(10, int(parsed.get("score", 5))))
            feedback_text = clean_ui_text(parsed.get("feedback")) or "Sin feedback."
            raw_suggestions = parsed.get("suggestions", [])
            suggestions = [clean_ui_text(item) for item in raw_suggestions if clean_ui_text(item)]
    except Exception as exc:
        print(f"WARNING: evaluate fallback: {exc}")
        last_natalia = latest_turn_text(request.history, "her")
        heuristic = heuristic_score(request.user_message, "", last_natalia)
        score = int(heuristic.get("score", 5))
        feedback_text = clean_ui_text(heuristic.get("feedback")) or "Evalua mejor el contexto visible."
        suggestions = [clean_ui_text(item) for item in heuristic.get("suggestions", []) if clean_ui_text(item)]

    evaluation = f"* {score}/10\n\n{feedback_text}"
    if suggestions:
        evaluation += "\n\nOpciones:\n" + "\n".join(f'- "{item}"' for item in suggestions)

    updated_history = request.history.copy()
    updated_history.append({"role": "user", "content": request.user_message})
    updated_history.append({"role": "assistant", "content": "[Natalia-Coach] Feedback generado; Natalia-Persona responde por /api/simulate-turn."})

    return EvaluateResponse(
        evaluation=evaluation,
        score=score,
        next_state="WAITING_USER",
        new_history=updated_history,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
