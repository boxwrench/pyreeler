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


def test_format_trims_float_noise():
    assert fields._format(28.0) == "28"
    assert fields._format(0.01) == "0.01"
    assert fields._format(10) == "10"


def test_stepped_value_increments_by_effective_step():
    p = Param("rho", float, 28.0)
    assert fields.stepped_value("28", p, +1) == "29"
    assert fields.stepped_value("28", p, -1) == "27"


def test_stepped_value_clamps_to_bounds():
    p = Param("duration", float, 30.0, min=1, step=1.0)
    assert fields.stepped_value("1", p, -1) == "1"  # min clamp


def test_stepped_value_recovers_from_unparseable_current():
    p = Param("fps", int, 24, min=1, step=1)
    # garbage current resets to default (24) then steps up
    assert fields.stepped_value("abc", p, +1) == "25"


def test_make_field_picks_the_right_widget():
    assert isinstance(fields.make_field(Param("palette", str, "phosphor",
                                              choices=("phosphor", "amber"))),
                      fields.ChoiceField)
    assert isinstance(fields.make_field(Param("rho", float, 28.0)),
                      fields.NumberField)
    assert isinstance(fields.make_field(Param("label", str, "hi")),
                      fields.TextField)


def test_choice_field_cycles_and_never_leaves_choices():
    p = Param("palette", str, "amber", choices=("phosphor", "amber", "ice"))
    f = fields.ChoiceField(p)
    assert f.param_value == "amber"
    f.cycle(1)
    assert f.param_value == "ice"
    f.cycle(1)  # wraps
    assert f.param_value == "phosphor"
    f.cycle(-1)  # wraps backward
    assert f.param_value == "ice"
    assert f.param_value in p.choices


def test_number_field_bump_steps_and_clamps():
    # Textual's Input cannot exist outside an app, so mount one NumberField in a
    # tiny harness app and drive it through a pilot.
    import asyncio
    from textual.app import App, ComposeResult
    from textual.widgets import Input

    class _Harness(App):
        def compose(self) -> ComposeResult:
            yield fields.NumberField(Param("duration", float, 30.0, min=1, step=1.0))

    async def body():
        app = _Harness()
        async with app.run_test() as pilot:
            await pilot.pause()
            field = app.query_one(fields.NumberField)
            assert field.param_value == "30"
            field._bump(-1)
            assert field.param_value == "29"
            app.query_one(Input).value = "1"
            field._bump(-1)  # clamped at min
            assert field.param_value == "1"

    asyncio.run(body())
