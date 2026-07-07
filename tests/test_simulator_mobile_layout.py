from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SIMULATOR_HTML = PROJECT_ROOT / "simulador_v1.2.html"
MOBILE_VIEWPORTS = (
    {"width": 390, "height": 844},
    {"width": 360, "height": 640},
)


def _open_mobile_page(playwright, viewport):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        viewport=viewport,
        is_mobile=True,
        has_touch=True,
    )
    page = context.new_page()
    page.goto(SIMULATOR_HTML.as_uri())
    page.wait_for_selector("#free-reply-input")
    page.wait_for_selector("#time-slider")
    page.wait_for_selector(".bottom-panel")
    return browser, context, page


def _element_box_in_viewport(page, selector):
    return page.locator(selector).evaluate(
        """(el) => {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return {
                top: rect.top,
                bottom: rect.bottom,
                left: rect.left,
                right: rect.right,
                width: rect.width,
                height: rect.height,
                display: style.display,
                visibility: style.visibility,
                opacity: Number(style.opacity),
                viewportWidth: window.innerWidth,
                viewportHeight: window.innerHeight,
            };
        }"""
    )


def _assert_visible_in_viewport(page, selector):
    box = _element_box_in_viewport(page, selector)

    assert box["display"] != "none"
    assert box["visibility"] != "hidden"
    assert box["opacity"] > 0
    assert box["width"] > 0
    assert box["height"] > 0
    assert box["top"] >= 0
    assert box["left"] >= 0
    assert box["bottom"] <= box["viewportHeight"]
    assert box["right"] <= box["viewportWidth"]


@pytest.mark.parametrize("viewport", MOBILE_VIEWPORTS)
def test_mobile_free_reply_controls_stay_visible(viewport):
    sync_api = pytest.importorskip("playwright.sync_api")

    with sync_api.sync_playwright() as playwright:
        try:
            browser, context, page = _open_mobile_page(playwright, viewport)
        except Exception as exc:
            pytest.skip(f"Playwright/Chromium no disponible en este entorno: {exc}")

        try:
            _assert_visible_in_viewport(page, "#free-reply-input")
            _assert_visible_in_viewport(page, "#time-slider")
            _assert_visible_in_viewport(page, "#slider-time-display")

            footer_box = _element_box_in_viewport(page, ".bottom-panel")
            assert footer_box["height"] <= viewport["height"] * 0.49

            page.locator("#free-reply-input").focus()
            page.wait_for_timeout(100)

            _assert_visible_in_viewport(page, "#free-reply-input")
            _assert_visible_in_viewport(page, "#time-slider")
            _assert_visible_in_viewport(page, "#slider-time-display")
        finally:
            context.close()
            browser.close()
