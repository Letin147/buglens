"""Layout channel: recompute overlay occlusion facts after the patch."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CoveredElement:
    overlay_cls: str
    tag: str
    cls: str
    text: str
    rect: list[int]


def covered_elements_in_region(overlays_path: Path, region: list[float]) -> list[CoveredElement]:
    """Elements still ≥50% covered by a fixed/sticky overlay, intersecting region.

    The reproducer's overlays.json already applies the ≥50%-area rule per
    entry; here we keep covered elements whose rect intersects the reported
    anomaly region at all (the defect zone must end up cover-free).
    """
    if not overlays_path.exists():
        return []
    try:
        entries = json.loads(overlays_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    rx, ry, rw, rh = (float(v) for v in region)
    hits: list[CoveredElement] = []
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            continue
        for covered in entry.get("covers", []):
            if not isinstance(covered, dict):
                continue
            rect = [int(v) for v in covered.get("rect", [0, 0, 0, 0])]
            cx, cy, cw, ch = rect
            overlap_x = max(0.0, min(rx + rw, cx + cw) - max(rx, cx))
            overlap_y = max(0.0, min(ry + rh, cy + ch) - max(ry, cy))
            if overlap_x > 0 and overlap_y > 0:
                hits.append(
                    CoveredElement(
                        overlay_cls=str(entry.get("cls", "")),
                        tag=str(covered.get("tag", "")),
                        cls=str(covered.get("cls", "")),
                        text=str(covered.get("text", "")),
                        rect=rect,
                    )
                )
    return hits


def layout_defects_in_region(layout_path: Path, region: list[float]) -> list[str]:
    """Executable DOM assertions for overflow / misalignment inside region.

    Reads the reproducer's layout_checks.json: horizontal overflow elements
    (scrollWidth > clientWidth) and sibling groups whose top spread exceeds
    24px; keeps those intersecting the reported anomaly region. This closes
    the false-positive hole where "pixels changed" passed unfixed defects
    (found on bug2/bug3 in the EXP-07 real run).
    """
    if not layout_path.exists():
        return []
    try:
        data = json.loads(layout_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, dict):
        return []
    rx, ry, rw, rh = (float(v) for v in region)
    defects: list[str] = []
    for item in data.get("overflow", []) if isinstance(data.get("overflow"), list) else []:
        if not isinstance(item, dict):
            continue
        x, y, w, h = (int(v) for v in item.get("rect", [0, 0, 0, 0]))
        if min(rx + rw, x + w) - max(rx, x) > 0 and min(ry + rh, y + h) - max(ry, y) > 0:
            defects.append(
                f"元素 <{item.get('tag')}> class={item.get('cls')!r} 横向溢出"
                f"（scrollWidth={item.get('scrollWidth')} > clientWidth={item.get('clientWidth')}，"
                f"文本={str(item.get('text'))[:20]!r}）"
            )
    for group in (
        data.get("misaligned", []) if isinstance(data.get("misaligned"), list) else []
    ):
        if not isinstance(group, dict):
            continue
        for rect in group.get("members", []) if isinstance(group.get("members"), list) else []:
            if not isinstance(rect, list) or len(rect) != 4:
                continue
            x, y, w, h = (int(v) for v in rect)
            if min(rx + rw, x + w) - max(rx, x) > 0 and min(ry + rh, y + h) - max(ry, y) > 0:
                defects.append(
                    f"兄弟元素组 {group.get('key')!r} 顶边不对齐"
                    f"（spread={group.get('spread')}px，tops={group.get('tops')}）"
                )
                break
    return defects
