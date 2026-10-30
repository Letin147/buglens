"""Repo indexing: TS/TSX tree-sitter slices + CSS rule slices (EXP-05)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import tree_sitter_typescript
from rank_bm25 import BM25Okapi
from tree_sitter import Language, Parser

from buglens.repo.embedder import Embedder

_TSX_LANGUAGE = Language(tree_sitter_typescript.language_tsx())

INDEX_DIR_NAME = ".buglens"

# Node types that mark a "unit of change" for localization purposes.
_SLICE_TYPES = {
    "function_declaration",
    "class_declaration",
    "export_statement",
    "variable_statement",
    "lexical_declaration",
    "expression_statement",
}

_CSS_RULE_RE = re.compile(
    r"(?P<selector>[^{}]+)\{(?P<body>[^{}]*)\}", re.MULTILINE
)

_SKIP_DIRS = {"node_modules", "dist", ".git", ".buglens"}

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_WORD_RE = re.compile(r"[A-Za-z0-9_]+")


def tokenize(text: str) -> list[str]:
    """Query/slice tokenizer: word tokens (lowercased) + CJK bigrams."""
    tokens = [t.lower() for t in _WORD_RE.findall(text) if len(t) > 1]
    cjk = "".join(_CJK_RE.findall(text))
    tokens.extend(a + b for a, b in zip(cjk, cjk[1:]))
    return tokens


@dataclass(frozen=True)
class CodeSlice:
    """One candidate unit: path is repo-relative, lines are 1-based inclusive."""

    path: str
    line_start: int
    line_end: int
    text: str

    @property
    def identifier_tokens(self) -> list[str]:
        return re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", self.text)

    @property
    def display(self) -> str:
        return f"{self.path}:{self.line_start}-{self.line_end}"


def iter_source_files(repo_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(repo_dir.rglob("*")):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in {".ts", ".tsx", ".css", ".js", ".jsx"}:
            files.append(path)
    return files


def slice_file(rel_path: str, source: str, suffix: str) -> list[CodeSlice]:
    """Slice one source file into localization units."""
    if suffix in {".ts", ".tsx", ".js", ".jsx"}:
        return _slice_code(rel_path, source)
    if suffix == ".css":
        return _slice_css(rel_path, source)
    return []


def _slice_code(rel_path: str, source: str) -> list[CodeSlice]:
    parser = Parser(_TSX_LANGUAGE)
    tree = parser.parse(source.encode("utf-8"))
    lines = source.splitlines()
    slices: list[CodeSlice] = []
    covered: list[tuple[int, int]] = []

    def walk(node: object) -> None:
        node_type = getattr(node, "type", "")
        if node_type in _SLICE_TYPES:
            start = getattr(node, "start_point")
            end = getattr(node, "end_point")
            start_line, end_line = start[0] + 1, end[0] + 1
            if not any(s <= start_line and end_line <= e for s, e in covered):
                covered.append((start_line, end_line))
                slices.append(
                    CodeSlice(
                        path=rel_path,
                        line_start=start_line,
                        line_end=end_line,
                        text="\n".join(lines[start_line - 1 : end_line]),
                    )
                )
            return  # do not descend into an accepted slice
        for child in getattr(node, "children", []):
            walk(child)

    walk(tree.root_node)
    if not slices:  # degenerate file: one slice per file
        slices.append(
            CodeSlice(path=rel_path, line_start=1, line_end=max(1, len(lines)), text=source)
        )
    return slices


def _slice_css(rel_path: str, source: str) -> list[CodeSlice]:
    lines = source.splitlines()
    slices: list[CodeSlice] = []
    for match in _CSS_RULE_RE.finditer(source):
        selector = " ".join(match.group("selector").split())
        if not selector or selector.startswith(("@", "}")):
            continue
        # selector span may swallow preceding whitespace/newlines; anchor on
        # the first visible character so line numbers are exact
        span_start = match.start("selector")
        while span_start < len(source) and source[span_start].isspace():
            span_start += 1
        start_line = source.count("\n", 0, span_start) + 1
        end_line = source.count("\n", 0, match.end()) + 1
        slices.append(
            CodeSlice(
                path=rel_path,
                line_start=start_line,
                line_end=end_line,
                text=f"{selector} {match.group('body')}".strip(),
            )
        )
    if not slices:
        slices.append(
            CodeSlice(path=rel_path, line_start=1, line_end=max(1, len(lines)), text=source)
        )
    return slices


@dataclass
class RepoIndex:
    """Everything the locator needs: slices + BM25 + optional vectors."""

    repo_dir: Path
    slices: list[CodeSlice]
    bm25: BM25Okapi | None
    vectors: list[list[float]] | None
    embedder_name: str | None

    def slice_text(self, index: int) -> str:
        return self.slices[index].text[:2000]


def build_index(
    repo_dir: Path,
    embedder: Embedder | None = None,
    progress: Callable[[str], None] = print,
) -> RepoIndex:
    """Slice, index and persist a repository under <repo>/.buglens/."""
    files = iter_source_files(repo_dir)
    progress(f"indexing {len(files)} source files in {repo_dir}")
    slices: list[CodeSlice] = []
    for path in files:
        rel = path.relative_to(repo_dir).as_posix()
        slices.extend(slice_file(rel, path.read_text(encoding="utf-8"), path.suffix))
    progress(f"built {len(slices)} slices")

    corpus = [tokenize(s.text) for s in slices]
    bm25 = BM25Okapi(corpus) if corpus else None

    vectors: list[list[float]] | None = None
    embedder_name: str | None = None
    if embedder is not None and slices:
        progress(f"embedding {len(slices)} slices with {embedder.name} ...")
        vectors = embedder.encode([s.text[:2000] for s in slices])
        embedder_name = embedder.name

    index = RepoIndex(
        repo_dir=repo_dir, slices=slices, bm25=bm25, vectors=vectors, embedder_name=embedder_name
    )
    _save(index)
    progress(f"index saved under {repo_dir / INDEX_DIR_NAME}")
    return index


def load_index(repo_dir: Path) -> RepoIndex:
    """Load a persisted index (vectors only if the embedder is available again)."""
    index_dir = repo_dir / INDEX_DIR_NAME
    meta = json.loads((index_dir / "meta.json").read_text(encoding="utf-8"))
    slices = [
        CodeSlice(
            path=item["path"],
            line_start=item["line_start"],
            line_end=item["line_end"],
            text=item["text"],
        )
        for item in json.loads((index_dir / "slices.json").read_text(encoding="utf-8"))
    ]
    corpus = [tokenize(s.text) for s in slices]
    return RepoIndex(
        repo_dir=repo_dir,
        slices=slices,
        bm25=BM25Okapi(corpus) if corpus else None,
        vectors=None,
        embedder_name=meta.get("embedder"),
    )


def _save(index: RepoIndex) -> None:
    index_dir = index.repo_dir / INDEX_DIR_NAME
    index_dir.mkdir(parents=True, exist_ok=True)
    payload = [
        {"path": s.path, "line_start": s.line_start, "line_end": s.line_end, "text": s.text}
        for s in index.slices
    ]
    (index_dir / "slices.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )
    meta = {"slice_count": len(index.slices), "embedder": index.embedder_name}
    (index_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
