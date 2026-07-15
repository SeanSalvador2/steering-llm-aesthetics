"""Manifest + generation-plan tests (PLAN §VI.3/§VI.4, §III.1; PREREG §11)."""
from p19 import manifest
from p19 import generation_vllm as gv
from p19 import generation_hf as gh


def test_sha256_deterministic(tmp_path):
    """File hashing is deterministic (reproducible CPU artifacts; PLAN §VI.4)."""
    p = tmp_path / "a.txt"
    p.write_text("hello")
    assert manifest.sha256_file(p) == manifest.sha256_file(p)
    assert manifest.sha256_bytes(b"hello") == manifest.sha256_file(p)


def test_manifest_register_and_resume(tmp_path):
    """Registered artifacts round-trip and expose hashed paths for resume-skip (PLAN §VI.6)."""
    p = tmp_path / "art.html"
    p.write_text("<html></html>")
    m = manifest.Manifest()
    m.register(p, "html", config_hash_="abc", engine="cpu")
    jl = tmp_path / "manifest.jsonl"
    m.to_jsonl(jl)
    reloaded = manifest.Manifest.load_jsonl(jl)
    assert str(p) in reloaded.hashed_paths()
    assert reloaded.records[0].kind == "html"


def test_run_manifest_provenance():
    """Run manifest carries model, sampling hash, and (best-effort) git commit (PREREG §11)."""
    man = manifest.run_manifest(engine="vllm", engine_version="0.5.4")
    assert man["model"] == "Qwen/Qwen2.5-Coder-7B-Instruct"
    assert man["engine"] == "vllm" and man["sampling_hash"]


def test_generation_plan_counts():
    """The plan reproduces dev 4000 + held-out 630 = 4630 units (PLAN §III.1 / PREREG §3)."""
    s = gv.dry_run()
    assert s["dev"] == 4000 and s["heldout"] == 630 and s["total"] == 4630
    assert s["matches_expected"]


def test_gen_unit_ids_unique():
    """Every (cell, prompt, seed) unit has a unique gen_id (PLAN §II.3 atomic row)."""
    units = gv.build_generation_plan("all")
    assert len({u.gen_id for u in units}) == len(units) == 4630


def test_heldout_reduced_cell_set():
    """Held-out uses {4 controls @5 + 5 LOO @3}, LOO at 3 seeds (PLAN §III.1)."""
    held = [u for u in gv.build_generation_plan("heldout")]
    cells = {u.cell_id for u in held}
    assert cells == {"FULL", "NEUTRAL", "BEAUTY1", "NOSYS",
                     "LOO-C1", "LOO-C2", "LOO-C3", "LOO-C4", "LOO-C5"}
    loo_seeds = {u.seed for u in held if u.cell_id == "LOO-C1"}
    assert loo_seeds == {0, 1, 2}


def test_hf_dry_run_arms():
    """HF Stage-2 dry-run enumerates the S2.4 arms + k=5 random draws (PLAN S2.4)."""
    plan = gh.dry_run()
    assert plan["random_draws"] == 5
    assert plan["unsteered"] == plan["steered"] == 18 * 3
