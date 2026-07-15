"""POC + the two pre-specified conditionals (THEORY §T7.10; PLAN §III.4; PREREG §4/§9)."""
import numpy as np
import pandas as pd

from p19 import poc


def _toy_df():
    """Small metric table with a render-failed unit, for POC-path tests."""
    base = dict(align_regularity=0.5, whitespace_ratio=0.5, type_scale_adherence=0.6,
                contrast_frac_below_4_5=0.1, n_overflow=0, n_overlap=0, psi=0.1,
                colorfulness=20.0)
    rows = []
    for i, (cell, rs, psi, cf) in enumerate([
            ("FULL", 1, 0.05, 22.0), ("FULL", 1, 0.06, 21.0),
            ("NEUTRAL", 1, 0.5, 40.0), ("NEUTRAL", 1, 0.6, 45.0),
            ("BAD", 0, 0.9, 90.0)]):  # render-failed unit
        r = dict(base); r.update(cell_id=cell, render_success=rs, psi=psi, colorfulness=cf,
                                 gen_id=f"g{i}")
        rows.append(r)
    return pd.DataFrame(rows)


def test_render_failed_excluded_from_poc():
    """Render-failed units get NaN POC and are excluded from the z-reference (THEORY T7.10)."""
    df = _toy_df()
    res = poc.compute_poc(df)
    poc_vals = res["poc"]
    assert np.isnan(poc_vals.iloc[-1])           # the render-failed BAD unit
    assert poc_vals.iloc[:4].notna().all()


def test_seven_term_vs_six_term_psi_conditional():
    """Conditional (i): PSI failing admission drops the -PSI term -> 6-term POC (PREREG §4)."""
    df = _toy_df()
    seven = poc.compute_poc(df, psi_admit=True)
    six = poc.compute_poc(df, psi_admit=False)
    assert seven["n_terms"] == 7 and six["n_terms"] == 6
    assert "psi" in seven["terms"] and "psi" not in six["terms"]


def test_psi_admission_gate():
    """PSI admitted iff Spearman rho >= 0.4; None (no data) provisionally admitted (PREREG §9)."""
    assert poc.resolve_psi_admission(0.5) is True
    assert poc.resolve_psi_admission(0.3) is False
    assert poc.resolve_psi_admission(None) is True


def test_c_star_fallback_branches():
    """Conditional (ii): >=30 human pages -> 'human'; else dev-FULL median; else population (PREREG §9)."""
    df = _toy_df()
    c_dev, branch_dev = poc.resolve_c_star(df, n_human_preferred=0)
    assert branch_dev == "dev_full"
    assert c_dev == np.median([22.0, 21.0])       # FULL colorfulness median
    c_hum, branch_hum = poc.resolve_c_star(df, n_human_preferred=40,
                                           human_preferred_colorfulness=[30.0] * 40)
    assert branch_hum == "human" and c_hum == 30.0
    # no FULL rows -> population branch
    df2 = df[df.cell_id != "FULL"]
    _, branch_pop = poc.resolve_c_star(df2, n_human_preferred=0)
    assert branch_pop == "population"


def test_poc_orientation_higher_is_better():
    """A page with better metrics scores higher POC than a worse one (THEORY T7.10 orientation)."""
    df = _toy_df()
    res = poc.compute_poc(df)
    df = df.assign(poc=res["poc"])
    good = df[df.cell_id == "FULL"].poc.mean()
    bad = df[df.cell_id == "NEUTRAL"].poc.mean()
    assert good > bad  # FULL (low PSI, colorfulness near c*) beats NEUTRAL
