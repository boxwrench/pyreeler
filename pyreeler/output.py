"""Where rendered films land, and how they avoid clobbering each other.

Both the CLI (no ``-o``) and the TUI write to ``~/Videos`` by default and pick a
name that never overwrites an earlier render. Keeping that logic in one place
means the two front-ends can't drift apart.
"""
from __future__ import annotations

from pathlib import Path


def videos_dir() -> Path:
    """The default destination for rendered films."""
    return Path.home() / "Videos"


def next_output_path(recipe_name: str, out_dir: Path | None = None) -> Path:
    """Return the next free ``<recipe>.mp4`` under ``out_dir`` (default ~/Videos).

    Read-only: this probes ``.exists()`` but creates nothing, so it is safe to
    call for status display. It walks ``lorenz.mp4`` -> ``lorenz-2.mp4`` ->
    ``lorenz-3.mp4`` ... so a new render never overwrites an earlier one.
    """
    out_dir = out_dir or videos_dir()
    candidate = out_dir / f"{recipe_name}.mp4"
    n = 2
    while candidate.exists():
        candidate = out_dir / f"{recipe_name}-{n}.mp4"
        n += 1
    return candidate
