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


class Hypothesis(BaseModel):
    """One root-cause hypothesis from the planner (EXP-06)."""

    id: str = Field(min_length=1)
    root_cause: str = Field(min_length=1)
    fix_plan: str = Field(min_length=1)
    target_path: str = Field(min_length=1)
    line_hint: int | None = None
    expected_visual_change: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=True)


class Patch(BaseModel):
    """A validated minimal patch produced by the fixer (EXP-06)."""

    hypothesis_id: str
    target_path: str
    diff_path: Path
    worktree_path: Path
    edit_count: int = Field(ge=1)

    model_config = ConfigDict(frozen=True)
