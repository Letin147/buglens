"""Prompt for the planner.

Version history:
- v1-20261030: first version (EXP-06): candidates + symptom + console excerpt
  -> up to 3 ranked hypotheses with target file taken from the candidate list.
- v2-20261030: failure feedback (EXP-07 loop) — previous rejected hypotheses
  and the verifier's channel evidence are injected so the next round proposes
  genuinely different fixes instead of repeating rejected ones.
"""

from __future__ import annotations

PROMPT_VERSION = "v2-feedback-20261030"

_TEMPLATE = (
    "你是前端缺陷修复规划师。根据以下信息，给出最多 3 个按可信度降序排列的根因假设。\n"
    "\n"
    "【视觉缺陷报告】\n"
    "症状：{symptom}\n"
    "异常区域：{region}\n"
    "\n"
    "【代码定位候选】（top-5，format: 文件:行范围 | 片段）\n"
    "{candidates}\n"
    "\n"
    "【浏览器控制台日志】\n"
    "{console}\n"
    "{feedback}"
    "要求：\n"
    "1. target_path 必须严格取自上面候选列表中的文件路径；\n"
    "2. 每个假设必须能解释症状（遮挡/溢出/错位等）；\n"
    "3. fix_plan 描述最小修改（改哪个规则的哪个属性/哪段 JSX 结构），不要重写文件；\n"
    "4. expected_visual_change 描述修复后截图应有的变化。\n"
    "\n"
    "只输出一个 JSON 对象，不要任何其他文字或代码块标记：\n"
    '{{"hypotheses":[{{"id":"H1","root_cause":"一句话","fix_plan":"一句话",'
    '"target_path":"候选中的路径","line_hint":行号或null,'
    '"expected_visual_change":"一句话","confidence":0到1小数}}]}}'
)

_FEEDBACK_BLOCK = (
    "\n【上一轮修复尝试（已失败，禁止重复同样的修改）】\n{history}\n"
    "验证失败证据（可执行 oracle 的判定）：\n{notes}\n"
    "请基于失败证据提出**不同方向**的新假设。\n"
)


def build_prompt(
    symptom: str,
    region: list[float],
    candidates_block: str,
    console: str,
    failure_notes: list[str] | None = None,
    tried_summary: str = "",
) -> str:
    feedback = ""
    if failure_notes:
        history = tried_summary or "（见失败证据）"
        notes = "\n".join(f"- {n}" for n in failure_notes)
        feedback = _FEEDBACK_BLOCK.format(history=history, notes=notes)
    return _TEMPLATE.format(
        symptom=symptom,
        region=region,
        candidates=candidates_block or "（无）",
        console=console or "（无输出）",
        feedback=feedback,
    )
