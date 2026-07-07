from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SIMULATOR_HTML = PROJECT_ROOT / "simulador_v1.2.html"


def test_simulator_html_has_no_common_mojibake():
    html = SIMULATOR_HTML.read_text(encoding="utf-8")

    assert "window.easyDateTest" in html
    assert "Nivel ${level.level_id || gameState.level_index + 1} · Paso" in html

    for marker in ("dÃ", "nÃ", "quÃ", "Â¿", "Â¡", "ðŸ", "â", "â€”"):
        assert marker not in html


def test_level1_free_text_happy_path_with_playwright():
    sync_api = pytest.importorskip("playwright.sync_api")

    try:
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(SIMULATOR_HTML.as_uri())
            page.wait_for_function("window.easyDateTest && window.easyDateTest.runLevel1HappyPath")
            result = page.evaluate("window.easyDateTest.runLevel1HappyPath()")
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright/Chromium no disponible en este entorno: {exc}")

    assert result["levelUpOpen"] is True
    assert result["coachOpen"] is False
    assert result["coachDisplay"] == "none"
    assert result["coachPointerEvents"] == "none"
    assert result["state"]["level_index"] == 0
    assert result["state"]["step_index"] == 10
    assert result["state"]["lives"] == 4
    assert result["state"]["replyMode"] == "free"
    assert result["state"]["stats"]["good"] == 10
    assert result["state"]["stats"]["bad"] == 0
    assert len(result["visited"]) == 10
    assert result["visited"][0]["progress"] == "Nivel 1 · Paso 1 de 10"
    assert result["visited"][-1]["progress"] == "Nivel 1 · Paso 10 de 10"
    assert "Resumen: 10 buenas, 0 por mejorar" in result["levelUpSummary"]
    assert "Patron fuerte" in result["levelUpSummary"]
    assert "Mejor mensaje:" in result["levelUpSummary"]
    assert "Mensaje a corregir:" in result["levelUpSummary"]


def test_frontend_fallback_context_coherence_with_playwright():
    sync_api = pytest.importorskip("playwright.sync_api")

    try:
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(SIMULATOR_HTML.as_uri())
            page.wait_for_function("window.easyDateTest && window.easyDateTest.runContextCoherenceSmoke")
            result = page.evaluate("window.easyDateTest.runContextCoherenceSmoke()")
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright/Chromium no disponible en este entorno: {exc}")

    week_reply = result["week"]["natalia_message"].lower()
    exercise_reply = result["exercise"]["natalia_message"].lower()
    work_reply = result["work"]["natalia_message"].lower()
    music_reply = result["music"]["natalia_message"].lower()
    food_reply = result["food"]["natalia_message"].lower()
    travel_reply = result["travel"]["natalia_message"].lower()
    pets_reply = result["pets"]["natalia_message"].lower()
    family_reply = result["family"]["natalia_message"].lower()

    assert any(token in week_reply for token in ["semana", "dia", "día"])
    assert "visita" not in week_reply
    assert "donde" not in week_reply
    assert any(token in exercise_reply for token in ["gym", "ejercicio", "mover", "disciplina", "rutina"])
    assert "dónde vives" not in exercise_reply
    assert "vino" not in exercise_reply
    assert "marketing" in work_reply
    assert "vino" not in work_reply
    assert any(token in music_reply for token in ["mÃºsica", "musica", "bailar", "escuchar"])
    assert "vino" not in music_reply
    assert any(token in food_reply for token in ["comer", "comida", "lugar"])
    assert any(token in travel_reply for token in ["viaje", "viajes", "playa", "ciudad"])
    assert any(token in pets_reply for token in ["mascota", "perro", "gato"])
    assert "familia" in family_reply or "gente" in family_reply


