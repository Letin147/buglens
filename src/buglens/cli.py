"""BugLens command-line interface."""

from pathlib import Path

import typer

from buglens import __version__

app = typer.Typer(
    name="buglens",
    help=(
        "From a UI bug screenshot to a mergeable fix PR — "
        "evidence-chained multimodal bug-fixing agents."
    ),
    no_args_is_help=True,
    add_completion=False,
)

index_app = typer.Typer(help="Repository index management (EXP-05).")
app.add_typer(index_app, name="index")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"buglens {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """BugLens — see it, reproduce it, fix it, prove it."""


@index_app.command("init")
def index_init(
    repo: Path = typer.Argument(..., exists=True, file_okay=False, help="Repository root"),
    vectors: bool = typer.Option(
        True, "--vectors/--no-vectors", help="Use the bge-m3 vector channel when available"
    ),
) -> None:
    """Slice, index and persist a repository under <repo>/.buglens/."""
    from buglens.repo.embedder import get_embedder
    from buglens.repo.indexer import build_index

    built = build_index(repo, embedder=get_embedder(vectors))
    typer.echo(
        f"indexed {len(built.slices)} slices "
        f"(embedder={built.embedder_name or 'none'}), saved under {repo / '.buglens'}"
    )


@app.command("fix")
def fix_cmd(
    repo: Path = typer.Argument(..., exists=True, file_okay=False, help="Repository root"),
    fragment: str = typer.Option("#/", "--fragment", help="URL fragment of the defect page"),
    port: int = typer.Option(5199, "--port", help="Port for the original dev server"),
    out: Path = typer.Option(
        Path("temp/fix-run") / "run", "--out", help="Working directory for artifacts"
    ),
    vectors: bool = typer.Option(
        True, "--vectors/--no-vectors", help="Use the bge-m3 vector channel when available"
    ),
) -> None:
    """End-to-end: capture, analyze, locate, fix, verify, and report (EXP-09)."""
    from buglens.graph.full_pipeline import FixOptions, run_fix
    from buglens.models.base import VLMError

    try:
        state = run_fix(FixOptions(repo=repo, fragment=fragment, port=port, out=out,
                                   vectors=vectors))
    except VLMError as exc:  # quota/network degradation: exit cleanly, never crash
        typer.secho(f"模型服务不可用（已按降级策略终止）：{exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    verdict = state.get("verdict")
    if state.get("passed") and state.get("report_path") is not None:
        typer.secho("PASS — 修复通过四通道可执行验证", fg=typer.colors.GREEN)
        typer.echo(f"报告：{state['report_path']}")
    else:
        typer.secho("FAIL — 未在重试上限内通过验证", fg=typer.colors.YELLOW)
        if state.get("error"):
            typer.echo(f"原因：{state['error']}")
    if verdict is not None:
        for name, detail in verdict.channels.items():
            typer.echo(f"  {name}: {detail}")
    for note in state.get("failure_notes", [])[-3:]:
        typer.echo(f"  · {note}")
    if not state.get("passed"):
        raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
