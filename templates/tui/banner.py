"""Reusable phosphor PYREELER launch banner for terminal-facing tools.

Tries TerminalTextEffects for an animated reveal when attached to a real terminal;
always falls back to a static ASCII logo so it is safe in captured output, CI, and
plain terminals without optional TUI dependencies.
"""
from __future__ import annotations

import sys
import time

PHOSPHOR = "\x1b[38;2;57;255;20m"
RESET = "\x1b[0m"

ASCII_LOGO = r"""
 ____  __   __ ____  _____ _____ _     _____ ____
|  _ \ \ \ / /|  _ \| ____| ____| |   | ____|  _ \
| |_) | \ V / | |_) |  _| |  _| | |   |  _| | |_) |
|  __/   | |  |  _ <| |___| |___| |___| |___|  _ <
|_|      |_|  |_| \_\_____|_____|_____|_____|_| \_\
         code-generated cinema, conjured from math
"""


def _tint(text: str) -> str:
    """Phosphor-green truecolor if writing to a terminal, else plain."""
    if sys.stdout.isatty():
        return f"{PHOSPHOR}{text}{RESET}"
    return text


def render_banner(
    text: str = "PYREELER", *, animate: bool = True, hold_seconds: float = 2.0
) -> str:
    """Play the launch banner; return the static ASCII logo string.

    Animated reveal (TerminalTextEffects) only runs on a real TTY; any version
    mismatch or absence falls back to the static phosphor logo. Always safe.
    """
    if animate and sys.stdout.isatty():
        try:
            from terminaltexteffects.effects.effect_beams import Beams

            effect = Beams(ASCII_LOGO)
            with effect.terminal_output() as terminal:
                for frame in effect:
                    terminal.print(frame)
            time.sleep(hold_seconds)
            return ASCII_LOGO
        except Exception:
            pass
    sys.stdout.write(_tint(ASCII_LOGO.rstrip("\n")) + "\n")
    sys.stdout.flush()
    if animate and sys.stdout.isatty():
        time.sleep(hold_seconds)
    return ASCII_LOGO
