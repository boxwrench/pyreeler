#!/usr/bin/env python3
"""Distribute canonical templates (and shared references) into each skill folder.

PyReeler ships as installable skills (`skills/claude/`, `skills/codex/`). An
installed skill must be self-contained, so its templates have to physically
live inside it — they cannot be symlinks back to a shared source. That forces
the same files to exist in several places, which silently drifts over time.

This script makes `templates/` (repo root) the single source of truth for
template code and copies it into every skill folder. A small set of reference
docs are byte-identical across skills, so those are synced too; the references
that legitimately differ per platform (tool naming, invocation syntax) are
left alone.

Usage:
    python3 sync.py            # copy canonical files into the skill folders
    python3 sync.py --check    # report drift without writing; exit 1 if any
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

# Skill folders that receive a copy of the canonical files.
SKILL_DIRS = ("claude", "codex")

# Template subfolders under the canonical top-level templates/ directory.
TEMPLATE_SUBDIRS = ("audio", "video")

# Reference docs that are identical across skills and should stay in lockstep.
# Per-platform docs (workflow.md, vocabulary-map.md) are intentionally excluded.
SHARED_REFERENCES = (
    "three-d-and-lensing.md",
    "creative-lenses.md",
    "audio-pipeline.md",
)

# Canonical source for references that are byte-identical across providers.
REFERENCE_SOURCE_DIR = REPO_ROOT / "skills" / "_shared" / "references"


def _file_pairs() -> list[tuple[Path, Path]]:
    """Return (source, target) pairs for every file sync manages."""
    pairs: list[tuple[Path, Path]] = []

    for skill in SKILL_DIRS:
        for sub in TEMPLATE_SUBDIRS:
            src_dir = REPO_ROOT / "templates" / sub
            dst_dir = REPO_ROOT / "skills" / skill / "templates" / sub
            for src in sorted(src_dir.glob("*.py")):
                pairs.append((src, dst_dir / src.name))

    for skill in SKILL_DIRS:
        dst_ref_dir = REPO_ROOT / "skills" / skill / "references"
        for name in SHARED_REFERENCES:
            pairs.append((REFERENCE_SOURCE_DIR / name, dst_ref_dir / name))

    return pairs


def check() -> list[str]:
    """Return human-readable descriptions of every drifted/missing target."""
    problems: list[str] = []
    for src, dst in _file_pairs():
        rel = dst.relative_to(REPO_ROOT)
        if not dst.exists():
            problems.append(f"missing: {rel}")
        elif not filecmp.cmp(src, dst, shallow=False):
            problems.append(f"drifted: {rel}")
    return problems


def sync() -> int:
    """Copy every canonical file into its targets. Returns the count copied."""
    copied = 0
    for src, dst in _file_pairs():
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or not filecmp.cmp(src, dst, shallow=False):
            shutil.copy2(src, dst)
            copied += 1
    return copied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift without writing; exit 1 if any target is stale",
    )
    args = parser.parse_args(argv)

    if args.check:
        problems = check()
        if problems:
            print("Skill files are out of sync with canonical sources:")
            for p in problems:
                print(f"  - {p}")
            print("\nRun `python3 sync.py` to fix.")
            return 1
        print("All skill templates and shared references are in sync.")
        return 0

    copied = sync()
    print(f"Synced {copied} file(s) into {', '.join(SKILL_DIRS)} skill folders.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
