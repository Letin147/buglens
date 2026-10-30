"""fixer.run: hypothesis -> validated patch on a worktree copy (originals untouched)."""

from __future__ import annotations

import difflib
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from buglens.agents.fixer.prompts import PROMPT_VERSION, build_prompt
from buglens.graph.state import Evidence, Hypothesis, Patch
from buglens.models.base import BaseLLM, VLMError, extract_json_object

_MAX_EDITS = 3
_EDIT_CONTEXT_LINES = 3


class EditNotUniqueError(VLMError):
    """The model's `old` fragment is absent or not unique — hypothesis rejected."""


@dataclass(frozen=True)
class FixerInput:
    hypothesis: Hypothesis
    repo_dir: Path
    worktree_dir: Path
    artifacts_dir: Path


@dataclass(frozen=True)
class FixerOutput:
    patch: Patch
    evidence: list[Evidence] = field(default_factory=list)


def run(inp: FixerInput, llm: BaseLLM) -> FixerOutput:
    """Generate, validate and apply a minimal patch on a worktree copy."""
    target_rel = inp.hypothesis.target_path
    original_path = inp.repo_dir / target_rel
    if not original_path.exists():
        raise VLMError(f"target file missing: {original_path}")
    original = original_path.read_text(encoding="utf-8")

    prompt = build_prompt(
        root_cause=inp.hypothesis.root_cause,
        fix_plan=inp.hypothesis.fix_plan,
        expected_visual_change=inp.hypothesis.expected_visual_change,
        target_path=target_rel,
        content=original,
    )

    inp.artifacts_dir.mkdir(parents=True, exist_ok=True)
    response = llm.complete_text(prompt)
    raw_path = inp.artifacts_dir / f"fixer_{inp.hypothesis.id}_raw.txt"
    raw_path.write_text(response.text, encoding="utf-8")

    edits = _validated_edits(extract_json_object(response.text), original)
    patched = original
    for old, new in edits:
        patched = patched.replace(old, new, 1)

    worktree_target = inp.worktree_dir / target_rel
    worktree_target.parent.mkdir(parents=True, exist_ok=True)
    worktree_target.write_text(patched, encoding="utf-8")

    diff_text = _unified_diff(original, patched, target_rel)
    diff_path = inp.artifacts_dir / f"patch_{inp.hypothesis.id}.diff"
    diff_path.write_text(diff_text, encoding="utf-8")

    patch = Patch(
        hypothesis_id=inp.hypothesis.id,
        target_path=target_rel,
        diff_path=diff_path,
        worktree_path=worktree_target,
        edit_count=len(edits),
    )
    evidence = [
        Evidence(
            kind="model_output",
            artifact=raw_path,
            claim=f"修复原始输出（{llm.name}, prompt={PROMPT_VERSION}, cached={response.cached}）",
            produced_by="fixer",
        ),
        Evidence(
            kind="diff",
            artifact=diff_path,
            claim=f"{target_rel} 最小补丁（{len(edits)} 处编辑，假设 {inp.hypothesis.id}）",
            produced_by="fixer",
        ),
    ]
    return FixerOutput(patch=patch, evidence=evidence)


def rollback(worktree_dir: Path) -> None:
    """Remove the worktree copy; the repository itself was never touched."""
    if worktree_dir.exists():
        shutil.rmtree(worktree_dir)


def _validated_edits(parsed: dict[str, Any], original: str) -> list[tuple[str, str]]:
    raw_edits = parsed.get("edits")
    if not isinstance(raw_edits, list) or not raw_edits:
        raise VLMError("fixer returned no edits")
    edits: list[tuple[str, str]] = []
    for item in raw_edits[:_MAX_EDITS]:
        if not isinstance(item, dict):
            continue
        old, new = item.get("old"), item.get("new")
        if not isinstance(old, str) or not old:
            continue
        count = original.count(old)
        if count != 1:
            raise EditNotUniqueError(
                f"edit fragment occurs {count}x (must be exactly 1): {old[:80]!r}"
            )
        if old != new:
            edits.append((old, new if isinstance(new, str) else ""))
    if not edits:
        raise VLMError("fixer produced no effective edit")
    return edits


def _unified_diff(original: str, patched: str, target_rel: str) -> str:
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        patched.splitlines(keepends=True),
        fromfile=f"a/{target_rel}",
        tofile=f"b/{target_rel}",
        n=_EDIT_CONTEXT_LINES,
    )
    return "".join(diff)
