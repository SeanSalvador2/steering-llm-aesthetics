"""Figure-builder smoke tests (PLAN §V.1). Each returns a matplotlib Figure headless (Agg)."""
import numpy as np

from p19 import figures


def test_forest_plot():
    fig = figures.forest_plot([{"label": "LOO-C5", "delta": -0.6, "lo": -0.9, "hi": -0.3}])
    assert fig.axes


def test_localization_plot():
    fig = figures.localization_plot([11, 13, 15], [0.8, 0.9, 0.85], [0.2, 0.3, 0.25],
                                    [0.3, 0.5, 0.4], band=[13, 15])
    assert fig.axes


def test_dose_response_and_heldout():
    figures.dose_response([0.1, 0.3, 0.5], [0.1, 0.4, -0.1], [0.95, 0.92, 0.7])
    fig = figures.heldout_bars({"unsteered": 0.0, "steered": 0.3, "random": 0.05, "FULL": 0.5},
                               reproduced_pct=60)
    assert fig.axes


def test_reliability_and_stability_and_heatmap():
    figures.reliability_bars(0.44, 0.88, 0.90, alpha_ci=(0.30, 0.58), ac1_ci=(0.80, 0.94))
    figures.stability_plot([20, 100, 200], [0.9, 0.995, 0.999])
    fig = figures.interaction_heatmap(np.zeros((5, 5)), star_mask=np.eye(5, dtype=bool))
    assert fig.axes


def test_new_figures_f2_f4_f6_f9_f12():
    """F2 (nec×suff), F4 (metric corr), F6 (α×layer), F9 (correspondence), F12 (anti-steerable)."""
    figures.necessity_sufficiency_scatter(
        [{"label": "C5", "suff": 0.5, "nec": 0.85, "suff_lo": 0.4, "suff_hi": 0.6,
          "nec_lo": 0.7, "nec_hi": 1.0},
         {"label": "C4", "suff": 0.02, "nec": 0.03}])
    figures.metric_correlation_matrix(np.eye(6), [f"m{i}" for i in range(6)], family_bounds=[3])
    figures.steering_heatmap([11, 15, 20], [0.1, 0.3, 0.7],
                             np.array([[0.1, 0.3, 0.1], [0.2, 0.6, 0.2], [-0.1, 0.0, -0.3]]),
                             guardrail_mask=np.array([[0, 0, 0], [0, 0, 0], [1, 1, 1]], bool),
                             star=(1, 1))
    figures.correspondence_figure(np.eye(6), [f"v{i}" for i in range(6)], np.eye(5),
                                  [f"s{i}" for i in range(5)], [f"a{i}" for i in range(5)])
    fig = figures.anti_steerable_bars(["landing", "settings", "admin-table"], [0.05, 0.4, 0.6],
                                      [True, False, False])
    assert fig.axes
