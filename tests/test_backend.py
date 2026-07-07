import importlib
import sqlite3
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_server(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY_1", "test-key-1")
    monkeypatch.setenv("GEMINI_API_KEY_2", "test-key-2")
    monkeypatch.setenv("GEMINI_API_KEY_3", "test-key-3")
    monkeypatch.setenv("GEMINI_LIVE_ENABLED", "1")
    monkeypatch.setenv("CHROMA_QUERY_ENABLED", "1")

    import backend.server as server

    return importlib.reload(server)


def test_health_reports_runtime_state(monkeypatch):
    server = load_server(monkeypatch)
    client = TestClient(server.app)

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["simulator"] == "simulador_v1.2.html"
    assert data["simulator_exists"] is True
    assert data["gemini_sdk"] == "google-genai"
    assert data["gemini_live_enabled"] is True
    assert data["gemini_coach_enabled"] is True
    assert data["gemini_keys_loaded"] >= 3
    assert data["chroma_query_enabled"] is True
    assert data["chroma_collection"] == "natalia_conversations"


def test_route_turn_request_sends_advice_to_maximus(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        user_message="Maximus, que le respondo para pedir WhatsApp?",
        visible_context={"last_natalia_message": "jaja no se, sorprendeme"},
    )

    route = server.route_turn_request(request)

    assert route["route"] == "maximus"
    assert route["reasons"]


def test_route_turn_request_keeps_normal_chat_with_natalia(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        user_message="Jaja me gusta eso, yo tambien soy de planes tranquilos",
        visible_context={"last_natalia_message": "prefiero planes tranquilos"},
    )

    route = server.route_turn_request(request)

    assert route["route"] == "natalia"
    assert route["reasons"] == []


def test_route_turn_request_does_not_steal_direct_cita_chat(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        user_message="Jaja entonces cuando es nuestra primera cita?",
        visible_context={"last_natalia_message": "me gusta como piensas"},
    )

    route = server.route_turn_request(request)

    assert route["route"] == "natalia"
    assert route["addressed_to_her"] is True


def test_natalia_prompt_uses_books_as_silent_strategy(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        user_message="Me gusta esa energia, deberiamos tomar algo pronto",
        visible_context={"last_natalia_message": "jaja me dio curiosidad"},
    )

    prompt = server.build_natalia_prompt(
        request,
        server.level_behavior(1),
        "CASO real hombre-mujer",
        "Fuente libro: Text Game\nConceptos: cierre, timing\nPrincipio de inversion y cierre suave.",
        {"score": 8, "natalia_stance": "open"},
        {"response_directive": "Responde al ultimo mensaje visible."},
    )

    assert "PRINCIPIOS TEXT GAME PARA RAZONAR EN SILENCIO" in prompt
    assert "No los cites" in prompt
    assert "no respondas como coach" in prompt


def test_simulate_turn_reports_strategy_context(monkeypatch):
    monkeypatch.setenv("GEMINI_COACH_ENABLED", "0")
    server = load_server(monkeypatch)

    monkeypatch.setattr(server, "retrieve_persona_cases", lambda request, behavior: [])
    monkeypatch.setattr(
        server,
        "retrieve_persona_strategy_cases",
        lambda request, behavior: [
            {
                "source": "books_chroma",
                "profile": "teoria_libros",
                "concepts": "cierre, timing",
                "text": "Fuente libro: Text Game\nConceptos: cierre, timing\nCierre suave.",
            }
        ],
    )
    monkeypatch.setattr(server, "retrieve_coach_cases", lambda request, behavior, persona_cases: [])

    prompts = []

    def fake_generate_content(prompt):
        prompts.append(prompt)
        return '{"message": "Jaja eso suena peligroso, pero me dio curiosidad.", "reply_time": "Tardo: 15 min"}'

    monkeypatch.setattr(server.rotator, "generate_content", fake_generate_content)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 1,
            "evaluated_step_id": 2,
            "lives": 4,
            "attraction": 50,
            "history": [{"sender": "her", "text": "jaja me dio curiosidad"}],
            "user_message": "Me gusta esa energia, deberiamos tomar algo pronto",
            "chosen_time": "15m",
            "visible_context": {"last_natalia_message": "jaja me dio curiosidad"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["retrieval_summary"]["strategy_context_cases"] == 1
    assert data["retrieval_summary"]["strategy_sources"]["books_chroma"] == 1
    assert any("PRINCIPIOS TEXT GAME PARA RAZONAR EN SILENCIO" in prompt for prompt in prompts)


def test_simulate_turn_maximus_route_does_not_spend_life(monkeypatch):
    monkeypatch.setenv("GEMINI_COACH_ENABLED", "0")
    server = load_server(monkeypatch)

    def fake_generate_content(_prompt):
        return '{"message": "respuesta temporal", "reply_time": "Tardo: 15 min"}'

    monkeypatch.setattr(server.rotator, "generate_content", fake_generate_content)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 3,
            "step_index": 2,
            "evaluated_step_id": 3,
            "lives": 2,
            "attraction": 45,
            "history": [{"sender": "her", "text": "jaja no se, sorprendeme"}],
            "user_message": "Maximus, que le respondo para pedir WhatsApp?",
            "chosen_time": "15m",
            "visible_context": {"last_natalia_message": "jaja no se, sorprendeme"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["coach_title"] == "Maximus Coach"
    assert data["lose_life"] is False
    assert data["attraction_delta"] == 0
    assert data["natalia_time"] == "Maximus"
    assert data["retrieval_summary"]["route"] == "maximus"
    assert data["retrieval_summary"]["natalia_live_used"] is False


def test_simulate_turn_writes_turn_audit_log(monkeypatch, tmp_path):
    server = load_server(monkeypatch)
    monkeypatch.setenv("GEMINI_LIVE_ENABLED", "0")
    db_path = tmp_path / "textgame.db"
    sqlite3.connect(db_path).close()
    monkeypatch.setattr(server, "DB_PATH", db_path)
    monkeypatch.setattr(server, "retrieve_persona_cases", lambda request, behavior: [])
    monkeypatch.setattr(server, "retrieve_persona_strategy_cases", lambda request, behavior: [])
    monkeypatch.setattr(server, "retrieve_coach_cases", lambda request, behavior, persona_cases: [])
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 0,
            "evaluated_step_id": 1,
            "lives": 4,
            "attraction": 50,
            "history": [{"sender": "her", "text": "Hola :)"}],
            "user_message": "Hola, que tal tu dia?",
            "chosen_time": "15m",
            "visible_context": {"last_natalia_message": "Hola :)"},
        },
    )

    assert response.status_code == 200
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT route, score, user_message_preview FROM turn_audit_log ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    assert row == ("natalia", response.json()["score"], "Hola, que tal tu dia?")


def test_simulate_turn_can_use_local_coach_and_live_natalia(monkeypatch):
    monkeypatch.setenv("GEMINI_COACH_ENABLED", "0")
    server = load_server(monkeypatch)
    prompts = []

    def fake_generate_content(prompt):
        prompts.append(prompt)
        return '{"message": "Trabajo en marketing visual, pero lo interesante es que haces fuera del gym.", "reply_time": "Tardo: 15 min"}'

    monkeypatch.setattr(server.rotator, "generate_content", fake_generate_content)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 2,
            "evaluated_step_id": 3,
            "lives": 4,
            "attraction": 50,
            "history": [
                {"sender": "her", "text": "me gusta eso, perfecto donde vives? yo en brickell y tu?"},
                {"sender": "user", "text": "yo vivo en bogota y en que trabajas?", "timeText": "1h"},
            ],
            "user_message": "yo vivo en bogota y en que trabajas?",
            "chosen_time": "1h",
            "visible_context": {
                "last_natalia_message": "me gusta eso, perfecto donde vives? yo en brickell y tu?",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(prompts) == 1
    assert "Natalia-Persona" in prompts[0]
    assert data["fallback"] is False
    assert data["retrieval_summary"]["gemini_coach_enabled"] is False
    assert data["retrieval_summary"]["coach_live_used"] is False
    assert data["retrieval_summary"]["natalia_live_used"] is True


def test_gemini_rotator_uses_quota_cooldown_after_all_keys_429(monkeypatch):
    server = load_server(monkeypatch)
    calls = []

    class FakeClient:
        def __init__(self, api_key, http_options=None):
            self.api_key = api_key
            self.http_options = http_options
            self.models = self

        def generate_content(self, model, contents):
            calls.append((self.api_key, model, contents))
            raise RuntimeError("429 quota exhausted")

    class FakeGoogleGenai:
        Client = FakeClient

    monkeypatch.setenv("GEMINI_QUOTA_COOLDOWN_SECONDS", "600")
    monkeypatch.setenv("GEMINI_MODEL_FALLBACKS", "")
    monkeypatch.setattr(server, "collect_gemini_keys", lambda: ["k1", "k2", "k3"])
    monkeypatch.setattr(server, "google_genai", FakeGoogleGenai)
    monkeypatch.setattr(server, "legacy_genai", None)

    rotator = server.GeminiRotator()

    with pytest.raises(server.HTTPException) as first:
        rotator.generate_content("hola")

    assert first.value.status_code == 429
    assert [call[0] for call in calls] == ["k1", "k2", "k3"]

    with pytest.raises(server.HTTPException) as second:
        rotator.generate_content("hola otra vez")

    assert second.value.status_code == 429
    assert [call[0] for call in calls] == ["k1", "k2", "k3"]


def test_gemini_rotator_enters_cooldown_when_any_key_hits_429(monkeypatch):
    server = load_server(monkeypatch)
    calls = []
    errors = {
        "k1": RuntimeError("504 upstream timeout"),
        "k2": RuntimeError("429 quota exhausted"),
        "k3": RuntimeError("429 quota exhausted"),
    }

    class FakeClient:
        def __init__(self, api_key, http_options=None):
            self.api_key = api_key
            self.models = self

        def generate_content(self, model, contents):
            calls.append(self.api_key)
            raise errors[self.api_key]

    class FakeGoogleGenai:
        Client = FakeClient

    monkeypatch.setenv("GEMINI_QUOTA_COOLDOWN_SECONDS", "600")
    monkeypatch.setenv("GEMINI_MODEL_FALLBACKS", "")
    monkeypatch.setattr(server, "collect_gemini_keys", lambda: ["k1", "k2", "k3"])
    monkeypatch.setattr(server, "google_genai", FakeGoogleGenai)
    monkeypatch.setattr(server, "legacy_genai", None)

    rotator = server.GeminiRotator()

    with pytest.raises(server.HTTPException) as first:
        rotator.generate_content("hola")

    assert first.value.status_code == 429
    assert calls == ["k1", "k2", "k3"]

    with pytest.raises(server.HTTPException) as second:
        rotator.generate_content("hola otra vez")

    assert second.value.status_code == 429
    assert calls == ["k1", "k2", "k3"]


def test_gemini_call_timeout_respects_provider_minimum(monkeypatch):
    server = load_server(monkeypatch)

    assert server.GEMINI_CALL_TIMEOUT_MS >= 10000
    assert server.GEMINI_HARD_TIMEOUT_SECONDS >= (server.GEMINI_CALL_TIMEOUT_MS + 999) // 1000 + 5


def test_gemini_rotator_hard_timeout_enters_cooldown(monkeypatch):
    server = load_server(monkeypatch)
    calls = []

    class SlowClient:
        def __init__(self, api_key, http_options=None):
            self.api_key = api_key
            self.models = self

        def generate_content(self, model, contents):
            calls.append(self.api_key)
            time.sleep(1)
            return type("Response", (), {"text": "too late"})()

    class FakeGoogleGenai:
        Client = SlowClient

    monkeypatch.setenv("GEMINI_QUOTA_COOLDOWN_SECONDS", "600")
    monkeypatch.setenv("GEMINI_MODEL_FALLBACKS", "")
    monkeypatch.setattr(server, "GEMINI_HARD_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(server, "collect_gemini_keys", lambda: ["k1", "k2", "k3"])
    monkeypatch.setattr(server, "google_genai", FakeGoogleGenai)
    monkeypatch.setattr(server, "legacy_genai", None)

    rotator = server.GeminiRotator()

    with pytest.raises(server.HTTPException) as first:
        rotator.generate_content("hola")

    assert first.value.status_code == 504
    assert calls == ["k1"]

    with pytest.raises(server.HTTPException) as second:
        rotator.generate_content("hola otra vez")

    assert second.value.status_code == 429
    assert calls == ["k1"]


def test_gemini_rotator_falls_back_to_lite_model(monkeypatch):
    server = load_server(monkeypatch)
    calls = []

    class FakeClient:
        def __init__(self, api_key, http_options=None):
            self.api_key = api_key
            self.models = self

        def generate_content(self, model, contents):
            calls.append((self.api_key, model))
            if model == "gemini-2.5-flash":
                raise RuntimeError("429 quota exhausted")
            return type("Response", (), {"text": '{"ok": true}'})()

    class FakeGoogleGenai:
        Client = FakeClient

    monkeypatch.setenv("GEMINI_MODEL_FALLBACKS", "gemini-2.5-flash-lite")
    monkeypatch.setattr(server, "collect_gemini_keys", lambda: ["k1"])
    monkeypatch.setattr(server, "google_genai", FakeGoogleGenai)
    monkeypatch.setattr(server, "legacy_genai", None)

    rotator = server.GeminiRotator()

    assert rotator.generate_content("hola") == '{"ok": true}'
    assert calls == [
        ("k1", "gemini-2.5-flash"),
        ("k1", "gemini-2.5-flash-lite"),
    ]


def test_gemini_live_disabled_skips_provider_call(monkeypatch):
    server = load_server(monkeypatch)
    calls = []

    class FakeClient:
        def __init__(self, api_key, http_options=None):
            self.models = self

        def generate_content(self, model, contents):
            calls.append(contents)
            return type("Response", (), {"text": "no deberia llamarse"})()

    class FakeGoogleGenai:
        Client = FakeClient

    monkeypatch.setenv("GEMINI_LIVE_ENABLED", "0")
    monkeypatch.setattr(server, "collect_gemini_keys", lambda: ["k1"])
    monkeypatch.setattr(server, "google_genai", FakeGoogleGenai)
    monkeypatch.setattr(server, "legacy_genai", None)

    rotator = server.GeminiRotator()

    with pytest.raises(server.HTTPException) as exc:
        rotator.generate_content("hola")

    assert exc.value.status_code == 503
    assert calls == []


def test_chroma_query_disabled_skips_collection(monkeypatch):
    server = load_server(monkeypatch)

    class ExplodingCollection:
        def query(self, *args, **kwargs):
            raise AssertionError("Chroma should not be queried when disabled")

    monkeypatch.setenv("CHROMA_QUERY_ENABLED", "0")
    monkeypatch.setattr(server, "chroma_collection", ExplodingCollection())

    assert server.retrieve_chroma_cases("hola", "coqueta") == []


def test_coach_suggestions_fills_without_duplicate_loop(monkeypatch):
    server = load_server(monkeypatch)
    analysis = server.analyze_visible_turn(
        "Trato hecho, te escribo con el lugar y sin discurso intenso 😉",
        "Mmm, va... pero usalo bien. Si el plan es bueno, te respondo 😉",
        "15m",
    )
    emojis = server.emoji_profile("Trato hecho, te escribo con el lugar y sin discurso intenso 😉")

    suggestions = server.coach_suggestions(
        ["emojis calibrados"],
        analysis,
        emojis,
        "cerrar_plan",
    )

    assert len(suggestions) == 3
    assert len(set(suggestions)) == 3


def test_turn_metrics_separates_context_objective_and_emojis(monkeypatch):
    server = load_server(monkeypatch)
    message = "Jaja trato hecho, jueves una copa corta y te escribo por WhatsApp 😉"
    analysis = server.analyze_visible_turn(message, "Mmm, si el plan es bueno te respondo.", "15m")

    metrics = server.turn_metrics_for_message(message, "Mmm, si el plan es bueno te respondo.", "15m", analysis)

    assert metrics["objective"]["moves_toward_contact_or_date"] is True
    assert metrics["tone"]["emoji_calibration"] == "calibrados"
    assert metrics["message_quality"]["overinvestment_risk"] <= 2
    assert metrics["context"]["context_congruence"] >= 5


def test_turn_metrics_flags_excessive_emojis_and_overinvestment(monkeypatch):
    server = load_server(monkeypatch)
    message = (
        "Hola hermosa por favor contestame, de verdad quiero conocerte y explicarte todo "
        "lo que siento porque eres preciosa y porque creo que podriamos tener una conexion "
        "muy especial si me das la oportunidad de contarte bien quien soy 😍😍😍😍"
    )
    analysis = server.analyze_visible_turn(message, "", "Ahora mismo")

    metrics = server.turn_metrics_for_message(message, "", "Ahora mismo", analysis)

    assert metrics["tone"]["emoji_calibration"] in {"excesivos", "demasiado romanticos"}
    assert metrics["message_quality"]["neediness_risk"] >= 7
    assert metrics["message_quality"]["overinvestment_risk"] > 0
    assert metrics["timing"]["too_immediate"] is True


def test_clean_ui_text_repairs_mojibake(monkeypatch):
    server = load_server(monkeypatch)

    assert server.clean_ui_text("TardÃ³: 15 min") == "Tardó: 15 min"
    assert server.clean_ui_text("Primero tendrÃ­amos que salir") == "Primero tendríamos que salir"


def test_clean_ui_text_repairs_double_mojibake_with_ascii_escapes(monkeypatch):
    server = load_server(monkeypatch)

    assert server.clean_ui_text("TardÃƒÂ³: 15 min") == "Tard\u00f3: 15 min"
    assert server.clean_ui_text("Primero tendrÃƒÂ­amos que salir") == "Primero tendr\u00edamos que salir"


def test_direct_question_topics_accepts_real_spanish_accents(monkeypatch):
    server = load_server(monkeypatch)

    assert server.direct_question_topics("¿En qué trabajas?", set()) == ["trabajo"]
    assert server.direct_question_topics("¿Dónde vives?", set()) == ["ubicacion"]
    assert server.direct_question_topics("¿Qué tal tu día?", set()) == ["dia"]


def test_question_detection_ignores_trailing_emoji_replacement_marks(monkeypatch):
    server = load_server(monkeypatch)
    message = "Trato hecho, te escribo con el lugar y sin discurso intenso ??"
    last = "Mmm, va... pero usalo bien. Si el plan es bueno, te respondo ??"

    analysis = server.analyze_visible_turn(message, last, "15m")
    score = server.heuristic_score(message, "15m", last)

    assert server.meaningful_question_mark_count(message) == 0
    assert analysis["asked_question"] is False
    assert analysis["direct_question_topics"] == []
    assert "demasiadas preguntas" not in score["feedback"]


def test_question_detection_handles_broken_accent_question_marks(monkeypatch):
    server = load_server(monkeypatch)

    music = server.analyze_visible_turn(
        "Y a ti qu? m?sica te gusta?",
        "jaja ok, eso me da curiosidad.",
        "15m",
    )
    work = server.analyze_visible_turn(
        "Vivo en Bogot?. ?Y t? en qu? trabajas?",
        "me gusta eso, perfecto donde vives?",
        "15m",
    )
    score = server.heuristic_score(
        "Y a ti qu? m?sica te gusta?",
        "15m",
        "jaja ok, eso me da curiosidad.",
    )

    assert music["direct_question_topics"] == ["musica"]
    assert music["asked_question"] is True
    assert work["direct_question_topics"] == ["trabajo"]
    assert "ubicacion" in work["answered_topics"]
    assert "demasiadas preguntas" not in score["feedback"]


def test_question_detection_handles_broken_accent_week_question(monkeypatch):
    server = load_server(monkeypatch)

    score = server.heuristic_score(
        "Hola Natalia, qu? lindo tu perfil. ?C?mo va tu semana?",
        "15m",
        "Hola, soy Natalia. Tu abridor decide si respondo o no.",
    )
    analysis = server.analyze_visible_turn(
        "Hola Natalia, qu? lindo tu perfil. ?C?mo va tu semana?",
        "Hola, soy Natalia. Tu abridor decide si respondo o no.",
        "15m",
    )

    assert analysis["direct_question_topics"] == ["dia"]
    assert "demasiadas preguntas" not in score["feedback"]


def test_direct_question_topics_prefers_active_question_segment(monkeypatch):
    server = load_server(monkeypatch)
    message = "Me gusta bailar, pero tambien un lugar tranquilo. ?Qu? comida te gusta?"

    analysis = server.analyze_visible_turn(message, "jaja ok, eso me da curiosidad.", "15m")
    request = server.SimulateTurnRequest(
        level=1,
        step_index=4,
        evaluated_step_id=5,
        lives=4,
        attraction=70,
        history=[{"sender": "her", "text": "jaja ok, eso me da curiosidad."}],
        user_message=message,
        chosen_time="15m",
        visible_context={"last_natalia_message": "jaja ok, eso me da curiosidad."},
    )

    reply = server.fallback_natalia_message(request, 8, server.level_behavior(1), [])

    assert analysis["direct_question_topics"] == ["comida"]
    assert any(token in reply.lower() for token in ["comida", "lugar", "recomendacion"])
    assert "playlist" not in reply.lower()


def test_broken_accent_question_prefers_last_cue_when_marker_is_removed(monkeypatch):
    server = load_server(monkeypatch)
    message = "Cuando no estoy ocupado me gusta bailar y salir por algo rico. Y a ti qu? m?sica te gusta?"

    analysis = server.analyze_visible_turn(message, "Hago marketing visual. Y tu?", "15m")
    request = server.SimulateTurnRequest(
        level=1,
        step_index=3,
        evaluated_step_id=4,
        lives=4,
        attraction=70,
        history=[{"sender": "her", "text": "Hago marketing visual. Y tu?"}],
        user_message=message,
        chosen_time="15m",
        visible_context={"last_natalia_message": "Hago marketing visual. Y tu?"},
    )

    reply = server.fallback_natalia_message(request, 8, server.level_behavior(1), [])

    assert analysis["direct_question_topics"] == ["musica"]
    assert any(token in reply.lower() for token in ["musica", "playlist", "bailar"])
    assert "lugar tranquilo" not in reply.lower()


def test_direct_question_intent_overrides_earlier_plan_words(monkeypatch):
    server = load_server(monkeypatch)
    message = "Cuando no estoy ocupado me gusta bailar y salir por algo rico. Y a ti que musica te gusta?"

    analysis = server.analyze_visible_turn(
        message,
        "Hago marketing visual para restaurantes. Y tu, que haces cuando no estas en modo trabajo?",
        "15m",
    )
    score = server.heuristic_score(
        message,
        "15m",
        "Hago marketing visual para restaurantes. Y tu, que haces cuando no estas en modo trabajo?",
    )

    assert analysis["direct_question_topics"] == ["musica"]
    assert analysis["intent"] == "pregunta_contextual"
    assert "avanzar hacia un objetivo concreto" not in score["feedback"]


def test_heuristic_score_uses_recovered_cases_as_learned_context(monkeypatch):
    server = load_server(monkeypatch)
    cases = [
        {
            "source": "sqlite_reddit_pair",
            "profile": "coqueta",
            "man_message": "Y a ti que musica te gusta?",
            "woman_response": "Me gusta bailar, depende del mood.",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "8",
        },
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "Que musica te gusta para salir?",
            "woman_response": "Algo con energia jaja.",
            "woman_signal": "risa",
            "success_score": "9",
        },
    ]

    coach = server.heuristic_score(
        "Y a ti que musica te gusta?",
        "15m",
        "Hago marketing visual para restaurantes. Y tu?",
        cases,
    )

    assert "Patron aprendido de casos reales: 2 pares compatibles" in coach["feedback"]
    assert "pregunta_de_vuelta" in coach["feedback"] or "risa" in coach["feedback"]


def test_question_detection_keeps_real_location_question(monkeypatch):
    server = load_server(monkeypatch)

    analysis = server.analyze_visible_turn(
        "Me gusta ese estilo, sin presiÃ³n. Â¿QuÃ© zona te queda cÃ³moda?",
        "Eso me gusta. Odio cuando el chat parece formulario.",
        "15m",
    )

    assert analysis["asked_question"] is True
    assert analysis["direct_question_topics"] == ["ubicacion"]


def test_heuristic_penalizes_two_meaningful_questions(monkeypatch):
    server = load_server(monkeypatch)

    score = server.heuristic_score(
        "Â¿DÃ³nde vives? Â¿En quÃ© trabajas?",
        "15m",
        "jaja ok",
    )

    assert "demasiadas preguntas" in score["feedback"]


def test_infer_woman_signal_cleans_encoding_and_emojis(monkeypatch):
    server = load_server(monkeypatch)

    assert server.infer_woman_signal("Pasame tu nÃºmero") == "contacto"
    assert server.infer_woman_signal("Jajaja 😂") == "risa"
    assert server.infer_woman_signal("¿Y tu?") == "pregunta_de_vuelta"


def test_evaluate_parses_gemini_json_without_real_api(monkeypatch):
    server = load_server(monkeypatch)

    def fake_generate_content(prompt):
        assert "MENSAJE DEL USUARIO" in prompt
        return '{"score": 8, "feedback": "Buen ritmo.", "suggestions": ["Sube un poco la chispa."]}'

    monkeypatch.setattr(server.rotator, "generate_content", fake_generate_content)
    client = TestClient(server.app)

    response = client.post(
        "/api/evaluate",
        json={"level": 1, "history": [], "user_message": "hey chica problema"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 8
    assert "Buen ritmo" in data["evaluation"]
    assert len(data["new_history"]) == 2


def test_evaluate_offline_skips_chroma_and_gemini(monkeypatch):
    server = load_server(monkeypatch)

    class ExplodingCollection:
        def query(self, *args, **kwargs):
            raise AssertionError("Chroma should not be queried when disabled")

    monkeypatch.setenv("GEMINI_LIVE_ENABLED", "0")
    monkeypatch.setenv("CHROMA_QUERY_ENABLED", "0")
    monkeypatch.setattr(server, "chroma_collection", ExplodingCollection())
    client = TestClient(server.app)

    response = client.post(
        "/api/evaluate",
        json={
            "level": 1,
            "history": [{"role": "assistant", "content": "Mmm, va... pero usalo bien."}],
            "user_message": "Trato hecho, te escribo con el lugar y sin discurso intenso ??",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["score"] >= 6
    assert "demasiadas preguntas" not in data["evaluation"]
    assert len(data["new_history"]) == 3


def test_retrieve_real_reply_pairs_uses_sqlite_training_data(monkeypatch):
    server = load_server(monkeypatch)

    pairs = server.retrieve_real_reply_pairs("datos curiosos trenes cochino", "coqueta", limit=3)

    assert pairs
    assert any(pair["source"] in {"sqlite_chat_pair", "sqlite_reddit_pair"} for pair in pairs)
    assert all(pair.get("woman_response") for pair in pairs)
    assert all(pair.get("intent") for pair in pairs)
    assert all(pair.get("woman_signal") for pair in pairs)


def test_level_behavior_has_concrete_persona_facts(monkeypatch):
    server = load_server(monkeypatch)
    behavior = server.level_behavior(1)

    assert behavior["location_area"] == "Brickell"
    assert "marketing" in behavior["work_hint"]
    assert behavior["off_mode"]


def test_selective_levels_raise_passing_score(monkeypatch):
    server = load_server(monkeypatch)

    assert server.passing_score_for_behavior(server.level_behavior(1)) == 6
    assert server.passing_score_for_behavior(server.level_behavior(2)) == 7
    assert server.passing_score_for_behavior(server.level_behavior(3)) == 8
    assert server.passing_score_for_behavior(server.level_behavior(4)) == 9


def test_same_score_loses_life_on_high_selectivity_level(monkeypatch):
    server = load_server(monkeypatch)

    def fake_generate_content(prompt):
        if "Natalia-Coach" in prompt:
            return '{"score": 7, "lose_life": false, "attraction_delta": 4, "feedback": "Mensaje aceptable.", "verdict": "acceptable", "natalia_stance": "neutral", "reason": "conecta", "suggestions": ["Mejor A", "Mejor B", "Mejor C"]}'
        return '{"message": "Me gusta la musica con buena energia, depende del mood.", "reply_time": "Tardo: 15 min"}'

    monkeypatch.setattr(server.rotator, "generate_content", fake_generate_content)
    client = TestClient(server.app)

    base_payload = {
        "step_index": 3,
        "evaluated_step_id": 4,
        "lives": 4,
        "attraction": 60,
        "history": [{"sender": "her", "text": "jaja ok, eso me da curiosidad."}],
        "user_message": "Que musica te gusta?",
        "chosen_time": "15m",
        "visible_context": {"last_natalia_message": "jaja ok, eso me da curiosidad."},
    }

    level1 = client.post("/api/simulate-turn", json={**base_payload, "level": 1}).json()
    level3 = client.post("/api/simulate-turn", json={**base_payload, "level": 3}).json()

    assert level1["score"] == 7
    assert level1["lose_life"] is False
    assert level1["retrieval_summary"]["passing_score"] == 6
    assert level3["score"] == 7
    assert level3["lose_life"] is True
    assert level3["retrieval_summary"]["passing_score"] == 8
    assert "perfil es mas selectivo" in level3["coach_feedback"]


def test_retrieve_cases_prioritizes_real_reply_pairs(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        level=1,
        step_index=0,
        evaluated_step_id=1,
        lives=4,
        attraction=50,
        history=[{"sender": "user", "text": "Tengo datos curiosos sobre trenes."}],
        user_message="Tengo datos curiosos sobre trenes.",
        chosen_time="15m",
        visible_context={"last_natalia_message": ""},
    )

    with pytest.raises(RuntimeError, match="deprecada"):
        server.retrieve_cases(request, server.level_behavior(1))


def test_emoji_profile_counts_real_unicode_categories(monkeypatch):
    server = load_server(monkeypatch)

    risky = server.emoji_profile("".join(map(chr, [0x1F346, 0x1F4A6])))
    warm = server.emoji_profile("".join(map(chr, [0x1F609, 0x1F642])))
    romantic = server.emoji_profile("".join(map(chr, [0x1F60D, 0x1F618, 0x2764, 0xFE0F])))

    assert risky["risky_count"] == 2
    assert risky["calibration"] == "riesgo sexual temprano"
    assert warm["warm_count"] == 2
    assert warm["calibration"] == "calibrados"
    assert romantic["romantic_count"] == 3
    assert romantic["calibration"] == "demasiado romanticos"


def test_retrieve_persona_cases_filters_success_support_by_direct_topic(monkeypatch):
    server = load_server(monkeypatch)

    request = server.SimulateTurnRequest(
        level=1,
        user_message="Que musica te gusta?",
        chosen_time="15m",
        history=[],
        visible_context={"last_natalia_message": "jaja, eso me da curiosidad."},
    )
    monkeypatch.setattr(
        server,
        "retrieve_real_reply_pairs",
        lambda *args, **kwargs: [
            {
                "source": "sqlite_chat_pair",
                "man_message": "Que musica escuchas?",
                "woman_response": "De todo, pero me gusta bailar.",
            }
        ],
    )
    monkeypatch.setattr(
        server,
        "retrieve_success_chroma_cases",
        lambda *args, **kwargs: [
            {"source": "success_chroma", "text": "Caso de cita y WhatsApp para cerrar rapido.", "objectives": "cita, whatsapp"},
            {"source": "success_chroma", "text": "Hablaron de musica y playlist antes de seguir.", "objectives": "humor"},
        ],
    )

    cases = server.retrieve_persona_cases(request, server.level_behavior(1))

    assert [case["source"] for case in cases] == ["sqlite_chat_pair", "success_chroma"]
    assert "musica" in cases[1]["text"]


def test_retrieve_real_reply_pairs_broadens_profiles_for_scarce_plan_intent(monkeypatch, tmp_path):
    server = load_server(monkeypatch)
    db_path = tmp_path / "textgame.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE chat_turns (user_message TEXT, girl_response TEXT, outcome TEXT, girl_profile_type TEXT)"
    )
    conn.execute(
        "CREATE TABLE reddit_conversations (post_id TEXT, transcription_json TEXT, girl_profile_type TEXT)"
    )
    conn.execute(
        """
        INSERT INTO chat_turns VALUES
        ('jueves una copa tranquila', 'Jueves puede ser, dime el lugar.', 'positivo', 'coqueta')
        """
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(server, "DB_PATH", db_path)

    pairs = server.retrieve_real_reply_pairs(
        "jueves una copa tranquila",
        "desinteresada",
        intent="cerrar_plan",
        limit=3,
    )

    assert pairs
    assert pairs[0]["profile"] == "coqueta"
    assert "jueves" in pairs[0]["woman_response"].lower()


def test_retrieve_real_reply_pairs_keeps_profile_strict_for_common_intent(monkeypatch, tmp_path):
    server = load_server(monkeypatch)
    db_path = tmp_path / "textgame.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE chat_turns (user_message TEXT, girl_response TEXT, outcome TEXT, girl_profile_type TEXT)"
    )
    conn.execute(
        "CREATE TABLE reddit_conversations (post_id TEXT, transcription_json TEXT, girl_profile_type TEXT)"
    )
    conn.execute(
        """
        INSERT INTO chat_turns VALUES
        ('tengo una historia rara', 'Cuentame, eso suena raro.', 'positivo', 'coqueta')
        """
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(server, "DB_PATH", db_path)

    pairs = server.retrieve_real_reply_pairs(
        "tengo una historia rara",
        "desinteresada",
        intent="conversacion",
        limit=3,
    )

    assert pairs == []


def test_training_status_reports_derived_pairs(monkeypatch):
    server = load_server(monkeypatch)
    client = TestClient(server.app)

    response = client.get("/api/training-status")

    assert response.status_code == 200
    data = response.json()
    assert data["sqlite"]["reddit_conversations"] >= 200
    assert data["sqlite"]["chat_turns"] >= 30
    assert data["sqlite"]["reddit_rows_with_pairs"] > 100
    assert data["sqlite"]["reddit_rows_without_pairs"] > 0
    assert data["sqlite"]["transcripts"]["success"]["total"] >= 40
    assert data["sqlite"]["transcripts"]["success"]["chars"] > 100000
    assert data["derived_training_pairs"] > data["sqlite"]["chat_turns"]
    assert "humor" in data["pair_intents"] or "pregunta_contextual" in data["pair_intents"]
    assert data["woman_signals"]
    assert "coqueta" in data["profile_training"]
    assert data["profile_training"]["coqueta"]["pairs"] > 0
    assert data["profile_training"]["coqueta"]["success_average"] > 0
    assert "profile_intent_gaps" in data


def test_simulate_turn_fallback_uses_visible_context(monkeypatch):
    server = load_server(monkeypatch)

    def quota_exhausted(_prompt):
        raise RuntimeError("429 quota")

    monkeypatch.setattr(server.rotator, "generate_content", quota_exhausted)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 2,
            "evaluated_step_id": 3,
            "lives": 4,
            "attraction": 45,
            "history": [
                {
                    "sender": "her",
                    "text": "me gusta eso, perfecto donde vives? yo en brickell y tu?",
                    "timeText": "Tardo: 20 min",
                },
                {"sender": "user", "text": "hola", "timeText": "15m"},
            ],
            "user_message": "hola",
            "chosen_time": "15m",
            "visible_context": {
                "evaluated_step_id": 3,
                "last_natalia_message": "me gusta eso, perfecto donde vives? yo en brickell y tu?",
                "last_user_message": "hola",
                "chat_snapshot": "Natalia: me gusta eso, perfecto donde vives? yo en brickell y tu?\nHombre: hola",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["fallback"] is True
    assert data["score"] < 6
    assert data["lose_life"] is True
    assert data["turn_analysis"]["ignored_question"] is True
    assert "pregunta visible" in data["coach_feedback"]
    assert "pregunta en el aire" in data["natalia_message"]


def test_simulate_turn_reports_training_pair_metadata(monkeypatch):
    server = load_server(monkeypatch)

    def quota_exhausted(_prompt):
        raise RuntimeError("429 quota")

    monkeypatch.setattr(server.rotator, "generate_content", quota_exhausted)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 0,
            "evaluated_step_id": 1,
            "lives": 4,
            "attraction": 50,
            "history": [{"sender": "user", "text": "Tengo datos curiosos sobre trenes.", "timeText": "15m"}],
            "user_message": "Tengo datos curiosos sobre trenes.",
            "chosen_time": "15m",
            "visible_context": {
                "evaluated_step_id": 1,
                "last_natalia_message": "",
                "last_user_message": "Tengo datos curiosos sobre trenes.",
                "chat_snapshot": "Hombre: Tengo datos curiosos sobre trenes.",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    pair_cases = [case for case in data["retrieved_cases"] if case["source"] in {"sqlite_chat_pair", "sqlite_reddit_pair"}]
    assert pair_cases
    assert any(case["intent"] for case in pair_cases)
    assert any(case["woman_signal"] for case in pair_cases)
    assert data["turn_analysis"]["intent"] in {"conversacion", "pregunta_contextual"}
    summary = data["retrieval_summary"]
    assert summary["persona_pair_cases"] > 0
    assert summary["coach_context_cases"] >= summary["persona_pair_cases"]
    assert set(summary["persona_sources"]).issubset({"sqlite_chat_pair", "sqlite_reddit_pair"})
    assert isinstance(summary["gemini_live_enabled"], bool)
    assert isinstance(summary["chroma_query_enabled"], bool)
    metrics = data["turn_metrics"]
    assert set(metrics) == {"message_quality", "context", "objective", "tone", "timing"}
    assert metrics["message_quality"]["word_count"] > 0
    assert metrics["objective"]["intent"] == data["turn_analysis"]["intent"]
    assert "emoji_calibration" in metrics["tone"]


def test_fallback_natalia_avoids_repeated_plan_reply(monkeypatch):
    server = load_server(monkeypatch)
    used_reply = "Jaja eso si suena mas interesante. Que tienes en mente?"
    request = server.SimulateTurnRequest(
        level=1,
        step_index=4,
        evaluated_step_id=5,
        lives=4,
        attraction=60,
        history=[
            {"sender": "her", "text": "un vino suena bien, pero dime el plan"},
            {"sender": "user", "text": "podemos ir por una copa tranquila"},
            {"sender": "her", "text": used_reply},
        ],
        user_message="Tengo un plan con vino y buena musica",
        chosen_time="15m",
        visible_context={"last_natalia_message": "un vino suena bien, pero dime el plan"},
    )

    reply = server.fallback_natalia_message(request, 7, server.level_behavior(1), [])

    assert reply
    assert reply != used_reply


def test_fallback_natalia_progresses_to_contact_late_level(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        level=1,
        step_index=8,
        evaluated_step_id=9,
        lives=4,
        attraction=85,
        history=[
            {"sender": "her", "text": "ok, y que plan tendrias en mente?"},
            {"sender": "user", "text": "una copa y caminamos un rato"},
        ],
        user_message="Entonces hagamos esa cita esta semana",
        chosen_time="15m",
        visible_context={"last_natalia_message": "ok, y que plan tendrias en mente?"},
    )

    reply = server.fallback_natalia_message(request, 8, server.level_behavior(1), [])

    assert "whatsapp" in reply.lower()


def test_reusable_real_reply_skips_empty_laughter(monkeypatch):
    server = load_server(monkeypatch)
    cases = [
        {
            "source": "sqlite_reddit_pair",
            "woman_response": "Jajajajajaja",
            "woman_signal": "risa",
            "success_score": "9",
        },
        {
            "source": "sqlite_reddit_pair",
            "woman_response": "Ok, eso si suena mas interesante.",
            "woman_signal": "receptiva",
            "success_score": "8",
        },
    ]

    reply = server.reusable_real_woman_reply(cases, 8, preferred_signals=["risa", "receptiva"])

    assert reply == "Ok, eso si suena mas interesante."


def test_reusable_real_reply_respects_topic_guard(monkeypatch):
    server = load_server(monkeypatch)
    cases = [
        {
            "source": "sqlite_chat_pair",
            "man_message": "Tengo datos curiosos sobre trenes.",
            "woman_response": "Dime tu dato de trenes mas cochino jajaja",
            "woman_signal": "risa",
            "success_score": "9",
        },
        {
            "source": "sqlite_chat_pair",
            "man_message": "A ti te gusta hacer ejercicio?",
            "woman_response": "Si, me gusta moverme jaja.",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "8",
        },
    ]

    reply = server.reusable_real_woman_reply(cases, 8, topic_guard={"ejercicio"})

    assert "moverme" in reply.lower()
    assert "trenes" not in reply.lower()


def test_reusable_real_reply_skips_non_spanish_ocr_noise(monkeypatch):
    server = load_server(monkeypatch)
    cases = [
        {
            "source": "sqlite_chat_pair",
            "man_message": "jueves una copa tranquila",
            "woman_response": "You called? I also like the term foliage father",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "9",
        },
        {
            "source": "sqlite_chat_pair",
            "man_message": "jueves una copa tranquila",
            "woman_response": "Jueves puede ser, pero dime el lugar.",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "8",
        },
    ]

    reply = server.reusable_real_woman_reply(cases, 8, topic_guard={"plan", "vino"})

    assert reply == "Jueves puede ser, pero dime el lugar."


def test_fallback_plan_intent_ignores_unrelated_real_pair(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        level=1,
        step_index=4,
        evaluated_step_id=5,
        lives=4,
        attraction=60,
        history=[
            {"sender": "her", "text": "un vino suena bien, pero dime el plan"},
            {"sender": "user", "text": "podemos ir por una copa tranquila"},
        ],
        user_message="Tengo un plan con vino y buena musica",
        chosen_time="15m",
        visible_context={"last_natalia_message": "un vino suena bien, pero dime el plan"},
    )
    cases = [
        {
            "source": "sqlite_chat_pair",
            "woman_response": "Dime tu dato de trenes mas cochino jajaja",
            "woman_signal": "risa",
            "success_score": "9",
        }
    ]

    reply = server.fallback_natalia_message(request, 8, server.level_behavior(1), cases)

    assert "trenes" not in reply.lower()
    assert "plan" in reply.lower() or "interesante" in reply.lower()


def test_simulate_turn_answers_location_and_work_question(monkeypatch):
    server = load_server(monkeypatch)

    def quota_exhausted(_prompt):
        raise RuntimeError("429 quota")

    monkeypatch.setattr(server.rotator, "generate_content", quota_exhausted)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 2,
            "evaluated_step_id": 3,
            "lives": 1,
            "attraction": 0,
            "history": [
                {"sender": "her", "text": "me gusta eso, perfecto donde vives? yo en brickell y tu?"},
                {"sender": "user", "text": "yo vivo en bogota y en que trabajas?", "timeText": "1h"},
            ],
            "user_message": "yo vivo en bogota y en que trabajas?",
            "chosen_time": "1h",
            "visible_context": {
                "evaluated_step_id": 3,
                "last_natalia_message": "me gusta eso, perfecto donde vives? yo en brickell y tu?",
                "last_user_message": "yo vivo en bogota y en que trabajas?",
                "chat_snapshot": "Natalia: me gusta eso, perfecto donde vives? yo en brickell y tu?\nHombre: yo vivo en bogota y en que trabajas?",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["fallback"] is True
    assert data["lose_life"] is False
    assert "ubicacion" in data["turn_analysis"]["answered_topics"]
    assert "trabajo" in data["turn_analysis"]["user_topics"]
    assert "marketing" in data["natalia_message"].lower()
    assert "vino" not in data["natalia_message"].lower()
    assert "respondio la ubicacion" in data["coach_feedback"]
    assert "metio una pregunta logistica extra" not in data["coach_feedback"]
    assert "sumo otra pregunta antes de cerrar el hilo anterior" not in data["coach_feedback"]


def test_heuristic_coach_accepts_location_answer_plus_work_question(monkeypatch):
    server = load_server(monkeypatch)

    result = server.heuristic_score(
        "yo vivo en bogota y en que trabajas?",
        "1h",
        "me gusta eso, perfecto donde vives? yo en brickell y tu?",
    )

    assert result["score"] >= 8
    assert result["lose_life"] is False
    assert "respondio la ubicacion" in result["feedback"]
    assert "metio una pregunta logistica extra" not in result["feedback"]
    assert "sumo otra pregunta antes de cerrar el hilo anterior" not in result["feedback"]
    assert result["suggestions"][0].startswith("Primero responde ubicacion")


def test_case_based_suggestions_require_answered_context_when_new_question_exists(monkeypatch):
    server = load_server(monkeypatch)
    analysis = server.analyze_visible_turn(
        "yo vivo en bogota y en que trabajas?",
        "me gusta eso, perfecto donde vives? yo en brickell y tu?",
        "1h",
    )
    cases = [
        {
            "source": "sqlite_chat_pair",
            "man_message": "Ah, que bien. En que trabajas?",
            "woman_response": "Trabajo en marketing.",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "8",
        },
        {
            "source": "sqlite_chat_pair",
            "man_message": "Yo vivo en Bogota. Y tu en que trabajas?",
            "woman_response": "Hago marketing visual.",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "8",
        },
    ]

    suggestions = server.case_based_suggestions(cases, analysis)

    assert suggestions == ["Yo vivo en Bogota. Y tu en que trabajas?"]


def test_topic_detector_does_not_create_false_location_or_pet_topics(monkeypatch):
    server = load_server(monkeypatch)

    salsa_topics = server.topic_set(
        "Soy de salsa y musica con energia. Tambien me gusta probar comida rica, que comida disfrutas?"
    )
    plan_topics = server.topic_set(
        "Prometo plan simple: una copa, buena conversacion y sin interrogatorio eterno. Te paso mi WhatsApp?"
    )

    assert "ubicacion" not in salsa_topics
    assert {"musica", "comida"}.issubset(salsa_topics)
    assert "mascotas" not in plan_topics
    assert {"plan", "contacto"}.issubset(plan_topics)


def test_heuristic_does_not_penalize_answer_plus_new_question(monkeypatch):
    server = load_server(monkeypatch)

    result = server.heuristic_score(
        "Soy de salsa y musica con energia. Tambien me gusta probar comida rica, que comida disfrutas?",
        "15m",
        "Me gusta la musica con buena energia, pero depende del mood. Tu eres mas de bailar o de escuchar tranquilo?",
    )

    assert result["lose_life"] is False
    assert "sumo otra pregunta antes de cerrar el hilo anterior" not in result["feedback"]
    assert "demasiadas preguntas" not in result["feedback"]


def test_heuristic_does_not_treat_copa_as_extra_topic_when_asking_contact(monkeypatch):
    server = load_server(monkeypatch)

    result = server.heuristic_score(
        "Prometo plan simple: una copa, buena conversacion y sin interrogatorio eterno. Te paso mi WhatsApp?",
        "15m",
        "Jueves puede funcionar. Me gusta que lo aterrices sin hacerlo intenso.",
    )

    assert result["lose_life"] is False
    assert "sumo otra pregunta antes de cerrar el hilo anterior" not in result["feedback"]
    assert "demasiadas preguntas" not in result["feedback"]


def test_simulate_turn_answers_exercise_question_without_script_jump(monkeypatch):
    server = load_server(monkeypatch)

    def quota_exhausted(_prompt):
        raise RuntimeError("429 quota")

    monkeypatch.setattr(server.rotator, "generate_content", quota_exhausted)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 1,
            "evaluated_step_id": 2,
            "lives": 4,
            "attraction": 50,
            "history": [
                {"sender": "her", "text": "esa soy yo totalmente jaja como va tu dia?"},
                {"sender": "user", "text": "bien en el gimnasio y a ti te gusta hacer ejercicio?", "timeText": "15m"},
            ],
            "user_message": "bien en el gimnasio y a ti te gusta hacer ejercicio?",
            "chosen_time": "15m",
            "visible_context": {
                "evaluated_step_id": 2,
                "last_natalia_message": "esa soy yo totalmente jaja como va tu dia?",
                "last_user_message": "bien en el gimnasio y a ti te gusta hacer ejercicio?",
                "chat_snapshot": "Natalia: esa soy yo totalmente jaja como va tu dia?\nHombre: bien en el gimnasio y a ti te gusta hacer ejercicio?",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["lose_life"] is False
    assert "ejercicio" in data["turn_analysis"]["user_topics"]
    assert "gym" in data["natalia_message"].lower() or "entren" in data["natalia_message"].lower() or "mover" in data["natalia_message"].lower()
    assert "donde vives" not in data["natalia_message"].lower()


def test_screenshot_flow_stays_synced_between_natalia_and_coach(monkeypatch):
    server = load_server(monkeypatch)

    def quota_exhausted(_prompt):
        raise RuntimeError("429 quota")

    monkeypatch.setattr(server.rotator, "generate_content", quota_exhausted)
    client = TestClient(server.app)

    first_payload = {
        "level": 1,
        "step_index": 1,
        "evaluated_step_id": 2,
        "lives": 4,
        "attraction": 50,
        "history": [
            {"sender": "user", "text": "hola", "timeText": "Ahora mismo"},
            {"sender": "her", "text": "esa soy yo totalmente jaja como va tu dia?", "timeText": "15m"},
        ],
        "user_message": "bien en el gimnasio y a ti te gusta hacer ejercicio?",
        "chosen_time": "Ahora mismo",
        "visible_context": {"last_natalia_message": "esa soy yo totalmente jaja como va tu dia?"},
    }
    first = client.post("/api/simulate-turn", json=first_payload).json()

    assert first["lose_life"] is False
    assert first["turn_analysis"]["direct_question_topics"] == ["ejercicio"]
    assert any(token in first["natalia_message"].lower() for token in ["gym", "entren", "mover", "pilates", "deporte", "rutina"])
    assert "vino" not in first["natalia_message"].lower()
    assert "donde vives" not in first["natalia_message"].lower()

    history = first_payload["history"] + [
        {"sender": "user", "text": first_payload["user_message"], "timeText": "Ahora mismo"},
        {"sender": "her", "text": first["natalia_message"], "timeText": first["natalia_time"]},
    ]
    second = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 2,
            "evaluated_step_id": 3,
            "lives": 4,
            "attraction": 60,
            "history": history,
            "user_message": "yo vivo en bogota y en que trabajas?",
            "chosen_time": "1h",
            "visible_context": {"last_natalia_message": first["natalia_message"]},
        },
    ).json()

    assert second["lose_life"] is False
    assert second["turn_analysis"]["direct_question_topics"] == ["trabajo"]
    assert "marketing" in second["natalia_message"].lower() or "trabajo" in second["natalia_message"].lower()
    assert "vino" not in second["natalia_message"].lower()
    assert "mover la conversacion hacia una cita concreta" not in second["coach_feedback"].lower()
    assert "contexto de la conversacion" in second["coach_feedback"].lower()


def test_opening_with_plan_word_does_not_get_false_unresolved_topic(monkeypatch):
    server = load_server(monkeypatch)

    result = server.heuristic_score(
        "Hola Natalia, esa sonrisa parece de alguien que sabe escoger buenos planes. Como va tu dia?",
        "15m",
        "",
    )

    assert result["lose_life"] is False
    assert "sumo otra pregunta antes de cerrar el hilo anterior" not in result["feedback"]


def test_direct_sport_question_is_treated_as_exercise(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        level=1,
        step_index=1,
        evaluated_step_id=2,
        lives=4,
        attraction=55,
        history=[{"sender": "her", "text": "esa soy yo totalmente jaja como va tu dia?"}],
        user_message="Bien, saliendo del gym. A ti que deporte te gusta?",
        chosen_time="15m",
        visible_context={"last_natalia_message": "esa soy yo totalmente jaja como va tu dia?"},
    )

    analysis = server.analyze_visible_turn(
        request.user_message,
        request.visible_context["last_natalia_message"],
        request.chosen_time,
    )
    reply = server.fallback_natalia_message(request, 7, server.level_behavior(1), [])

    assert analysis["direct_question_topics"] == ["ejercicio"]
    assert any(token in reply.lower() for token in ["pilates", "caminar", "deporte", "mover"])
    assert "vino" not in reply.lower()
    assert "donde vives" not in reply.lower()


def test_persona_training_rejects_profile_cards_and_unsafe_pairs(monkeypatch):
    server = load_server(monkeypatch)

    assert not server.valid_persona_pair(
        "[Perfil de Fantasma/Esqueleto] Si te gusta que te dejen en visto, desliza a la izquierda.",
        "[Perfil de Loteria] Si pones estos numeros en tu celular, tienes cena gratis.",
    )
    assert not server.valid_persona_pair(
        "Me tengo que ir a enterrar vivo.",
        "Jajajajajaja",
    )
    assert not server.valid_persona_pair(
        "Donde estoy ahora? Estoy despierto?",
        "Acabo de tener un sueno rarisimo donde se te rompieron los pantalones.",
    )
    assert not server.valid_persona_pair(
        "Dile lo que sientes. Todo va a salir bien",
        "NO PUEDE SER. AMIGO. ME DIJO QUE LE GUSTO",
    )

    pairs = server.retrieve_real_reply_pairs(
        "bien en el gimnasio y a ti te gusta hacer ejercicio?",
        "coqueta",
        limit=5,
    )

    combined = "\n".join(f"{case.get('man_message')} {case.get('woman_response')}" for case in pairs).lower()
    assert "[perfil" not in combined
    assert "enterrar vivo" not in combined
    assert "loter" not in combined


def test_high_selectivity_fallback_sounds_less_available(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        level=3,
        step_index=1,
        evaluated_step_id=2,
        lives=2,
        attraction=55,
        history=[{"sender": "her", "text": "esa soy yo totalmente jaja como va tu dia?"}],
        user_message="Bien, saliendo del gym. A ti que deporte te gusta?",
        chosen_time="15m",
        visible_context={"last_natalia_message": "esa soy yo totalmente jaja como va tu dia?"},
    )

    easy_reply = server.fallback_natalia_message(request, 7, server.level_behavior(1), [])
    selective_reply = server.fallback_natalia_message(request, 7, server.level_behavior(3), [])

    assert selective_reply != easy_reply
    assert "pilates" in selective_reply.lower() or "mover" in selective_reply.lower()
    assert any(token in selective_reply.lower() for token in ["nada de", "sorprendeme", "menos"])


def test_extreme_selectivity_contact_fallback_requires_clear_plan(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        level=4,
        step_index=7,
        evaluated_step_id=8,
        lives=2,
        attraction=78,
        history=[{"sender": "her", "text": "Mmm, el plan podria sonar bien."}],
        user_message="Te paso mi WhatsApp?",
        chosen_time="15m",
        visible_context={"last_natalia_message": "Mmm, el plan podria sonar bien."},
    )

    reply = server.fallback_natalia_message(request, 8, server.level_behavior(4), [])

    assert any(token in reply.lower() for token in ["plan", "concretar", "novela", "entrevista"])


def test_fallback_direct_work_question_gets_direct_answer(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        level=1,
        step_index=3,
        evaluated_step_id=4,
        lives=4,
        attraction=55,
        history=[{"sender": "her", "text": "jaja ok, me dio curiosidad"}],
        user_message="y tu en que trabajas?",
        chosen_time="15m",
        visible_context={"last_natalia_message": "jaja ok, me dio curiosidad"},
    )

    reply = server.fallback_natalia_message(request, 7, server.level_behavior(1), [])

    assert "marketing" in reply.lower()
    assert "vino" not in reply.lower()


def test_simulate_turn_shares_same_turn_analysis_with_coach_and_natalia(monkeypatch):
    server = load_server(monkeypatch)
    prompts = []

    def fake_generate_content(prompt):
        prompts.append(prompt)
        if "Natalia-Coach" in prompt:
            return '{"score": 7, "lose_life": false, "attraction_delta": 4, "feedback": "Conecta bien.", "verdict": "acceptable", "natalia_stance": "neutral", "reason": "respondio ubicacion", "suggestions": ["Mejor A", "Mejor B", "Mejor C"]}'
        return '{"message": "Trabajo en algo creativo, pero Bogota suena interesante jaja.", "reply_time": "Tardo: 15 min"}'

    monkeypatch.setattr(server.rotator, "generate_content", fake_generate_content)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 2,
            "evaluated_step_id": 3,
            "lives": 4,
            "attraction": 50,
            "history": [
                {"sender": "her", "text": "me gusta eso, perfecto donde vives? yo en brickell y tu?"},
                {"sender": "user", "text": "yo vivo en bogota y en que trabajas?", "timeText": "1h"},
            ],
            "user_message": "yo vivo en bogota y en que trabajas?",
            "chosen_time": "1h",
            "visible_context": {
                "last_natalia_message": "me gusta eso, perfecto donde vives? yo en brickell y tu?",
            },
        },
    )

    assert response.status_code == 200
    assert len(prompts) == 2
    assert all("ANALISIS COMPARTIDO DEL TURNO:" in prompt for prompt in prompts)
    assert "Natalia-Coach" in prompts[0]
    assert "Natalia-Persona" in prompts[1]
    assert "Razon Coach" not in prompts[1]
    assert "Postura normalizada de Natalia" in prompts[1]
    assert "- Temas respondidos al ultimo mensaje: ubicacion" in prompts[0]
    assert "- Temas respondidos al ultimo mensaje: ubicacion" in prompts[1]
    data = response.json()
    assert data["turn_analysis"]["answered_topics"] == ["ubicacion"]


def test_simulate_turn_rejects_model_reply_that_jumps_to_unrelated_topic(monkeypatch):
    server = load_server(monkeypatch)

    def fake_generate_content(prompt):
        if "Natalia-Coach" in prompt:
            return '{"score": 8, "lose_life": false, "attraction_delta": 8, "feedback": "Respondio ubicacion y pregunto algo normal.", "verdict": "good", "natalia_stance": "open", "reason": "respondio ubicacion", "suggestions": ["Mejor A", "Mejor B", "Mejor C"]}'
        return '{"message": "jaja que loco. te gusta el vino? es mi favorito", "reply_time": "Tardo: 30 min"}'

    monkeypatch.setattr(server.rotator, "generate_content", fake_generate_content)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 2,
            "evaluated_step_id": 3,
            "lives": 4,
            "attraction": 50,
            "history": [
                {"sender": "her", "text": "me gusta eso, perfecto donde vives? yo en brickell y tu?"},
                {"sender": "user", "text": "yo vivo en bogota y en que trabajas?", "timeText": "1h"},
            ],
            "user_message": "yo vivo en bogota y en que trabajas?",
            "chosen_time": "1h",
            "visible_context": {
                "last_natalia_message": "me gusta eso, perfecto donde vives? yo en brickell y tu?",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["fallback"] is True
    assert "marketing" in data["natalia_message"].lower()
    assert "vino" not in data["natalia_message"].lower()
    assert data["turn_analysis"]["direct_question_topics"] == ["trabajo"]


def test_contextual_question_rejects_opportunistic_topic_jump(monkeypatch):
    server = load_server(monkeypatch)
    analysis = server.analyze_visible_turn(
        "y a ti que musica te gusta?",
        "jaja ok, eso me da curiosidad.",
        "15m",
    )

    assert analysis["direct_question_topics"] == ["musica"]
    assert server.natalia_response_is_invalid("jaja si, vamos por vino mejor", 7, analysis) is True
    assert server.natalia_response_is_invalid("Me gusta mas la musica tranquila, depende del dia.", 7, analysis) is False


def test_accented_active_music_question_overrides_earlier_work_topic(monkeypatch):
    server = load_server(monkeypatch)
    message = "Cuando no estoy en modo trabajo me gusta bailar y probar comida rica. ¿Qué música te gusta?"
    last = "Hago marketing visual para restaurantes. Y tu, que haces cuando no estas en modo trabajo?"
    request = server.SimulateTurnRequest(
        level=1,
        step_index=3,
        evaluated_step_id=4,
        lives=4,
        attraction=65,
        history=[{"sender": "her", "text": last}],
        user_message=message,
        chosen_time="15m",
        visible_context={"last_natalia_message": last},
    )

    analysis = server.analyze_visible_turn(message, last, "15m")
    reply = server.fallback_natalia_message(request, 7, server.level_behavior(1), [])

    assert analysis["direct_question_topics"] == ["musica"]
    assert any(token in reply.lower() for token in ["musica", "playlist", "bailar"])
    assert "marketing" not in reply.lower()


def test_plan_proposal_does_not_reuse_unrelated_visit_reply(monkeypatch):
    server = load_server(monkeypatch)
    message = "Si te late, el jueves podemos tomar una copa tranquila y me cuentas si Brickell es tan cool."
    last = "Ok, lugar tranquilo suma. Ahora dime cual y veo si confio en tu gusto."
    request = server.SimulateTurnRequest(
        level=1,
        step_index=6,
        evaluated_step_id=7,
        lives=4,
        attraction=75,
        history=[{"sender": "her", "text": last}],
        user_message=message,
        chosen_time="15m",
        visible_context={"last_natalia_message": last},
    )

    reply = server.fallback_natalia_message(
        request,
        8,
        server.level_behavior(1),
        [
            {
                "source": "sqlite_reddit_pair",
                "profile": "coqueta",
                "man_message": "Estoy aqui de visita por una semana.",
                "woman_response": "¿De dónde vienes de visita?",
                "woman_signal": "pregunta_de_vuelta",
                "success_score": "9",
            }
        ],
    )

    assert "visita" not in reply.lower()
    assert "jueves" in reply.lower() or "lugar" in reply.lower() or "plan" in reply.lower()


@pytest.mark.parametrize(
    ("message", "topic", "expected_tokens"),
    [
        ("Y a ti que musica te gusta?", "musica", ["musica", "playlist", "bailar"]),
        ("Que comida te gusta?", "comida", ["comida", "lugar", "recomendacion"]),
        ("Te gusta viajar o eres mas de quedarte?", "viajes", ["viajes", "viajar", "playa", "ciudad"]),
        ("Tienes perro o gato?", "mascotas", ["mascota", "perro", "gato"]),
        ("Eres cercana con tu familia?", "familia", ["familia", "gente", "vida"]),
    ],
)
def test_fallback_answers_common_human_topics_without_script_jump(monkeypatch, message, topic, expected_tokens):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        level=1,
        step_index=3,
        evaluated_step_id=4,
        lives=4,
        attraction=65,
        history=[{"sender": "her", "text": "jaja ok, eso me da curiosidad."}],
        user_message=message,
        chosen_time="15m",
        visible_context={"last_natalia_message": "jaja ok, eso me da curiosidad."},
    )

    analysis = server.analyze_visible_turn(message, "jaja ok, eso me da curiosidad.", "15m")
    reply = server.fallback_natalia_message(request, 7, server.level_behavior(1), [])
    lowered = reply.lower()

    assert analysis["direct_question_topics"] == [topic]
    assert any(token in lowered for token in expected_tokens)
    assert "vino" not in lowered
    assert "whatsapp" not in lowered


def test_simulate_turn_rejects_model_wine_jump_for_music_question(monkeypatch):
    server = load_server(monkeypatch)

    def fake_generate_content(prompt):
        if "Natalia-Coach" in prompt:
            return '{"score": 8, "lose_life": false, "attraction_delta": 8, "feedback": "Pregunta humana.", "verdict": "good", "natalia_stance": "open", "reason": "pregunta musica", "suggestions": ["Mejor A", "Mejor B", "Mejor C"]}'
        return '{"message": "jaja si, vamos por vino mejor", "reply_time": "Tardo: 15 min"}'

    monkeypatch.setattr(server.rotator, "generate_content", fake_generate_content)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 3,
            "evaluated_step_id": 4,
            "lives": 4,
            "attraction": 65,
            "history": [{"sender": "her", "text": "jaja ok, eso me da curiosidad."}],
            "user_message": "Y a ti que musica te gusta?",
            "chosen_time": "15m",
            "visible_context": {"last_natalia_message": "jaja ok, eso me da curiosidad."},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["fallback"] is True
    assert data["turn_analysis"]["direct_question_topics"] == ["musica"]
    assert "vino" not in data["natalia_message"].lower()
    assert any(token in data["natalia_message"].lower() for token in ["musica", "playlist", "bailar"])


def test_simulate_turn_rejects_visit_reply_when_user_asks_about_week(monkeypatch):
    server = load_server(monkeypatch)

    def fake_generate_content(prompt):
        if "Natalia-Coach" in prompt:
            return '{"score": 7, "lose_life": false, "attraction_delta": 4, "feedback": "Pregunta normal de apertura.", "verdict": "acceptable", "natalia_stance": "neutral", "reason": "pregunta contextual", "suggestions": ["Mejor A", "Mejor B", "Mejor C"]}'
        return '{"message": "Si, claro. De donde vienes de visita?", "reply_time": "Tardo: 15 min"}'

    monkeypatch.setattr(server.rotator, "generate_content", fake_generate_content)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 0,
            "evaluated_step_id": 1,
            "lives": 4,
            "attraction": 50,
            "history": [
                {"sender": "user", "text": "Hola Natalia, que lindo tu perfil. Que tal tu semana?", "timeText": "15m"},
            ],
            "user_message": "Hola Natalia, que lindo tu perfil. Que tal tu semana?",
            "chosen_time": "15m",
            "visible_context": {
                "last_natalia_message": "",
                "last_user_message": "Hola Natalia, que lindo tu perfil. Que tal tu semana?",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["fallback"] is True
    assert data["turn_analysis"]["direct_question_topics"] == ["dia"]
    lowered = data["natalia_message"].lower()
    assert "semana" in lowered or "dia" in lowered or "día" in lowered
    assert "visita" not in lowered
    assert "donde" not in lowered


def test_day_reply_with_plain_dia_satisfies_direct_day_question(monkeypatch):
    server = load_server(monkeypatch)
    analysis = server.analyze_visible_turn(
        "Hola Natalia, como va tu dia?",
        "",
        "15m",
    )

    assert analysis["direct_question_topics"] == ["dia"]
    assert server.natalia_response_is_invalid("Mi dia va de maravilla, y el tuyo?", 0, analysis) is False


def test_simulate_turn_rejects_non_spanish_model_reply(monkeypatch):
    server = load_server(monkeypatch)

    def fake_generate_content(prompt):
        if "Natalia-Coach" in prompt:
            return '{"score": 8, "lose_life": false, "attraction_delta": 8, "feedback": "Buen avance.", "verdict": "good", "natalia_stance": "open", "reason": "plan concreto", "suggestions": ["Mejor A", "Mejor B", "Mejor C"]}'
        return '{"message": "You called? I also like the term foliage father", "reply_time": "Tardo: 15 min"}'

    monkeypatch.setattr(server.rotator, "generate_content", fake_generate_content)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 5,
            "evaluated_step_id": 6,
            "lives": 4,
            "attraction": 78,
            "history": [{"sender": "her", "text": "Eso me gusta. Odio cuando el chat parece formulario, prefiero algo con chispa."}],
            "user_message": "Jaja va, entonces nombro lugar y dia: jueves una copa corta?",
            "chosen_time": "15m",
            "visible_context": {"last_natalia_message": "Eso me gusta. Odio cuando el chat parece formulario, prefiero algo con chispa."},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["fallback"] is True
    assert "you called" not in data["natalia_message"].lower()
    assert "jueves" in data["natalia_message"].lower()


def test_fallback_does_not_treat_date_plan_as_week_question(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        level=1,
        step_index=5,
        evaluated_step_id=6,
        lives=4,
        attraction=78,
        history=[
            {"sender": "her", "text": "Eso me gusta. Odio cuando el chat parece formulario, prefiero algo con chispa."},
            {"sender": "user", "text": "Jaja va, entonces nombro lugar y dia: jueves una copa corta?"},
        ],
        user_message="Jaja va, entonces nombro lugar y dia: jueves una copa corta?",
        chosen_time="15m",
        visible_context={"last_natalia_message": "Eso me gusta. Odio cuando el chat parece formulario, prefiero algo con chispa."},
    )

    analysis = server.analyze_visible_turn(request.user_message, request.visible_context["last_natalia_message"], request.chosen_time)
    reply = server.fallback_natalia_message(request, 8, server.level_behavior(1), [])

    assert "dia" not in analysis["direct_question_topics"]
    assert "semana" not in reply.lower()
    assert "caos" not in reply.lower()
    assert any(token in reply.lower() for token in ["plan", "jueves", "copa", "cuando", "interesante", "whatsapp"])


def test_backend_uses_history_over_stale_visible_context(monkeypatch):
    server = load_server(monkeypatch)

    def quota_exhausted(_prompt):
        raise RuntimeError("429 quota")

    monkeypatch.setattr(server.rotator, "generate_content", quota_exhausted)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 2,
            "evaluated_step_id": 3,
            "lives": 4,
            "attraction": 50,
            "history": [
                {"sender": "her", "text": "me gusta eso, perfecto donde vives? yo en brickell y tu?"},
                {"sender": "user", "text": "yo vivo en bogota y en que trabajas?", "timeText": "1h"},
            ],
            "user_message": "yo vivo en bogota y en que trabajas?",
            "chosen_time": "1h",
            "visible_context": {
                "last_natalia_message": "un vino suena bien, pero dime el plan",
                "last_user_message": "yo vivo en bogota y en que trabajas?",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["turn_analysis"]["last_topics"] == ["ubicacion"]
    assert "marketing" in data["natalia_message"].lower()
    assert "vino" not in data["natalia_message"].lower()


def test_heuristic_coach_suggestions_are_context_specific(monkeypatch):
    server = load_server(monkeypatch)

    coach = server.heuristic_score(
        "hola",
        "15m",
        "me gusta eso, perfecto donde vives? yo en brickell y tu?",
    )

    suggestions = " ".join(coach["suggestions"]).lower()
    assert "ubicacion" in suggestions or "pregunto" in suggestions or "visible" in suggestions
    assert coach["suggestions"] != [
        "Haz una respuesta corta que conecte con lo que ella acaba de decir.",
        "Usa humor ligero y evita convertirlo en entrevista.",
        "Usa 0-2 emojis calibrados; evita saturar o sexualizar demasiado pronto.",
    ]


def test_fallback_plan_with_day_gets_specific_logistics(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        level=1,
        step_index=5,
        evaluated_step_id=6,
        lives=4,
        attraction=78,
        history=[
            {"sender": "her", "text": "Eso me gusta. Odio cuando el chat parece formulario, prefiero algo con chispa."},
        ],
        user_message="Jaja va, entonces nombro lugar y dia: jueves una copa corta?",
        chosen_time="15m",
        visible_context={"last_natalia_message": "Eso me gusta. Odio cuando el chat parece formulario, prefiero algo con chispa."},
    )

    reply = server.fallback_natalia_message(request, 8, server.level_behavior(1), [])

    assert "jueves" in reply.lower()
    assert "semana" not in reply.lower()


def test_fallback_can_use_compatible_real_reply_for_plan_intent(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        level=1,
        step_index=5,
        evaluated_step_id=6,
        lives=4,
        attraction=70,
        history=[{"sender": "her", "text": "me gusta cuando aterrizan el plan sin hacerlo intenso"}],
        user_message="jueves una copa tranquila",
        chosen_time="15m",
        visible_context={"last_natalia_message": "me gusta cuando aterrizan el plan sin hacerlo intenso"},
    )
    cases = [
        {
            "source": "sqlite_chat_pair",
            "man_message": "jueves una copa tranquila",
            "woman_response": "Jueves puede ser, pero dime el lugar.",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "9",
        }
    ]

    reply = server.fallback_natalia_message(request, 8, server.level_behavior(1), cases)

    assert reply == "Jueves puede ser, pero dime el lugar."


def test_case_based_suggestions_uses_compatible_real_cases(monkeypatch):
    server = load_server(monkeypatch)
    cases = [
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "Jueves una copa tranquila y sin entrevista.",
            "woman_response": "Jueves puede ser, pero dime el lugar.",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "9",
            "text": "PAR REAL HOMBRE-MUJER\nHombre: Jueves una copa tranquila y sin entrevista.\nMujer: Jueves puede ser, pero dime el lugar.",
        },
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "Tengo datos curiosos sobre trenes.",
            "woman_response": "Dime tu dato de trenes mas raro.",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "10",
            "text": "PAR REAL HOMBRE-MUJER\nHombre: Tengo datos curiosos sobre trenes.\nMujer: Dime tu dato de trenes mas raro.",
        }
    ]
    analysis = server.analyze_visible_turn(
        "jueves una copa tranquila",
        "me gusta cuando aterrizan el plan sin hacerlo intenso",
        "15m",
    )

    suggestions = server.case_based_suggestions(cases, analysis)
    merged = server.merge_suggestions(["Aterriza el plan sin entrevista."], suggestions)

    assert suggestions == ["Jueves una copa tranquila y sin entrevista."]
    assert merged[0] == "Jueves una copa tranquila y sin entrevista."


def test_case_based_suggestions_filters_absurd_location_noise_in_plan(monkeypatch):
    server = load_server(monkeypatch)
    cases = [
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "¿Dónde estoy ahora? ¿Estoy despierto?",
            "woman_response": "jaja",
            "woman_signal": "risa",
            "success_score": "10",
        },
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "Primero tendriamos que salir.",
            "woman_response": "Puede ser.",
            "woman_signal": "receptiva",
            "success_score": "9",
        },
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "Jueves una copa tranquila en un lugar con buena musica.",
            "woman_response": "Jueves puede ser, pero dime el lugar.",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "8",
        },
    ]
    analysis = server.analyze_visible_turn(
        "Si te late, el jueves podemos tomar una copa tranquila y me cuentas si Brickell es tan cool.",
        "Ok, lugar tranquilo suma. Ahora dime cual y veo si confio en tu gusto.",
        "15m",
    )

    assert server.case_based_suggestions(cases, analysis) == [
        "Jueves una copa tranquila en un lugar con buena musica."
    ]


def test_case_based_suggestions_filters_vacation_case_outside_travel_context(monkeypatch):
    server = load_server(monkeypatch)
    cases = [
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "¿Te gustaría? Estoy aquí de vacaciones por otra semana.",
            "woman_response": "Puede ser.",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "9",
        },
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "Jueves una copa tranquila y sin entrevista.",
            "woman_response": "Jueves puede ser.",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "8",
        },
    ]
    analysis = server.analyze_visible_turn(
        "Jueves una copa tranquila y sin hacerlo intenso.",
        "Me gusta cuando aterrizan el plan.",
        "15m",
    )

    assert server.case_based_suggestions(cases, analysis) == [
        "Jueves una copa tranquila y sin entrevista."
    ]


def test_case_based_suggestions_requires_clear_topic(monkeypatch):
    server = load_server(monkeypatch)
    cases = [
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "¿Te gustaría? Estoy aquí de vacaciones por otra semana.",
            "woman_response": "Puede ser.",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "9",
        }
    ]
    analysis = server.analyze_visible_turn("Hola Natalia, qué lindo tu perfil.", "", "15m")

    assert server.case_based_suggestions(cases, analysis) == []


