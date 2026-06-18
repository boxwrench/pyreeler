from .base import (  # noqa: F401
    Param, Recipe, PALETTES, STANDARD_PARAMS, REGISTRY,
    register, get, list_recipes, UnknownRecipeError,
)
from .params import merged_params, resolve_params, ParamError  # noqa: F401
from . import lorenz, rossler  # noqa: F401,E402  (import-time registration)
