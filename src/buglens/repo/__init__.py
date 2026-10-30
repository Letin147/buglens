"""Repo indexing: TS/TSX tree-sitter slices + CSS rule slices (EXP-05)."""

from buglens.repo.embedder import Embedder, get_embedder
from buglens.repo.indexer import CodeSlice, RepoIndex, build_index, load_index
from buglens.repo.search import bm25_search, identifier_search, vector_search

__all__ = [
    "CodeSlice",
    "Embedder",
    "RepoIndex",
    "bm25_search",
    "build_index",
    "get_embedder",
    "identifier_search",
    "load_index",
    "vector_search",
]
