"""visual_analyst.run: pure function over (screenshot, overlays) -> (report, evidence)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from buglens.agents.visual_analyst.prompts import PROMPT_VERSION, build_prompt
from buglens.graph.state import Evidence, VisualReport
from buglens.models.base import BaseVLM, VLMError, extract_json_object

NO_OVERLAYS_NOTE = "（本页未检测到 fixed/sticky 覆盖元素）"


@dataclass(frozen=True)
class VisualAnalystInput:
    screenshot: Path
    overlays: Path | None
    artifacts_dir: Path


@dataclass(frozen=True)
class VisualAnalystOutput:
    report: VisualReport
    evidence: list[Evidence] = field(default_factory=list)


def run(inp: VisualAnalystInput, vlm: BaseVLM) -> VisualAnalystOutput:
    """Analyze one reproduction screenshot; raises VLMError on unusable output."""
    dom_facts = _format_overlays(inp.overlays)
    prompt = build_prompt(dom_facts)
    response = vlm.complete_vision(inp.screenshot, prompt)

    inp.artifacts_dir.mkdir(parents=True, exist_ok=True)
    raw_path = inp.artifacts_dir / "visual_analyst_raw.txt"
    raw_path.write_text(response.text, encoding="utf-8")

    parsed = extract_json_object(response.text)
    try:
        report = VisualReport(
            anomaly_region=parsed["anomaly_region"],
            symptom=parsed["symptom"],
            severity=parsed["severity"],
            confidence=parsed["confidence"],
            prompt_version=PROMPT_VERSION,
            model=vlm.name,
        )
    except (KeyError, TypeError, ValidationError) as exc:
        raise VLMError(f"visual report failed schema validation: {exc}") from exc

    evidence = [
        Evidence(
            kind="screenshot",
            artifact=inp.screenshot,
            claim="待分析的复现截图",
            produced_by="visual_analyst",
        ),
        Evidence(
            kind="model_output",
            artifact=raw_path,
            claim=f"视觉分析原始输出（{vlm.name}, {response.total_tokens} tokens, "
            f"cached={response.cached}）",
            produced_by="visual_analyst",
        ),
    ]
    if inp.overlays is not None and inp.overlays.exists():
        evidence.append(
            Evidence(
                kind="overlays",
                artifact=inp.overlays,
                claim="页面 fixed/sticky 覆盖元素清单（提示词 DOM 事实来源）",
                produced_by="reproducer",
            )
        )
    return VisualAnalystOutput(report=report, evidence=evidence)


def _format_overlays(overlays_path: Path | None) -> str:
    if overlays_path is None or not overlays_path.exists():
        return NO_OVERLAYS_NOTE
    entries: list[dict[str, Any]]
    try:
        entries = json.loads(overlays_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return NO_OVERLAYS_NOTE
    if not entries:
        return NO_OVERLAYS_NOTE
    lines = []
    for entry in entries:
        rect = entry.get("rect", [0, 0, 0, 0])
        lines.append(
            f"- <{entry.get('tag', '?')}> class={entry.get('cls', '')!r} "
            f"矩形 [x={rect[0]}, y={rect[1]}, w={rect[2]}, h={rect[3]}] "
            f"z-index={entry.get('zIndex', 'auto')}"
        )
    return "\n".join(lines)
