"""Tests for contact_sheet.py — the parameter-sweep contact-sheet tool.

Tests use tiny synthetic render functions returning solid-color tiles, so they
are deterministic and need only Pillow/NumPy (already CI deps).
"""
import os
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from contact_sheet import _to_image  # noqa: E402


def test_to_image_accepts_numpy_uint8():
    arr = np.zeros((4, 6, 3), dtype=np.uint8)
    img = _to_image(arr, value=1)
    assert isinstance(img, Image.Image)
    assert img.size == (6, 4)  # PIL size is (width, height)


def test_to_image_accepts_pil():
    src = Image.new("RGB", (6, 4), (10, 20, 30))
    img = _to_image(src, value=1)
    assert isinstance(img, Image.Image)
    assert img.size == (6, 4)


def test_to_image_rejects_wrong_array_shape():
    arr = np.zeros((4, 6), dtype=np.uint8)  # missing channel axis
    with pytest.raises(TypeError):
        _to_image(arr, value=7)


def test_to_image_rejects_wrong_type():
    with pytest.raises(TypeError):
        _to_image("not an image", value=7)


from contact_sheet import sweep  # noqa: E402


def _solid(width=20, height=20):
    """Render factory: returns a render fn producing solid tiles colored by value.

    The value is expected to be an (r, g, b) tuple so each cell is distinct.
    """
    def render(value):
        arr = np.zeros((height, width, 3), dtype=np.uint8)
        arr[:, :] = value
        return arr
    return render


def test_default_grid_is_square_ish():
    render = lambda v: np.zeros((20, 30, 3), dtype=np.uint8)  # 30 wide, 20 tall
    sheet = sweep(render, "v", [1, 2, 3, 4], labels=False, pad=0)
    # n=4 -> cols=ceil(sqrt(4))=2, rows=2; cell 30x20 -> 60x40
    assert sheet.size == (60, 40)


def test_cols_override_changes_layout():
    render = lambda v: np.zeros((20, 30, 3), dtype=np.uint8)
    sheet = sweep(render, "v", [1, 2, 3, 4], cols=4, labels=False, pad=0)
    # cols=4, rows=1 -> 120x20
    assert sheet.size == (120, 20)


def test_each_value_lands_in_its_cell():
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    sheet = sweep(_solid(20, 20), "rgb", colors, cols=2, labels=False, pad=0)
    for i, color in enumerate(colors):
        r, c = divmod(i, 2)
        px = sheet.getpixel((c * 20 + 10, r * 20 + 10))  # cell center
        assert px == color


def test_accepts_pil_and_numpy_renders():
    arr_render = lambda v: np.full((20, 20, 3), 128, dtype=np.uint8)
    pil_render = lambda v: Image.new("RGB", (20, 20), (128, 128, 128))
    a = sweep(arr_render, "v", [1, 2], labels=False, pad=0)
    b = sweep(pil_render, "v", [1, 2], labels=False, pad=0)
    assert a.size == b.size


def test_empty_values_raises():
    with pytest.raises(ValueError):
        sweep(lambda v: np.zeros((2, 2, 3), np.uint8), "v", [])


def test_bad_cols_raises():
    with pytest.raises(ValueError):
        sweep(lambda v: np.zeros((2, 2, 3), np.uint8), "v", [1], cols=0)
