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
    prompt = build_prompt(inp.report.symptom, inp.report.anomaly_region, candidates_block, console)

    inp.artifacts_dir.mkdir(parents=True, exist_ok=True)
    response = llm.complete_text(prompt)
    raw_path = inp.artifacts_dir / "planner_raw.txt"
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
            target = _normalize_path(str(item["target_path"]))
            hypothesis = Hypothesis(
                id=str(item["id"]),
                root_cause=str(item["root_cause"]),
                fix_plan=str(item["fix_plan"]),
                target_path=target,
                line_hint=item.get("line_hint"),
                expected_visual_change=str(item["expected_visual_change"]),
                confidence=float(item["confidence"]),
            )
        except (KeyError, TypeError, ValueError, ValidationError):
            continue
        if hypothesis.target_path not in allowed_paths:
            continue  # planner hallucinated a file: drop, never trust
        hypotheses.append(hypothesis)

    if not hypotheses:
        raise VLMError("planner produced no valid hypothesis targeting the candidates")

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


def _normalize_path(path: str) -> str:
    """Models echo candidate display format ("src/x.css:41-48"); strip the range."""
    return _LINE_RANGE_SUFFIX.sub("", path.strip())


def _read_console(console_path: Path | None) -> str:
    if console_path is None or not console_path.exists():
        return ""
    text = console_path.read_text(encoding="utf-8", errors="replace").strip()
    return text[-_CONSOLE_LIMIT:]
