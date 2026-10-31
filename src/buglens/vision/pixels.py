"""Pixel channel: how much did the anomaly region change after the patch?"""

from __future__ import annotations

from pathlib import Path


def region_change_ratio(
    before_png: Path, after_png: Path, region: list[float], tolerance: int = 12
) -> float:
    """Fraction of pixels inside `region` that changed beyond `tolerance`.

    0.0 = identical rendering (suspicious: the patch changed nothing);
    1.0 = every pixel in the region changed. Grayscale, per-pixel max-channel
    delta compared against tolerance to ignore antialiasing jitter.
    """
    import numpy as np
    from PIL import Image

    x, y, w, h = (int(v) for v in region)
    before = np.asarray(Image.open(before_png).convert("RGB"), dtype=np.int16)
    after = np.asarray(Image.open(after_png).convert("RGB"), dtype=np.int16)
    if before.shape != after.shape:
        return 1.0  # layout dimensions changed drastically: counts as change
    x2, y2 = max(0, x), max(0, y)
    w, h = max(0, min(w, before.shape[1] - x2)), max(0, min(h, before.shape[0] - y2))
    if w == 0 or h == 0:
        return 0.0
    window_b = before[y2 : y2 + h, x2 : x2 + w]
    window_a = after[y2 : y2 + h, x2 : x2 + w]
    delta = np.abs(window_b - window_a).max(axis=2)
    return float((delta > tolerance).mean())
