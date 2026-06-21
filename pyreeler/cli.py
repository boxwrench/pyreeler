"""Command-line interface: `pyreeler list` / `pyreeler render` / (no args -> TUI)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .recipes import (
    get, list_recipes, merged_params, resolve_params,
    UnknownRecipeError, ParamError,
)
from .engine import render_film
from .output import next_output_path


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return _launch_tui()
    command = argv[0]
    if command == "list":
        return _cmd_list()
    if command == "info":
        return _cmd_info(argv[1:])
    if command == "render":
        return _cmd_render(argv[1:])
    # Unknown command: let argparse produce a helpful usage/error.
    _build_parser().parse_args(argv)
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pyreeler", description="Make code-generated films from recipes.")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("list", help="list available recipes")
    info = sub.add_parser("info", help="show information about a recipe")
    info.add_argument("recipe", help="recipe name (see `pyreeler list`)")
    render = sub.add_parser("render", help="render a recipe to an mp4")
    render.add_argument("recipe", help="recipe name (see `pyreeler list`)")
    render.add_argument("-o", "--out", default=None, help="output path")
    return parser


def _cmd_list() -> int:
    for recipe in list_recipes():
        print(f"{recipe.name:12} {recipe.summary}")
    return 0


def _cmd_info(args: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="pyreeler info")
    parser.add_argument("recipe")
    namespace = parser.parse_args(args)
    try:
        recipe = get(namespace.recipe)
    except UnknownRecipeError as exc:
        print(exc, file=sys.stderr)
        return 2

    print(f"Recipe: {recipe.name}")
    print(f"Summary: {recipe.summary}")
    if getattr(recipe, "description", None):
        print(f"\n{recipe.description}")
    print("\nParameters:")
    schema = merged_params(recipe)
    for p in schema:
        print(f"  --{p.name:10} {p.help} (default: {p.default})")
    return 0


def _cmd_render(args: list[str]) -> int:
    # Stage 1: pull out the recipe name (and -o) so we know which flags exist.
    pre = argparse.ArgumentParser(prog="pyreeler render", add_help=False)
    pre.add_argument("recipe")
    pre.add_argument("-o", "--out", default=None)
    known, _ = pre.parse_known_args(args)
    try:
        recipe = get(known.recipe)
    except UnknownRecipeError as exc:
        print(exc, file=sys.stderr)
        return 2

    # Stage 2: build the real parser with this recipe's generated flags.
    schema = merged_params(recipe)
    parser = argparse.ArgumentParser(prog=f"pyreeler render {recipe.name}")
    parser.add_argument("recipe")
    parser.add_argument("-o", "--out", default=None)
    for p in schema:
        parser.add_argument(f"--{p.name}", default=None,
                            help=f"{p.help} (default {p.default})")
    namespace = parser.parse_args(args)

    overrides = {p.name: getattr(namespace, p.name)
                 for p in schema
                 if getattr(namespace, p.name) is not None}
    try:
        params = resolve_params(recipe, overrides)
    except ParamError as exc:
        print(exc, file=sys.stderr)
        return 2

    # Explicit -o is honored verbatim (scriptable, may overwrite). With no -o we
    # default to ~/Videos with a name that never clobbers an earlier render —
    # the same destination and policy the TUI uses (pyreeler.output).
    if namespace.out:
        out = Path(namespace.out)
    else:
        out = next_output_path(recipe.name)
        out.parent.mkdir(parents=True, exist_ok=True)

    def progress(done, total):
        print(f"\rframe {done}/{total}", end="", file=sys.stderr, flush=True)

    try:
        render_film(recipe, params, out, on_progress=progress)
    except (RuntimeError, OSError) as exc:
        print(f"\nrender failed: {exc}", file=sys.stderr)
        return 1
    print(f"\nwrote {out}", file=sys.stderr)
    return 0


def _launch_tui() -> int:
    try:
        from .tui.app import run as run_tui
    except ImportError:
        print("The PyReeler TUI needs extra packages. Install them with:\n"
              "    pip install -r requirements-tui.txt", file=sys.stderr)
        return 1
    return run_tui()