def test_case_based_suggestions_ignores_day_opening_cases(monkeypatch):
    server = load_server(monkeypatch)
    cases = [
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "¿Te gustaria? Estoy aqui de vacaciones por otra semana.",
            "woman_response": "Puede ser.",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "9",
        }
    ]
    analysis = server.analyze_visible_turn("Hola Natalia, que lindo tu perfil. Como va tu semana?", "", "15m")

    assert analysis["direct_question_topics"] == ["dia"]
    assert server.case_based_suggestions(cases, analysis) == []


def test_case_based_suggestions_must_match_direct_question_topic(monkeypatch):
    server = load_server(monkeypatch)
    cases = [
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "Asi que eres de Brasil, verdad?",
            "woman_response": "Si jaja.",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "9",
        },
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "Yo trabajo en algo creativo, pero me gusta mas hablar de planes.",
            "woman_response": "Eso suena mejor.",
            "woman_signal": "receptiva",
            "success_score": "8",
        },
    ]
    analysis = server.analyze_visible_turn(
        "Vivo en Bogota. Y tu en que trabajas?",
        "Eso me gusta. Odio cuando el chat parece formulario.",
        "15m",
    )

    assert analysis["direct_question_topics"] == ["trabajo"]
    assert server.case_based_suggestions(cases, analysis) == [
        "Yo trabajo en algo creativo, pero me gusta mas hablar de planes."
    ]


