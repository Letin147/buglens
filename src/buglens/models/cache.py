"""Content-addressed response cache: identical (image, prompt) never re-billed."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from buglens.models.base import VLMResponse


class FileCache:
    """Flat-file cache under a root dir; keys are sha256(image_bytes + prompt)."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, key: str) -> Path:
        return self.root / f"{key}.json"

    def _key(self, image: Path, prompt: str) -> str:
        digest = hashlib.sha256()
        digest.update(image.read_bytes())
        digest.update(prompt.encode("utf-8"))
        return digest.hexdigest()[:32]

    def get(self, image: Path, prompt: str) -> VLMResponse | None:
        path = self._path(self._key(image, prompt))
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        response = VLMResponse(**data)
        return VLMResponse(
            text=response.text,
            elapsed_s=response.elapsed_s,
            total_tokens=response.total_tokens,
            cached=True,
        )

    def put(self, image: Path, prompt: str, response: VLMResponse) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        fresh = VLMResponse(
            text=response.text,
            elapsed_s=response.elapsed_s,
            total_tokens=response.total_tokens,
            cached=False,
        )
        payload = json.dumps(asdict(fresh), ensure_ascii=False, indent=2)
        self._path(self._key(image, prompt)).write_text(payload, encoding="utf-8")

    # text-only entries (planner/fixer prompts have no image)

    def _text_path(self, prompt: str) -> Path:
        key = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:32]
        return self.root / f"text-{key}.json"

    def get_text(self, prompt: str) -> VLMResponse | None:
        path = self._text_path(prompt)
        if not path.exists():
            return None
        response = VLMResponse(**json.loads(path.read_text(encoding="utf-8")))
        return VLMResponse(
            text=response.text,
            elapsed_s=response.elapsed_s,
            total_tokens=response.total_tokens,
            cached=True,
        )

    def put_text(self, prompt: str, response: VLMResponse) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        fresh = VLMResponse(
            text=response.text,
            elapsed_s=response.elapsed_s,
            total_tokens=response.total_tokens,
            cached=False,
        )
        self._text_path(prompt).write_text(
            json.dumps(asdict(fresh), ensure_ascii=False, indent=2), encoding="utf-8"
        )
