"""Pluggable embedder for the vector channel (bge-m3 on CPU, local-first)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

DEFAULT_MODEL_DIR = Path("temp/models/bge-m3")


class Embedder(Protocol):
    """Minimal protocol: name + encode(list[str]) -> list of float vectors."""

    name: str

    def encode(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover
        ...


class NullEmbedder:
    """Two-channel fallback when the model is unavailable (documented deviation)."""

    name = "null"

    def encode(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("NullEmbedder cannot encode; use identifier+BM25 channels only")


class BgeM3Embedder:
    """bge-m3 via sentence-transformers, loaded from a local ModelScope download."""

    name = "bge-m3"

    def __init__(self, model_dir: str | Path | None = None) -> None:
        from sentence_transformers import SentenceTransformer  # lazy heavy import

        candidates: list[Path] = []
        if model_dir is not None:
            candidates.append(Path(model_dir))
        env_dir = os.environ.get("BUGLENS_EMBEDDER_PATH")
        if env_dir:
            candidates.append(Path(env_dir))
        candidates.append(DEFAULT_MODEL_DIR)
        for candidate in candidates:
            if (candidate / "config.json").exists():
                self._model = SentenceTransformer(str(candidate))
                break
        else:
            raise FileNotFoundError(
                f"bge-m3 not found in {[str(c) for c in candidates]}; "
                "download via modelscope (see manual/03-EXPERIMENTS EXP-05)"
            )

    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [[float(x) for x in vec] for vec in vectors]


def get_embedder(prefer_vectors: bool = True) -> Embedder | None:
    """Return bge-m3 when available locally, else None (two-channel mode).

    Catches broadly on purpose: any model-load failure (missing files, CVE
    torch.load gates, CUDA issues) must degrade to two-channel retrieval
    instead of crashing the pipeline (02-MANUAL class-D fallback).
    """
    if not prefer_vectors:
        return None
    try:
        return BgeM3Embedder()
    except Exception:  # noqa: BLE001 - documented fallback boundary
        return None