def test_retrieve_persona_cases_filters_unrelated_direct_question_pairs(monkeypatch):
    server = load_server(monkeypatch)
    cases = [
        {
            "source": "sqlite_reddit_pair",
            "profile": "coqueta",
            "man_message": "Me encanta esa comida, deberiamos ir por tacos.",
            "woman_response": "Jaja puede ser.",
            "woman_signal": "receptiva",
            "success_score": "8",
        },
        {
            "source": "sqlite_reddit_pair",
            "profile": "coqueta",
            "man_message": "Yo trabajo en algo creativo, pero me gusta mas hablar de planes.",
            "woman_response": "Eso suena mejor.",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "9",
        },
    ]

    def fake_retrieve_real_reply_pairs(query, profile, intent=None, limit=8):
        return cases

    monkeypatch.setattr(server, "retrieve_real_reply_pairs", fake_retrieve_real_reply_pairs)
    request = server.SimulateTurnRequest(
        level=1,
        step_index=3,
        evaluated_step_id=4,
        user_message="Vivo en Bogota. Y tu en que trabajas?",
        chosen_time="15m",
        visible_context={"last_natalia_message": "Eso me gusta. Odio cuando el chat parece formulario."},
    )

    filtered = server.retrieve_persona_cases(request, server.level_behavior(1))
    filtered_pairs = [case for case in filtered if case.get("source") == "sqlite_reddit_pair"]

    assert [case["man_message"] for case in filtered_pairs] == [
        "Yo trabajo en algo creativo, pero me gusta mas hablar de planes."
    ]

