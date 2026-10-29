"""Fixed reproduction profile: every capture runs under identical conditions."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ReproProfile(BaseModel):
    """All knobs that influence rendering must be pinned here (EXP-03 card)."""

    viewport_width: int = 1280
    viewport_height: int = 800
    device_scale_factor: float = 1.0
    timezone_id: str = "Asia/Shanghai"
    locale: str = "zh-CN"
    reduced_motion: bool = True
    disable_animations_css: bool = True
    settle_ms: int = 800
    network_idle_timeout_ms: int = 5000
    navigation_timeout_ms: int = 30_000

    model_config = ConfigDict(frozen=True)
