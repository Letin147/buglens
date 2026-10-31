"""Prompt for the planner.

Version history:
- v1-20261030: first version (EXP-06): candidates + symptom + console excerpt
  -> up to 3 ranked hypotheses with target file taken from the candidate list.
- v2-20261030: failure feedback (EXP-07 loop) — previous rejected hypotheses
  and the verifier's channel evidence are injected so the next round proposes
  genuinely different fixes instead of repeating rejected ones.
- v3-20261030: defect-class repair patterns distilled from measured no-op
  fixes (EXP-06/07): z-index on non-positioned elements, widening outer
  containers for overflow, shifting the whole parent for sibling misalign —
  all verified no-ops by the executable oracle; the pattern library steers
  the planner toward effective fixes.
- v3.1-20261030: misalignment pattern hardened — inline styles beat class
  selectors, so a JS inline style defect must be edited in the JSX itself
  (CSS margin-top: 0 measured as no-op against style={{marginTop: 56}}).
"""

from __future__ import annotations

PROMPT_VERSION = "v3.1-inline-20261030"

_PATTERNS = (
    "【缺陷类修复模式库（依据可执行 oracle 实测，标⚠的修法已被证伪为无效）】\n"
    "1. 遮挡类（元素被 fixed/sticky 覆盖层遮住）：增大内容容器的 padding-top 使其≥覆盖层高度，"
    "或消除覆盖关系。⚠ 实测无效：给无 position 的元素加 z-index（渲染零变化）。\n"
    "2. 溢出类（元素 scrollWidth > clientWidth，长串/长词撑出容器）：在溢出元素或其直接容器上"
    "加 `overflow-wrap: anywhere;`（或 `word-break: break-all;`）。⚠ 实测无效：扩大外层页面容器"
    "的 max-width（溢出元素相对容器依旧溢出）。\n"
    "3. 错位类（同父兄弟组顶边不齐、spread 大）：定位 top 异常的那一个成员，把它的 margin-top / "
    "transform / 样式恢复为与兄弟一致。⚠ 内联 style 优先级高于 CSS 类选择器：若异常成员带有内联"
    "样式（如 JSX 中 style={{marginTop: 56}}），**必须直接修改该 JSX 内联样式**（改小或删除），"
    "对 CSS 类加 margin-top: 0 实测无效；此时 target 应选包含该内联样式的 JSX 文件。"
    "⚠ 实测无效：修改父容器 padding 或整体位移（兄弟相对差不变）。\n"
)

_TEMPLATE = (
    "你是前端缺陷修复规划师。根据以下信息，给出最多 3 个按可信度降序排列的根因假设。\n"
    "\n"
    "【视觉缺陷报告】\n"
    "症状：{symptom}\n"
    "异常区域：{region}\n"
    "\n"
    "{patterns}"
    "\n"
    "【代码定位候选】（top-5）\n"
    "{candidates}\n"
    "\n"
    "【浏览器控制台日志】\n"
    "{console}\n"
    "{feedback}"
    "要求：\n"
    "1. target_path 必须是纯文件路径（如 src/index.css），严格取自候选列表，"
    "禁止附加行号、\":\"、\"|\" 或选择器后缀；\n"
    "2. 每个假设必须能解释症状，并优先采用上面模式库中对应缺陷类的有效修法；\n"
    "3. fix_plan 描述最小修改（精确到选择器的属性值 / JSX 内联样式），不要重写文件；\n"
    "4. expected_visual_change 描述修复后截图应有的变化。\n"
    "\n"
    "只输出一个 JSON 对象，不要任何其他文字或代码块标记：\n"
    '{{"hypotheses":[{{"id":"H1","root_cause":"一句话","fix_plan":"一句话",'
    '"target_path":"候选中的路径","line_hint":行号或null,'
    '"expected_visual_change":"一句话","confidence":0到1小数}}]}}\n'
    "注意：JSON 字符串内的换行写成 \\n 转义，值内不要出现未转义双引号。"
)

_FEEDBACK_BLOCK = (
    "\n【上一轮修复尝试（已失败，禁止重复同样的修改）】\n{history}\n"
    "验证失败证据（可执行 oracle 的判定）：\n{notes}\n"
    "请基于失败证据提出**不同方向**的新假设，并对照模式库选择有效修法。\n"
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
        patterns=_PATTERNS,
        candidates=candidates_block or "（无）",
        console=console or "（无输出）",
        feedback=feedback,
    )