def test_case_based_suggestions_filters_dark_or_unsafe_lines(monkeypatch):
    server = load_server(monkeypatch)
    cases = [
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "Si... si... fue divertido ponernos al dia. Me tengo que ir a enterrar vivo.",
            "woman_response": "jaja",
            "woman_signal": "risa",
            "success_score": "10",
        },
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "Trato hecho, te escribo con el lugar y sin discurso intenso.",
            "woman_response": "bien",
            "woman_signal": "receptiva",
            "success_score": "8",
        },
    ]
    analysis = server.analyze_visible_turn(
        "Trato hecho, te escribo con el lugar y sin discurso intenso.",
        "Mmm, va... pero usalo bien. Si el plan es bueno, te respondo.",
        "15m",
    )

    suggestions = server.case_based_suggestions(cases, analysis)

    assert suggestions == ["Trato hecho, te escribo con el lugar y sin discurso intenso."]


def test_fallback_answers_zone_logistics_without_generic_curiosity(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        level=1,
        step_index=6,
        evaluated_step_id=7,
        lives=4,
        attraction=75,
        history=[{"sender": "her", "text": "Mmm me gusta. ¿Y qué día dices tú?"}],
        user_message="Me gusta ese estilo, sin presión. ¿Qué zona te queda cómoda?",
        chosen_time="15m",
        visible_context={"last_natalia_message": "Mmm me gusta. ¿Y qué día dices tú?"},
    )

    reply = server.fallback_natalia_message(request, 8, server.level_behavior(1), [])

    assert "brickell" in reply.lower() or "zona" in reply.lower()
    assert "curiosidad" not in reply.lower()
    assert "cuentame" not in reply.lower()


