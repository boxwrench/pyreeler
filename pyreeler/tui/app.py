"""Textual TUI: browse recipes, tune parameters, render — the phosphor front-end."""
from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button, Footer, Header, Input, Label, ListItem, ListView, ProgressBar, Static,
)

from ..recipes import get, list_recipes, merged_params, resolve_params, ParamError

RECIPE_PREFIX = "recipe-"


class PyReelerApp(App):
    """The PyReeler recipe browser + renderer."""

    CSS_PATH = "styles.tcss"
    TITLE = "PyReeler"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            with Vertical(id="sidebar"):
                yield Label("RECIPES", classes="heading")
                yield ListView(
                    *[
                        ListItem(Label(r.name), id=f"{RECIPE_PREFIX}{r.name}")
                        for r in list_recipes()
                    ],
                    id="recipe-list",
                )
            with Vertical(id="detail"):
                yield Static("", id="summary")
                yield Vertical(id="form")
                yield Button("Render", id="render-btn", variant="success")
                yield ProgressBar(id="progress", total=100, show_eta=False)
                yield Static("", id="status")
        yield Footer()


def run() -> int:
    """Entry point used by the CLI's no-arg path."""
    PyReelerApp().run()
    return 0
