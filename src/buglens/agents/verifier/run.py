"""verifier.run: pixel + layout(+tests) oracle; writes failure notes for planner."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from buglens.graph.state import Evidence, Patch, VisualReport
from buglens.repro.patched_env import patched_server, prepare_patched_repo
from buglens.repro.reproducer import Reproducer
from buglens.vision.layout import covered_elements_in_region, layout_defects_in_region
from buglens.vision.pixels import region_change_ratio

MIN_REGION_CHANGE = 0.005
# Anti-no-op guard, empirically calibrated (EXP-07/09 real runs): under
# deterministic reproduction a no-op patch measures EXACTLY 0.0% (SSIM=1.0),
# while real fixes measured 1.9%–43.6%. The old 2% bar false-negatived a real
# 56px card shift (1.92%) because uniform backgrounds dilute the ratio.
TEST_TIMEOUT_S = 600


class Verdict(BaseModel):
    """Outcome of the executable oracle (EXP-07 core artifact)."""

    passed: bool
    channels: dict[str, str] = Field(default_factory=dict)
    failure_notes: list[str] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


@dataclass(frozen=True)
class VerifyInput:
    report: VisualReport
    patch: Patch
    repo_dir: Path
    capture_dir: Path  # pre-fix artifacts (screenshot.png / overlays.json)
    url_fragment: str  # e.g. "#/bug1"
    run_dir: Path      # verifier workdir (patched repo + re-capture)
    port: int = 5574


@dataclass(frozen=True)
class VerifyOutput:
    verdict: Verdict
    after_screenshot: Path | None = None
    after_overlays: Path | None = None
    evidence: list[Evidence] = field(default_factory=list)


def run(inp: VerifyInput) -> VerifyOutput:
    """Re-render the patched copy and judge the three channels."""
    patched_root = inp.run_dir / "patched_repo"
    # patch.worktree_path = <worktree_root>/<target_rel>: walk up rel depth
    # (passing worktree_path.parent loses directory levels — found in the
    # EXP-07 real run, where patches landed at patched_repo/index.css)
    worktree_root = inp.patch.worktree_path
    for _ in Path(inp.patch.target_path).parts:
        worktree_root = worktree_root.parent
    prepare_patched_repo(inp.repo_dir, worktree_root, patched_root)
    repro = Reproducer(f"http://127.0.0.1:{inp.port}/{inp.url_fragment}")
    with patched_server(patched_root, inp.port):
        after = repro.capture(inp.run_dir / "after")

    channels: dict[str, str] = {}
    notes: list[str] = []

    change = region_change_ratio(
        inp.capture_dir / "screenshot.png", after.screenshot, inp.report.anomaly_region
    )
    if change < MIN_REGION_CHANGE:
        channels["pixel"] = f"fail（异常区域仅 {change:.1%} 像素变化——补丁疑似无效/no-op）"
        notes.append(
            f"像素通道：修复后异常区域变化率仅 {change:.1%}（阈值 {MIN_REGION_CHANGE:.0%}），"
            "补丁没有产生可见效果；请给出会产生实际渲染变化的修改。"
        )
    else:
        channels["pixel"] = f"pass（异常区域变化率 {change:.1%}）"

    covered = covered_elements_in_region(after.overlays, inp.report.anomaly_region)
    if covered:
        described = "、".join(
            f"<{c.tag} class={c.cls!r} text={c.text!r}>" for c in covered[:3]
        )
        channels["layout"] = f"fail（修复后仍被覆盖层遮挡：{described}）"
        notes.append(f"布局通道：修复后异常区域内仍有元素被覆盖层遮挡：{described}；遮挡未解除。")
    else:
        channels["layout"] = "pass（异常区域内无被覆盖元素）"

    dom_defects = layout_defects_in_region(
        after.layout_checks, inp.report.anomaly_region
    )
    if dom_defects:
        described = "；".join(dom_defects[:3])
        channels["dom"] = f"fail（{described}）"
        notes.append(f"DOM 通道：修复后异常区域内仍存在结构性布局缺陷：{described}。")
    else:
        channels["dom"] = "pass（区域内无溢出/错位缺陷）"

    tests_result = _run_existing_tests(patched_root)
    channels["tests"] = tests_result[0]
    if tests_result[1]:
        notes.append(tests_result[1])

    passed = all(
        not value.startswith("fail") for value in channels.values()
    )
    evidence = [
        Evidence(
            kind="render_diff",
            artifact=after.screenshot,
            claim=f"修复后重渲染截图（{channels['pixel']}；{channels['layout']}）",
            produced_by="verifier",
        ),
        Evidence(
            kind="overlays",
            artifact=after.overlays,
            claim="修复后覆盖层/被覆盖元素重算结果",
            produced_by="verifier",
        ),
    ]
    return VerifyOutput(
        verdict=Verdict(passed=passed, channels=channels, failure_notes=notes),
        after_screenshot=after.screenshot,
        after_overlays=after.overlays,
        evidence=evidence,
    )


def _run_existing_tests(repo_dir: Path) -> tuple[str, str]:
    """Channel 3: run the repo's own test script when one exists."""
    package_json = repo_dir / "package.json"
    if not package_json.exists():
        return "n-a（无 package.json）", ""
    scripts = package_json.read_text(encoding="utf-8")
    if '"test"' not in scripts:
        return "n-a（仓库无测试脚本）", ""
    try:
        proc = subprocess.run(
            ["npm", "test"],
            cwd=str(repo_dir),
            shell=True,
            capture_output=True,
            timeout=TEST_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return "fail（测试超时）", "测试通道：npm test 超时。"
    if proc.returncode == 0:
        return "pass（npm test 通过）", ""
    tail = proc.stdout.decode("utf-8", errors="replace")[-300:]
    return "fail（npm test 失败）", f"测试通道：npm test 失败，输出尾部：{tail}"
