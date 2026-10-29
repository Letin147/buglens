"""Tests for the BugLens CLI skeleton."""

from typer.testing import CliRunner

from buglens import __version__
from buglens.cli import app

runner = CliRunner()


def test_help_shows_name_and_usage() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "buglens" in result.output.lower()
    assert "screenshot" in result.output.lower()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output
