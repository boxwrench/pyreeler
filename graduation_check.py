#!/usr/bin/env python3
"""Template graduation manifest checker."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any
import tomllib

import sync


REPO_ROOT = Path(__file__).resolve().parent


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


def validate(entries: list[TemplateEntry], repo_root: Path) -> list[str]:
    """Return human-readable manifest problems."""
    repo_root = repo_root.resolve()
    problems: list[str] = []
    seen: set[str] = set()
    declared: set[str] = set()
    managed_sources = _sync_managed_sources(repo_root)

    for entry in entries:
        rel_path = entry.path
        if rel_path in seen:
            problems.append(f"duplicate template entry: {rel_path}")
        seen.add(rel_path)
        declared.add(rel_path)

        path = _repo_path(repo_root, rel_path)
        if path is None:
            problems.append(f"{rel_path} points outside the repo")
            continue

        kind_from_path = _kind_from_template_path(rel_path)
        if kind_from_path is None:
            problems.append(
                f"{rel_path} is not under templates/audio, templates/video, or templates/tui"
            )
        elif entry.kind != kind_from_path:
            problems.append(
                f"{rel_path} kind {entry.kind} does not match {kind_from_path} path"
            )

        if entry.status != "graduated":
            problems.append(f"{rel_path} status {entry.status} is not graduated")

        if not path.exists():
            problems.append(f"{rel_path} does not exist")

        for test_path in entry.tests:
            if not _path_exists_under_repo(repo_root, test_path):
                problems.append(f"{rel_path} test path missing: {test_path}")

        for example_path in entry.examples:
            if not _path_exists_under_repo(repo_root, example_path):
                problems.append(f"{rel_path} example path missing: {example_path}")

        if rel_path not in managed_sources:
            problems.append(f"{rel_path} is not covered by sync.py targets")

    for template_path in _current_template_paths(repo_root):
        if template_path not in declared:
            problems.append(f"missing manifest entry for template: {template_path}")

    return problems


def _kind_from_template_path(path: str) -> str | None:
    if path.startswith("templates/audio/"):
        return "audio"
    if path.startswith("templates/video/"):
        return "video"
    if path.startswith("templates/tui/"):
        return "tui"
    return None


def _current_template_paths(repo_root: Path) -> set[str]:
    templates_dir = repo_root / "templates"
    return {str(path.relative_to(repo_root)) for path in templates_dir.glob("*/*.py")}


def _sync_managed_sources(repo_root: Path) -> set[str]:
    if repo_root != sync.REPO_ROOT.resolve():
        return set()
    return {str(src.relative_to(repo_root)) for src, _ in sync._file_pairs()}


def _path_exists_under_repo(repo_root: Path, rel_path: str) -> bool:
    path = _repo_path(repo_root, rel_path)
    return path is not None and path.exists()


def _repo_path(repo_root: Path, rel_path: str) -> Path | None:
    path = (repo_root / rel_path).resolve()
    try:
        path.relative_to(repo_root)
    except ValueError:
        return None
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default="template_graduation.toml",
        help="path to the template graduation TOML manifest",
    )
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = REPO_ROOT / manifest_path

    problems = validate(load_manifest(manifest_path), REPO_ROOT)
    if problems:
        print("Template graduation manifest has problems:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print("Template graduation manifest is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
