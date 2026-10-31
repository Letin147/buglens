"""reporter.run: render the PR description; assertions without evidence fail."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from buglens.agents.verifier.run import Verdict
from buglens.evidence.store import EvidenceGapError
from buglens.graph.state import Evidence, Hypothesis, Patch, VisualReport

REQUIRED_KINDS = ("screenshot", "render_diff", "diff")


@dataclass(frozen=True)
class ReporterInput:
    report: VisualReport
    hypothesis: Hypothesis
    patch: Patch
    verdict: Verdict
    evidence: list[Evidence]
    before_png: Path
    after_png: Path
    out_path: Path


def run(inp: ReporterInput) -> Path:
    """Validate the evidence chain, then render markdown to out_path."""
    _require_evidence(inp.evidence)
    diff_text = (
        inp.patch.diff_path.read_text(encoding="utf-8") if inp.patch.diff_path.exists() else ""
    )
    inp.out_path.write_text(render_pr_report(inp, diff_text), encoding="utf-8")
    return inp.out_path


def _require_evidence(evidence: list[Evidence]) -> None:
    kinds = {e.kind for e in evidence}
    missing = [kind for kind in REQUIRED_KINDS if kind not in kinds]
    if missing:
        raise EvidenceGapError(f"证据链缺少必需类型：{missing}")
    absent = [str(e.artifact) for e in evidence if not e.artifact.exists()]
    if absent:
        raise EvidenceGapError(f"证据工件不存在：{absent}")


def render_pr_report(inp: ReporterInput, diff_text: str) -> str:
    channel_rows = "\n".join(
        f"| {name} | {detail} |" for name, detail in inp.verdict.channels.items()
    )
    evidence_rows = "\n".join(
        f"| {e.claim} | `{e.artifact.name}` | {e.produced_by} |" for e in inp.evidence
    )
    return (
        "# BugLens 修复建议（draft）\n"
        "\n"
        "> ⚠️ 本 PR 由 BugLens 自动生成，**仅供人工审阅，未自动合并**（S03）。\n"
        "\n"
        "## 概述\n"
        f"- 视觉缺陷：{inp.report.symptom}\n"
        f"- 异常区域：{inp.report.anomaly_region}（置信度 {inp.report.confidence}，"
        f"检测模型 {inp.report.model}）\n"
        f"- 根因假设：{inp.hypothesis.root_cause}（{inp.hypothesis.id}，"
        f"置信度 {inp.hypothesis.confidence}）\n"
        "\n"
        "## 修复方案\n"
        f"{inp.hypothesis.fix_plan}（目标：`{inp.patch.target_path}`，"
        f"{inp.patch.edit_count} 处最小编辑）\n"
        "\n"
        "## 补丁\n"
        "```diff\n"
        f"{diff_text.strip()}\n"
        "```\n"
        "\n"
        "## 可执行验证（oracle 判定）\n"
        "| 通道 | 结果 |\n"
        "|---|---|\n"
        f"{channel_rows}\n"
        "\n"
        "## 修复前后对比\n"
        f"- 修复前：`{inp.before_png.name}`\n"
        f"- 修复后：`{inp.after_png.name}`\n"
        "\n"
        "## 证据链（每个断言 ↔ 工件）\n"
        "| 断言 | 工件 | 产生者 |\n"
        "|---|---|---|\n"
        f"{evidence_rows}\n"
        "\n"
        "## 复现步骤\n"
        "1. 在仓库根目录运行 `buglens index init .`\n"
        "2. 以缺陷截图运行修复闭环（复现 → 定位 → 修复 → 可执行验证）\n"
        "3. 本报告与全部证据工件由上述流程自动生成，可逐条复核\n"
    )
