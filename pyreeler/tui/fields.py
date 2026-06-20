"""Param-control widgets for the TUI form, plus the pure stepper helpers.

Each Param renders as a ParamField exposing a uniform `param_value` string that
feeds the existing `resolve_params` validation. Numeric params get +/- steppers,
enum params get a cycler, free strings keep a plain Input.
"""
from __future__ import annotations

import math

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Input, Label, Static

from ..recipes.base import Param


def _round_1sf(x: float) -> float:
    """Round to one significant figure (1.4 -> 1, 0.014 -> 0.01, 530 -> 500)."""
    if x == 0:
        return 0.0
    exp = math.floor(math.log10(abs(x)))
    factor = 10 ** exp
    return round(x / factor) * factor


def effective_step(param: Param):
    """The stepper increment for `param`: its explicit `step`, else a
    magnitude-aware ~5%-of-default value rounded to one significant figure."""
    if param.step is not None:
        return param.step
    default = param.default
    is_int = param.type is int
    if not default:  # 0, 0.0, or None
        return 1 if is_int else 0.1
    nice = _round_1sf(0.05 * abs(default))
    if is_int:
        return max(1, int(round(nice)))
    return max(nice, 1e-9)


def _format(value) -> str:
    """Render a number without trailing-zero noise (28.0 -> '28')."""
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".") or "0"
    return str(value)


def stepped_value(current: str, param: Param, delta: int) -> str:
    """Apply `delta * effective_step` to `current`, clamp to bounds, format.

    `delta` is +1 or -1. An unparseable `current` resets to the param default
    before stepping, so the control can never get wedged.
    """
    step = effective_step(param)
    try:
        value = param.type(current)
    except (TypeError, ValueError):
        value = param.default
    value = value + delta * step
    if param.min is not None and value < param.min:
        value = param.min
    if param.max is not None and value > param.max:
        value = param.max
    return _format(param.type(value))


class ParamField(Horizontal):
    """One param row. Subclasses expose the current value as a string."""

    def __init__(self, param: Param) -> None:
        super().__init__(id=f"field-{param.name}", classes="param-field")
        self.param = param

    @property
    def param_value(self) -> str:
        raise NotImplementedError


class TextField(ParamField):
    """Free-text / optional param: a plain Input (today's behavior).

    Note: Textual's Input cannot be constructed outside an app, so it is created
    in compose() and read through `query_one(Input)` rather than cached.
    """

    def __init__(self, param: Param) -> None:
        super().__init__(param)
        self._default = "" if param.default is None else str(param.default)

    def compose(self) -> ComposeResult:
        yield Label(self.param.name, classes="param-label")
        yield Input(value=self._default, id=f"param-{self.param.name}")

    @property
    def param_value(self) -> str:
        return self.query_one(Input).value


class ChoiceField(ParamField):
    """Enum param: a `< value >` cycler that can never hold an invalid value."""

    def __init__(self, param: Param) -> None:
        super().__init__(param)
        self._choices = list(param.choices)
        try:
            self._index = self._choices.index(param.default)
        except ValueError:
            self._index = 0
        self._value = Static(self.param_value, id=f"choice-{param.name}",
                             classes="choice-value")

    @property
    def param_value(self) -> str:
        return str(self._choices[self._index])

    def cycle(self, delta: int) -> None:
        self._index = (self._index + delta) % len(self._choices)
        if self.is_mounted:
            self._value.update(self.param_value)

    def compose(self) -> ComposeResult:
        yield Label(self.param.name, classes="param-label")
        yield Button("‹", id=f"prev-{self.param.name}", classes="cycle-btn")
        yield self._value
        yield Button("›", id=f"next-{self.param.name}", classes="cycle-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == f"prev-{self.param.name}":
            self.cycle(-1)
            event.stop()
        elif event.button.id == f"next-{self.param.name}":
            self.cycle(1)
            event.stop()


class NumberField(ParamField):
    """Numeric param: [-] Input [+]. Typing is still allowed.

    Input is created in compose() (Textual forbids it outside an app) and read
    through `query_one(Input)`, so the displayed value is always the source of
    truth — no cached copy to drift.
    """

    def __init__(self, param: Param) -> None:
        super().__init__(param)
        self._default = _format(param.default)

    def compose(self) -> ComposeResult:
        yield Label(self.param.name, classes="param-label")
        yield Button("-", id=f"dec-{self.param.name}", classes="step-btn")
        yield Input(value=self._default, id=f"param-{self.param.name}")
        yield Button("+", id=f"inc-{self.param.name}", classes="step-btn")

    @property
    def param_value(self) -> str:
        return self.query_one(Input).value

    def _bump(self, delta: int) -> None:
        inp = self.query_one(Input)
        inp.value = stepped_value(inp.value, self.param, delta)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == f"dec-{self.param.name}":
            self._bump(-1)
            event.stop()
        elif event.button.id == f"inc-{self.param.name}":
            self._bump(1)
            event.stop()


def make_field(param: Param) -> ParamField:
    """Pick the control widget for a param: cycler for enums, stepper for
    numbers, plain input otherwise."""
    if param.choices:
        return ChoiceField(param)
    if param.type in (int, float) and param.default is not None:
        return NumberField(param)
    return TextField(param)
