"""DOM-side objective metrics (PLAN §III.3 families V/A/L/T; THEORY §T7; Appendix B).

Computed on the RENDERED DOM (bounding boxes + computed styles from src/p19/rendering.py),
never on raw code strings (CLAUDE.md). Implements exactly the formulas in THEORY §T7.1-T7.3,
T7.5, and the DOM half of PSI (T7.6). Screenshot-pixel metrics live in metrics_visual.py.

Families here:
  V  render-success / hermeticity / overflow / overlap / axe violations by impact
  A  WCAG contrast (piecewise sRGB luminance, size-aware AA)
  L  Ngo balance/equilibrium/symmetry, alignment regularity, gap entropy, whitespace/density
  T  distinct font sizes/families, modular type-scale adherence
  + PSI DOM subcomponents: gradient prevalence, Inter/Roboto share, centered-hero flag
"""
from __future__ import annotations

import math
from typing import Any

from .config import render_config

# canonical modular ratios for type-scale fitting (THEORY T7.7 / Appendix B.4)
_MODULAR_RATIOS = [1.125, 1.2, 1.25, 1.333, 1.414, 1.5]
_SLOP_FONTS = ("inter", "roboto", "system-ui")


# --------------------------------------------------------------------------- WCAG (family A)

def _lin(c: float) -> float:
    """Undo sRGB gamma for a channel in [0,1] (THEORY T7.1)."""
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb) -> float:
    """WCAG relative luminance L = 0.2126 R + 0.7152 G + 0.0722 B on linearized channels."""
    r, g, b = rgb[0], rgb[1], rgb[2]
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(rgb1, rgb2) -> float:
    """WCAG contrast ratio (L1+0.05)/(L2+0.05) in [1, 21] (THEORY T7.2)."""
    l1 = relative_luminance(rgb1)
    l2 = relative_luminance(rgb2)
    hi, lo = (l1, l2) if l1 >= l2 else (l2, l1)
    return (hi + 0.05) / (lo + 0.05)


def _aa_threshold(font_size: float, weight: str) -> float:
    """Size-aware AA threshold: 3.0 for large text (>=24px, or >=18.66px bold), else 4.5."""
    try:
        w = int(float(weight))
    except (TypeError, ValueError):
        w = 700 if str(weight).lower() in ("bold", "bolder") else 400
    large = font_size >= 24 or (font_size >= 18.66 and w >= 700)
    return 3.0 if large else 4.5


