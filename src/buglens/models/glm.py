"""GLM vision provider (Zhipu BigModel v4 chat completions, OpenAI-style body)."""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from buglens.models.base import BaseLLM, BaseVLM, VLMError, VLMResponse
from buglens.models.cache import FileCache
from buglens.models.config import get_api_key

ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-4.6v-flash"
DEFAULT_TIMEOUT_S = 180.0


class GLMProvider(BaseVLM, BaseLLM):
    """Primary free-tier provider; 429s are retried with linear backoff."""

    def __init__(
        self,
        cache: FileCache | None = None,
        model: str = DEFAULT_MODEL,
        retries: int = 3,
        retry_wait_s: float = 30.0,
    ) -> None:
        super().__init__(cache=cache)
        self.model = model
        self.name = model
        self.retries = retries
        self.retry_wait_s = retry_wait_s

    def complete_vision(self, image: Path, prompt: str) -> VLMResponse:
        if isinstance(self.cache, FileCache):
            hit = self.cache.get(image, prompt)
            if hit is not None:
                return hit
        response = self._call_with_retry(_vision_body(image, prompt))
        if isinstance(self.cache, FileCache):
            self.cache.put(image, prompt, response)
        return response

    def complete_text(self, prompt: str) -> VLMResponse:
        if isinstance(self.cache, FileCache):
            hit = self.cache.get_text(prompt)
            if hit is not None:
                return hit
        response = self._call_with_retry(_text_body(prompt))
        if isinstance(self.cache, FileCache):
            self.cache.put_text(prompt, response)
        return response

    def _call_with_retry(self, body: dict[str, Any]) -> VLMResponse:
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                return self._call(body)
            except _RateLimited as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(self.retry_wait_s * attempt)
        raise VLMError(f"GLM rate-limited after {self.retries} attempts") from last_error

    def _call(self, body: dict[str, Any]) -> VLMResponse:
        api_key = get_api_key("BUGLENS_GLM_API_KEY")
        request = urllib.request.Request(  # noqa: S310 - fixed https endpoint
            ENDPOINT,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_S) as resp:  # noqa: S310
                data = json.load(resp)
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise _RateLimited("429") from exc
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise VLMError(f"GLM HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise VLMError(f"GLM network error: {exc}") from exc
        elapsed = time.monotonic() - started
        try:
            content = data["choices"][0]["message"]["content"]
            tokens = int(data.get("usage", {}).get("total_tokens", 0))
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise VLMError(f"unexpected GLM response shape: {str(data)[:200]}") from exc
        if not isinstance(content, str) or not content.strip():
            raise VLMError("GLM returned empty content")
        return VLMResponse(text=content, elapsed_s=elapsed, total_tokens=tokens)


class _RateLimited(Exception):
    """Internal signal so retries stay inside the provider."""


def _data_url(image: Path) -> str:
    encoded = base64.b64encode(image.read_bytes()).decode()
    return f"data:image/png;base64,{encoded}"


def _vision_body(image: Path, prompt: str) -> dict[str, Any]:
    return {
        "model": DEFAULT_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": _data_url(image)}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }


def _text_body(prompt: str) -> dict[str, Any]:
    return {
        "model": DEFAULT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
