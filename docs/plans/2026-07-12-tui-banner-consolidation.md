# TUI Banner Consolidation

**Date:** 2026-07-12
**Status:** Complete

## Outcome

The polished non-AI TUI banner in `pyreeler/tui/banner.py` is the canonical
PYREELER terminal banner. Its appearance and behavior are unchanged:
TerminalTextEffects provides the animated reveal on a real TTY, and the static
phosphor ASCII logo remains the safe fallback.

`sync.py` now copies the packaged banner to `templates/tui/banner.py` before
copying canonical templates into the Claude and Codex skill distributions. This
keeps standalone tools and installed skills self-contained without maintaining
a second banner implementation.

## Guardrails

- The local TUI owns the canonical visual implementation.
- Provider distributions remain physical, self-contained copies.
- The existing template graduation and provider sync gates remain required.
- No new banner abstraction, runtime dependency, or visual redesign was added.

## Validation

Focused banner, sync, and graduation tests passed. The full suite and installed-
wheel smoke are required before commit.
