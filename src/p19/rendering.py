"""Deterministic Playwright rendering + DOM extraction (PLAN §III.8, §VI.5; 06_playwright_determinism).

Renders hermetic single-file HTML to a screenshot PNG + a DOM-JSON (per-element bounding boxes
and the computed styles the metrics need) + a render/hermeticity/console record. Network is
BLOCKED: every external request is aborted and counted as a hermeticity violation. axe-core is
injected from the vendored copy (no network) and run to collect violations by impact.

Chromium is preinstalled at /opt/pw-browsers (PLAYWRIGHT_BROWSERS_PATH); do NOT `playwright install`.
Playwright is a core CPU dependency; it is imported lazily so the module still imports if the
browser is briefly unavailable (tests then skip with a clear reason).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import VENDOR_DIR
from .config import render_config

# JS run in-page to extract everything the DOM metrics need. Returns a plain-JSON structure.
_DOM_EXTRACT_JS = r"""
() => {
  const vw = window.innerWidth, vh = window.innerHeight;
  const doc = document.documentElement;
  const parseColor = (s) => {
    // returns [r,g,b,a] in 0..255 / 0..1, or null for transparent/none
    if (!s || s === 'transparent' || s === 'none') return null;
    const m = s.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(x => parseFloat(x.trim()));
    const a = p.length > 3 ? p[3] : 1;
    if (a === 0) return null;
    return [p[0], p[1], p[2], a];
  };
  const effectiveBg = (el) => {
    let node = el;
    while (node && node !== document) {
      const cs = getComputedStyle(node);
      const c = parseColor(cs.backgroundColor);
      if (c && c[3] >= 0.5) return [c[0], c[1], c[2]];
      node = node.parentElement;
    }
    return [255, 255, 255]; // default canvas white
  };
  const hasDirectText = (el) => {
    for (const n of el.childNodes) {
      if (n.nodeType === 3 && n.textContent.trim().length > 0) return true;
    }
    return false;
  };
  const els = [];
  const all = document.body ? document.body.querySelectorAll('*') : [];
  all.forEach((el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return;
    const bgImage = cs.backgroundImage || 'none';
    const color = parseColor(cs.color);
    const isText = hasDirectText(el);
    els.push({
      tag: el.tagName.toLowerCase(),
      x: r.left, y: r.top, w: r.width, h: r.height,
      color: color ? [color[0], color[1], color[2]] : null,
      bg: effectiveBg(el),
      bgImage: bgImage,
      hasGradient: /gradient/i.test(bgImage),
      fontFamily: cs.fontFamily || '',
      fontSize: parseFloat(cs.fontSize) || 0,
      fontWeight: cs.fontWeight || '',
      textLen: (el.textContent || '').trim().length,
      directText: isText,
      cx: r.left + r.width / 2, cy: r.top + r.height / 2,
      scrollW: el.scrollWidth, clientW: el.clientWidth,
      scrollH: el.scrollHeight, clientH: el.clientHeight,
    });
  });
  return {
    viewport: { w: vw, h: vh, scrollW: doc.scrollWidth, scrollH: doc.scrollHeight },
    n_elements: els.length,
    elements: els,
  };
}
"""


@dataclass
class RenderResult:
    gen_id: str
    render_success: bool
    hermetic: bool
    n_external_requests: int
    console_errors: int
    viewport: dict
    dom: dict
    screenshots: dict[str, str] = field(default_factory=dict)
    dom_json_path: str | None = None
    error: str | None = None

    def summary(self) -> dict:
        return {
            "gen_id": self.gen_id,
            "render_success": int(self.render_success),
            "hermetic": int(self.hermetic),
            "n_external_requests": self.n_external_requests,
            "console_errors": self.console_errors,
            "n_elements": self.dom.get("n_elements", 0) if self.dom else 0,
        }


def _axe_source() -> str:
    return (VENDOR_DIR / render_config()["axe_vendor"]).read_text(encoding="utf-8")


def _is_external(url: str) -> bool:
    """External = a real network scheme; data:/about:/blob: and the in-memory doc are hermetic."""
    u = url.lower()
    if u.startswith(("data:", "about:", "blob:")):
        return False
    return u.startswith(("http://", "https://", "ftp://", "ws://", "wss://"))


def render_html(
    html: str,
    gen_id: str = "adhoc",
    out_dir: str | Path | None = None,
    viewports: tuple[str, ...] = ("desktop",),
    run_axe: bool = True,
) -> RenderResult:
    """Render an HTML string hermetically and extract DOM + axe results.

    Parameters mirror the frozen recipe (config/render.yaml): DSF 1, animations disabled, caret
    hidden, network offline (external requests aborted+counted), fonts.ready awaited, settle delay.
    """
    from playwright.sync_api import sync_playwright  # lazy import (browser may be unavailable)

    rc = render_config()
    dims = {"desktop": rc["desktop"], "mobile": rc["mobile"]}
    settle_ms = rc.get("settle_ms", 400)

    out = Path(out_dir) if out_dir else None
    if out:
        out.mkdir(parents=True, exist_ok=True)

    external = {"count": 0}
    console_errors = {"count": 0}
    result = RenderResult(
        gen_id=gen_id, render_success=False, hermetic=True, n_external_requests=0,
        console_errors=0, viewport={}, dom={}, screenshots={},
    )

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--force-color-profile=srgb", "--hide-scrollbars"])
            primary = viewports[0]
            context = browser.new_context(
                viewport={"width": dims[primary][0], "height": dims[primary][1]},
                device_scale_factor=rc.get("dsf", 1),
                reduced_motion="reduce",
                offline=True,
            )

            def _route(route):
                req_url = route.request.url
                if _is_external(req_url):
                    external["count"] += 1
                    route.abort()
                else:
                    route.continue_()

            context.route("**/*", _route)
            page = context.new_page()
            page.on("console", lambda m: console_errors.__setitem__(
                "count", console_errors["count"] + (1 if m.type == "error" else 0)))
            page.on("pageerror", lambda e: console_errors.__setitem__(
                "count", console_errors["count"] + 1))

            try:
                page.set_content(html, wait_until="load", timeout=15000)
            except Exception:
                # networkidle can hang if aborted requests retry; 'load' is sufficient hermetically
                pass
            try:
                page.wait_for_load_state("networkidle", timeout=4000)
            except Exception:
                pass
            if rc.get("fonts_ready", True):
                try:
                    page.evaluate("() => document.fonts && document.fonts.ready")
                except Exception:
                    pass
            page.wait_for_timeout(settle_ms)

            dom = page.evaluate(_DOM_EXTRACT_JS)
            result.dom = dom
            result.viewport = dom.get("viewport", {})

            if run_axe:
                try:
                    page.add_script_tag(content=_axe_source())
                    axe = page.evaluate(
                        "async () => { const r = await axe.run(document, "
                        "{resultTypes:['violations']}); return r.violations.map(v => "
                        "({impact: v.impact, nodes: v.nodes.length})); }"
                    )
                    dom["axe_violations"] = axe
                except Exception as e:  # axe failure is non-fatal; recorded as empty
                    dom["axe_violations"] = []
                    dom["axe_error"] = str(e)[:200]

            # screenshots
            for vp in viewports:
                if vp != primary:
                    page.set_viewport_size({"width": dims[vp][0], "height": dims[vp][1]})
                    page.wait_for_timeout(settle_ms)
                shot = page.screenshot(
                    full_page=True, animations="disabled", caret="hide",
                    path=str(out / f"{gen_id}_{vp}.png") if out else None,
                )
                if out:
                    result.screenshots[vp] = str(out / f"{gen_id}_{vp}.png")

            result.render_success = True
            browser.close()
    except Exception as e:  # hard render failure
        result.error = str(e)[:300]
        result.render_success = False

    result.n_external_requests = external["count"]
    result.console_errors = console_errors["count"]
    result.hermetic = external["count"] == 0
    # a non-hermetic page is re-scored render_success=0 for POC purposes (ADR-006 / PLAN B.1)
    if not result.hermetic:
        result.render_success = False

    if out and result.dom:
        djson = out / f"{gen_id}_dom.json"
        djson.write_text(json.dumps(result.dom), encoding="utf-8")
        result.dom_json_path = str(djson)

    return result


def render_file(path: str | Path, **kwargs) -> RenderResult:
    """Render an HTML file. gen_id defaults to the file stem."""
    p = Path(path)
    kwargs.setdefault("gen_id", p.stem)
    return render_html(p.read_text(encoding="utf-8"), **kwargs)
