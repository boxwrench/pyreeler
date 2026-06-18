"""Tests for the shared attractor plotter."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler.recipes._plot import scatter_trail  # noqa: E402


def _spiral(n=2000):
    """A simple non-degenerate trajectory of shape (n, 1, 3)."""
    t = np.linspace(0, 8 * np.pi, n)
    xyz = np.stack([np.cos(t) * t, np.sin(t) * t, t], axis=1)
    return xyz[:, None, :]  # (n, 1, 3)


def test_returns_image_of_requested_size():
    img = scatter_trail(_spiral(), 5, 10, 200, 150, trail=400, color=(57, 255, 20))
    assert isinstance(img, Image.Image)
    assert img.size == (200, 150)  # (width, height)


def test_distinct_frames_differ():
    traj = _spiral()
    a = scatter_trail(traj, 1, 10, 200, 200, trail=400, color=(57, 255, 20))
    b = scatter_trail(traj, 6, 10, 200, 200, trail=400, color=(57, 255, 20))
    assert np.asarray(a).tobytes() != np.asarray(b).tobytes()


def test_color_channels_follow_palette():
    # A green palette must not paint blue.
    img = scatter_trail(_spiral(), 6, 10, 200, 200, trail=400, color=(57, 255, 20))
    arr = np.asarray(img)
    assert arr[..., 2].max() <= arr[..., 1].max()  # blue <= green