def test_fallback_answers_place_logistics_without_generic_curiosity(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        level=1,
        step_index=7,
        evaluated_step_id=8,
        lives=4,
        attraction=80,
        history=[{"sender": "her", "text": "Por Brickell puede ser. Ahora dime que lugar tienes en mente."}],
        user_message="Perfecto, yo propongo un lugar tranquilo y tú me dices si te convence.",
        chosen_time="15m",
        visible_context={"last_natalia_message": "Por Brickell puede ser. Ahora dime que lugar tienes en mente."},
    )

    reply = server.fallback_natalia_message(request, 8, server.level_behavior(1), [])

    assert "lugar" in reply.lower()
    assert "curiosidad" not in reply.lower()
    assert "entrevista" not in reply.lower()


def test_fallback_closes_after_contact_without_reasking_place(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        level=1,
        step_index=8,
        evaluated_step_id=9,
        lives=4,
        attraction=90,
        history=[{"sender": "her", "text": "Mmm, va... pero usalo bien. Si el plan es bueno, te respondo 😉"}],
        user_message="Trato hecho, te escribo con el lugar y sin discurso intenso 😉",
        chosen_time="15m",
        visible_context={"last_natalia_message": "Mmm, va... pero usalo bien. Si el plan es bueno, te respondo 😉"},
    )

    reply = server.fallback_natalia_message(request, 8, server.level_behavior(1), [])
    lowered = reply.lower()

    assert "dime el lugar" not in lowered
    assert "lugar tienes" not in lowered
    assert "plan" in lowered or "claro" in lowered or "cumples" in lowered


