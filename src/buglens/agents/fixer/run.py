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
    try:
        edits = _validated_edits(extract_json_object(response.text), original)
    except EditNotUniqueError:
        # deterministic local repair first (no API): near-miss fragments where
        # only one line differs between old/new — the copied context may be
        # imperfect but the intended edit line is usually exact
        recovered = _line_level_repair(extract_json_object(response.text), original)
        if recovered is not None:
            edits = recovered
        else:
            edits = _repair_round(inp, llm, prompt, original)
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


def _repair_round(inp: FixerInput, llm: BaseLLM, prompt: str, original: str) -> list[tuple[str, str]]:
    """One API repair round with the exact rejection reason, as last resort."""
    repair = (
        prompt
        + "\n\n你上一次的 edits 被拒绝：old 与文件原文不匹配或不在文件中唯一。\n"
        "请重新输出 JSON：old 必须逐字符从文件原文复制"
        "（注意注释闭合符、每行缩进与行尾空格），且在文件中恰好出现一次。"
    )
    response = llm.complete_text(repair)
    retry_path = inp.artifacts_dir / f"fixer_{inp.hypothesis.id}_raw_retry.txt"
    retry_path.write_text(response.text, encoding="utf-8")
    return _validated_edits(extract_json_object(response.text), original)


def _line_level_repair(
    parsed: dict[str, Any], original: str
) -> list[tuple[str, str]] | None:
    """When old and new differ in exactly one line, edit that line directly.

    Real-run pattern (EXP-07): the model copies a whole rule as context but
    drops a comment closer or drifts indentation — while the single changed
    line (the property value) is byte-exact and unique in the file.
    """
    raw_edits = parsed.get("edits")
    if not isinstance(raw_edits, list) or len(raw_edits) != 1:
        return None
    item = raw_edits[0]
    if not isinstance(item, dict):
        return None
    old, new = item.get("old"), item.get("new")
    if not isinstance(old, str) or not isinstance(new, str):
        return None
    old_lines, new_lines = old.splitlines(), new.splitlines()
    if len(old_lines) != len(new_lines):
        return None
    diff = [i for i in range(len(old_lines)) if old_lines[i] != new_lines[i]]
    if len(diff) != 1:
        return None
    k = diff[0]
    target = old_lines[k].rstrip()
    replacement = new_lines[k].rstrip()
    if not target or target == replacement:
        return None
    if original.count(target) != 1:
        return None
    return [(target, replacement)]


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
