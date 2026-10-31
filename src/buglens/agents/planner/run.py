"""planner.run: pure function over (report, candidates, console) -> hypotheses."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from buglens.agents.locator.run import CodeCandidate
from buglens.agents.planner.prompts import PROMPT_VERSION, build_prompt
from buglens.graph.state import Evidence, Hypothesis, VisualReport
from buglens.models.base import BaseLLM, VLMError, extract_json_object

_MAX_HYPOTHESES = 3
_CONSOLE_LIMIT = 1200
_LINE_RANGE_SUFFIX = re.compile(r":\d+-\d+$")


@dataclass(frozen=True)
class PlannerInput:
    report: VisualReport
    candidates: list[CodeCandidate]
    console_path: Path | None = None
    artifacts_dir: Path = Path("temp")
    failure_notes: list[str] = field(default_factory=list)
    tried_summary: str = ""


@dataclass(frozen=True)
class PlannerOutput:
    hypotheses: list[Hypothesis] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)


def run(inp: PlannerInput, llm: BaseLLM) -> PlannerOutput:
    """Ask the planner for ranked hypotheses; validate target files strictly."""
    candidates_block = "\n".join(
        f"- {c.display} | {c.snippet[:120]}" for c in inp.candidates
    )
    console = _read_console(inp.console_path)
    prompt = build_prompt(
        inp.report.symptom,
        inp.report.anomaly_region,
        candidates_block,
        console,
        failure_notes=inp.failure_notes,
        tried_summary=inp.tried_summary,
    )

    inp.artifacts_dir.mkdir(parents=True, exist_ok=True)
    response = llm.complete_text(prompt)
    raw_path = inp.artifacts_dir / "planner_raw.txt"
    raw_path.write_text(response.text, encoding="utf-8")
    try:
        parsed = extract_json_object(response.text)
    except VLMError:
        # one self-repair retry: models occasionally emit malformed JSON on
        # feedback rounds; ask again before giving the round up (EXP-07 real run)
        repair_prompt = (
            prompt
            + "\n\n注意：你上一次的输出无法解析为 JSON。请重新输出，且只输出规定格式的"
            " JSON 对象；字符串值内部不要出现未转义的双引号。"
        )
        response = llm.complete_text(repair_prompt)
        raw_path = inp.artifacts_dir / "planner_raw_retry.txt"
        raw_path.write_text(response.text, encoding="utf-8")
        parsed = extract_json_object(response.text)
    raw_hypotheses = parsed.get("hypotheses")
    if not isinstance(raw_hypotheses, list) or not raw_hypotheses:
        raise VLMError("planner returned no hypotheses")

    allowed_paths = {c.path for c in inp.candidates}
    hypotheses: list[Hypothesis] = []
    for item in raw_hypotheses[:_MAX_HYPOTHESES]:
        if not isinstance(item, dict):
            continue
        try:
            target = _match_allowed_path(str(item["target_path"]), allowed_paths)
            if target is None:
                continue  # planner hallucinated a file: drop, never trust
            hypothesis = Hypothesis(
                id=str(item["id"]),
                root_cause=str(item["root_cause"]),
                fix_plan=str(item["fix_plan"]),
                target_path=target,
                line_hint=_coerce_line_hint(item.get("line_hint")),
                expected_visual_change=str(item["expected_visual_change"]),
                confidence=float(item["confidence"]),
            )
        except (KeyError, TypeError, ValueError, ValidationError):
            continue
        hypotheses.append(hypothesis)

    if not hypotheses:
        raise VLMError("planner produced no valid hypothesis targeting the candidates")

    hypotheses = _diversify_by_file(hypotheses)
    evidence = [
        Evidence(
            kind="model_output",
            artifact=raw_path,
            claim=f"规划原始输出（{llm.name}, {response.total_tokens} tokens, "
            f"prompt={PROMPT_VERSION}, cached={response.cached}）",
            produced_by="planner",
        )
    ]
    return PlannerOutput(hypotheses=hypotheses, evidence=evidence)


def _diversify_by_file(hypotheses: list[Hypothesis]) -> list[Hypothesis]:
    """Keep the best hypothesis per target file (EXP-09: M0/bug3 blocker).

    Real-run finding: all three hypotheses targeted the same CSS file while
    the defect lived in a JSX inline style on the top-1 candidate file —
    one-file monoculture starves the retry rotation. Best-per-file by
    confidence, overall order by confidence, cap 3.
    """
    best_per_file: dict[str, Hypothesis] = {}
    for h in hypotheses:
        current = best_per_file.get(h.target_path)
        if current is None or h.confidence > current.confidence:
            best_per_file[h.target_path] = h
    return sorted(best_per_file.values(), key=lambda h: h.confidence, reverse=True)[:3]


def _normalize_path(path: str) -> str:
    """Models echo candidate display format ("src/x.css:41-48"); strip the range."""
    return _LINE_RANGE_SUFFIX.sub("", path.strip())


def _match_allowed_path(target: str, allowed: set[str]) -> str | None:
    """Canonicalize noisy model output to one of the candidate paths.

    Seen in the wild (EXP-07 real runs): "src/x.css:41-48", "src/x.css:41-48 |
    .rule-name". Accept prefix matches on any allowed path; reject everything
    else so hallucinated files never reach the fixer.
    """
    t = _normalize_path(target.strip())
    for path in allowed:
        if t == path:
            return path
    head = re.split(r"[|\s]", t, maxsplit=1)[0]
    head = _normalize_path(head)
    return head if head in allowed else None


def _coerce_line_hint(value: object) -> int | None:
    """line_hint arrives as int, null, or strings like "121-124" (v3 real run)."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    match = re.search(r"\d+", str(value))
    return int(match.group(0)) if match else None


def _read_console(console_path: Path | None) -> str:
    if console_path is None or not console_path.exists():
        return ""
    text = console_path.read_text(encoding="utf-8", errors="replace").strip()
    return text[-_CONSOLE_LIMIT:]
