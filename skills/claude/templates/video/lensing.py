"""Gravitational-lensing displacement on a 2D RGBA layer.

Pure-numpy implementation of a Schwarzschild-style radial warp. Given a
base RGBA image (e.g. a rendered starfield) and one or more lens centers
in screen coordinates, this returns a warped copy where pixels near each
lens center are pulled inward, mimicking a black hole bending light around
itself.

This is intentionally light: a few hundred milliseconds per frame at
1280x720 on a modern CPU. Use it as the headline effect of a piece, not
applied to every layer.
"""
from __future__ import annotations

import numpy as np
from PIL import Image


def apply_lensing(layer: Image.Image,
                  lens_centers: list,
                  K: float,
                  k_scale: float = 4000.0,
                  max_pull: float = 0.95) -> Image.Image:
    """Warp `layer` by accumulating radial displacement around each lens center.

    Parameters
    ----------
    layer : PIL.Image.Image
        Source RGBA layer to warp. Returned unchanged when K == 0 or no centers.
    lens_centers : list of (cx, cy, strength)
        Screen-space lens centers. `strength` in [0, 1] is a per-lens weight
        (e.g. the cube face's camera-facing-ness). Multiple centers compose
        additively in screen-space displacement.
    K : float
        Global lens strength curve (typically driven by an arc_state timeline,
        in [0, 1]).
    k_scale : float
        Pixel-area constant. Default 4000 means roughly a ~30 px event-horizon
        radius at K=0.5. Raise to widen the warp, lower to tighten it.
    max_pull : float
        Cap on the scale factor so we don't fold pixels through the singularity.

    Returns
    -------
    PIL.Image.Image
        Same size and mode as `layer`. Bilinear-resampled.
    """
    if K <= 0.0 or not lens_centers:
        return layer.copy()

    src = np.array(layer, dtype=np.float32)
    h, w = src.shape[:2]

    yy, xx = np.meshgrid(np.arange(h, dtype=np.float32),
                         np.arange(w, dtype=np.float32),
                         indexing="ij")
    sum_dx = np.zeros_like(xx)
    sum_dy = np.zeros_like(yy)

    for cx, cy, strength in lens_centers:
        dx = xx - cx
        dy = yy - cy
        r2 = dx * dx + dy * dy + 1.0  # +1 epsilon avoids singularity at center
        k_eff = K * strength * k_scale
        scale = np.minimum(k_eff / r2, max_pull)
        sum_dx -= scale * dx
        sum_dy -= scale * dy

    src_x = xx + sum_dx
    src_y = yy + sum_dy

    # Bilinear sample, clipped to image bounds.
    x0 = np.floor(src_x).astype(np.int32)
    y0 = np.floor(src_y).astype(np.int32)
    x1 = x0 + 1
    y1 = y0 + 1
    fx = src_x - x0
    fy = src_y - y0
    x0 = np.clip(x0, 0, w - 1)
    x1 = np.clip(x1, 0, w - 1)
    y0 = np.clip(y0, 0, h - 1)
    y1 = np.clip(y1, 0, h - 1)

    out = np.zeros_like(src)
    for c in range(src.shape[2]):
        ch = src[..., c]
        out[..., c] = (
            ch[y0, x0] * (1 - fx) * (1 - fy) +
            ch[y0, x1] *      fx  * (1 - fy) +
            ch[y1, x0] * (1 - fx) *      fy  +
            ch[y1, x1] *      fx  *      fy
        )
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), mode=layer.mode)
