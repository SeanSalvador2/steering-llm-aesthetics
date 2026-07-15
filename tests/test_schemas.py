"""Results-schema tests (PLAN §VI.3)."""
import pyarrow as pa
import pytest

from p19 import schemas


def test_all_schemas_present_and_versioned():
    """The five results tables exist and carry a schema version (PLAN §VI.3)."""
    assert set(schemas.SCHEMAS) == {
        "generations", "metrics", "judgments", "activations_meta", "steering_runs"}
    for name, sch in schemas.SCHEMAS.items():
        assert sch.metadata[b"schema_version"] == schemas.SCHEMA_VERSION.encode()


def test_generation_row_roundtrip():
    """A GenerationRow serializes into the generations schema (PLAN §VI.3)."""
    row = schemas.GenerationRow(
        gen_id="abc", cell_id="FULL", prompt_id="L01", seed=0, system_variant="FULL",
        engine="vllm", engine_version="0.5.4", sampling_hash="deadbeef", prompt_tokens=500,
        output_tokens=3000, html_path="x.html", ts="2026-07-15T00:00:00")
    tbl = pa.Table.from_pylist([schemas.row_to_dict(row)], schema=schemas.GENERATIONS_SCHEMA)
    assert tbl.num_rows == 1 and tbl.column("cell_id")[0].as_py() == "FULL"


def test_validate_columns():
    """validate_columns accepts a superset and rejects missing columns (PLAN §VI.3)."""
    cols = schemas.METRICS_SCHEMA.names + ["extra_diag"]
    schemas.validate_columns("metrics", cols)  # ok
    with pytest.raises(ValueError):
        schemas.validate_columns("metrics", ["gen_id"])


def test_empty_table():
    assert schemas.empty_table("judgments").num_rows == 0
