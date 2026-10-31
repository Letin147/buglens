"""LangGraph assembly: locator -> planner -> fixer -> verifier with retry loop.

EXP-07 scope: verifier fail and retries < 3 loops back to the planner with
the oracle's failure notes; pass (or exhausted retries / hard error) ends.
intake/reproducer/critic/reporter join in EXP-08 per the roadmap.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, TypedDict

from langgraph.graph import END, START, StateGraph

from buglens.agents.fixer import EditNotUniqueError, FixerInput
from buglens.agents.fixer import run as fixer_run
from buglens.agents.locator.run import LocatorInput
from buglens.agents.locator.run import run as locator_run
from buglens.agents.planner import PlannerInput
from buglens.agents.planner import run as planner_run
from buglens.agents.verifier.run import Verdict, VerifyInput, VerifyOutput
from buglens.agents.verifier.run import run as verify_run
from buglens.graph.state import Evidence, Hypothesis, Patch, VisualReport
from buglens.models.base import BaseLLM, VLMError
from buglens.repo.embedder import Embedder
from buglens.repo.indexer import RepoIndex

MAX_RETRIES = 3  # S04


class PipelineState(TypedDict, total=False):
    report: VisualReport
    candidates: list[Any]
    hypotheses: list[Hypothesis]
    patch: Patch | None
    verdict: Verdict | None
    passed: bool
    retries: int
    failure_notes: list[str]
    tried_summary: str
    evidence: list[Evidence]
    error: str


@dataclass(frozen=True)
class PipelineDeps:
    repo_dir: Path
    capture_dir: Path
    url_fragment: str
    llm: BaseLLM
    index: RepoIndex | None = None
    embedder: Embedder | None = None
    artifacts_root: Path = Path("temp/pipeline")
    port: int = 5574
    verify_fn: Callable[[VerifyInput], VerifyOutput] | None = None


def build_pipeline(deps: PipelineDeps) -> Any:
    """Compile the graph; `verify_fn` is injectable for loop tests."""

    def locator_node(state: PipelineState) -> PipelineState:
        if deps.index is None:
            return state  # candidates pre-seeded (tests / pre-indexed runs)
        out = locator_run(
            LocatorInput(
                report=state["report"],
                repo_dir=deps.repo_dir,
                dom_path=deps.capture_dir / "dom.html",
                overlays_path=deps.capture_dir / "overlays.json",
                embedder=deps.embedder,
            ),
            deps.index,
            deps.index.vectors,
        )
        return {**state, "candidates": out.candidates, "evidence": _merge(state, out.evidence)}

    def planner_node(state: PipelineState) -> PipelineState:
        try:
            out = planner_run(
                PlannerInput(
                    report=state["report"],
                    candidates=state["candidates"],
                    console_path=deps.capture_dir / "console.log",
                    artifacts_dir=deps.artifacts_root / "planner",
                    failure_notes=state.get("failure_notes", []),
                    tried_summary=state.get("tried_summary", ""),
                ),
                deps.llm,
            )
        except VLMError as exc:
            return {**state, "error": f"planner: {exc}"}
        tried = state.get("tried_summary", "")
        for h in out.hypotheses:
            tried += f"- [{h.id}] {h.fix_plan}（target={h.target_path}）\n"
        return {**state, "hypotheses": out.hypotheses, "tried_summary": tried,
                "evidence": _merge(state, out.evidence)}

    def fixer_node(state: PipelineState) -> PipelineState:
        hypotheses = state.get("hypotheses") or []
        retries = state.get("retries", 0)
        if not hypotheses:
            # planner errored (e.g. quota) or produced nothing usable
            return {**state, "passed": False, "patch": None,
                    "error": state.get("error") or "planner produced no hypotheses"}
        hypothesis = hypotheses[min(retries, len(hypotheses) - 1)]
        try:
            out = fixer_run(
                FixerInput(
                    hypothesis=hypothesis,
                    repo_dir=deps.repo_dir,
                    worktree_dir=deps.artifacts_root / "worktree" / f"try{retries}",
                    artifacts_dir=deps.artifacts_root / f"try{retries}",
                ),
                deps.llm,
            )
        except (VLMError, EditNotUniqueError) as exc:
            notes = list(state.get("failure_notes", []))
            notes.append(f"修复生成失败：{exc}")
            # clear the stale patch: the verifier must never re-judge an old one
            return {**state, "patch": None, "failure_notes": notes, "passed": False}
        return {**state, "patch": out.patch, "evidence": _merge(state, out.evidence)}

    def verifier_node(state: PipelineState) -> PipelineState:
        retries = state.get("retries", 0)
        patch = state.get("patch")
        if patch is None:
            return {**state, "passed": False}  # fixer failed; loop with notes
        inp = VerifyInput(
            report=state["report"],
            patch=patch,
            repo_dir=deps.repo_dir,
            capture_dir=deps.capture_dir,
            url_fragment=deps.url_fragment,
            run_dir=deps.artifacts_root / f"try{retries}",
            port=deps.port,
        )
        out = (deps.verify_fn or verify_run)(inp)
        notes = list(state.get("failure_notes", [])) + list(out.verdict.failure_notes)
        return {
            **state,
            "passed": out.verdict.passed,
            "verdict": out.verdict,
            "failure_notes": notes if not out.verdict.passed else [],
            "evidence": _merge(state, out.evidence),
        }

    def route_after_verifier(state: PipelineState) -> str:
        if state.get("error") or state.get("passed"):
            return "end"
        if state.get("retries", 0) + 1 >= MAX_RETRIES:
            return "end"
        return "retry"

    def retry_node(state: PipelineState) -> PipelineState:
        return {**state, "retries": state.get("retries", 0) + 1}

    graph = StateGraph(PipelineState)
    graph.add_node("locator", locator_node)
    graph.add_node("planner", planner_node)
    graph.add_node("fixer", fixer_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("retry", retry_node)
    graph.add_edge(START, "locator")
    graph.add_edge("locator", "planner")
    graph.add_edge("planner", "fixer")
    graph.add_edge("fixer", "verifier")
    graph.add_conditional_edges("verifier", route_after_verifier, {"retry": "retry", "end": END})
    graph.add_edge("retry", "planner")
    return graph.compile()


def _merge(state: PipelineState, new: list[Evidence]) -> list[Evidence]:
    return list(state.get("evidence", [])) + new


__all__ = ["MAX_RETRIES", "PipelineDeps", "PipelineState", "build_pipeline"]
