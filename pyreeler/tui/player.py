"""Open a rendered file in the OS default player. Pure stdlib, no Textual."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def open_in_player(path: Path) -> None:
    """Open `path` in the system default player.

    Uses `os.startfile` on Windows, `open` on macOS, `xdg-open` elsewhere.
    Launches detached so it never blocks the UI thread. Raises `OSError` if the
    opener is missing or fails.
    """
    path = Path(path)
    if sys.platform == "win32":
        os.startfile(str(path))  # type: ignore[attr-defined]  # noqa: S606
        return
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([opener, str(path)],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
