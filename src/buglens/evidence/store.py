"""Content-addressed evidence store: every claim points at immutable bytes.

Design (02-MANUAL §9):
- ids are `ev-{sha8}-{kind}{ext}`; identical content dedups to one artifact;
- the manifest (manifest.jsonl) is append-only — corrections add rows, never
  rewrite history;
- files are written once and never mutated afterwards.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from buglens.graph.state import Evidence, EvidenceKind

_EXT_BY_KIND: dict[str, str] = {
    "screenshot": ".png",
    "render_diff": ".png",
    "dom": ".html",
    "overlays": ".json",
    "code_span": ".txt",
    "diff": ".diff",
    "test_run": ".txt",
    "model_output": ".txt",
}


class EvidenceGapError(RuntimeError):
    """An assertion lacks the evidence required to render it (hard constraint)."""


class EvidenceStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest = self.root / "manifest.jsonl"

    def put(
        self,
        kind: EvidenceKind,
        data: bytes,
        claim: str,
        produced_by: str,
    ) -> Evidence:
        """Store bytes content-addressed; identical content dedups silently."""
        sha8 = hashlib.sha256(data).hexdigest()[:8]
        name = f"ev-{sha8}-{kind}{_EXT_BY_KIND.get(kind, '.bin')}"
        path = self.root / name
        if not path.exists():
            path.write_bytes(data)
        self._append_manifest(name, kind, claim, produced_by, dedup=path.exists())
        return Evidence(kind=kind, artifact=path, claim=claim, produced_by=produced_by)

    def register(self, source: Path, kind: EvidenceKind, claim: str, produced_by: str) -> Evidence:
        """Copy an existing artifact into the store and return its evidence."""
        return self.put(kind, source.read_bytes(), claim, produced_by)

    def _append_manifest(
        self, name: str, kind: EvidenceKind, claim: str, produced_by: str, dedup: bool
    ) -> None:
        row = {
            "id": name,
            "kind": kind,
            "claim": claim,
            "produced_by": produced_by,
            "dedup": dedup,
        }
        with self.manifest.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
