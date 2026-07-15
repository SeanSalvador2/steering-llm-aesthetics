"""Artifact manifest + hashing + run provenance (PLAN §VI.4; PREREG §11).

Records every artifact (HTML, PNG, DOM-JSON, activation shard, results file) with a SHA-256, its
producing config hash, engine + version, and the git commit, so a re-run with unchanged
config+seed reproduces identical CPU-artifact hashes. The manifest itself is committed; artifacts
live under artifacts/ (gitignored).

Git provenance is read directly from .git (a file read for provenance) — this module performs NO
git operations (no commit/push), consistent with the commit policy.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path

from . import REPO_ROOT
from .config import sampling_hash, config_hash, model_config


def sha256_file(path: str | Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_commit() -> str | None:
    """Best-effort current commit SHA read from .git (no subprocess, no git ops)."""
    git_dir = REPO_ROOT / ".git"
    try:
        head = (git_dir / "HEAD").read_text().strip()
        if head.startswith("ref:"):
            ref = head.split(" ", 1)[1].strip()
            ref_path = git_dir / ref
            if ref_path.exists():
                return ref_path.read_text().strip()
            # packed-refs fallback
            packed = git_dir / "packed-refs"
            if packed.exists():
                for line in packed.read_text().splitlines():
                    if line.endswith(ref):
                        return line.split(" ", 1)[0].strip()
            return None
        return head  # detached HEAD
    except Exception:
        return None


@dataclass
class ArtifactRecord:
    path: str
    kind: str                 # html|png|dom_json|activation|results|screenshot
    sha256: str
    config_hash: str
    engine: str
    engine_version: str
    ts: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))


class Manifest:
    """Append-only artifact registry (PLAN §VI.4)."""

    def __init__(self):
        self.records: list[ArtifactRecord] = []

    def register(self, path: str | Path, kind: str, config_hash_: str,
                 engine: str = "cpu", engine_version: str = "") -> ArtifactRecord:
        rec = ArtifactRecord(
            path=str(path), kind=kind, sha256=sha256_file(path),
            config_hash=config_hash_, engine=engine, engine_version=engine_version,
        )
        self.records.append(rec)
        return rec

    def to_jsonl(self, path: str | Path) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            for r in self.records:
                fh.write(json.dumps(asdict(r)) + "\n")

    @staticmethod
    def load_jsonl(path: str | Path) -> "Manifest":
        m = Manifest()
        for line in Path(path).read_text().splitlines():
            if line.strip():
                m.records.append(ArtifactRecord(**json.loads(line)))
        return m

    def hashed_paths(self) -> set[str]:
        """Paths already registered (for resume-skip; PLAN §VI.6 resume logic)."""
        return {r.path for r in self.records}


def run_manifest(engine: str = "cpu", engine_version: str = "", extra: dict | None = None) -> dict:
    """Provenance block for a run (engine/version/sampling/config hashes + git commit; PREREG §11)."""
    mc = model_config()
    man = {
        "model": mc["model"]["name"],
        "engine": engine,
        "engine_version": engine_version,
        "sampling_hash": sampling_hash(),
        "sampling": mc["sampling"],
        "git_commit": git_commit(),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if extra:
        man["config_hashes"] = {k: config_hash(v) for k, v in extra.items()}
    return man
