"""Unit tests for the visual analyst agent with a fake VLM (no network)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from buglens.agents.visual_analyst import PROMPT_VERSION, VisualAnalystInput, run
from buglens.models.base import BaseVLM, VLMError, VLMResponse, extract_json_object
from buglens.models.cache import FileCache

GOOD_ANSWER = (
    "```json\n"
    '{"anomaly_region": [320, 35, 640, 48], "symptom": "提交订单按钮被导航栏遮挡", '
    '"severity": "high", "confidence": 0.9}\n'
    "```"
)


class FakeVLM(BaseVLM):
    name = "fake-vlm"

    def __init__(self, answer: str = GOOD_ANSWER) -> None:
        super().__init__(cache=None)
        self.answer = answer
        self.calls = 0

    def complete_vision(self, image: Path, prompt: str) -> VLMResponse:
        self.calls += 1
        return VLMResponse(text=self.answer, elapsed_s=0.01, total_tokens=42)


def _make_inputs(tmp_path: Path, overlays: list[dict[str, object]] | None) -> VisualAnalystInput:
    shot = tmp_path / "screenshot.png"
    shot.write_bytes(b"fake-image-bytes")
    overlays_path: Path | None = None
    if overlays is not None:
        overlays_path = tmp_path / "overlays.json"
        overlays_path.write_text(json.dumps(overlays), encoding="utf-8")
    return VisualAnalystInput(
        screenshot=shot, overlays=overlays_path, artifacts_dir=tmp_path / "agent"
    )


def test_run_parses_and_attaches_evidence(tmp_path: Path) -> None:
    vlm = FakeVLM()
    overlays = [
        {"tag": "nav", "cls": "navbar", "rect": [0, 0, 1280, 64], "zIndex": "1000"}
    ]
    out = run(_make_inputs(tmp_path, overlays), vlm)

    assert vlm.calls == 1
    assert out.report.anomaly_region == [320, 35, 640, 48]
    assert out.report.prompt_version == PROMPT_VERSION
    assert out.report.model == "fake-vlm"
    kinds = [e.kind for e in out.evidence]
    assert kinds == ["screenshot", "model_output", "overlays"]
    assert (tmp_path / "agent" / "visual_analyst_raw.txt").exists()


def test_prompt_contains_dom_facts(tmp_path: Path) -> None:
    captured: list[str] = []

    class CapturingVLM(FakeVLM):
        def complete_vision(self, image: Path, prompt: str) -> VLMResponse:
            captured.append(prompt)
            return super().complete_vision(image, prompt)

    overlays = [{"tag": "nav", "cls": "navbar", "rect": [0, 0, 1280, 64], "zIndex": "1000"}]
    run(_make_inputs(tmp_path, overlays), CapturingVLM())
    assert "来自 DOM 实测" in captured[0]
    assert "y=0" in captured[0] and "h=64" in captured[0]


def test_schema_violation_raises_vlmerror(tmp_path: Path) -> None:
    bad = json.dumps({"anomaly_region": [1, 2], "symptom": "x", "severity": "meh", "confidence": 2})
    with pytest.raises(VLMError):
        run(_make_inputs(tmp_path, None), FakeVLM(answer=bad))


def test_extract_json_object_variants() -> None:
    assert extract_json_object('废话 {"a": 1} 结尾') == {"a": 1}
    assert extract_json_object("```json\n{\"a\": 2}\n```") == {"a": 2}
    with pytest.raises(VLMError):
        extract_json_object("没有任何对象")


def test_cache_hit_means_zero_api_calls(tmp_path: Path) -> None:
    class CachedVLM(FakeVLM):
        def __init__(self, cache: FileCache) -> None:
            super().__init__()
            self.cache = cache

        def complete_vision(self, image: Path, prompt: str) -> VLMResponse:  # type: ignore[override]
            hit = self.cache.get(image, prompt)
            if hit is not None:
                return hit
            response = super().complete_vision(image, prompt)
            self.cache.put(image, prompt, response)
            return response

    fast = CachedVLM(FileCache(tmp_path / "cache"))
    run(_make_inputs(tmp_path, None), fast)
    run(_make_inputs(tmp_path, None), fast)
    assert fast.calls == 1  # second run served from cache