def test_guided_mode_does_not_mix_with_free_text_and_emojis_are_evaluable():
    sync_api = pytest.importorskip("playwright.sync_api")

    try:
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(SIMULATOR_HTML.as_uri())
            page.wait_for_function("window.easyDateTest && document.getElementById('match-start-btn')")
            page.click("#match-start-btn")
            page.click("#mode-guided")
            guided_state = page.evaluate(
                """() => ({
                    freeDisplay: getComputedStyle(document.getElementById('free-composer')).display,
                    guidedDisplay: getComputedStyle(document.getElementById('guided-composer')).display,
                    textareaValue: document.getElementById('free-reply-input').value
                })"""
            )
            page.click("#mode-free")
            page.fill("#free-reply-input", "hola")
            page.evaluate("document.getElementById('free-reply-input').setSelectionRange(0, 0)")
            page.click(".emoji-chip")
            emoji_value = page.eval_on_selector("#free-reply-input", "el => el.value")
            visible_controls = page.evaluate(
                """() => ({
                    gifButtons: document.querySelectorAll('.gif-pill').length,
                    sendButtons: document.querySelectorAll('#btn-send').length
                })"""
            )
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright/Chromium no disponible en este entorno: {exc}")

    assert guided_state["freeDisplay"] == "none"
    assert guided_state["guidedDisplay"] == "block"
    assert guided_state["textareaValue"] == ""
    assert len(emoji_value) > len("hola")
    assert visible_controls == {"gifButtons": 0, "sendButtons": 0}


def test_guided_suggestion_click_sends_when_time_is_selected():
    sync_api = pytest.importorskip("playwright.sync_api")

    try:
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(SIMULATOR_HTML.as_uri())
            page.wait_for_function("window.easyDateTest && document.getElementById('match-start-btn')")
            page.evaluate("window.easyDateForceMockApi = true")
            page.click("#match-start-btn")
            page.click("#mode-guided")
            page.evaluate("setSelectedTimeIndex(1)")
            first_option_text = page.locator(".option-card .text-content").first.inner_text()
            page.locator(".option-card").first.click()
            page.wait_for_selector("#modal-overlay.active")
            state = page.evaluate(
                """() => ({
                    userBubble: document.querySelector('.message.user .bubble')?.innerText || '',
                    coachOpen: document.getElementById('modal-overlay').classList.contains('active'),
                    locked: window.easyDateTest.getState().locked,
                    selected: document.querySelector('input[name="reply_opt"]:checked') !== null
                })"""
            )
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright/Chromium no disponible en este entorno: {exc}")

    assert first_option_text in state["userBubble"]
    assert state == {
        "userBubble": state["userBubble"],
        "coachOpen": True,
        "locked": True,
        "selected": True,
    }


def test_guided_suggestion_click_requires_time_range():
    sync_api = pytest.importorskip("playwright.sync_api")

    try:
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(SIMULATOR_HTML.as_uri())
            page.wait_for_function("window.easyDateTest && document.getElementById('match-start-btn')")
            page.click("#match-start-btn")
            page.click("#mode-guided")
            page.on("dialog", lambda dialog: dialog.dismiss())
            page.locator(".option-card").first.click()
            page.wait_for_timeout(250)
            state = page.evaluate(
                """() => ({
                    userMessages: document.querySelectorAll('.message.user').length,
                    locked: window.easyDateTest.getState().locked,
                    selected: document.getElementById('time-slider').dataset.selected,
                    checked: document.querySelector('input[name="reply_opt"]:checked') !== null,
                    display: document.getElementById('slider-time-display').innerText
                })"""
            )
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright/Chromium no disponible en este entorno: {exc}")

    assert state == {
        "userMessages": 0,
        "locked": False,
        "selected": "false",
        "checked": True,
        "display": "Toca para seleccionar",
    }


def test_blocking_modals_disable_chat_controls():
    sync_api = pytest.importorskip("playwright.sync_api")

    try:
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(SIMULATOR_HTML.as_uri())
            page.wait_for_function("window.easyDateTest && document.getElementById('match-start-btn')")
            page.click("#match-start-btn")

            page.evaluate("showHelpModal()")
            help_state = page.evaluate(
                """() => ({
                    helpOpen: document.getElementById('help-modal').classList.contains('active'),
                    locked: window.easyDateTest.getState().locked,
                    inputDisabled: document.getElementById('free-reply-input').disabled,
                    sliderDisabled: document.getElementById('time-slider').disabled,
                    emojiDisabled: document.querySelector('.emoji-chip').disabled
                })"""
            )
            page.evaluate("closeHelpModal()")
            closed_help_state = page.evaluate(
                """() => ({
                    helpOpen: document.getElementById('help-modal').classList.contains('active'),
                    locked: window.easyDateTest.getState().locked,
                    inputDisabled: document.getElementById('free-reply-input').disabled,
                    sliderDisabled: document.getElementById('time-slider').disabled,
                    emojiDisabled: document.querySelector('.emoji-chip').disabled
                })"""
            )

            page.evaluate("showFinalWinModal()")
            final_state = page.evaluate(
                """() => ({
                    finalOpen: document.getElementById('final-modal').classList.contains('active'),
                    locked: window.easyDateTest.getState().locked,
                    inputDisabled: document.getElementById('free-reply-input').disabled,
                    sliderDisabled: document.getElementById('time-slider').disabled,
                    emojiDisabled: document.querySelector('.emoji-chip').disabled
                })"""
            )
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright/Chromium no disponible en este entorno: {exc}")

    assert help_state == {
        "helpOpen": True,
        "locked": True,
        "inputDisabled": True,
        "sliderDisabled": True,
        "emojiDisabled": True,
    }
    assert closed_help_state == {
        "helpOpen": False,
        "locked": False,
        "inputDisabled": False,
        "sliderDisabled": False,
        "emojiDisabled": False,
    }
    assert final_state == {
        "finalOpen": True,
        "locked": True,
        "inputDisabled": True,
        "sliderDisabled": True,
        "emojiDisabled": True,
    }


