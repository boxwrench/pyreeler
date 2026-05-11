"""Terminal-style text narration timeline.

A TextTrack owns a fixed script of timed lines and exposes:
- typed_text(line, t)          how much of a line has been typed by time t
- visible_at(t, max_lines)     the most recent N lines that have started
- isolated_visible_at(t)       a single isolated 'punchline' line, if active
- keystroke_events()           list of times where command-line keystrokes fire
                               (useful for audio sync — e.g. soft click samples
                               on each '$' line)

The script is a list of (start_t_seconds, text). Lines starting with '$' are
treated as command lines (cyan / keystroke-emitting); others are responses.
Mark a line as `isolated=True` to render it separately (e.g. a final '$ exit'
that pops centered after the main block has faded).

This template covers the structure. Color, font, layout, and fade are choices
of the calling renderer.
"""
from __future__ import annotations

from dataclasses import dataclass


DEFAULT_TYPING_CPS = 30.0


@dataclass
class TextLine:
    start_t: float
    text: str
    is_command: bool
    isolated: bool = False


class TextTrack:
    """Timeline of lines with per-character typing.

    Parameters
    ----------
    script : list of (float, str) or list of (float, str, bool)
        Two-tuple form: (start_t, text). Three-tuple form adds `isolated` flag.
        Any line whose stripped text starts with "$" is treated as a command.
    typing_cps : float
        Characters per second for the typewriter reveal.
    """

    def __init__(self, script: list, typing_cps: float = DEFAULT_TYPING_CPS) -> None:
        self.typing_cps = typing_cps
        self.timeline: list[TextLine] = []
        for row in script:
            if len(row) == 2:
                start_t, text = row
                isolated = False
            else:
                start_t, text, isolated = row
            is_cmd = text.lstrip().startswith("$")
            self.timeline.append(TextLine(float(start_t), text, is_cmd, isolated))

    def typed_text(self, line: TextLine, t: float) -> str:
        """How much of `line.text` has been typed at time t."""
        if t <= line.start_t:
            return ""
        chars = int((t - line.start_t) * self.typing_cps)
        return line.text[:chars]

    def visible_at(self, t: float, max_lines: int = 10) -> list[TextLine]:
        """Return the most recent up-to-`max_lines` non-isolated lines that
        have started by time `t`, oldest-first."""
        started = [l for l in self.timeline
                   if l.start_t <= t and not l.isolated]
        return started[-max_lines:]

    def isolated_visible_at(self, t: float, hold_seconds: float = 1.5) -> TextLine | None:
        """Return the isolated line whose window contains `t`, or None.

        Isolated lines are considered active for `hold_seconds` after their
        start. The renderer is responsible for placement and styling.
        """
        for line in self.timeline:
            if line.isolated and line.start_t <= t <= line.start_t + hold_seconds:
                return line
        return None

    def keystroke_events(self) -> list[float]:
        """Times where a keystroke click should fire (one per command line)."""
        return [l.start_t for l in self.timeline if l.is_command]
