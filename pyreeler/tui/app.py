"""Textual TUI: browse recipes, tune parameters, render — the phosphor front-end."""
from __future__ import annotations

from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button, Footer, Header, Input, Label, ListItem, ListView, ProgressBar, Sparkline,
    Static,
)

from ..recipes import get, list_recipes, merged_params, resolve_params, ParamError

RECIPE_PREFIX = "recipe-"


class PyReelerApp(App):
    """The PyReeler recipe browser + renderer."""

    CSS_PATH = "styles.tcss"
    TITLE = "PyReeler"
    BINDINGS = [Binding("escape", "quit", "Back", priority=True)]
    _current_name: str = ""

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
                yield Sparkline([], id="spark")
                yield Static("", id="status")
        yield Footer()

    async def on_mount(self) -> None:
        first = list_recipes()[0].name
        self.query_one("#recipe-list", ListView).index = 0
        await self._load_recipe(first)

    async def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        item = event.item
        if item is not None and item.id and item.id.startswith(RECIPE_PREFIX):
            name = item.id[len(RECIPE_PREFIX):]
            if name != self._current_name:
                await self._load_recipe(name)

    async def _load_recipe(self, name: str) -> None:
        recipe = get(name)
        self._current_name = name
        self.query_one("#summary", Static).update(recipe.summary)
        form = self.query_one("#form", Vertical)
        await form.remove_children()
        for p in merged_params(recipe):
            form.mount(Label(p.name, classes="param-label"))
            form.mount(Input(value=str(p.default), id=f"param-{p.name}"))
        self.query_one("#status", Static).update(
            f"output: {self._output_path(recipe.name)}"
        )

    def _collect_params(self) -> dict:
        """Read the form inputs into a validated params dict."""
        recipe = get(self._current_name)
        overrides = {}
        for p in merged_params(recipe):
            value = self.query_one(f"#param-{p.name}", Input).value.strip()
            if value:
                overrides[p.name] = value
        return resolve_params(recipe, overrides)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "render-btn":
            self._start_render()

    def _start_render(self) -> None:
        try:
            params = self._collect_params()
        except ParamError as exc:
            self.query_one("#status", Static).update(f"error: {exc}")
            return
        recipe = get(self._current_name)
        total = max(1, round(params["duration"] * params["fps"]))
        self.query_one("#progress", ProgressBar).update(total=total, progress=0)
        out = self._output_path(recipe.name)
        self.query_one("#status", Static).update(f"rendering to {out}...")
        self._render_worker(recipe, params, out)

    @work(thread=True, exclusive=True)
    def _render_worker(self, recipe, params, out) -> None:
        from ..engine import render_film

        def progress(done, total):
            self.call_from_thread(self._on_progress, done)

        try:
            render_film(recipe, params, out, on_progress=progress)
            self.call_from_thread(self._on_done, out)
        except Exception as exc:
            self.call_from_thread(self._on_error, exc)

    def _on_progress(self, done: int) -> None:
        self.query_one("#progress", ProgressBar).update(progress=done)
        spark = self.query_one("#spark", Sparkline)
        spark.data = list(spark.data or []) + [done]

    def _on_done(self, out) -> None:
        self.query_one("#status", Static).update(f"wrote {out}")

    def _on_error(self, exc) -> None:
        self.query_one("#status", Static).update(f"error: {exc}")

    def _output_path(self, recipe_name: str) -> Path:
        return Path(f"{recipe_name}.mp4").resolve()


def run() -> int:
    """Entry point used by the CLI's no-arg path: banner, then the app."""
    from .banner import render_banner

    render_banner()
    PyReelerApp().run()
    return 0
