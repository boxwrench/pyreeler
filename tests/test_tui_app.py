"""Tests for the Textual TUI app. Skipped entirely when textual is not installed
(so the numpy+pillow CI stays green). Async pilots are driven via asyncio.run."""
import asyncio
import sys
from pathlib import Path

import pytest

pytest.importorskip("textual")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler.tui.app import PyReelerApp  # noqa: E402


def test_app_mounts_and_lists_recipes():
    async def body():
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import ListView
            lst = app.query_one("#recipe-list", ListView)
            # one ListItem per registered recipe; lorenz + rossler present
            ids = [item.id for item in lst.query("ListItem")]
            assert "recipe-lorenz" in ids
            assert "recipe-rossler" in ids
    asyncio.run(body())


def test_escape_is_bound_as_back_out_key():
    bindings = PyReelerApp.BINDINGS
    assert any(binding.key == "escape" and binding.action == "quit" for binding in bindings)


def test_selecting_recipe_populates_summary_and_form():
    async def body():
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import Input, Static
            from pyreeler.tui.fields import ParamField, ChoiceField
            assert app.query_one("#summary", Static).content
            assert "output:" in str(app.query_one("#status", Static).content)
            from pyreeler.recipes import get, merged_params
            recipe = get(app._current_name)
            # one ParamField per merged param
            assert len(app.query(ParamField)) == len(merged_params(recipe))
            # rho is a numeric field whose inner Input keeps id param-rho
            rho = app.query_one("#param-rho", Input)
            assert rho.value == "28"
            # palette is a cycler, not an Input
            assert isinstance(app.query_one("#field-palette", ParamField), ChoiceField)
    asyncio.run(body())


def test_collect_params_reads_form_values():
    async def body():
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import Input
            app.query_one("#param-rho", Input).value = "30"
            app.query_one("#param-duration", Input).value = "2"
            params = app._collect_params()
            assert params["rho"] == 30.0
            assert params["duration"] == 2.0
    asyncio.run(body())


def test_output_path_targets_videos_and_never_overwrites(tmp_path, monkeypatch):
    # Path.home() resolves via $HOME on POSIX, so we can sandbox the dir.
    monkeypatch.setenv("HOME", str(tmp_path))
    videos = tmp_path / "Videos"
    videos.mkdir()
    app = PyReelerApp()
    # clean slate -> the plain base name under ~/Videos
    assert app._output_path("lorenz") == videos / "lorenz.mp4"
    # _output_path is read-only: probing must not create the file
    assert not (videos / "lorenz.mp4").exists()
    # once names are taken, it walks to the next free suffix instead of clobbering
    (videos / "lorenz.mp4").touch()
    assert app._output_path("lorenz") == videos / "lorenz-2.mp4"
    (videos / "lorenz-2.mp4").touch()
    assert app._output_path("lorenz") == videos / "lorenz-3.mp4"


def test_bad_numeric_param_shows_error_in_status():
    async def body():
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import Input, Static
            app.query_one("#param-rho", Input).value = "not-a-number"
            app._start_render()  # invalid -> should set status, not raise
            await pilot.pause()
            status = str(app.query_one("#status", Static).content)
            assert "rho" in status
    asyncio.run(body())


def test_search_filters_recipe_list():
    async def body():
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import ListView
            await app._apply_filter("ross")
            ids = [item.id for item in app.query_one("#recipe-list", ListView).query("ListItem")]
            assert ids == ["recipe-rossler"]
            await app._apply_filter("")  # cleared -> all back
            ids = [item.id for item in app.query_one("#recipe-list", ListView).query("ListItem")]
            assert "recipe-lorenz" in ids and "recipe-rossler" in ids
    asyncio.run(body())


def test_play_enables_after_render_and_opens_file(monkeypatch, tmp_path):
    async def body():
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import Button
            # play disabled until a render completes
            assert app.query_one("#play-btn", Button).disabled is True
            out = tmp_path / "lorenz.mp4"
            out.write_bytes(b"x")
            app._on_done(out)  # simulate a finished render
            await pilot.pause()
            assert app.query_one("#play-btn", Button).disabled is False
            opened = {}
            import pyreeler.tui.app as appmod
            monkeypatch.setattr(appmod, "open_in_player",
                                lambda p: opened.update(path=p))
            app.action_play()
            assert opened["path"] == out
    asyncio.run(body())


def test_play_with_no_render_shows_hint(monkeypatch):
    async def body():
        import pyreeler.tui.app as appmod
        called = {}
        monkeypatch.setattr(appmod, "open_in_player",
                            lambda p: called.update(path=p))
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import Static
            app.action_play()
            await pilot.pause()
            status = str(app.query_one("#status", Static).content)
            assert "nothing to play yet" in status
            assert "path" not in called
    asyncio.run(body())


def test_play_surfaces_open_error(monkeypatch, tmp_path):
    async def body():
        import pyreeler.tui.app as appmod
        monkeypatch.setattr(appmod, "open_in_player",
                            lambda p: (_ for _ in ()).throw(OSError("boom")))
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import Static
            out = tmp_path / "lorenz.mp4"
            out.write_bytes(b"x")
            app._last_output = out
            app.action_play()
            await pilot.pause()
            status = str(app.query_one("#status", Static).content)
            assert "cannot open" in status
    asyncio.run(body())
