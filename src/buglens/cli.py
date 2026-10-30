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


if __name__ == "__main__":
    app()
