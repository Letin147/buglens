"""EXP-06 tests: planner parsing/validation and fixer apply/rollback (no network)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from buglens.agents.fixer import EditNotUniqueError, FixerInput, rollback
from buglens.agents.fixer import run as fixer_run
from buglens.agents.locator.run import CodeCandidate
from buglens.agents.planner import PlannerInput
from buglens.agents.planner import run as planner_run
from buglens.graph.state import Hypothesis, VisualReport
from buglens.models.base import BaseLLM, VLMError, VLMResponse

GOLDEN1 = Path(__file__).resolve().parents[1] / "examples" / "golden-1"

PLANNER_ANSWER = json.dumps(
    {
        "hypotheses": [
            {
                "id": "H1",
                "root_cause": "内容区顶部留白不足，按钮进入导航栏覆盖范围",
                "fix_plan": "将 .bug1-page 的 padding-top 从 12px 增加到 84px",
                "target_path": "src/index.css",
                "line_hint": 45,
                "expected_visual_change": "提交订单按钮完整出现在导航栏下方",
                "confidence": 0.9,
            },
            {
                "id": "H2",
                "root_cause": "幻觉文件（应被丢弃）",
                "fix_plan": "x",
                "target_path": "src/not/a/file.css",
                "expected_visual_change": "x",
                "confidence": 0.5,
            },
        ]
    },
    ensure_ascii=False,
)

FIXER_ANSWER = json.dumps(
    {"edits": [{"old": "padding-top: 12px;", "new": "padding-top: 84px;"}]},
    ensure_ascii=False,
)


class FakeLLM(BaseLLM):
    name = "fake-llm"

    def __init__(self, answer: str) -> None:
        self.answer = answer

    def complete_text(self, prompt: str) -> VLMResponse:
        return VLMResponse(text=self.answer, elapsed_s=0.01, total_tokens=7)


def _report() -> VisualReport:
    return VisualReport(
        anomaly_region=[345, 37, 590, 48],
        symptom='导航栏遮挡了"提交订单"按钮，导致按钮内容部分被截断',
        severity="high",
        confidence=1.0,
        prompt_version="v4-covered-20261029",
        model="fake",
    )


def _candidates() -> list[CodeCandidate]:
    return [
        CodeCandidate(
            path="src/index.css",
            line_start=41,
            line_end=48,
            score=0.97,
            channels=["bm25", "identifier", "vector"],
            snippet=".bug1-page { padding-top: 12px; ...",
        )
    ]


def test_planner_parses_and_drops_hallucinated_paths(tmp_path: Path) -> None:
    out = planner_run(
        PlannerInput(report=_report(), candidates=_candidates(), artifacts_dir=tmp_path),
        FakeLLM(PLANNER_ANSWER),
    )
    assert len(out.hypotheses) == 1
    assert out.hypotheses[0].id == "H1"
    assert out.hypotheses[0].target_path == "src/index.css"
    assert (tmp_path / "planner_raw.txt").exists()
    assert out.evidence[0].kind == "model_output"


def test_planner_rejects_when_nothing_valid(tmp_path: Path) -> None:
    answer = json.dumps(
        {
            "hypotheses": [
                {
                    "id": "H1",
                    "root_cause": "x",
                    "fix_plan": "x",
                    "target_path": "elsewhere.css",
                    "expected_visual_change": "x",
                    "confidence": 0.5,
                }
            ]
        }
    )
    with pytest.raises(VLMError):
        planner_run(
            PlannerInput(report=_report(), candidates=_candidates(), artifacts_dir=tmp_path),
            FakeLLM(answer),
        )


def test_fixer_applies_patch_and_original_stays_untouched(tmp_path: Path) -> None:
    css = GOLDEN1 / "src" / "index.css"
    before = css.read_text(encoding="utf-8")
    hypothesis = Hypothesis(
        id="H1",
        root_cause="内容区顶部留白不足",
        fix_plan="增加 .bug1-page 的 padding-top",
        target_path="src/index.css",
        line_hint=45,
        expected_visual_change="按钮完整可见",
        confidence=0.9,
    )
    out = fixer_run(
        FixerInput(
            hypothesis=hypothesis,
            repo_dir=GOLDEN1,
            worktree_dir=tmp_path / "worktree",
            artifacts_dir=tmp_path,
        ),
        FakeLLM(FIXER_ANSWER),
    )

    assert css.read_text(encoding="utf-8") == before, "original repo file must not change"
    patched = out.patch.worktree_path.read_text(encoding="utf-8")
    assert "padding-top: 84px;" in patched and "padding-top: 12px;" not in patched
    diff_text = out.patch.diff_path.read_text(encoding="utf-8")
    assert "-  padding-top: 12px;" in diff_text
    assert "+  padding-top: 84px;" in diff_text
    assert out.patch.edit_count == 1

    rollback(tmp_path / "worktree")
    assert not (tmp_path / "worktree").exists()
    assert css.read_text(encoding="utf-8") == before


def test_fixer_rejects_non_unique_fragment(tmp_path: Path) -> None:
    hypothesis = Hypothesis(
        id="H9",
        root_cause="x",
        fix_plan="x",
        target_path="src/index.css",
        expected_visual_change="x",
        confidence=0.1,
    )
    answer = json.dumps({"edits": [{"old": "padding", "new": "margin"}]})
    with pytest.raises(EditNotUniqueError):
        fixer_run(
            FixerInput(
                hypothesis=hypothesis,
                repo_dir=GOLDEN1,
                worktree_dir=tmp_path / "worktree",
                artifacts_dir=tmp_path,
            ),
            FakeLLM(answer),
        )