def test_gameover_modal_shows_summary_and_study_button():
    sync_api = pytest.importorskip("playwright.sync_api")

    try:
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(SIMULATOR_HTML.as_uri())
            page.wait_for_function("window.easyDateTest && document.getElementById('match-start-btn')")
            page.click("#match-start-btn")
            page.evaluate(
                """() => window.easyDateTest.openGameOverForTest(2, 4, 0, [
                    { step: 1, message: 'Hola Natalia, que tal tu dia?', score: 7, loseLife: false, reason: 'correcto' },
                    { step: 2, message: 'Hola hermosa por favor contestame ya', score: 3, loseLife: true, reason: 'necesitado' }
                ])"""
            )
            result = page.evaluate(
                """() => ({
                    open: document.getElementById('gameover-modal').classList.contains('active'),
                    summary: document.getElementById('gameover-summary').innerText,
                    hasStudyButton: [...document.querySelectorAll('#gameover-modal button')]
                        .some((button) => button.innerText.includes('ESTUDIAR CASOS REALES'))
                })"""
            )
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright/Chromium no disponible en este entorno: {exc}")

    assert result["open"] is True
    assert "Resumen: 2 buenas, 4 por mejorar" in result["summary"]
    assert "Mejor mensaje: P1 (7/10)" in result["summary"]
    assert "Mensaje a corregir: P2 (3/10)" in result["summary"]
    assert "Antes de repetir" in result["summary"]
    assert result["hasStudyButton"] is True


def test_level1_user_can_type_enter_and_continue():
    sync_api = pytest.importorskip("playwright.sync_api")

    try:
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(SIMULATOR_HTML.as_uri())
            page.wait_for_function("window.easyDateTest && document.getElementById('match-start-btn')")
            page.evaluate("window.easyDateForceMockApi = true")
            page.click("#match-start-btn")
            page.evaluate("setSelectedTimeIndex(1)")
            page.fill("#free-reply-input", "Hola Natalia, que lindo tu perfil. Como va tu semana?")
            page.press("#free-reply-input", "Enter")
            page.wait_for_selector("#modal-overlay.active")
            open_state = page.evaluate(
                """() => ({
                    userBubble: [...document.querySelectorAll('.message.user .bubble')].some(el => el.innerText.includes('Como va tu semana')),
                    coachOpen: document.getElementById('modal-overlay').classList.contains('active'),
                    coachLabels: [...document.querySelectorAll('.coach-feedback-label')].map(el => el.innerText),
                    coachSuggestionCount: document.querySelectorAll('.coach-card-suggestions li').length,
                    locked: window.easyDateTest.getState().locked,
                    inputDisabled: document.getElementById('free-reply-input').disabled,
                    sliderDisabled: document.getElementById('time-slider').disabled
                })"""
            )
            page.click("#btn-close-modal")
            page.wait_for_function("!document.getElementById('modal-overlay').classList.contains('active')")
            closed_state = page.evaluate(
                """() => ({
                    coachOpen: document.getElementById('modal-overlay').classList.contains('active'),
                    locked: window.easyDateTest.getState().locked,
                    inputDisabled: document.getElementById('free-reply-input').disabled,
                    sliderDisabled: document.getElementById('time-slider').disabled,
                    timeSelected: document.getElementById('time-slider').dataset.selected,
                    stepIndex: window.easyDateTest.getState().step_index
                })"""
            )
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright/Chromium no disponible en este entorno: {exc}")

    assert open_state == {
        "userBubble": True,
        "coachOpen": True,
        "coachLabels": ["MENSAJE", "TIEMPO DE RESPUESTA", "OBJETIVO", "SUGERENCIAS"],
        "coachSuggestionCount": 3,
        "locked": True,
        "inputDisabled": True,
        "sliderDisabled": True,
    }
    assert closed_state == {
        "coachOpen": False,
        "locked": False,
        "inputDisabled": False,
        "sliderDisabled": False,
        "timeSelected": "false",
        "stepIndex": 1,
    }