def contrast_metrics(elements: list[dict]) -> dict:
    """Per-text-node contrast: fraction failing AA, min, median (PLAN B.2).

    contrast_frac_below_4_5 uses the size-aware AA threshold (4.5 normal / 3.0 large; THEORY
    T7.1's stated AA bands) — "4_5" names the nominal AA bar, the check is WCAG-correct.
    """
    crs: list[float] = []
    fails = 0
    for el in elements:
        if not el.get("directText") or el.get("textLen", 0) == 0 or el.get("color") is None:
            continue
        cr = contrast_ratio(el["color"], el["bg"])
        crs.append(cr)
        if cr < _aa_threshold(el.get("fontSize", 16), el.get("fontWeight", "400")):
            fails += 1
    if not crs:
        return {"contrast_frac_below_4_5": 0.0, "contrast_min": 21.0, "contrast_median": 21.0,
                "n_text_nodes": 0}
    crs.sort()
    n = len(crs)
    median = crs[n // 2] if n % 2 else 0.5 * (crs[n // 2 - 1] + crs[n // 2])
    return {
        "contrast_frac_below_4_5": fails / n,
        "contrast_min": crs[0],
        "contrast_median": median,
        "n_text_nodes": n,
    }


# --------------------------------------------------------------------------- overflow/overlap (family V)

def _area(el) -> float:
    return max(0.0, el["w"]) * max(0.0, el["h"])


def _intersection_area(a, b) -> float:
    ix = max(0.0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    iy = max(0.0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    return ix * iy


def overflow_overlap(dom: dict) -> dict:
    """Count content/viewport overflow elements and significant sibling overlaps (family V)."""
    vp = dom["viewport"]
    els = dom["elements"]
    vw = vp["w"]
    tol = 2.0
    overflow_ids = set()
    for i, el in enumerate(els):
        content_overflow = el.get("scrollW", 0) > el.get("clientW", 0) + tol
        beyond_viewport = (el["x"] >= -tol) and (el["x"] + el["w"] > vw + tol)
        if content_overflow or beyond_viewport:
            overflow_ids.add(i)
    n_overflow = len(overflow_ids)

    # overlaps: significant intersection, excluding containment (parent-child).
    n_overlap = 0
    n = len(els)
    for i in range(n):
        for j in range(i + 1, n):
            inter = _intersection_area(els[i], els[j])
            if inter <= 0:
                continue
            amin = min(_area(els[i]), _area(els[j]))
            if amin <= 0:
                continue
            frac = inter / amin
            if frac >= 0.95:  # containment (one box inside the other) -> not an overlap defect
                continue
            if frac >= 0.20:
                n_overlap += 1
    return {"n_overflow": n_overflow, "n_overlap": n_overlap}


def axe_counts(dom: dict) -> dict:
    """axe-core violation counts by impact + total (family V)."""
    by_impact = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
    total = 0
    for v in dom.get("axe_violations", []) or []:
        imp = v.get("impact") or "minor"
        by_impact[imp] = by_impact.get(imp, 0) + 1
        total += 1
    return {"axe_violations_by_impact": by_impact, "axe_total": total}


# --------------------------------------------------------------------------- Ngo layout (family L)

def ngo_measures(dom: dict) -> dict:
    """Ngo balance BM, equilibrium EM, symmetry SYM in [0,1], higher = better (THEORY T7.3/T7.4)."""
    vp = dom["viewport"]
    W, H = vp["w"], vp["h"]
    cx, cy = W / 2.0, H / 2.0
    els = [e for e in dom["elements"] if _area(e) > 0]
    if not els:
        return {"ngo_balance": 0.0, "ngo_equilibrium": 0.0, "ngo_symmetry": 0.0}

    # Balance: summed area x distance-to-axis on each side (T7.3).
    def _bm(axis: str) -> float:
        pos = neg = 0.0
        for e in els:
            a = _area(e)
            if axis == "v":  # vertical center axis -> left/right
                d = e["cx"] - cx
            else:            # horizontal center axis -> top/bottom
                d = e["cy"] - cy
            if d >= 0:
                pos += a * abs(d)
            else:
                neg += a * abs(d)
        denom = max(pos, neg)
        return 0.0 if denom == 0 else (pos - neg) / denom

    bm = 1.0 - (abs(_bm("v")) + abs(_bm("h"))) / 2.0

    # Equilibrium: area-weighted center-of-mass offset from the frame center (T7.4),
    # normalized to [-1,1] as 2 * mean-offset / frame-dimension.
    tot_area = sum(_area(e) for e in els) or 1.0
    sum_ax = sum(_area(e) * (e["cx"] - cx) for e in els)
    sum_ay = sum(_area(e) * (e["cy"] - cy) for e in els)
    em_x = max(-1.0, min(1.0, 2.0 * sum_ax / (tot_area * W))) if W else 0.0
    em_y = max(-1.0, min(1.0, 2.0 * sum_ay / (tot_area * H))) if H else 0.0
    em = 1.0 - (abs(em_x) + abs(em_y)) / 2.0

    # Symmetry: quadrant reflection agreement over normalized (x,y,w,h,dist) (T7.4, simplified Ngo).
    sym = _ngo_symmetry(els, cx, cy, W, H)
    return {"ngo_balance": max(0.0, bm), "ngo_equilibrium": max(0.0, em), "ngo_symmetry": sym}


def _ngo_symmetry(els, cx, cy, W, H) -> float:
    """Quadrant-based Ngo symmetry (vertical + horizontal), in [0,1]."""
    quads = {"UL": [], "UR": [], "LL": [], "LR": []}
    for e in els:
        h = "L" if e["cx"] < cx else "R"
        v = "U" if e["cy"] < cy else "L"
        quads[("U" if v == "U" else "L") + ("L" if h == "L" else "R")].append(e)

    def _vec(q):
        if not q:
            return (0.0, 0.0, 0.0, 0.0, 0.0)
        n = len(q)
        return (
            sum(abs(e["cx"] - cx) for e in q) / n / (W / 2),
            sum(abs(e["cy"] - cy) for e in q) / n / (H / 2),
            sum(e["w"] for e in q) / n / W,
            sum(e["h"] for e in q) / n / H,
            sum(math.hypot(e["cx"] - cx, e["cy"] - cy) for e in q) / n / math.hypot(W / 2, H / 2),
        )

    ul, ur, ll, lr = _vec(quads["UL"]), _vec(quads["UR"]), _vec(quads["LL"]), _vec(quads["LR"])

    def _diff(a, b):
        return sum(abs(x - y) for x, y in zip(a, b)) / len(a)

    # vertical symmetry: left mirrors right; horizontal symmetry: top mirrors bottom
    v_sym = 1.0 - 0.5 * (_diff(ul, ur) + _diff(ll, lr))
    h_sym = 1.0 - 0.5 * (_diff(ul, ll) + _diff(ur, lr))
    return max(0.0, min(1.0, 0.5 * (v_sym + h_sym)))


def alignment_regularity(dom: dict) -> dict:
    """align_regularity = 1 - n_distinct_edges/n_elements + gap entropy (THEORY T7.5/T7.6)."""
    els = dom["elements"]
    n = len(els)
    if n == 0:
        return {"align_regularity": 0.0, "gap_entropy": 1.0}
    xr = set()
    yr = set()
    for e in els:
        xr.add(round(e["x"]))
        xr.add(round(e["x"] + e["w"]))
        yr.add(round(e["y"]))
        yr.add(round(e["y"] + e["h"]))
    n_distinct = len(xr) + len(yr)
    align = 1.0 - n_distinct / n

    # gap entropy (T7.6): vertical gaps between consecutive elements sorted by top edge.
    bin_px = render_config().get("gap_bin_px", 4)
    tops = sorted(e["y"] for e in els)
    gaps = [max(0.0, tops[i + 1] - tops[i]) for i in range(len(tops) - 1)]
    if not gaps:
        gap_entropy = 0.0
    else:
        bins: dict[int, int] = {}
        for g in gaps:
            b = int(g // bin_px)
            bins[b] = bins.get(b, 0) + 1
        total = sum(bins.values())
        H = -sum((c / total) * math.log(c / total) for c in bins.values())
        max_h = math.log(len(bins)) if len(bins) > 1 else 1.0
        gap_entropy = H / max_h if max_h > 0 else 0.0
    return {"align_regularity": align, "gap_entropy": gap_entropy}


_REPLACED_TAGS = {"img", "svg", "picture", "button", "input", "select", "textarea",
                  "canvas", "video", "hr", "iframe"}


def _is_content(e: dict, page_area: float) -> bool:
    """A visible content element for occupancy: text, media/controls, or a filled/gradient block.

    Transparent/plain layout containers (their padding is visual whitespace) and any full-page
    wrapper (area > 0.6 page) are excluded, so whitespace_ratio reflects content coverage (Ngo).
    """
    if _area(e) > 0.6 * page_area:
        return False
    if e.get("directText"):
        return True
    if e.get("tag") in _REPLACED_TAGS:
        return True
    if e.get("hasGradient"):
        return True
    bg = e.get("bg")
    # a filled colour block that departs from the near-white canvas
    if bg is not None and (abs(bg[0] - 255) + abs(bg[1] - 255) + abs(bg[2] - 255)) > 40 \
            and _area(e) < 0.5 * page_area:
        return True
    return False


def whitespace_density(dom: dict) -> dict:
    """whitespace_ratio = 1 - occupied/viewport; density = occupied/viewport (union via raster)."""
    vp = dom["viewport"]
    W, H = int(vp["w"]), int(vp["h"])
    if W <= 0 or H <= 0:
        return {"whitespace_ratio": 1.0, "density": 0.0}
    cell = 16
    page_area = float(W * H)
    gw, gh = max(1, W // cell), max(1, H // cell)
    grid = bytearray(gw * gh)
    for e in dom["elements"]:
        if not _is_content(e, page_area):
            continue
        x0 = max(0, int(e["x"] // cell))
        y0 = max(0, int(e["y"] // cell))
        x1 = min(gw, int((e["x"] + e["w"]) // cell) + 1)
        y1 = min(gh, int((e["y"] + e["h"]) // cell) + 1)
        for gy in range(y0, y1):
            base = gy * gw
            for gx in range(x0, x1):
                grid[base + gx] = 1
    occupied = sum(grid) / (gw * gh)
    return {"whitespace_ratio": 1.0 - occupied, "density": occupied}


# --------------------------------------------------------------------------- typography (family T)

def typography(dom: dict) -> dict:
    """distinct font sizes/families + modular-scale adherence (THEORY T7.7 / Appendix B.4)."""
    els = [e for e in dom["elements"] if e.get("textLen", 0) > 0 and e.get("fontSize", 0) > 0]
    sizes = sorted({round(e["fontSize"], 1) for e in els})
    fams = set()
    for e in els:
        fam = (e.get("fontFamily", "") or "").split(",")[0].strip().strip("'\"").lower()
        if fam:
            fams.add(fam)
    n_sizes = len(sizes)
    n_fams = len(fams)

    if n_sizes < 2:
        adherence = 1.0
    else:
        ratios = [sizes[i + 1] / sizes[i] for i in range(len(sizes) - 1) if sizes[i] > 0]
        best = 0
        for r in _MODULAR_RATIOS:
            hits = sum(1 for rk in ratios if abs(math.log(rk) - math.log(r)) <= math.log(1.10))
            best = max(best, hits)
        adherence = best / len(ratios) if ratios else 1.0
    return {"n_font_sizes": n_sizes, "n_font_families": n_fams, "type_scale_adherence": adherence}


# --------------------------------------------------------------------------- PSI DOM subcomponents

def psi_dom_subcomponents(dom: dict) -> dict:
    """gradientBgPrevalence, InterRobotoShare, centeredHeroFlag (THEORY T7.6, DOM half)."""
    vp = dom["viewport"]
    W, H = vp["w"], vp["h"]
    els = dom["elements"]
    page_area = max(1.0, W * H)

    large = [e for e in els if _area(e) >= 0.12 * page_area]
    grad = sum(1 for e in large if e.get("hasGradient"))
    psi_gradient = grad / len(large) if large else 0.0

    text_els = [e for e in els if e.get("textLen", 0) > 0]
    inter = 0
    for e in text_els:
        fam = (e.get("fontFamily", "") or "").lower()
        first = fam.split(",")[0].strip().strip("'\"")
        if any(sf in first for sf in _SLOP_FONTS):
            inter += 1
    psi_inter = inter / len(text_els) if text_els else 0.0

    # centered hero: a large element centered horizontally in the top third of the viewport
    centered = 0
    for e in els:
        if _area(e) < 0.10 * page_area:
            continue
        if e["cy"] > H / 3.0:
            continue
        off = abs(e["cx"] - W / 2.0) / (W / 2.0)
        if off < 0.12 and e["w"] > 0.5 * W:
            centered = 1
            break
    return {"psi_gradient": float(psi_gradient), "psi_inter": float(psi_inter),
            "psi_centered": float(centered)}


# --------------------------------------------------------------------------- aggregate

def compute(render_result) -> dict[str, Any]:
    """Full DOM-metric dict for a RenderResult (families V/A/L/T + PSI DOM subcomponents)."""
    dom = render_result.dom or {"viewport": {"w": 1440, "h": 900, "scrollW": 1440, "scrollH": 900},
                                "elements": [], "n_elements": 0}
    row: dict[str, Any] = {}
    row["render_success"] = int(render_result.render_success)
    row["hermetic"] = int(render_result.hermetic)
    row["n_external_requests"] = render_result.n_external_requests
    row["console_errors"] = render_result.console_errors
    row.update(overflow_overlap(dom))
    row.update(axe_counts(dom))
    row.update(contrast_metrics(dom["elements"]))
    row.update(ngo_measures(dom))
    row.update(alignment_regularity(dom))
    row.update(whitespace_density(dom))
    row.update(typography(dom))
    row.update(psi_dom_subcomponents(dom))
    return row
