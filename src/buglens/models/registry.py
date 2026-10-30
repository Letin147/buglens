"""Provider registry: get_vlm()/get_llm() return configured providers (T09/T03)."""

from __future__ import annotations

import os

from buglens.models.base import BaseLLM, BaseVLM, VLMError
from buglens.models.cache import FileCache
from buglens.models.config import load_env
from buglens.models.glm import GLMProvider

_REGISTRY: dict[str, type[BaseVLM]] = {
    "glm": GLMProvider,
}

DEFAULT_PROVIDER = "glm"


def _resolve(cache: FileCache | None, provider: str | None) -> BaseVLM:
    load_env()
    name = (provider or os.environ.get("BUGLENS_PROVIDER") or DEFAULT_PROVIDER).lower()
    cls = _REGISTRY.get(name)
    if cls is None:
        raise VLMError(f"unknown provider {name!r}; available: {sorted(_REGISTRY)}")
    return cls(cache=cache)


def get_vlm(cache: FileCache | None = None, provider: str | None = None) -> BaseVLM:
    return _resolve(cache, provider)


def get_llm(cache: FileCache | None = None, provider: str | None = None) -> BaseLLM:
    resolved = _resolve(cache, provider)
    if not isinstance(resolved, BaseLLM):
        raise VLMError(f"provider {resolved.name!r} has no text capability")
    return resolved
