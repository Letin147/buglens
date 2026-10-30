"""EXP-05 tests: slicing, tokenizer, and golden-1 top-5 localization (no network)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from buglens.agents.locator.run import LocatorInput, run
from buglens.graph.state import VisualReport
from buglens.repo.indexer import build_index, slice_file, tokenize

GOLDEN1 = Path(__file__).resolve().parents[1] / "examples" / "golden-1"


def _line_of(path: Path, marker: str) -> int:
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if marker in line:
            return i
    raise AssertionError(f"marker {marker!r} not found in {path}")


def test_tokenize_mixed_text() -> None:
    tokens = tokenize("按钮被btn-primary遮挡")
    assert "btn" in tokens and "primary" in tokens
    assert "按钮" in tokens and "遮挡" in tokens


def test_slice_css_rules() -> None:
    css = ".a { color: red; }\n@media x { }\n.b { padding-top: 12px; }"
    slices = slice_file("x.css", css, ".css")
    selectors = [s.text.split(" ")[0] for s in slices]
    assert ".a" in selectors and ".b" in selectors
    gt = next(s for s in slices if "padding-top" in s.text)
    assert gt.line_start == 3


def test_slice_tsx_components() -> None:
    tsx = "export default function Bug9() {\n  return <div className=\"x\">hi</div>;\n}\n"
    slices = slice_file("Bug9.tsx", tsx, ".tsx")
    assert len(slices) == 1
    assert slices[0].line_start == 1 and "Bug9" in slices[0].text


@pytest.fixture()
def golden_index(tmp_path: Path) -> Path:
    """Index golden-1 without the vector channel (CI-safe, no model needed)."""
    build_index(GOLDEN1, embedder=None, progress=lambda _msg: None)
    return GOLDEN1


def _make_report(symptom: str) -> VisualReport:
    return VisualReport(
        anomaly_region=[0, 0, 1, 1],
        symptom=symptom,
        severity="mid",
        confidence=0.8,
        prompt_version="test",
        model="test",
    )


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def _top5(repo: Path, tmp: Path, report: VisualReport, dom: str, overlays: list | None):
    from buglens.repo.indexer import load_index

    dom_path = _write(tmp, "dom.html", dom)
    overlays_path = None
    if overlays is not None:
        overlays_path = _write(tmp, "overlays.json", json.dumps(overlays))
    return run(
        LocatorInput(
            report=report,
            repo_dir=repo,
            dom_path=dom_path,
            overlays_path=overlays_path,
        ),
        load_index(repo),
    )


def test_locate_bug1_occlusion(golden_index: Path, tmp_path: Path) -> None:
    dom = '<nav class="navbar"></nav><main class="bug1-page"><section class="checkout-card"></section></main>'
    overlays = [
        {
            "tag": "nav",
            "cls": "navbar",
            "rect": [0, 0, 1280, 64],
            "zIndex": "1000",
            "covers": [
                {"tag": "button", "cls": "btn-primary", "text": "提交订单", "rect": [320, 36, 640, 48]}
            ],
        }
    ]
    out = _top5(
        golden_index,
        tmp_path,
        _make_report("顶部按钮被导航栏遮挡，只显示下半部分"),
        dom,
        overlays,
    )
    assert out.candidates, "locator returned nothing"
    css_gt = _line_of(GOLDEN1 / "src" / "index.css", "padding-top: 12px")
    tsx_gt = _line_of(GOLDEN1 / "src" / "bugs" / "Bug1.tsx", "提交订单")
    hit = any(
        (c.path.endswith("index.css") and c.line_start <= css_gt <= c.line_end)
        or (c.path.endswith("Bug1.tsx") and c.line_start <= tsx_gt <= c.line_end)
        for c in out.candidates
    )
    assert hit, f"top-5 missed bug1 GT: {[c.display for c in out.candidates]}"


def test_locate_bug2_overflow(golden_index: Path, tmp_path: Path) -> None:
    dom = '<div class="spec-grid"><section class="spec-card"></section></div>'
    out = _top5(
        golden_index,
        tmp_path,
        _make_report("SKU 文字内容超出卡片容器边界，压到右侧卡片"),
        dom,
        None,
    )
    gt = _line_of(GOLDEN1 / "src" / "bugs" / "Bug2.tsx", "SKU2026XT9000")
    hit = any(
        c.path.endswith("Bug2.tsx") and c.line_start <= gt <= c.line_end for c in out.candidates
    )
    assert hit, f"top-5 missed bug2 GT: {[c.display for c in out.candidates]}"


def test_locate_bug3_misalignment(golden_index: Path, tmp_path: Path) -> None:
    dom = '<div class="pricing-grid"><section class="price-card"></section></div>'
    out = _top5(
        golden_index,
        tmp_path,
        _make_report("专业版卡片相比左右卡片垂直位置下沉，明显错位"),
        dom,
        None,
    )
    gt = _line_of(GOLDEN1 / "src" / "bugs" / "Bug3.tsx", "marginTop: 56")
    hit = any(
        c.path.endswith("Bug3.tsx") and c.line_start <= gt <= c.line_end for c in out.candidates
    )
    assert hit, f"top-5 missed bug3 GT: {[c.display for c in out.candidates]}"
