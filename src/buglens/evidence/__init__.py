"""Evidence store: content-addressed, append-only (EXP-08, §9 evidence chain)."""

from buglens.evidence.store import EvidenceGapError, EvidenceStore

__all__ = ["EvidenceGapError", "EvidenceStore"]
