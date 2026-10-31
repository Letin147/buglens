"""EXP-08 tests: evidence store, critic, reporter, and graph end-to-end report.

Self-contained on purpose: a cross-file fixture import (test_exp07_loop)
sorted differently across ruff versions and broke CI (PR#4 lesson).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from buglens.agents.critic import CriticInput
from buglens.agents.critic import run as critic_run
from buglens.agents.locator.run import CodeCandidate
from buglens.agents.reporter import ReporterInput
from buglens.agents.reporter import run as reporter_run
from buglens.agents.verifier.run import Verdict, VerifyInput, VerifyOutput
from buglens.evidence.store import EvidenceGapError, EvidenceStore
from buglens.graph.builder import PipelineDeps, build_pipeline
from buglens.graph.state import Evidence, Hypothesis, Patch, VisualReport
from buglens.models.base import BaseLLM, VLMResponse

PLANNER_OK = json.dumps(
    {
        "hypotheses": [
            {
                "id": "H1",
                "root_cause": "中间卡片 marginTop 过大",
                "fix_plan": "把 Bug3.tsx 内联 marginTop: 56 改为 0",
                "target_path": "src/bugs/Bug3.tsx",
                "line_hint": 15,
                "expected_visual_change": "三卡顶部对齐",
                "confidence": 0.9,
            }
        ]
    },
    ensure_ascii=False,
)

FIXER_OK = json.dumps(
    {"edits": [{"old": "marginTop: 56", "new": "marginTop: 0"}]}, ensure_ascii=False
)


class StubLLM(BaseLLM):
    """Routes by prompt role: planner prompts get a plan, fixer prompts get edits."""

    name = "stub"

    def complete_text(self, prompt: str) -> VLMResponse:
        answer = PLANNER_OK if "修复规划师" in prompt else FIXER_OK
        return VLMResponse(text=answer, elapsed_s=0.01, total_tokens=5)


def _report() -> VisualReport:
    return VisualReport(
        anomaly_region=[420, 170, 590, 470],
        symptom="专业版卡片垂直位置低于基础版与企业版",
        severity="mid",
        confidence=0.8,
        prompt_version="test",
        model="stub",
    )


def _candidates() -> list[CodeCandidate]:
    return [
        CodeCandidate(
            path="src/bugs/Bug3.tsx",
            line_start=1,
            line_end=38,
            score=0.98,
            channels=["bm25", "identifier", "vector"],
            snippet="export default function Bug3() ...",
        )
    ]


def test_store_content_addressing_and_manifest(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path / "ev")
    e1 = store.put("model_output", b"hello", "断言A", "tester")
    e2 = store.put("model_output", b"hello", "断言A（重复内容）", "tester")
    assert e1.artifact == e2.artifact, "identical bytes must dedup to one artifact"
    assert len(list((tmp_path / "ev").glob("ev-*.txt"))) == 1
    e3 = store.put("model_output", b"different", "断言B", "tester")
    assert e3.artifact != e1.artifact
    rows = (tmp_path / "ev" / "manifest.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 3
    assert json.loads(rows[0])["id"] == e1.artifact.name


def _evidence_kinds_ok(tmp_path: Path) -> list[Evidence]:
    paths = {
        "screenshot": tmp_path / "before.png",
        "render_diff": tmp_path / "after.png",
        "diff": tmp_path / "evidence.diff",  # distinct from _patch()'s p.diff
    }
    paths["screenshot"].write_bytes(b"png")
    paths["render_diff"].write_bytes(b"png")
    paths["diff"].write_text("--- a/x\n+++ b/x\n", encoding="utf-8")
    return [
        Evidence(kind=kind, artifact=path, claim=f"{kind} 证据", produced_by="tester")
        for kind, path in paths.items()
    ]


def _patch(tmp_path: Path) -> Patch:
    diff = tmp_path / "p.diff"
    diff.write_text("--- a/src/x.css\n+++ b/src/x.css\n@@\n-a\n+b\n", encoding="utf-8")
    return Patch(
        hypothesis_id="H1",
        target_path="src/x.css",
        diff_path=diff,
        worktree_path=tmp_path / "wt" / "src" / "x.css",
        edit_count=1,
    )


def _hypothesis() -> Hypothesis:
    return Hypothesis(
        id="H1",
        root_cause="root",
        fix_plan="plan",
        target_path="src/x.css",
        expected_visual_change="change",
        confidence=0.9,
    )


def _verdict(passed: bool = True) -> Verdict:
    return Verdict(
        passed=passed,
        channels={"pixel": "pass（x%）", "layout": "pass", "dom": "pass", "tests": "n-a"},
    )


def test_critic_approves_and_rejects(tmp_path: Path) -> None:
    ok = critic_run(
        CriticInput(patch=_patch(tmp_path), verdict=_verdict(), evidence=_evidence_kinds_ok(tmp_path))
    )
    assert ok.approved and not ok.reasons

    bad_verdict = Verdict(passed=False, channels={"pixel": "fail（0%）"})
    rejected = critic_run(
        CriticInput(patch=_patch(tmp_path), verdict=bad_verdict, evidence=[])
    )
    assert not rejected.approved
    assert any("未通过" in r for r in rejected.reasons)
    assert any("证据链为空" in r for r in rejected.reasons)

    stray = tmp_path / "stray.diff"
    stray.write_text("--- a/src/x.css\n+++ b/src/x.css\n--- a/src/y.ts\n+++ b/src/y.ts\n",
                     encoding="utf-8")
    stray_patch = Patch(
        hypothesis_id="H1",
        target_path="src/x.css",
        diff_path=stray,
        worktree_path=tmp_path / "wt" / "src" / "x.css",
        edit_count=1,
    )
    multi = critic_run(
        CriticInput(patch=stray_patch, verdict=_verdict(), evidence=_evidence_kinds_ok(tmp_path))
    )
    assert not multi.approved and any("目标之外" in r for r in multi.reasons)


def test_reporter_renders_and_enforces_evidence(tmp_path: Path) -> None:
    out = tmp_path / "PR_REPORT.md"
    path = reporter_run(
        ReporterInput(
            report=_report(),
            hypothesis=_hypothesis(),
            patch=_patch(tmp_path),
            verdict=_verdict(),
            evidence=_evidence_kinds_ok(tmp_path),
            before_png=tmp_path / "before.png",
            after_png=tmp_path / "after.png",
            out_path=out,
        )
    )
    text = path.read_text(encoding="utf-8")
    assert "仅供人工审阅，未自动合并" in text
    assert "证据链" in text and "before.png" in text
    assert "oracle 判定" in text

    incomplete = [e for e in _evidence_kinds_ok(tmp_path) if e.kind != "render_diff"]
    with pytest.raises(EvidenceGapError):
        reporter_run(
            ReporterInput(
                report=_report(),
                hypothesis=_hypothesis(),
                patch=_patch(tmp_path),
                verdict=_verdict(),
                evidence=incomplete,
                before_png=tmp_path / "before.png",
                after_png=tmp_path / "after.png",
                out_path=out,
            )
        )


def test_graph_end_to_end_produces_report(tmp_path: Path) -> None:
    golden = Path(__file__).resolve().parents[1] / "examples" / "golden-1"
    before = tmp_path / "before.png"
    before.write_bytes(b"png")
    after = tmp_path / "after.png"
    after.write_bytes(b"png")
    evidence = [
        Evidence(kind="screenshot", artifact=before, claim="修复前截图", produced_by="reproducer"),
        Evidence(kind="render_diff", artifact=after, claim="修复后截图", produced_by="verifier"),
    ]

    def passing_verify(inp: VerifyInput) -> VerifyOutput:
        diff = inp.patch.diff_path
        evidence.append(
            Evidence(kind="diff", artifact=diff, claim="最小补丁", produced_by="fixer")
        )
        return VerifyOutput(
            verdict=_verdict(),
            after_screenshot=after,
            evidence=[e for e in evidence if e.kind in ("render_diff", "screenshot")],
        )

    deps = PipelineDeps(
        repo_dir=golden,
        capture_dir=tmp_path,
        url_fragment="#/bug3",
        llm=StubLLM(),
        artifacts_root=Path("temp/test_exp08"),
        verify_fn=passing_verify,
    )
    app = build_pipeline(deps)
    result = app.invoke({"report": _report(), "candidates": _candidates()})
    assert result.get("passed") is True
    report_path = result.get("report_path")
    assert report_path is not None and Path(report_path).exists()
    text = Path(report_path).read_text(encoding="utf-8")
    assert "未自动合并" in text and "marginTop: 0" in text
