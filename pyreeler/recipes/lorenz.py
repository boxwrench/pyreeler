"""Lorenz strange attractor recipe."""
from __future__ import annotations

from experimental.tools.attractors import generate_lorenz

from .base import Param, Recipe, PALETTES, register
from ._plot import scatter_trail

PARAMS = (
    Param("sigma", float, 10.0, help="Lorenz sigma"),
    Param("rho", float, 28.0, help="Lorenz rho"),
    Param("beta", float, 8 / 3, help="Lorenz beta"),
    Param("points", int, 10000, min=100, help="trajectory integration steps"),
    Param("trail", int, 10000, min=1, help="trail length in points (>=points shows the whole attractor)"),
)


def _prepare(params):
    return generate_lorenz(
        n_points=params["points"], n_particles=1,
        sigma=params["sigma"], rho=params["rho"], beta=params["beta"],
    )


def _make_frame(prepared, params, frame_idx, total):
    return scatter_trail(
        prepared, frame_idx, total,
        params["width"], params["height"], params["trail"],
        PALETTES[params["palette"]],
    )


RECIPE = register(Recipe(
    name="lorenz",
    summary="Lorenz strange attractor — the iconic butterfly.",
    params=PARAMS, prepare=_prepare, make_frame=_make_frame,
))