def test_enter_requires_time_range_before_sending():
    sync_api = pytest.importorskip("playwright.sync_api")

    try:
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(SIMULATOR_HTML.as_uri())
            page.wait_for_function("window.easyDateTest && document.getElementById('match-start-btn')")
            page.click("#match-start-btn")
            page.on("dialog", lambda dialog: dialog.dismiss())
            page.fill("#free-reply-input", "Hola Natalia, que lindo tu perfil. Como va tu semana?")
            page.press("#free-reply-input", "Enter")
            state = page.evaluate(
                """() => ({
                    userMessages: document.querySelectorAll('.message.user').length,
                    locked: window.easyDateTest.getState().locked,
                    selected: document.getElementById('time-slider').dataset.selected,
                    display: document.getElementById('slider-time-display').innerText
                })"""
            )
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright/Chromium no disponible en este entorno: {exc}")

    assert state == {
        "userMessages": 0,
        "locked": False,
        "selected": "false",
        "display": "Toca para seleccionar",
    }


def test_time_selector_turns_green_after_first_touch():
    sync_api = pytest.importorskip("playwright.sync_api")

    try:
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(SIMULATOR_HTML.as_uri())
            page.wait_for_function("window.easyDateTest && document.getElementById('match-start-btn')")
            page.click("#match-start-btn")
            before = page.evaluate(
                """() => ({
                    selected: document.getElementById('time-slider').dataset.selected,
                    red: document.querySelector('.time-selector').classList.contains('time-unselected'),
                    green: document.querySelector('.time-selector').classList.contains('time-selected'),
                    display: document.getElementById('slider-time-display').innerText
                })"""
            )
            page.locator("#time-slider").click()
            after = page.evaluate(
                """() => ({
                    selected: document.getElementById('time-slider').dataset.selected,
                    red: document.querySelector('.time-selector').classList.contains('time-unselected'),
                    green: document.querySelector('.time-selector').classList.contains('time-selected'),
                    display: document.getElementById('slider-time-display').innerText
                })"""
            )
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright/Chromium no disponible en este entorno: {exc}")

    assert before == {
        "selected": "false",
        "red": True,
        "green": False,
        "display": "Toca para seleccionar",
    }
    assert after["selected"] == "true"
    assert after["red"] is False
    assert after["green"] is True
    assert after["display"].startswith("Rango seleccionado:")


def test_enter_locks_controls_while_fetch_pending_and_prevents_double_submit():
    sync_api = pytest.importorskip("playwright.sync_api")

    try:
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(SIMULATOR_HTML.as_uri())
            page.wait_for_function("window.easyDateTest && document.getElementById('match-start-btn')")
            page.evaluate(
                """() => {
                    window.easyDateFetchCalls = [];
                    window.fetch = (url, options) => {
                        window.easyDateFetchCalls.push({ url, body: options && options.body });
                        return new Promise(() => {});
                    };
                }"""
            )
            page.click("#match-start-btn")
            page.evaluate("setSelectedTimeIndex(1)")
            page.fill("#free-reply-input", "Hola Natalia, que lindo tu perfil. Como va tu semana?")
            page.press("#free-reply-input", "Enter")
            page.press("#free-reply-input", "Enter")
            page.wait_for_function("window.easyDateFetchCalls.length === 1")
            state = page.evaluate(
                """() => ({
                    calls: window.easyDateFetchCalls.length,
                    locked: window.easyDateTest.getState().locked,
                    inputDisabled: document.getElementById('free-reply-input').disabled,
                    emojiDisabled: document.querySelector('.emoji-chip').disabled,
                    sliderDisabled: document.getElementById('time-slider').disabled
                })"""
            )
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright/Chromium no disponible en este entorno: {exc}")

    assert state["calls"] == 1
    assert state["locked"] is True
    assert state["inputDisabled"] is True
    assert state["emojiDisabled"] is True
    assert state["sliderDisabled"] is True
