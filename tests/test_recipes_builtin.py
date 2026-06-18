"""Tests for the built-in lorenz and rossler recipes."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pyreeler.recipes as recipes  # noqa: E402


def test_both_recipes_registered():
    names = {r.name for r in recipes.list_recipes()}
    assert {"lorenz", "rossler"} <= names


def test_lorenz_make_frame_is_correct_size_and_moves():
    r = recipes.get("lorenz")
    params = recipes.resolve_params(r, {"points": 1500, "width": 200, "height": 200})
    prepared = r.prepare(params)
    f0 = r.make_frame(prepared, params, 0, 10)
    f5 = r.make_frame(prepared, params, 5, 10)
    assert isinstance(f0, Image.Image) and f0.size == (200, 200)
    assert np.asarray(f0).tobytes() != np.asarray(f5).tobytes()


def test_rossler_prepare_returns_trajectory():
    r = recipes.get("rossler")
    params = recipes.resolve_params(r, {"points": 1200})
    prepared = r.prepare(params)
    assert prepared.shape[0] == 1200 and prepared.shape[2] == 3


def test_rossler_make_frame_is_correct_size_and_moves():
    r = recipes.get("rossler")
    params = recipes.resolve_params(r, {"points": 1500, "width": 200, "height": 200})
    prepared = r.prepare(params)
    f0 = r.make_frame(prepared, params, 0, 10)
    f5 = r.make_frame(prepared, params, 5, 10)
    assert isinstance(f0, Image.Image) and f0.size == (200, 200)
    assert np.asarray(f0).tobytes() != np.asarray(f5).tobytes()
