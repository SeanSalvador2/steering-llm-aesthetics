"""Objective-metric tests on the fixtures + known-value checks (THEORY §T7; PLAN App B).

The fixtures are hand-authored so every metric has a known-direction case (PLAN §VI.1):
clean beats slop on POC; slop's PSI > clean's; the overflow fixture triggers overflow/overlap;
axe counts are nonzero where designed.
"""
import pytest

from p19 import metrics_dom as md


# --- known-value unit checks (THEORY T7.1/T7.2) ---

def test_wcag_contrast_black_white():
    """CR(black,white) = 21; CR(x,x) = 1 (THEORY T7.2)."""
    assert abs(md.contrast_ratio([0, 0, 0], [255, 255, 255]) - 21.0) < 1e-6
    assert abs(md.contrast_ratio([120, 120, 120], [120, 120, 120]) - 1.0) < 1e-9


def test_relative_luminance_endpoints():
    """Relative luminance: black=0, white=1 (THEORY T7.1)."""
    assert md.relative_luminance([0, 0, 0]) == 0.0
    assert abs(md.relative_luminance([255, 255, 255]) - 1.0) < 1e-9


def test_size_aware_aa_threshold():
    """Large text uses the 3.0 AA bar, normal text 4.5 (THEORY T7.1)."""
    assert md._aa_threshold(28, "400") == 3.0
    assert md._aa_threshold(16, "400") == 4.5
    assert md._aa_threshold(19, "700") == 3.0  # >=18.66px bold is large


# --- fixture-level orderings (the demo requirements) ---

def test_all_fixtures_render_hermetically(rendered_fixtures):
    """Every fixture renders with zero external requests (hermetic; PLAN App B.1)."""
    for name, r in rendered_fixtures.items():
        assert r.render_success, name
        assert r.hermetic and r.n_external_requests == 0, name


def test_clean_beats_slop_on_poc(fixture_metrics_df):
    """clean_landing POC > slop_landing POC (the oracle direction; PLAN §VI.1)."""
    df = fixture_metrics_df.set_index("gen_id")
    assert df.loc["clean_landing", "poc"] > df.loc["slop_landing", "poc"]


def test_slop_psi_exceeds_clean(fixture_metrics_df):
    """slop_landing PSI > clean_landing PSI (THEORY T7.9)."""
    df = fixture_metrics_df.set_index("gen_id")
    assert df.loc["slop_landing", "psi"] > df.loc["clean_landing", "psi"]
    assert df.loc["slop_landing", "psi"] > 0.5  # the slop tells fire
    assert df.loc["clean_landing", "psi"] < 0.1


def test_overflow_fixture_triggers_counts(fixture_metrics_df):
    """overflow_broken triggers overflow AND overlap counts (family V; THEORY T7)."""
    df = fixture_metrics_df.set_index("gen_id")
    assert df.loc["overflow_broken", "n_overflow"] > 0
    assert df.loc["overflow_broken", "n_overlap"] > 0
    # well-formed fixtures do not overflow or overlap
    assert df.loc["minimal_valid", "n_overflow"] == 0
    assert df.loc["clean_landing", "n_overflow"] == 0
    assert df.loc["clean_landing", "n_overlap"] == 0


def test_axe_nonzero_where_designed(fixture_metrics_df):
    """slop_landing has axe violations (low contrast); minimal_valid has none (family V)."""
    df = fixture_metrics_df.set_index("gen_id")
    assert df.loc["slop_landing", "axe_total"] > 0
    assert df.loc["slop_landing", "contrast_frac_below_4_5"] > 0  # low-contrast text present


def test_psi_subcomponents_on_slop(fixture_metrics_df):
    """slop fires gradient, Inter, and centered-hero PSI subcomponents (THEORY T7.9)."""
    df = fixture_metrics_df.set_index("gen_id")
    assert df.loc["slop_landing", "psi_gradient"] > 0
    assert df.loc["slop_landing", "psi_inter"] > 0.5
    assert df.loc["slop_landing", "psi_centered"] == 1.0
    assert df.loc["slop_landing", "psi_hue"] > 0.3  # purple pixels


def test_colorfulness_ordering(fixture_metrics_df):
    """Hasler colorfulness: slop (purple gradient) >> minimal (near-monochrome) (THEORY T7.8)."""
    df = fixture_metrics_df.set_index("gen_id")
    assert df.loc["slop_landing", "colorfulness"] > df.loc["minimal_valid", "colorfulness"]
