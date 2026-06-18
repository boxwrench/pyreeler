"""Render a rotating, fading attractor trail into a single-color frame."""
from __future__ import annotations

import numpy as np
from PIL import Image

from experimental.tools.attractors import rotate_points


def scatter_trail(trajectory, frame_idx, total, width, height, trail, color):
    """Plot the trail window ending at this frame, rotated and color-tinted.

    Args:
        trajectory: array of shape (n_points, n_particles, 3).
        frame_idx, total: position in the animation (drives window + rotation).
        width, height: output size in pixels.
        trail: number of trailing points to draw.
        color: (r, g, b) tint for the accumulated intensity.

    Returns:
        An (width x height) RGB PIL.Image.
    """
    n_points, n_particles, _ = trajectory.shape
    total = max(1, total)
    angle = 2 * np.pi * frame_idx / total

    mins = trajectory.min(axis=(0, 1))
    maxs = trajectory.max(axis=(0, 1))
    ranges = maxs - mins
    ranges[ranges == 0] = 1.0

    center = int(frame_idx / total * (n_points - 1))
    start = max(0, center - trail)
    end = min(n_points, center + 1)

    buf = np.zeros((height, width), dtype=np.float32)
    for p in range(n_particles):
        pts = trajectory[start:end, p, :].copy()
        if pts.shape[0] == 0:
            continue
        pts = rotate_points(pts, angle_y=angle)
        pts = (pts - mins) / ranges
        x = (pts[:, 0] * (width - 100) + 50).astype(int)
        y = (pts[:, 1] * (height - 100) + 50).astype(int)
        weight = np.linspace(0.15, 1.0, pts.shape[0]).astype(np.float32)
        inside = (x >= 0) & (x < width) & (y >= 0) & (y < height)
        np.add.at(buf, (y[inside], x[inside]), weight[inside])

    peak = float(buf.max())
    if peak > 0:
        buf /= peak
    rgb = (buf[..., None] * np.array(color, dtype=np.float32)).clip(0, 255).astype(np.uint8)
    return Image.fromarray(rgb, "RGB")
