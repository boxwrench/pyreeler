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

    # Rotation-invariant framing: center on the trajectory centroid and scale by
    # the max radius, so the attractor stays centered and fully on-screen at every
    # rotation angle (normalizing by un-rotated bounds would let it spin off-frame).
    flat = trajectory.reshape(-1, 3)
    centroid = flat.mean(axis=0)
    centered = flat - centroid
    # A Y-rotation can grow |x| up to sqrt(x^2 + z^2); y is left unchanged.
    radius_xz = float(np.sqrt(centered[:, 0] ** 2 + centered[:, 2] ** 2).max())
    radius_y = float(np.abs(centered[:, 1]).max())
    scale = max(radius_xz, radius_y, 1e-9)

    margin = max(2, int(round(0.06 * min(width, height))))
    span_x = width - 2 * margin
    span_y = height - 2 * margin

    center = int(frame_idx / total * (n_points - 1))
    start = max(0, center - trail)
    end = min(n_points, center + 1)

    buf = np.zeros((height, width), dtype=np.float32)
    for p in range(n_particles):
        pts = trajectory[start:end, p, :].copy()
        if pts.shape[0] == 0:
            continue
        pts = rotate_points(pts - centroid, angle_y=angle)
        nx = pts[:, 0] / scale * 0.5 + 0.5
        ny = pts[:, 1] / scale * 0.5 + 0.5
        x = (nx * span_x + margin).astype(int)
        y = (ny * span_y + margin).astype(int)
        weight = np.linspace(0.15, 1.0, pts.shape[0]).astype(np.float32)
        inside = (x >= 0) & (x < width) & (y >= 0) & (y < height)
        np.add.at(buf, (y[inside], x[inside]), weight[inside])

    peak = float(buf.max())
    if peak > 0:
        buf /= peak
        # Gamma lift: pull faint trail pixels up so the whole structure glows,
        # not just the bright head where recent points overlap.
        buf = buf ** 0.5
    rgb = (buf[..., None] * np.array(color, dtype=np.float32)).clip(0, 255).astype(np.uint8)
    return Image.fromarray(rgb, "RGB")
