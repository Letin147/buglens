"""Prompt for the visual analyst.

Version history (kept here per 02-MANUAL: prompt changes are code changes):
- v1-20261029: open-ended "find the most obvious defect" (EXP-02: nitpicks only)
- v2-20261029: enumerated functional defect classes, excludes style taste
  (EXP-02: fixed misalignment miss; overflow hit after supplement; occlusion still missed)
- v3-20261029: adds trustworthy DOM facts about fixed/sticky overlay elements and
  directs attention to content they may cover (EXP-04: occlusion region-hit, cause inverted)
- v4-20261029: adds covered-element clues (what sits under each overlay), so the
  model can name the occluded element instead of guessing the direction
"""

from __future__ import annotations

PROMPT_VERSION = "v4-covered-20261029"

_TEMPLATE = (
    "你是 UI 缺陷检测器。仔细检查这张网页截图（1280x800 像素），找出最严重的「功能性视觉缺陷」。\n"
    "按以下优先级逐类检查：\n"
    "1. 遮挡/截断：元素被其他元素遮挡或切断，文字只显示一半；\n"
    "2. 溢出/重叠：文字或元素超出其容器边界、压到相邻元素上；\n"
    "3. 错位：同类元素（卡片、列、行）之间明显不对齐、垂直位置异常；\n"
    "4. 布局破碎：元素挤在一起导致不可读。\n"
    "注意：颜色、边框、圆角、间距大小等设计风格偏好不算缺陷，除非造成了上述遮挡/溢出/错位/不可读。\n"
    "\n"
    "页面布局事实（来自 DOM 实测，完全可信）：\n"
    "{dom_facts}\n"
    "解读规则：上面每个「覆盖层」会遮住其矩形范围内的内容；其 covers 列表给出实测"
    "被它遮住超过一半面积的元素（含文字）。若 covers 非空，说明确有内容被该覆盖层遮挡，"
    "缺陷方向是「覆盖层遮住了 covers 中的元素」，请以截图对照确认。\n"
    "\n"
    "只输出一个 JSON 对象，不要任何其他文字、解释或代码块标记：\n"
    '{{"anomaly_region": [x, y, w, h], "symptom": "一句话中文描述", '
    '"severity": "low|mid|high", "confidence": 0到1之间的小数}}\n'
    "anomaly_region 是缺陷区域的外接矩形 [左上角x, 左上角y, 宽, 高]，"
    "以图像左上角为原点，单位像素，图像尺寸 1280x800。"
)


def build_prompt(dom_facts: str) -> str:
    """Render the v3 prompt with DOM facts inserted."""
    return _TEMPLATE.format(dom_facts=dom_facts)
