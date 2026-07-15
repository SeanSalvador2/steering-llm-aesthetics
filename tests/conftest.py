"""Shared pytest fixtures (rendered fixtures, tiny Qwen2 stand-in, fixture metric table)."""
from __future__ import annotations

from pathlib import Path

import pytest

from p19 import REPO_ROOT

FIXTURE_NAMES = ["clean_landing", "slop_landing", "overflow_broken", "minimal_valid"]


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return REPO_ROOT / "fixtures"


@pytest.fixture(scope="session")
def rendered_fixtures(tmp_path_factory, fixtures_dir):
    """Render all fixtures once (hermetic, with axe). Returns {name: RenderResult}."""
    from p19.rendering import render_file

    out = tmp_path_factory.mktemp("renders")
    results = {}
    for name in FIXTURE_NAMES:
        results[name] = render_file(fixtures_dir / f"{name}.html", out_dir=out, run_axe=True)
    return results


@pytest.fixture(scope="session")
def fixture_metrics_df(rendered_fixtures):
    """Assemble the full metric vector + POC for the fixtures (the demo table)."""
    import pandas as pd
    from p19 import poc

    rows = []
    for name, r in rendered_fixtures.items():
        row = poc.assemble_row(r, r.screenshots["desktop"])
        row["gen_id"] = name
        row["cell_id"] = name
        rows.append(row)
    df = pd.DataFrame(rows)
    res = poc.compute_poc(df, psi_admit=True)
    df["poc"] = res["poc"].values
    df.attrs["poc_meta"] = res
    return df


@pytest.fixture(scope="session")
def tiny_qwen2():
    """A randomly-initialized Qwen2 stand-in (hidden=64, 3 layers) — NEVER the 7B (compute policy)."""
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    from transformers import Qwen2Config, Qwen2ForCausalLM

    torch.manual_seed(0)
    cfg = Qwen2Config(
        hidden_size=64, num_hidden_layers=3, num_attention_heads=4, num_key_value_heads=2,
        intermediate_size=128, vocab_size=200, max_position_embeddings=64,
        tie_word_embeddings=False,
    )
    model = Qwen2ForCausalLM(cfg).eval()
    return model
