"""Config validation tests (PLAN §III.1/§II.2.1; PREREG §3; CLAUDE.md model lock)."""
from p19 import config


def test_validate_all_passes():
    """All YAML configs satisfy the PLAN/PREREG structural invariants (PREREG §3)."""
    rep = config.validate_all()
    assert rep["cells"] == {"n": 24, "n_fraction": 16}
    assert rep["prompts"]["splits"] == {"dev": 40, "heldout_seen": 8, "heldout_unseen": 10}
    assert rep["model"] == "Qwen/Qwen2.5-Coder-7B-Instruct"


def test_model_lock():
    """Subject model is locked to Qwen2.5-Coder-7B-Instruct, both stages (CLAUDE.md / ADR-001)."""
    mc = config.model_config()
    assert mc["model"]["name"] == "Qwen/Qwen2.5-Coder-7B-Instruct"
    assert mc["model"]["d_model"] == 3584 and mc["model"]["n_layers"] == 28
    assert mc["sampling"] == {
        "temperature": 0.7, "top_p": 0.9, "top_k": 40, "repetition_penalty": 1.05,
        "max_new_tokens": 4096, "seeds": [0, 1, 2, 3, 4],
    }


def test_config_hash_deterministic():
    """Canonical config hashing is order-insensitive and reproducible (PREREG §11)."""
    a = config.config_hash({"x": 1, "y": [1, 2]})
    b = config.config_hash({"y": [1, 2], "x": 1})
    assert a == b
    assert config.sampling_hash() == config.sampling_hash()


def test_seed_allocation():
    """Headline/LOO/AOI = 5 seeds; interaction = 3 seeds (PLAN §II.3)."""
    for c in config.cells_config()["cells"]:
        expected = 5 if c["tier"] in ("control", "loo", "aoi") else 3
        assert c["seeds"] == expected, c["id"]
