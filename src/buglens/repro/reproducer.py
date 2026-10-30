"""Reproducer: capture one page under the fixed profile, artifact-first.

Every capture produces screenshot.png / dom.html / console.log / network.har
plus a dom sha256 so downstream steps can compare runs byte-wise (EXP-03).
"""

from __future__ import annotations

import hashlib
import json
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
    overlays: Path
    layout_checks: Path
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
            overlays = _collect_overlays(page)
            layout_checks = _collect_layout_checks(page)
            shot_path = run_dir / "screenshot.png"
            page.screenshot(path=str(shot_path), full_page=False)
            context.close()  # flushes the HAR
            browser.close()
        dom_path = run_dir / "dom.html"
        dom_path.write_text(dom_html, encoding="utf-8")
        console_path = run_dir / "console.log"
        console_path.write_text("\n".join(console_lines) + "\n", encoding="utf-8")
        overlays_path = run_dir / "overlays.json"
        overlays_path.write_text(
            json.dumps(overlays, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        layout_path = run_dir / "layout_checks.json"
        layout_path.write_text(
            json.dumps(layout_checks, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return ReproArtifacts(
            run_dir=run_dir,
            screenshot=shot_path,
            dom=dom_path,
            console=console_path,
            har=run_dir / "network.har",
            overlays=overlays_path,
            layout_checks=layout_path,
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


_OVERLAYS_JS = """
() => {
  const all = Array.from(document.querySelectorAll('*'));
  const out = [];
  for (const el of all) {
    const cs = getComputedStyle(el);
    if (cs.position !== 'fixed' && cs.position !== 'sticky') continue;
    const r = el.getBoundingClientRect();
    if (r.width < 40 || r.height < 20) continue;
    const covers = [];
    for (const other of all) {
      if (other === el || el.contains(other) || other.contains(el)) continue;
      const or = other.getBoundingClientRect();
      if (or.width < 10 || or.height < 4) continue;
      const ix = Math.max(0, Math.min(r.right, or.right) - Math.max(r.left, or.left));
      const iy = Math.max(0, Math.min(r.bottom, or.bottom) - Math.max(r.top, or.top));
      if (ix > or.width * 0.5 && iy > or.height * 0.5) {
        covers.push({
          tag: other.tagName.toLowerCase(),
          cls: String(other.className || '').slice(0, 60),
          text: (other.textContent || '').trim().slice(0, 30),
          rect: [Math.round(or.x), Math.round(or.y), Math.round(or.width), Math.round(or.height)],
        });
        if (covers.length >= 5) break;
      }
    }
    out.push({
      tag: el.tagName.toLowerCase(),
      cls: String(el.className || '').slice(0, 60),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      zIndex: cs.zIndex,
      covers,
    });
  }
  return out;
}
"""


_LAYOUT_JS = """
() => {
  const out = {overflow: [], misaligned: []};
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const r = el.getBoundingClientRect();
    if (r.width >= 40 && r.height >= 8 && el.scrollWidth > el.clientWidth + 2) {
      out.overflow.push({
        tag: el.tagName.toLowerCase(),
        cls: String(el.className || '').slice(0, 60),
        text: (el.textContent || '').trim().slice(0, 40),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        scrollWidth: el.scrollWidth,
        clientWidth: el.clientWidth,
      });
    }
  }
  const groups = new Map();
  for (const el of document.querySelectorAll('body *')) {
    const p = el.parentElement;
    if (!p) continue;
    const cls = String(el.className || '').trim().split(/\\s+/)[0];
    if (!cls || cls.startsWith('bug')) continue;
    const key = cls + '@' + p.tagName + ':' + String(p.className || '').trim().slice(0, 40);
    if (!groups.has(key)) groups.set(key, []);
    const r = el.getBoundingClientRect();
    if (r.width >= 60 && r.height >= 40) {
      groups.get(key).push({cls, top: Math.round(r.y), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]});
    }
  }
  for (const [key, members] of groups) {
    if (members.length < 3) continue;
    const tops = members.map(m => m.top);
    const spread = Math.max(...tops) - Math.min(...tops);
    if (spread > 24) out.misaligned.push({key, tops, spread, members: members.map(m => m.rect)});
  }
  return out;
}
"""


def _collect_layout_checks(page: Page) -> dict[str, object]:
    """DOM channel facts: horizontal overflow + sibling top misalignment."""
    result: object = page.evaluate(_LAYOUT_JS)
    return result if isinstance(result, dict) else {}


def _collect_overlays(page: Page) -> list[dict[str, object]]:
    """DOM channel facts for EXP-04: fixed/sticky overlays that can hide content."""
    result: object = page.evaluate(_OVERLAYS_JS)
    if not isinstance(result, list):
        return []
    return [entry for entry in result if isinstance(entry, dict)]


def _guard_local_only(route: Route, request: Request) -> None:
    """T10 spirit without Docker yet: block every non-loopback request."""
    host = urlparse(request.url).hostname or ""
    if host in ALLOWED_HOSTS:
        route.continue_()
    else:
        route.abort()
