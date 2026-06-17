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
