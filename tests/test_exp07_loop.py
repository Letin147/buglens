"""EXP-07 tests: oracle primitives and the LangGraph retry loop (no network)."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from buglens.agents.fixer import FixerInput, rollback
from buglens.agents.fixer import run as fixer_run
from buglens.agents.locator.run import CodeCandidate
from buglens.agents.verifier.run import Verdict, VerifyInput, VerifyOutput
from buglens.graph.builder import PipelineDeps, PipelineState, build_pipeline
from buglens.graph.state import Hypothesis, VisualReport
from buglens.models.base import BaseLLM, VLMResponse
from buglens.vision.layout import covered_elements_in_region
from buglens.vision.pixels import region_change_ratio


def _solid_png(path: Path, rgb: tuple[int, int, int]) -> None:
    Image.new("RGB", (100, 100), rgb).save(path)


def test_region_change_ratio_identical_and_changed(tmp_path: Path) -> None:
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    c = tmp_path / "c.png"
    _solid_png(a, (10, 10, 10))
    _solid_png(b, (10, 10, 10))
    _solid_png(c, (200, 200, 200))
    assert region_change_ratio(a, b, [10, 10, 50, 50]) == 0.0
    assert region_change_ratio(a, c, [10, 10, 50, 50]) == 1.0
    # change outside the region must not count
    image = Image.new("RGB", (100, 100), (10, 10, 10))
    for x in range(100):
        for y in range(100):
            if x < 10:
                image.putpixel((x, y), (200, 200, 200))
    image.save(c)
    assert region_change_ratio(a, c, [50, 50, 40, 40]) == 0.0


def test_covered_elements_in_region(tmp_path: Path) -> None:
    overlays = [
        {
            "tag": "nav",
            "cls": "navbar",
            "rect": [0, 0, 1280, 64],
            "covers": [
                {"tag": "button", "cls": "btn-primary", "text": "提交订单",
                 "rect": [345, 37, 590, 48]}
            ],
        }
    ]
    path = tmp_path / "overlays.json"
    path.write_text(json.dumps(overlays), encoding="utf-8")
    hits = covered_elements_in_region(path, [320, 30, 640, 60])
    assert len(hits) == 1 and hits[0].cls == "btn-primary"
    assert covered_elements_in_region(path, [0, 300, 500, 200]) == []


GOOD_HYPOTHESIS = Hypothesis(
    id="H1",
    root_cause="中间卡片 marginTop 过大",
    fix_plan="把 Bug3.tsx 内联 marginTop: 56 改为 0",
    target_path="src/bugs/Bug3.tsx",
    line_hint=15,
    expected_visual_change="三卡顶部对齐",
    confidence=0.9,
)

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


def _fake_verdict(passed: bool) -> VerifyOutput:
    return VerifyOutput(
        verdict=Verdict(
            passed=passed,
            channels={"pixel": "pass" if passed else "fail（no-op）"},
            failure_notes=[] if passed else ["像素通道：修复无效"],
        )
    )


def _run_graph(verify_fn) -> PipelineState:
    golden = Path(__file__).resolve().parents[1] / "examples" / "golden-1"
    deps = PipelineDeps(
        repo_dir=golden,
        capture_dir=Path("temp/exp05/bug3"),
        url_fragment="#/bug3",
        llm=StubLLM(),
        artifacts_root=Path("temp/test_pipeline"),
        verify_fn=verify_fn,
    )
    app = build_pipeline(deps)
    result: PipelineState = app.invoke(
        {"report": _report(), "candidates": _candidates()}
    )
    return result


def test_loop_recovers_after_bad_patch(tmp_path: Path) -> None:
    calls = {"n": 0}

    def flaky_verify(inp: VerifyInput) -> VerifyOutput:
        calls["n"] += 1
        return _fake_verdict(passed=calls["n"] >= 2)

    result = _run_graph(flaky_verify)
    assert result["passed"] is True
    assert result["retries"] == 1
    assert calls["n"] == 2
    assert result["patch"] is not None and result["patch"].edit_count == 1


def test_loop_caps_at_three_retries() -> None:
    calls = {"n": 0}

    def always_fail(inp: VerifyInput) -> VerifyOutput:
        calls["n"] += 1
        return _fake_verdict(passed=False)

    result = _run_graph(always_fail)
    assert result.get("passed") is False
    assert result["retries"] == 2  # initial try + 2 retries = 3 attempts total
    assert calls["n"] == 3


def test_fixer_worktree_roundtrip(tmp_path: Path) -> None:
    golden = Path(__file__).resolve().parents[1] / "examples" / "golden-1"
    before = (golden / "src/bugs/Bug3.tsx").read_text(encoding="utf-8")
    out = fixer_run(
        FixerInput(
            hypothesis=GOOD_HYPOTHESIS,
            repo_dir=golden,
            worktree_dir=tmp_path / "wt",
            artifacts_dir=tmp_path,
        ),
        StubLLM(),
    )
    assert "marginTop: 0" in out.patch.worktree_path.read_text(encoding="utf-8")
    assert (golden / "src/bugs/Bug3.tsx").read_text(encoding="utf-8") == before
    rollback(tmp_path / "wt")
    assert not (tmp_path / "wt").exists()


def test_layout_defects_in_region(tmp_path: Path) -> None:
    from buglens.vision.layout import layout_defects_in_region

    data = {
        "overflow": [
            {"tag": "p", "cls": "", "text": "SKU2026...", "rect": [212, 130, 700, 20],
             "scrollWidth": 850, "clientWidth": 260}
        ],
        "misaligned": [
            {"key": "price-card@DIV:pricing-grid", "tops": [52, 106, 52], "spread": 54,
             "members": [[240, 52, 240, 240], [520, 106, 240, 240], [800, 52, 240, 240]]}
        ],
    }
    path = tmp_path / "layout_checks.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    overflow_region = [150, 100, 400, 180]
    defects = layout_defects_in_region(path, overflow_region)
    assert any("横向溢出" in d for d in defects)
    pricing_region = [420, 170, 590, 470]
    defects = layout_defects_in_region(path, pricing_region)
    assert any("顶边不对齐" in d for d in defects)
    clean_region = [0, 700, 1280, 100]
    assert layout_defects_in_region(path, clean_region) == []
