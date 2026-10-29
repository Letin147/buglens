"""Typed state models shared by agents; every claim carries its evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EvidenceKind = Literal[
    "screenshot", "dom", "overlays", "code_span", "diff", "render_diff", "test_run",
    "model_output",
]


class Evidence(BaseModel):
    """One verifiable artifact plus the claim it supports (§9 evidence chain)."""

    kind: EvidenceKind
    artifact: Path
    claim: str
    produced_by: str

    model_config = ConfigDict(frozen=True)


Severity = Literal["low", "mid", "high"]


class VisualReport(BaseModel):
    """Structured output of the visual_analyst agent (prompt-versioned)."""

    anomaly_region: list[float] = Field(min_length=4, max_length=4)
    symptom: str = Field(min_length=1)
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    prompt_version: str
    model: str

    model_config = ConfigDict(frozen=True)
