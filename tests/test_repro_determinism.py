"""EXP-03 acceptance: golden-1 reproduces deterministically.

Run count is controlled by BUGLENS_REPRO_RUNS (default 3 for quick checks,
10 for the EXP-03 acceptance run). Skipped when golden-1 deps are absent
(e.g. fresh CI) so the fast suite stays green.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from buglens.repro.launcher import DevServerLauncher
from buglens.repro.reproducer import Reproducer

GOLDEN1 = Path(__file__).resolve().parents[1] / "examples" / "golden-1"
RUNS = int(os.environ.get("BUGLENS_REPRO_RUNS", "3"))
PAGE = "#/bug1"

pytestmark = pytest.mark.skipif(
    not (GOLDEN1 / "node_modules").exists(),
    reason="golden-1 deps missing: run `npm install` in examples/golden-1",
)


def _block_ssim(a_png: Path, b_png: Path) -> float:
    """Block SSIM (7x7 windows, stride 8) on grayscale; a determinism gate,
    not a perceptual study. 1.0 = identical."""
    import numpy as np
    from PIL import Image

    a = np.asarray(Image.open(a_png).convert("L"), dtype=np.float64)
    b = np.asarray(Image.open(b_png).convert("L"), dtype=np.float64)
    c1, c2 = (0.01 * 255.0) ** 2, (0.03 * 255.0) ** 2
    win, stride = 7, 8
    scores: list[float] = []
    for y in range(0, a.shape[0] - win, stride):
        for x in range(0, a.shape[1] - win, stride):
            wa = a[y : y + win, x : x + win]
            wb = b[y : y + win, x : x + win]
            va, vb = wa.var(), wb.var()
            cov = ((wa - wa.mean()) * (wb - wb.mean())).mean()
            denom = (wa.mean() ** 2 + wb.mean() ** 2 + c1) * (va + vb + c2)
            scores.append(((2 * wa.mean() * wb.mean() + c1) * (2 * cov + c2)) / denom)
    return sum(scores) / len(scores)


def test_golden1_deterministic(tmp_path: Path) -> None:
    out_root = Path("temp/exp03").resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    results = []
    for run in range(1, RUNS + 1):
        with DevServerLauncher(GOLDEN1, "npm run dev") as server:
            repro = Reproducer(f"{server.url}{PAGE}")
            art = repro.capture(out_root / f"run-{run:02d}")
        results.append(art)
        print(
            f"run {run:02d}: dom={art.dom_sha256[:12]} "
            f"capture={art.elapsed_s:.1f}s server={server.start_elapsed_s:.1f}s"
        )

    hashes = {r.dom_sha256 for r in results}
    assert len(hashes) == 1, f"DOM is not deterministic across {RUNS} runs: {hashes}"

    base = results[0]
    for run, art in enumerate(results[1:], start=2):
        ssim = _block_ssim(base.screenshot, art.screenshot)
        print(f"ssim(run1 vs run{run}) = {ssim:.6f}")
        assert ssim >= 0.999, f"run {run} screenshot drifted (SSIM {ssim:.6f})"

    assert max(r.elapsed_s for r in results) < 180.0, "single capture exceeded 3 minutes"
