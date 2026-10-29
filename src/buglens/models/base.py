"""Base classes and shared helpers for VLM providers."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class VLMError(RuntimeError):
    """Raised when a provider call fails after retries (downstream must degrade)."""


@dataclass(frozen=True)
class VLMResponse:
    text: str
    elapsed_s: float
    total_tokens: int = 0
    cached: bool = False


class BaseVLM(ABC):
    """A vision-language model that answers a prompt about one image."""

    name: str

    def __init__(self, cache: object | None = None) -> None:
        self.cache = cache

    @abstractmethod
    def complete_vision(self, image: Path, prompt: str) -> VLMResponse:
        """Return the model's raw text answer for the given image and prompt."""


def extract_json_object(text: str) -> dict[str, Any]:
    """Best-effort extraction of the first JSON object from a model answer.

    Handles markdown fences and surrounding prose; raises VLMError when no
    object is found so callers can treat it as a parse failure.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("` \n")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        raise VLMError(f"no JSON object found in model output: {text[:200]!r}")
    try:
        obj = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise VLMError(f"model output is not valid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise VLMError("model output JSON is not an object")
    return obj
