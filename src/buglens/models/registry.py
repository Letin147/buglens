"""Provider registry: get_vlm() returns the configured provider (T09/T03)."""

from __future__ import annotations

import os

from buglens.models.base import BaseVLM, VLMError
from buglens.models.cache import FileCache
from buglens.models.config import load_env
from buglens.models.glm import GLMProvider

_REGISTRY: dict[str, type[BaseVLM]] = {
    "glm": GLMProvider,
}

DEFAULT_PROVIDER = "glm"


def get_vlm(cache: FileCache | None = None, provider: str | None = None) -> BaseVLM:
    load_env()
    name = (provider or os.environ.get("BUGLENS_PROVIDER") or DEFAULT_PROVIDER).lower()
    cls = _REGISTRY.get(name)
    if cls is None:
        raise VLMError(f"unknown provider {name!r}; available: {sorted(_REGISTRY)}")
    return cls(cache=cache)
