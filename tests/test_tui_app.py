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
