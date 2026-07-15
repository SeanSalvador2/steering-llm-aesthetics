"""Rendering tests (PLAN §III.8, §VI.5; 06_playwright_determinism).

Chromium is preinstalled at /opt/pw-browsers (PLAYWRIGHT_BROWSERS_PATH); do NOT `playwright install`.
"""
import pytest

from p19 import rendering


def test_hermetic_flag_helpers():
    """External-scheme detection: data:/about:/blob: are hermetic; http(s) are external (App B.1)."""
    assert rendering._is_external("https://fonts.googleapis.com/x.css")
    assert not rendering._is_external("data:image/png;base64,AAAA")
    assert not rendering._is_external("about:blank")


@pytest.mark.slow
def test_external_request_blocked_and_counted():
    """A page requesting an external resource is blocked, counted, and re-scored non-hermetic (B.1)."""
    html = '<html><head><link rel="stylesheet" href="https://example.com/x.css"></head>' \
           '<body><h1>hi</h1></body></html>'
    r = rendering.render_html(html, gen_id="ext")
    assert r.n_external_requests >= 1
    assert not r.hermetic and not r.render_success  # non-hermetic -> render_success re-scored 0


@pytest.mark.slow
def test_fixture_renders_and_extracts_dom(rendered_fixtures):
    """Fixtures render hermetically and produce a DOM with per-element boxes + axe results (§III.8)."""
    r = rendered_fixtures["clean_landing"]
    assert r.render_success and r.hermetic
    assert r.dom["n_elements"] > 5
    el = r.dom["elements"][0]
    for key in ("x", "y", "w", "h", "color", "bg", "fontFamily", "fontSize"):
        assert key in el
    assert "axe_violations" in r.dom


@pytest.mark.slow
def test_screenshot_written(rendered_fixtures):
    """A desktop PNG is produced for each fixture (screenshot spec §III.8)."""
    r = rendered_fixtures["minimal_valid"]
    assert "desktop" in r.screenshots
    from pathlib import Path
    assert Path(r.screenshots["desktop"]).exists()
