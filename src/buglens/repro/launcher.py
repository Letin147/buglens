"""Launch and stop a local dev server for reproduction.

The Docker sandbox for untrusted third-party repos arrives with EXP-10
(delivery/github_action); golden cases are first-party trusted code, so a
local subprocess is acceptable for now (deviation recorded in REPORT-001).
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path


class DevServerLauncher:
    """Context manager: start a dev server and wait until its port answers."""

    def __init__(
        self,
        repo_dir: Path,
        command: str,
        host: str = "127.0.0.1",
        port: int = 5173,
        readiness_timeout_s: float = 90.0,
    ) -> None:
        self.repo_dir = repo_dir
        self.command = command
        self.host = host
        self.port = port
        self.readiness_timeout_s = readiness_timeout_s
        self._proc: subprocess.Popen[bytes] | None = None
        self.start_elapsed_s: float = 0.0

    def __enter__(self) -> DevServerLauncher:
        self.start()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.stop()

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/"

    def start(self) -> None:
        if self._port_ready():
            raise RuntimeError(
                f"port {self.port} already listening — a stale dev server would silently "
                "poison reproduction semantics; kill it first"
            )
        t0 = time.monotonic()
        self._proc = subprocess.Popen(  # noqa: S602 - command comes from project config
            self.command,
            cwd=str(self.repo_dir),
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = t0 + self.readiness_timeout_s
        while time.monotonic() < deadline:
            if self._proc.poll() is not None:
                raise RuntimeError(
                    f"dev server exited early with code {self._proc.returncode}: {self.command!r}"
                )
            if self._port_ready():
                self.start_elapsed_s = time.monotonic() - t0
                return
            time.sleep(0.5)
        self.stop()
        raise TimeoutError(f"dev server not ready within {self.readiness_timeout_s}s: {self.url}")

    def stop(self) -> None:
        proc = self._proc
        if proc is not None and proc.poll() is None:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                    check=False,
                    capture_output=True,
                )
            else:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
        self._proc = None
        for _ in range(20):
            if not self._port_ready():
                return
            time.sleep(0.5)
        raise RuntimeError(f"port {self.port} still listening after stop() — leaked dev server")

    def _port_ready(self) -> bool:
        try:
            with socket.create_connection((self.host, self.port), timeout=1.0):
                return True
        except OSError:
            return False
