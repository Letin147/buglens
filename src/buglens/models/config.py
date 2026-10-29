"""Project configuration: BUGLENS_* env vars with optional .env loading."""

from __future__ import annotations

import os
from pathlib import Path


def load_env(env_file: str | Path = ".env") -> None:
    """Load KEY=VALUE lines into os.environ without overriding existing values."""
    path = Path(env_file)
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def get_api_key(name: str) -> str:
    """Return the named BUGLENS_* key or raise an actionable error."""
    load_env()
    value = os.environ.get(name, "")
    if not value or value == "your-key-here":
        raise VLMKeyError(name)
    return value


class VLMKeyError(RuntimeError):
    def __init__(self, name: str) -> None:
        super().__init__(
            f"missing API key: set {name} in the environment or in a .env file "
            "(see .env.example)"
        )
