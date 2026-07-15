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
    figures.reliability_bars(0.44, 0.88, 0.90)
    figures.stability_plot([20, 100, 200], [0.9, 0.995, 0.999])
    fig = figures.interaction_heatmap(np.zeros((5, 5)))
    assert fig.axes
