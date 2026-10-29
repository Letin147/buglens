"""BugLens command-line interface."""

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


if __name__ == "__main__":
    app()
