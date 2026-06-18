"""Tests for the recipe registry core (pyreeler.recipes.base)."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler.recipes import base  # noqa: E402


@pytest.fixture(autouse=True)
def _preserve_registry():
    """Snapshot and restore REGISTRY so per-test clear()s don't leak to other files."""
    saved = dict(base.REGISTRY)
    try:
        yield
    finally:
        base.REGISTRY.clear()
        base.REGISTRY.update(saved)


def _dummy_recipe(name="dummy"):
    return base.Recipe(
        name=name, summary="a test recipe", params=(),
        prepare=lambda params: None,
        make_frame=lambda prepared, params, i, total: None,
    )


def test_register_and_get_round_trip():
    base.REGISTRY.clear()
    r = _dummy_recipe("alpha")
    base.register(r)
    assert base.get("alpha") is r


def test_list_recipes_is_sorted_by_name():
    base.REGISTRY.clear()
    base.register(_dummy_recipe("zed"))
    base.register(_dummy_recipe("abe"))
    assert [r.name for r in base.list_recipes()] == ["abe", "zed"]


def test_get_unknown_raises_with_suggestion():
    base.REGISTRY.clear()
    base.register(_dummy_recipe("lorenz"))
    with pytest.raises(base.UnknownRecipeError) as exc:
        base.get("loranz")
    assert "lorenz" in str(exc.value)  # close-match suggestion


def test_standard_params_define_core_film_knobs():
    names = {p.name for p in base.STANDARD_PARAMS}
    assert {"duration", "fps", "width", "height", "palette"} <= names
    palette = next(p for p in base.STANDARD_PARAMS if p.name == "palette")
    assert set(palette.choices) == set(base.PALETTES)
