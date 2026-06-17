#!/usr/bin/env python3
"""Template graduation manifest checker.

Task 1 only loads the manifest into typed records. Validation and CLI behavior
land in the next task from the implementation plan.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import tomllib


@dataclass(frozen=True)
class TemplateEntry:
    """One `[[template]]` declaration from template_graduation.toml."""

    path: str
    kind: str
    status: str
    tests: list[str]
    examples: list[str]
    notes: str


def load_manifest(path: Path) -> list[TemplateEntry]:
    """Load template graduation entries from a TOML manifest."""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    raw_entries = data.get("template", [])
    return [_entry_from_mapping(entry) for entry in raw_entries]


def _entry_from_mapping(entry: dict[str, Any]) -> TemplateEntry:
    return TemplateEntry(
        path=str(entry["path"]),
        kind=str(entry["kind"]),
        status=str(entry["status"]),
        tests=[str(item) for item in entry["tests"]],
        examples=[str(item) for item in entry["examples"]],
        notes=str(entry.get("notes", "")),
    )
