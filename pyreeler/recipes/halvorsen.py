"""Halvorsen attractor recipe."""
from __future__ import annotations

from experimental.tools.attractors import generate_halvorsen

from .base import Param, Recipe, PALETTES, register
from ._plot import scatter_trail

PARAMS = (
    Param("a", float, 1.89, help="Halvorsen a parameter"),
    Param("points", int, 10000, min=100, help="trajectory integration steps"),
    Param("trail", int, 10000, min=1, help="trail length in points (>=points shows the whole attractor)"),
)


def _prepare(params):
    return generate_halvorsen(
        n_points=params["points"], n_particles=1,
        a=params["a"],
    )


def _make_frame(prepared, params, frame_idx, total):
    return scatter_trail(
        prepared, frame_idx, total,
        params["width"], params["height"], params["trail"],
        PALETTES[params["palette"]],
        thickness=params["thickness"],
    )


RECIPE = register(Recipe(
    name="halvorsen",
    summary="Halvorsen strange attractor.",
    description=(
        "The Halvorsen attractor is a cyclically symmetric 3D strange attractor. "
        "It exhibits complex chaotic dynamics and features three intersecting lobes "
        "reminiscent of a three-leaf clover in its phase space."
    ),
    params=PARAMS, prepare=_prepare, make_frame=_make_frame,
))
