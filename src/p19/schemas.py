"""Versioned result schemas (PLAN §VI.3).

Each results table has a pyarrow schema (for Parquet round-trips) and a lightweight
dataclass for row construction. `SCHEMA_VERSION` is stamped into every table's metadata
so a later reader can detect drift. Validation helpers assert a DataFrame's columns match.

Tables (PLAN §VI.3): generations, metrics, judgments, activations_meta, steering_runs.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

import pyarrow as pa

SCHEMA_VERSION = "1"


# --------------------------------------------------------------------------- generations
GENERATIONS_SCHEMA = pa.schema(
    [
        ("gen_id", pa.string()),
        ("cell_id", pa.string()),
        ("prompt_id", pa.string()),
        ("seed", pa.int32()),
        ("system_variant", pa.string()),  # FULL|NEUTRAL|BEAUTY1|NOSYS|LOO-Ci|AOI-Ci|F-...
        ("engine", pa.string()),  # vllm|hf
        ("engine_version", pa.string()),
        ("sampling_hash", pa.string()),
        ("prompt_tokens", pa.int32()),
        ("output_tokens", pa.int32()),
        ("html_path", pa.string()),
        ("ts", pa.string()),
    ],
    metadata={b"schema_version": SCHEMA_VERSION.encode()},
)


@dataclass
class GenerationRow:
    gen_id: str
    cell_id: str
    prompt_id: str
    seed: int
    system_variant: str
    engine: str
    engine_version: str
    sampling_hash: str
    prompt_tokens: int
    output_tokens: int
    html_path: str
    ts: str


# --------------------------------------------------------------------------- metrics
# axe_violations_by_impact is stored as a JSON string column (stable, engine-agnostic).
METRICS_SCHEMA = pa.schema(
    [
        ("gen_id", pa.string()),
        ("render_success", pa.int8()),
        ("hermetic", pa.int8()),
        ("n_external_requests", pa.int32()),
        ("console_errors", pa.int32()),
        ("n_overflow", pa.int32()),
        ("n_overlap", pa.int32()),
        ("axe_violations_by_impact", pa.string()),  # json: {"critical":.., "serious":.., ...}
        ("axe_total", pa.int32()),
        ("contrast_frac_below_4_5", pa.float64()),
        ("contrast_min", pa.float64()),
        ("contrast_median", pa.float64()),
        ("ngo_balance", pa.float64()),
        ("ngo_equilibrium", pa.float64()),
        ("ngo_symmetry", pa.float64()),
        ("align_regularity", pa.float64()),
        ("gap_entropy", pa.float64()),
        ("whitespace_ratio", pa.float64()),
        ("density", pa.float64()),
        ("n_font_sizes", pa.int32()),
        ("n_font_families", pa.int32()),
        ("type_scale_adherence", pa.float64()),
        ("colorfulness", pa.float64()),
        ("n_dominant_colors", pa.int32()),
        ("figure_ground", pa.float64()),
        ("visual_complexity", pa.float64()),
        ("psi", pa.float64()),
        ("psi_hue", pa.float64()),
        ("psi_gradient", pa.float64()),
        ("psi_inter", pa.float64()),
        ("psi_centered", pa.float64()),
        ("uiclip", pa.float64()),  # nullable; -1.0 sentinel when not computed
        ("clip_relevance", pa.float64()),  # nullable; -1.0 sentinel
        ("poc", pa.float64()),  # nullable; filled by a POC pass over the population
    ],
    metadata={b"schema_version": SCHEMA_VERSION.encode()},
)


# --------------------------------------------------------------------------- judgments
JUDGMENTS_SCHEMA = pa.schema(
    [
        ("judgment_id", pa.string()),
        ("edge", pa.string()),
        ("cellA", pa.string()),
        ("cellB", pa.string()),
        ("prompt_id", pa.string()),
        ("seedA", pa.int32()),
        ("seedB", pa.int32()),
        ("winner", pa.string()),  # A|B|tie (consistency-resolved)
        ("confidence", pa.float64()),
        ("per_criterion", pa.string()),  # json
        ("rationale", pa.string()),
        ("consistent", pa.int8()),
        ("raw_ab_winner", pa.string()),
        ("raw_ba_winner", pa.string()),
        ("judge_model", pa.string()),
        ("ts", pa.string()),
    ],
    metadata={b"schema_version": SCHEMA_VERSION.encode()},
)


# --------------------------------------------------------------------------- activations_meta
ACTIVATIONS_META_SCHEMA = pa.schema(
    [
        ("example_id", pa.string()),
        ("cell_id", pa.string()),
        ("prompt_id", pa.string()),
        ("seed", pa.int32()),
        ("layer", pa.int32()),
        ("variant", pa.string()),  # mean_response|last_prompt_token|first_k
        ("mean_vec_path", pa.string()),
        ("norm", pa.float64()),
    ],
    metadata={b"schema_version": SCHEMA_VERSION.encode()},
)


# --------------------------------------------------------------------------- steering_runs
STEERING_RUNS_SCHEMA = pa.schema(
    [
        ("run_id", pa.string()),
        ("stage", pa.string()),  # S2.3|S2.4|S2.5|...
        ("layer", pa.int32()),
        ("rho", pa.float64()),
        ("abs_mult", pa.float64()),
        ("variant", pa.string()),
        ("arm", pa.string()),  # unsteered|steered|random|full_ref
        ("prompt_id", pa.string()),
        ("seed", pa.int32()),
        ("kl", pa.float64()),
        ("render_success", pa.int8()),
        ("poc", pa.float64()),
        ("html_path", pa.string()),
    ],
    metadata={b"schema_version": SCHEMA_VERSION.encode()},
)


SCHEMAS: dict[str, pa.Schema] = {
    "generations": GENERATIONS_SCHEMA,
    "metrics": METRICS_SCHEMA,
    "judgments": JUDGMENTS_SCHEMA,
    "activations_meta": ACTIVATIONS_META_SCHEMA,
    "steering_runs": STEERING_RUNS_SCHEMA,
}


def empty_table(name: str) -> pa.Table:
    """Return an empty pyarrow Table with the named schema."""
    return SCHEMAS[name].empty_table()


def validate_columns(name: str, columns) -> None:
    """Assert `columns` is a superset of the required schema fields (order-insensitive).

    Raises ValueError listing any missing columns. Extra columns are allowed (diagnostics).
    """
    required = set(SCHEMAS[name].names)
    present = set(columns)
    missing = required - present
    if missing:
        raise ValueError(f"table '{name}' missing required columns: {sorted(missing)}")


def row_to_dict(row: Any) -> dict:
    """Dataclass row -> plain dict (for DataFrame construction)."""
    return asdict(row)
