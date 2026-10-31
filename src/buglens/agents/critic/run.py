"""critic.run: deterministic asymmetric review — reads artifacts, never the
planner/fixer self-descriptions.

Rule-based MVP (documented deviation from the LLM critic on the EXP-08 card:
quota-free, fully auditable; the LLM variant can layer on later without
changing the contract).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from buglens.agents.verifier.run import Verdict
from buglens.graph.state import Evidence, Patch

MAX_EDITS = 3


@dataclass(frozen=True)
class CriticInput:
    patch: Patch
    verdict: Verdict
    evidence: list[Evidence]


@dataclass(frozen=True)
class CriticOutput:
    approved: bool
    reasons: list[str] = field(default_factory=list)


def run(inp: CriticInput) -> CriticOutput:
    """Approve only when every deterministic check passes on the artifacts."""
    reasons: list[str] = []

    diff_text = (
        inp.patch.diff_path.read_text(encoding="utf-8") if inp.patch.diff_path.exists() else ""
    )
    touched: set[str] = set()
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            touched.add("b/" + line[len("+++ b/") :])
        elif line.startswith("--- a/"):
            touched.add("a/" + line[len("--- a/") :])
    allowed = {f"a/{inp.patch.target_path}", f"b/{inp.patch.target_path}"}
    if not touched:
        reasons.append("diff 文件缺失或为空")
    elif not touched <= allowed:
        reasons.append(f"diff 改动了目标之外的文件：{sorted(touched - allowed)}")

    if not inp.verdict.passed:
        reasons.append("verifier 判定未通过")
    failed_channels = [k for k, v in inp.verdict.channels.items() if v.startswith("fail")]
    if failed_channels:
        reasons.append(f"存在失败通道：{failed_channels}")

    if inp.patch.edit_count > MAX_EDITS:
        reasons.append(f"edit_count={inp.patch.edit_count} 超过最小补丁上限 {MAX_EDITS}")

    if not inp.evidence:
        reasons.append("证据链为空")

    return CriticOutput(approved=not reasons, reasons=reasons)
