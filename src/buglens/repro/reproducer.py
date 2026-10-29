"""Reproducer: capture one page under the fixed profile, artifact-first.

Every capture produces screenshot.png / dom.html / console.log / network.har
plus a dom sha256 so downstream steps can compare runs byte-wise (EXP-03).
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import (
    Browser,
    BrowserContext,
    ConsoleMessage,
    Page,
    Request,
    Route,
    sync_playwright,
)
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from buglens.repro.profile import ReproProfile

NO_ANIMATION_CSS = (
    "*, *::before, *::after { animation: none !important; "
    "transition: none !important; scroll-behavior: auto !important; "
    "caret-color: transparent !important; }"
)

ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


@dataclass(frozen=True)
class ReproArtifacts:
    run_dir: Path
    screenshot: Path
    dom: Path
    console: Path
    har: Path
    dom_sha256: str
    elapsed_s: float


class Reproducer:
    """Capture a live URL deterministically; server lifecycle is caller's job."""

    def __init__(self, url: str, profile: ReproProfile | None = None) -> None:
        self.url = url
        self.profile = profile if profile is not None else ReproProfile()

    def capture(self, run_dir: Path) -> ReproArtifacts:
        run_dir.mkdir(parents=True, exist_ok=True)
        t0 = time.monotonic()
        console_lines: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = self._new_context(browser, har_path=run_dir / "network.har")
            page = context.new_page()
            page.on("console", lambda msg: console_lines.append(_fmt_console(msg)))
            page.goto(self.url, wait_until="load", timeout=self.profile.navigation_timeout_ms)
            self._wait_network_settled(page)
            if self.profile.disable_animations_css:
                page.add_style_tag(content=NO_ANIMATION_CSS)
            page.wait_for_timeout(self.profile.settle_ms)
            dom_html = page.content()
            shot_path = run_dir / "screenshot.png"
            page.screenshot(path=str(shot_path), full_page=False)
            context.close()  # flushes the HAR
            browser.close()
        dom_path = run_dir / "dom.html"
        dom_path.write_text(dom_html, encoding="utf-8")
        console_path = run_dir / "console.log"
        console_path.write_text("\n".join(console_lines) + "\n", encoding="utf-8")
        return ReproArtifacts(
            run_dir=run_dir,
            screenshot=shot_path,
            dom=dom_path,
            console=console_path,
            har=run_dir / "network.har",
            dom_sha256=hashlib.sha256(dom_html.encode("utf-8")).hexdigest(),
            elapsed_s=time.monotonic() - t0,
        )

    def _new_context(self, browser: Browser, har_path: Path) -> BrowserContext:
        context = browser.new_context(
            viewport={
                "width": self.profile.viewport_width,
                "height": self.profile.viewport_height,
            },
            device_scale_factor=self.profile.device_scale_factor,
            timezone_id=self.profile.timezone_id,
            locale=self.profile.locale,
            reduced_motion="reduce" if self.profile.reduced_motion else "no-preference",
            record_har_path=str(har_path),
        )
        context.route("**/*", _guard_local_only)
        return context

    def _wait_network_settled(self, page: Page) -> None:
        try:
            page.wait_for_load_state(
                "networkidle", timeout=self.profile.network_idle_timeout_ms
            )
        except PlaywrightTimeoutError:
            # Dev-server websockets (HMR) keep the network busy; the fixed
            # settle time after this is the actual determinism anchor.
            pass


def _fmt_console(msg: ConsoleMessage) -> str:
    return f"[{msg.type}] {msg.text}"


def _guard_local_only(route: Route, request: Request) -> None:
    """T10 spirit without Docker yet: block every non-loopback request."""
    host = urlparse(request.url).hostname or ""
    if host in ALLOWED_HOSTS:
        route.continue_()
    else:
        route.abort()
