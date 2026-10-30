"""Three retrieval channels over a RepoIndex: identifier, BM25, vector."""

from __future__ import annotations

from buglens.repo.embedder import Embedder
from buglens.repo.indexer import RepoIndex, tokenize

_RRF_K = 60


def identifier_search(index: RepoIndex, query_tokens: list[str], top_k: int = 20) -> list[int]:
    """Channel 1: token overlap between query terms and slice identifiers.

    Query terms are re-tokenized first: DOM class names arrive hyphenated
    ("spec-card") while slice identifiers are split tokens ("spec", "card") —
    found via the EXP-05 real run (bug2 miss), not by fixtures.
    """
    wanted = set(tokenize(" ".join(query_tokens)))
    scores: list[tuple[int, int]] = []
    for i, code_slice in enumerate(index.slices):
        have = {t.lower() for t in code_slice.identifier_tokens}
        overlap = len(wanted & have)
        if overlap > 0:
            scores.append((overlap, i))
    scores.sort(reverse=True)
    return [i for _, i in scores[:top_k]]


def bm25_search(index: RepoIndex, query_text: str, top_k: int = 20) -> list[int]:
    """Channel 2: lexical BM25 over slice text."""
    if index.bm25 is None:
        return []
    scores = index.bm25.get_scores(tokenize(query_text))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return [i for i in ranked if scores[i] > 0][:top_k]


def vector_search(
    index: RepoIndex,
    query_text: str,
    embedder: Embedder,
    index_vectors: list[list[float]],
    top_k: int = 20,
) -> list[int]:
    """Channel 3: cosine similarity (vectors are L2-normalized at encode time)."""
    if not index_vectors:
        return []
    query_vec = embedder.encode([query_text[:2000]])[0]
    sims = []
    for i, vec in enumerate(index_vectors):
        dot = sum(a * b for a, b in zip(query_vec, vec))
        sims.append(dot)
    ranked = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)
    return ranked[:top_k]


def rrf_fuse(rankings: dict[str, list[int]], top_k: int = 5) -> list[tuple[int, float, list[str]]]:
    """Reciprocal-rank fusion across channels -> (slice_idx, score, channels)."""
    fused: dict[int, float] = {}
    channels_of: dict[int, set[str]] = {}
    for channel, ranking in rankings.items():
        for rank, slice_idx in enumerate(ranking, start=1):
            fused[slice_idx] = fused.get(slice_idx, 0.0) + 1.0 / (_RRF_K + rank)
            channels_of.setdefault(slice_idx, set()).add(channel)
    ordered = sorted(fused.items(), key=lambda item: item[1], reverse=True)[:top_k]
    return [(idx, score, sorted(channels_of[idx])) for idx, score in ordered]


def normalized_score(raw: float) -> float:
    """Map an RRF score of a typical 3-channel hit into a 0..1 confidence."""
    return max(0.0, min(1.0, raw / (3.0 / _RRF_K))) if raw > 0 else 0.0
