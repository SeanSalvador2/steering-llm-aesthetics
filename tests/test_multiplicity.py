"""Multiplicity tests: Holm + BH + the confirmatory family registry (THEORY §T6.4; PREREG §4)."""
import pytest

from p19 import multiplicity as mp


def test_confirmatory_family_is_twelve():
    """The frozen confirmatory family has exactly 12 tests (PREREG §4)."""
    assert len(mp.CONFIRMATORY_FAMILY) == 12
    assert mp.CONFIRMATORY_FAMILY.count("FULL-NEUTRAL") == 1
    assert sum(1 for n in mp.CONFIRMATORY_FAMILY if n.startswith("FULL-LOO")) == 5
    assert sum(1 for n in mp.CONFIRMATORY_FAMILY if n.startswith("AOI")) == 5


def test_holm_controls_and_orders():
    """Holm rejects the smallest p when it clears alpha/m and steps down (THEORY T6.4)."""
    ps = [0.001, 0.02, 0.03, 0.5]
    res = mp.holm(ps, ["a", "b", "c", "d"], alpha=0.05)
    by = {r.name: r for r in res}
    assert by["a"].reject                # 0.001 <= 0.05/4
    assert not by["d"].reject            # 0.5 not rejected
    # adjusted p-values are monotone non-decreasing in p
    assert by["a"].adjusted_p <= by["b"].adjusted_p <= by["c"].adjusted_p


def test_holm_more_powerful_than_bonferroni():
    """Holm rejects at least as much as Bonferroni (larger later thresholds; THEORY T6.4)."""
    ps = [0.01, 0.02, 0.049, 0.5]
    holm_rej = sum(r.reject for r in mp.holm(ps, alpha=0.05))
    bonf_rej = sum(p <= 0.05 / len(ps) for p in ps)
    assert holm_rej >= bonf_rej


def test_bh_step_up():
    """BH finds k* and rejects the k* smallest (THEORY T6.4)."""
    ps = [0.001, 0.008, 0.02, 0.5, 0.9]
    res = mp.benjamini_hochberg(ps, q=0.10)
    rejected = {r.name for r in res if r.reject}
    assert "H0" in rejected and "H1" in rejected  # the two smallest survive FDR 0.10
    assert "H4" not in rejected


def test_confirmatory_holm_requires_exact_family():
    """confirmatory_holm guards against testing a set other than the frozen family (PREREG §4)."""
    good = {n: 0.01 for n in mp.CONFIRMATORY_FAMILY}
    out = mp.confirmatory_holm(good)
    assert len(out) == 12
    with pytest.raises(ValueError):
        mp.confirmatory_holm({"FULL-NEUTRAL": 0.01})  # missing 11
