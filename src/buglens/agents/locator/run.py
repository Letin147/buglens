"""locator.run: pure function from visual report + DOM clues to top-5 candidates."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from buglens.graph.state import Evidence, VisualReport
from buglens.repo.embedder import Embedder
from buglens.repo.indexer import RepoIndex
from buglens.repo.search import bm25_search, identifier_search, normalized_score, rrf_fuse

_CLASS_ATTR_RE = re.compile(r'class(?:Name)?="([^"]+)"')
_HTML_CLASS_RE = re.compile(r'class="([^"]+)"')


@dataclass(frozen=True)
class LocatorInput:
    report: VisualReport
    repo_dir: Path
    dom_path: Path | None = None
    overlays_path: Path | None = None
    embedder: Embedder | None = None


@dataclass(frozen=True)
class CodeCandidate:
    path: str
    line_start: int
    line_end: int
    score: float
    channels: list[str]
    snippet: str

    @property
    def display(self) -> str:
        return f"{self.path}:{self.line_start}-{self.line_end}"


@dataclass(frozen=True)
class LocatorOutput:
    candidates: list[CodeCandidate] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    query_terms: list[str] = field(default_factory=list)


def run(inp: LocatorInput, index: RepoIndex, index_vectors: list[list[float]] | None = None) -> LocatorOutput:
    """Fuse three recall channels into line-level top-5 candidates."""
    query_terms = _query_terms(inp)
    query_text = " ".join(query_terms)

    rankings: dict[str, list[int]] = {
        "identifier": identifier_search(index, query_terms),
        "bm25": bm25_search(index, query_text),
    }
    vectors = index_vectors if index_vectors is not None else index.vectors
    if inp.embedder is not None and vectors:
        rankings["vector"] = _vector_channel(index, vectors, query_text, inp.embedder)

    fused = rrf_fuse(rankings, top_k=5)
    candidates = [
        CodeCandidate(
            path=index.slices[idx].path,
            line_start=index.slices[idx].line_start,
            line_end=index.slices[idx].line_end,
            score=round(normalized_score(score), 3),
            channels=channels,
            snippet=index.slices[idx].text[:160],
        )
        for idx, score, channels in fused
    ]

    evidence: list[Evidence] = []
    if inp.dom_path is not None and inp.dom_path.exists():
        evidence.append(
            Evidence(kind="dom", artifact=inp.dom_path, claim="DOM 快照（类名线索来源）",
                     produced_by="reproducer")
        )
    if inp.overlays_path is not None and inp.overlays_path.exists():
        evidence.append(
            Evidence(kind="overlays", artifact=inp.overlays_path,
                     claim="覆盖层与被覆盖元素清单（遮挡线索来源）", produced_by="reproducer")
        )
    for candidate in candidates:
        artifact = inp.repo_dir / candidate.path
        evidence.append(
            Evidence(
                kind="code_span",
                artifact=artifact,
                claim=f"候选 {candidate.display}（channels={candidate.channels}, "
                f"score={candidate.score}）",
                produced_by="locator",
            )
        )
    return LocatorOutput(candidates=candidates, evidence=evidence, query_terms=query_terms)


def _vector_channel(
    index: RepoIndex,
    vectors: list[list[float]],
    query_text: str,
    embedder: Embedder,
) -> list[int]:
    from buglens.repo.search import vector_search

    return vector_search(index, query_text, embedder, vectors)


def _query_terms(inp: LocatorInput) -> list[str]:
    """Symptom text + class names from DOM + overlay/covered-element clues."""
    terms: list[str] = [inp.report.symptom]
    if inp.dom_path is not None and inp.dom_path.exists():
        dom = inp.dom_path.read_text(encoding="utf-8", errors="replace")
        for match in _HTML_CLASS_RE.finditer(dom):
            terms.append(match.group(1))
    if inp.overlays_path is not None and inp.overlays_path.exists():
        try:
            overlays: Any = json.loads(inp.overlays_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            overlays = []
        if isinstance(overlays, list):
            for entry in overlays:
                if isinstance(entry, dict):
                    terms.append(str(entry.get("cls", "")))
                    for covered in entry.get("covers", []):
                        if isinstance(covered, dict):
                            terms.append(str(covered.get("cls", "")))
                            terms.append(str(covered.get("text", "")))
    seen: set[str] = set()
    unique: list[str] = []
    for term in terms:
        if term and term not in seen:
            seen.add(term)
            unique.append(term)
    return unique
