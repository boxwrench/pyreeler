"""Phosphor PYREELER launch banner for the TUI.

Tries TerminalTextEffects for an animated reveal when attached to a real terminal;
always falls back to a static phosphor ASCII logo so it works (and tests) anywhere.
"""
from __future__ import annotations

import sys

PHOSPHOR = "\x1b[38;2;57;255;20m"
RESET = "\x1b[0m"

ASCII_LOGO = r"""
 ____  _   _ ____  _____ _____ _     _____ ____
|  _ \| | | |  _ \| ____| ____| |   | ____|  _ \
| |_) | | | | |_) |  _| |  _| | |   |  _| | |_) |
|  __/| |_| |  _ <| |___| |___| |___| |___|  _ <
|_|    \___/|_| \_\_____|_____|_____|_____|_| \_\
         code-generated cinema, conjured from math
"""


def _tint(text: str) -> str:
    """Phosphor-green truecolor if writing to a terminal, else plain."""
    if sys.stdout.isatty():
        return f"{PHOSPHOR}{text}{RESET}"
    return text


def render_banner(text: str = "PYREELER", *, animate: bool = True) -> str:
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
            return ASCII_LOGO
        except Exception:
            pass  # any TTE/version problem -> fall through to the static logo
    sys.stdout.write(_tint(ASCII_LOGO.rstrip("\n")) + "\n")
    sys.stdout.flush()
    return ASCII_LOGO
