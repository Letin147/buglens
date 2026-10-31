"""Serve a patched copy of a repository: originals untouched (EXP-07).

Copies the source tree (ignoring node_modules/.buglens/dist), links
node_modules via a Windows junction (no admin rights needed), then launches
the dev server on a caller-chosen port so the patched page can be re-captured.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from buglens.repro.launcher import DevServerLauncher

_IGNORE = shutil.ignore_patterns("node_modules", ".buglens", "dist", ".git")


def prepare_patched_repo(repo_dir: Path, worktree_dir: Path, dest: Path) -> Path:
    """Copy repo sources into dest, overlay patched files, link node_modules."""
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(repo_dir, dest, ignore=_IGNORE)
    # overlay every patched file from the fixer worktree
    for patched in sorted(worktree_dir.rglob("*")):
        if patched.is_file():
            rel = patched.relative_to(worktree_dir)
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(patched, target)
    node_modules = repo_dir / "node_modules"
    if node_modules.exists() and not (dest / "node_modules").exists():
        _junction(dest / "node_modules", node_modules)
    return dest


def patched_server(dest: Path, port: int) -> DevServerLauncher:
    """Launcher for the patched copy; vite overrides the config port via CLI."""
    return DevServerLauncher(dest, f"npm run dev -- --port {port}", port=port)


def _junction(link: Path, target: Path) -> None:
    if sys.platform == "win32":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            check=True,
            capture_output=True,
        )
    else:
        link.symlink_to(target, target_is_directory=True)
