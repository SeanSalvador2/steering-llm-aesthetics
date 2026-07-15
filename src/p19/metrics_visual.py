"""Screenshot-pixel objective metrics (PLAN §III.3 family C/X; THEORY §T7.4-T7.6; Appendix B.5-B.7).

Computed on the desktop 1440x900 PNG. Implements Hasler-Susstrunk colorfulness, dominant-color
count, figure-ground contrast, quadtree visual complexity, the PSI hue subcomponent, and the PSI
composite (combining the DOM subcomponents from metrics_dom.py).

UIClip / CLIP are learned signals -> import-guarded optional stubs only (THEORY T7.8); never
oracle evidence.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

# PSI default weights (PLAN §III.3 / THEORY T7.9 / Appendix B.7).
PSI_WEIGHTS = {"hue": 0.30, "gradient": 0.30, "inter": 0.25, "centered": 0.15}


def _load_rgb(png_path: str | Path, max_w: int = 720) -> np.ndarray:
    """Load PNG as an HxWx3 uint8 array, downsampled to <= max_w wide for deterministic speed."""
    img = Image.open(png_path).convert("RGB")
    if img.width > max_w:
        scale = max_w / img.width
        img = img.resize((max_w, max(1, int(img.height * scale))), Image.BILINEAR)
    return np.asarray(img, dtype=np.uint8)


def hasler_colorfulness(arr: np.ndarray) -> float:
    """Hasler-Susstrunk colorfulness M = sigma_rgyb + 0.3 mu_rgyb (THEORY T7.8)."""
    r = arr[..., 0].astype(np.float64)
    g = arr[..., 1].astype(np.float64)
    b = arr[..., 2].astype(np.float64)
    rg = r - g
    yb = 0.5 * (r + g) - b
    sigma = math.sqrt(rg.var() + yb.var())
    mu = math.sqrt(rg.mean() ** 2 + yb.mean() ** 2)
    return sigma + 0.3 * mu


def dominant_colors(arr: np.ndarray, coverage: float = 0.02, n_bins: int = 4) -> int:
    """Count quantized colors each covering >= `coverage` of pixels (Appendix B.5)."""
    step = 256 // n_bins
    buckets = (arr // step).reshape(-1, 3)
    keys = buckets[:, 0].astype(np.int64) * n_bins * n_bins + buckets[:, 1] * n_bins + buckets[:, 2]
    counts = np.bincount(keys, minlength=n_bins ** 3)
    total = keys.shape[0]
    return int(np.sum(counts >= coverage * total))


def figure_ground(arr: np.ndarray, n_bins: int = 8) -> float:
    """Figure-ground contrast: distance from the background (modal) color to the foreground mean.

    Normalized by max RGB distance (441.7) -> [0,1] (Appendix B.5).
    """
    step = 256 // n_bins
    buckets = (arr // step).reshape(-1, 3)
    keys = buckets[:, 0].astype(np.int64) * n_bins * n_bins + buckets[:, 1] * n_bins + buckets[:, 2]
    counts = np.bincount(keys, minlength=n_bins ** 3)
    bg_key = int(np.argmax(counts))
    pixels = arr.reshape(-1, 3).astype(np.float64)
    bg_mask = keys == bg_key
    bg_color = pixels[bg_mask].mean(axis=0)
    fg = pixels[~bg_mask]
    if fg.shape[0] == 0:
        return 0.0
    fg_color = fg.mean(axis=0)
    dist = float(np.linalg.norm(fg_color - bg_color))
    return min(1.0, dist / 441.673)


def visual_complexity(arr: np.ndarray, var_threshold: float = 250.0, min_cell: int = 8) -> float:
    """Quadtree leaf count to a variance threshold, normalized to [0,1] (Appendix B.6)."""
    gray = arr.mean(axis=2)
    H, W = gray.shape
    max_leaves = (H / min_cell) * (W / min_cell)
    leaves = 0
    stack = [(0, 0, H, W)]
    while stack:
        y0, x0, h, w = stack.pop()
        region = gray[y0:y0 + h, x0:x0 + w]
        if region.size == 0:
            continue
        if h <= min_cell or w <= min_cell or region.var() <= var_threshold:
            leaves += 1
            continue
        hh, hw = h // 2, w // 2
        if hh == 0 or hw == 0:
            leaves += 1
            continue
        stack.append((y0, x0, hh, hw))
        stack.append((y0, x0 + hw, hh, w - hw))
        stack.append((y0 + hh, x0, h - hh, hw))
        stack.append((y0 + hh, x0 + hw, h - hh, w - hw))
    return min(1.0, leaves / max_leaves) if max_leaves > 0 else 0.0


def psi_hue_fraction(png_path: str | Path) -> float:
    """Share of SALIENT pixels with HSV hue in [260,290] deg (purple band; THEORY T7.9)."""
    img = Image.open(png_path).convert("RGB")
    if img.width > 720:
        scale = 720 / img.width
        img = img.resize((720, max(1, int(img.height * scale))), Image.BILINEAR)
    hsv = np.asarray(img.convert("HSV"), dtype=np.float64)
    h = hsv[..., 0] * 360.0 / 255.0
    s = hsv[..., 1] / 255.0
    v = hsv[..., 2] / 255.0
    salient = (s > 0.15) & (v > 0.10) & (v < 0.95)
    n_sal = int(salient.sum())
    if n_sal == 0:
        return 0.0
    purple = salient & (h >= 260.0) & (h <= 290.0)
    return float(purple.sum()) / n_sal


def psi_composite(hue: float, gradient: float, inter: float, centered: float) -> dict:
    """PSI composite + subcomponents (THEORY T7.9). Lower = less slop."""
    w = PSI_WEIGHTS
    psi = w["hue"] * hue + w["gradient"] * gradient + w["inter"] * inter + w["centered"] * centered
    return {"psi": psi, "psi_hue": hue, "psi_gradient": gradient, "psi_inter": inter,
            "psi_centered": centered}


def compute(png_path: str | Path) -> dict[str, Any]:
    """Screenshot metric dict (family C/X + PSI hue). psi_hue is combined with DOM subcomponents."""
    arr = _load_rgb(png_path)
    return {
        "colorfulness": hasler_colorfulness(arr),
        "n_dominant_colors": dominant_colors(arr),
        "figure_ground": figure_ground(arr),
        "visual_complexity": visual_complexity(arr),
        "psi_hue": psi_hue_fraction(png_path),
    }


# ------------------------------------------------------------------ learned aux (optional stubs)

def uiclip_score(png_path: str | Path) -> float:  # pragma: no cover - GPU/model dep
    """UIClip design-quality score (auxiliary only; THEORY T7.8). Import-guarded stub.

    Admitted as a *secondary* signal only if rho(UIClip, human win-rate) >= 0.3 (PREREG §9);
    never enters POC. Requires the UIClip checkpoint on Colab; returns -1.0 sentinel here.
    """
    try:
        import torch  # noqa: F401
        raise NotImplementedError(
            "UIClip scoring runs on Colab with the UIClip checkpoint (PLAN aux; THEORY T7.8)."
        )
    except ImportError:
        return -1.0


def clip_relevance(png_path: str | Path, brief: str) -> float:  # pragma: no cover - GPU/model dep
    """CLIP prompt<->screenshot relevance (auxiliary only). Import-guarded stub; -1.0 sentinel."""
    try:
        import torch  # noqa: F401
        raise NotImplementedError("CLIP relevance runs on Colab with a CLIP checkpoint.")
    except ImportError:
        return -1.0
