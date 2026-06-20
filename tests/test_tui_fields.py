"""Unit tests for the TUI param-control helpers and widgets."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("textual")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler.recipes.base import Param  # noqa: E402
from pyreeler.tui import fields  # noqa: E402


def test_effective_step_uses_explicit_step_when_set():
    p = Param("fps", int, 24, step=1)
    assert fields.effective_step(p) == 1


def test_effective_step_is_magnitude_aware_for_ints():
    assert fields.effective_step(Param("points", int, 10000)) == 500
    assert fields.effective_step(Param("width", int, 854)) == 40


def test_effective_step_is_magnitude_aware_for_floats():
    assert fields.effective_step(Param("rho", float, 28.0)) == pytest.approx(1.0)
    assert fields.effective_step(Param("a", float, 0.2)) == pytest.approx(0.01)


def test_effective_step_zero_default_falls_back():
    assert fields.effective_step(Param("z", int, 0)) == 1
    assert fields.effective_step(Param("z", float, 0.0)) == pytest.approx(0.1)