def test_numeric_phone_message_is_contact_intent(monkeypatch):
    server = load_server(monkeypatch)
    request = server.SimulateTurnRequest(
        level=1,
        step_index=8,
        evaluated_step_id=9,
        lives=4,
        attraction=85,
        history=[{"sender": "her", "text": "Mmm va, pero usalo bien. Si el plan es bueno, te respondo."}],
        user_message="Te lo paso: +1 305 555 0188. Lo usamos solo para cuadrar bien.",
        chosen_time="15m",
        visible_context={"last_natalia_message": "Mmm va, pero usalo bien. Si el plan es bueno, te respondo."},
    )

    analysis = server.analyze_visible_turn(
        request.user_message,
        request.visible_context["last_natalia_message"],
        request.chosen_time,
    )
    reply = server.fallback_natalia_message(request, 8, server.level_behavior(1), [])

    assert analysis["intent"] == "pedir_contacto"
    assert "contacto" in analysis["user_topics"]
    assert any(token in reply.lower() for token in ["respondo", "cuadrar", "whatsapp", "plan"])


def test_level1_human_coherence_contract_across_full_session(monkeypatch):
    server = load_server(monkeypatch)

    def quota_exhausted(_prompt):
        raise RuntimeError("429 quota")

    monkeypatch.setattr(server.rotator, "generate_content", quota_exhausted)
    client = TestClient(server.app)
    history = []
    last_natalia = ""
    messages = [
        (
            "Hola Natalia, esa sonrisa parece de alguien que sabe escoger buenos planes. Como va tu dia?",
            ["dia"],
            ["semana", "dia", "trabajo"],
            ["vino", "whatsapp", "donde vives"],
        ),
        (
            "Bien, saliendo del gym. A ti que deporte te gusta?",
            ["ejercicio"],
            ["pilates", "caminar", "gym", "aire libre", "mover"],
            ["vino", "donde vives", "whatsapp"],
        ),
        (
            "Hago pesas y algo de cardio, sin volverme fanatico. Y tu en que trabajas?",
            ["trabajo"],
            ["marketing", "trabajo"],
            ["vino", "whatsapp"],
        ),
        (
            "Marketing visual suena creativo. Cuando no estas trabajando, que musica te gusta?",
            ["musica"],
            ["musica", "bailar", "escuchar", "playlist"],
            ["vino", "whatsapp"],
        ),
        (
            "Soy mas de bailar salsa y musica con energia. Que comida disfrutas?",
            ["comida"],
            ["comer", "comida", "lugar"],
            ["whatsapp"],
        ),
        (
            "Entonces te debo un lugar rico, buena musica y cero entrevista.",
            [],
            ["lugar", "concret", "gusto", "confio", "filtro"],
            ["whatsapp"],
        ),
        (
            "Si te late, el jueves podemos tomar una copa tranquila por Brickell y vemos si mi gusto pasa tu filtro.",
            [],
            ["jueves", "funcionar", "posible", "lugar"],
            ["marketing"],
        ),
        (
            "Prometo plan simple: una copa, buena conversacion y sin interrogatorio eterno. Te paso mi WhatsApp?",
            ["contacto"],
            ["va", "usalo", "whatsapp", "respondo", "plan", "te lo paso", "entrevista"],
            ["mascota", "gato"],
        ),
        (
            "Te lo paso: +1 305 555 0188. Lo usamos solo para cuadrar bien.",
            [],
            ["respondo", "cuadrar", "whatsapp", "plan"],
            ["veterana de tinder", "primera cita"],
        ),
        (
            "Trato hecho, te escribo con lugar y hora, sin discurso intenso.",
            [],
            ["claro", "plan", "vuelta", "cumples", "simple"],
            ["dime el lugar", "whatsapp?"],
        ),
    ]
    replies = []

    for index, (message, direct_topics, expected_reply_tokens, forbidden_reply_tokens) in enumerate(messages):
        response = client.post(
            "/api/simulate-turn",
            json={
                "level": 1,
                "step_index": index,
                "evaluated_step_id": index + 1,
                "lives": 4,
                "attraction": 50 + index * 5,
                "history": history,
                "user_message": message,
                "chosen_time": "15m",
                "visible_context": {
                    "last_natalia_message": last_natalia,
                    "last_user_message": message,
                    "chat_snapshot": "\n".join(
                        f"{'Natalia' if item['sender'] == 'her' else 'Hombre'}: {item['text']}"
                        for item in history[-6:]
                    ),
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        reply = data["natalia_message"].lower()
        feedback = data["coach_feedback"].lower()

        assert data["lose_life"] is False, (index + 1, message, data["coach_feedback"])
        for topic in direct_topics:
            assert topic in data["turn_analysis"]["direct_question_topics"], (index + 1, data["turn_analysis"])
        assert any(token in reply for token in expected_reply_tokens), (index + 1, reply)
        assert not any(token in reply for token in forbidden_reply_tokens), (index + 1, reply)
        assert "contexto de la conversacion" in feedback
        assert "objetivo del turno" in feedback
        assert data["retrieval_summary"]["persona_pair_cases"] >= 0

        replies.append(server.normalized_reply_text(reply))
        history.append({"sender": "user", "text": message, "timeText": "15m"})
        history.append({"sender": "her", "text": data["natalia_message"], "timeText": data["natalia_time"]})
        last_natalia = data["natalia_message"]

    assert len(set(replies)) == len(replies)


def test_simulate_turn_accepts_plain_text_live_natalia_when_coherent(monkeypatch):
    monkeypatch.setenv("GEMINI_COACH_ENABLED", "0")
    server = load_server(monkeypatch)

    def plain_text_reply(_prompt):
        return "Me gusta caminar y algo de pilates, pero sin volverme intensa con el tema."

    monkeypatch.setattr(server.rotator, "generate_content", plain_text_reply)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 1,
            "evaluated_step_id": 2,
            "lives": 4,
            "attraction": 55,
            "history": [{"sender": "her", "text": "Va tranquila mi semana. Y la tuya?"}],
            "user_message": "Bien, saliendo del gym. A ti que deporte te gusta?",
            "chosen_time": "15m",
            "visible_context": {"last_natalia_message": "Va tranquila mi semana. Y la tuya?"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["fallback"] is False
    assert data["retrieval_summary"]["natalia_live_used"] is True
    assert "pilates" in data["natalia_message"].lower()


def test_plain_text_live_natalia_still_rejects_topic_jump(monkeypatch):
    monkeypatch.setenv("GEMINI_COACH_ENABLED", "0")
    server = load_server(monkeypatch)

    def bad_plain_text_reply(_prompt):
        return "Jaja mejor vamos por vino este jueves."

    monkeypatch.setattr(server.rotator, "generate_content", bad_plain_text_reply)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 1,
            "evaluated_step_id": 2,
            "lives": 4,
            "attraction": 55,
            "history": [{"sender": "her", "text": "Va tranquila mi semana. Y la tuya?"}],
            "user_message": "Bien, saliendo del gym. A ti que deporte te gusta?",
            "chosen_time": "15m",
            "visible_context": {"last_natalia_message": "Va tranquila mi semana. Y la tuya?"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["fallback"] is True
    assert data["retrieval_summary"]["natalia_live_used"] is False
    assert data["retrieval_summary"]["natalia_fallback_category"] == "guardrail"
    assert "vino" not in data["natalia_message"].lower()


def test_simulate_turn_reports_api_fallback_reason(monkeypatch):
    monkeypatch.setenv("GEMINI_COACH_ENABLED", "0")
    server = load_server(monkeypatch)

    def fake_generate_content(_prompt):
        raise server.HTTPException(status_code=429, detail="Gemini quota cooldown active for 30s.")

    monkeypatch.setattr(server.rotator, "generate_content", fake_generate_content)
    client = TestClient(server.app)

    response = client.post(
        "/api/simulate-turn",
        json={
            "level": 1,
            "step_index": 1,
            "evaluated_step_id": 2,
            "lives": 4,
            "attraction": 60,
            "history": [{"sender": "her", "text": "esa soy yo totalmente jaja como va tu dia?"}],
            "user_message": "Bien, saliendo de entrenar suave. A ti que deporte te gusta?",
            "chosen_time": "15m",
            "visible_context": {"last_natalia_message": "esa soy yo totalmente jaja como va tu dia?"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["fallback"] is True
    assert data["retrieval_summary"]["natalia_live_used"] is False
    assert data["retrieval_summary"]["natalia_fallback_category"] == "api"
    assert "quota cooldown" in data["retrieval_summary"]["natalia_fallback_reason"].lower()


def test_persona_prompt_uses_only_human_reply_pairs(monkeypatch):
    server = load_server(monkeypatch)
    cases = [
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "Jueves una copa tranquila.",
            "woman_response": "Puede ser, dime el lugar.",
            "text": "PAR REAL HOMBRE-MUJER\nHombre: Jueves una copa tranquila.\nMujer: Puede ser, dime el lugar.",
        },
        {
            "source": "sqlite_youtube",
            "profile": "theory",
            "text": "Transcripcion YouTube sobre teoria que Natalia no debe imitar.",
        },
    ]

    prompt = server.persona_cases_to_prompt(cases)

    assert "Puede ser, dime el lugar" in prompt
    assert "YouTube" not in prompt


def test_cases_to_prompt_can_compact_without_losing_labels(monkeypatch):
    server = load_server(monkeypatch)
    cases = [
        {
            "source": "sqlite_reddit_pair",
            "profile": "coqueta",
            "intent": "cerrar_plan",
            "woman_signal": "pregunta_de_vuelta",
            "success_score": "8",
            "text": "x" * 1000,
        },
        {
            "source": "chroma",
            "profile": "coqueta",
            "text": "y" * 1000,
        },
    ]

    prompt = server.cases_to_prompt(cases, max_cases=1, max_text_chars=120)

    assert "CASO 1 [sqlite_reddit_pair/coqueta intent=cerrar_plan signal=pregunta_de_vuelta success=8]" in prompt
    assert "CASO 2" not in prompt
    assert len(prompt) < 260
    assert prompt.endswith("...")


def test_persona_cases_to_prompt_compacts_human_pairs(monkeypatch):
    server = load_server(monkeypatch)
    cases = [
        {
            "source": "sqlite_chat_pair",
            "profile": "coqueta",
            "man_message": "Jueves una copa tranquila.",
            "woman_response": "Puede ser, dime el lugar.",
            "text": "PAR REAL HOMBRE-MUJER\n" + ("detalle " * 200),
        },
        {
            "source": "sqlite_youtube",
            "profile": "theory",
            "text": "Transcripcion YouTube sobre teoria que Natalia no debe imitar.",
        },
    ]

    prompt = server.persona_cases_to_prompt(cases, max_text_chars=80)

    assert "sqlite_chat_pair" in prompt
    assert "YouTube" not in prompt
    assert len(prompt) < 220
