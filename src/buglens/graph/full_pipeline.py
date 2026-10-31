"""Full-pipeline orchestration: capture -> analyze -> loop -> report (EXP-09).

Assembly-level composition only — all logic lives in the agents/graph nodes.
The original dev server runs on `port`; the verifier's patched server uses
`port + 1` (never the same port).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from buglens.agents.visual_analyst import VisualAnalystInput
from buglens.agents.visual_analyst import run as visual_analyst_run
from buglens.graph.builder import PipelineDeps, PipelineState, build_pipeline
from buglens.models.base import BaseLLM, BaseVLM
from buglens.models.cache import FileCache
from buglens.models.glm import GLMProvider
from buglens.repro.launcher import DevServerLauncher
from buglens.repro.reproducer import Reproducer
from buglens.repo.embedder import get_embedder
from buglens.repo.indexer import build_index


@dataclass(frozen=True)
class FixOptions:
    repo: Path
    fragment: str = "#/"
    port: int = 5199
    out: Path = Path("temp/fix-run") / "run"
    vectors: bool = True
    dev_command: str = "npm run dev"


def run_fix(
    opts: FixOptions,
    vlm: BaseVLM | None = None,
    llm: BaseLLM | None = None,
) -> PipelineState:
    """One command end-to-end: capture, analyze, locate, fix, verify, report."""
    cache = FileCache(Path("temp/cache/vlm"))
    provider = vlm if vlm is not None else GLMProvider(cache=cache)
    text_llm = llm if llm is not None else GLMProvider(cache=cache)

    with DevServerLauncher(
        opts.repo, f"{opts.dev_command} -- --port {opts.port}", port=opts.port
    ) as server:
        capture = Reproducer(f"http://127.0.0.1:{opts.port}/{opts.fragment}").capture(
            opts.out / "capture"
        )
    va_out = visual_analyst_run(
        VisualAnalystInput(
            screenshot=capture.screenshot,
            overlays=capture.overlays,
            artifacts_dir=opts.out / "visual_analyst",
        ),
        provider,
    )

    embedder = get_embedder(opts.vectors)
    index = build_index(opts.repo, embedder=embedder, progress=lambda _m: None)
    deps = PipelineDeps(
        repo_dir=opts.repo,
        capture_dir=opts.out / "capture",
        url_fragment=opts.fragment,
        llm=text_llm,
        index=index,
        embedder=embedder,
        artifacts_root=opts.out / "loop",
        port=opts.port + 1,
    )
    app: Any = build_pipeline(deps)
    state: PipelineState = app.invoke(
        {"report": va_out.report, "evidence": list(va_out.evidence)}
    )
    return state
