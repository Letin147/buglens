"""Prompt for the fixer.

Version history:
- v1-20261030: first version (EXP-06): exact-string constrained edits; the
  unified diff is generated programmatically (difflib) after validation, so
  the model never hand-writes line numbers.
- v2-20261030: multi-line fragment rules after the first real run — the model
  wrote a multi-line CSS rule as one line and was (correctly) rejected.
- v3-20261030: feed the RAW file (no line numbers) — with a numbered view the
  models copied the " 62 | " prefixes into `old` or invented rules; exact
  string editing never needed line numbers anyway.
"""

from __future__ import annotations

PROMPT_VERSION = "v3-raw-20261030"

_TEMPLATE = (
    "你是前端修复工程师。请根据根因假设，对目标文件做最小修复。\n"
    "\n"
    "【根因假设】\n"
    "根因：{root_cause}\n"
    "修复方案：{fix_plan}\n"
    "预期视觉变化：{expected_visual_change}\n"
    "\n"
    "【目标文件】{target_path}（以下为文件原文）\n"
    "```\n"
    "{content}\n"
    "```\n"
    "\n"
    "只输出一个 JSON 对象，不要任何其他文字或代码块标记：\n"
    '{{"edits":[{{"old":"文件原文中连续的精确片段",'
    '"new":"替换后的片段"}}]}}\n'
    "\n"
    "硬性约束：\n"
    "1. **old 必须从上面文件原文中逐字符原样复制**（含换行与每行缩进），"
    "且在整个文件中恰好出现一次；禁止自己拼写、合并或改写格式；\n"
    "2. old 可以跨多行；若假设提到的选择器/属性在文件中不存在，"
    "请改为修改文件中真实存在的最接近片段，实现等价的最小修复；\n"
    "3. 每个 edit 是一处最小改动，总 edit 数不超过 3；"
    "只修改与根因相关的内容，禁止重排/重命名无关代码；只修改这一个文件。\n"
    "4. JSON 字符串中的换行请写成 \\n 转义。"
)


def build_prompt(
    root_cause: str,
    fix_plan: str,
    expected_visual_change: str,
    target_path: str,
    content: str,
) -> str:
    return _TEMPLATE.format(
        root_cause=root_cause,
        fix_plan=fix_plan,
        expected_visual_change=expected_visual_change,
        target_path=target_path,
        content=content,
    )
