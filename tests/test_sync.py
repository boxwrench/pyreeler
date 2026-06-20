"""Tests for sync.py — the template/reference distribution guard.

The PyReeler skills must be self-contained when installed, so the canonical
templates have to be physically copied into each skill folder. These tests
verify the copy is faithful and that --check detects drift.
"""
import filecmp
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import sync  # noqa: E402


def test_sync_makes_skill_templates_identical_to_canonical():
    sync.sync()
    for skill in sync.SKILL_DIRS:
        for sub in sync.TEMPLATE_SUBDIRS:
            canonical = REPO_ROOT / "templates" / sub
            target = REPO_ROOT / "skills" / skill / "templates" / sub
            match, mismatch, errors = filecmp.cmpfiles(
                canonical, target, [p.name for p in canonical.glob("*.py")]
            )
            assert not mismatch, f"{skill}/{sub} drifted: {mismatch}"
            assert not errors, f"{skill}/{sub} missing files: {errors}"


def test_check_passes_after_sync():
    sync.sync()
    assert sync.check() == []


def test_shared_references_are_synced_but_divergent_ones_are_not():
    assert sync.REFERENCE_SOURCE_DIR == REPO_ROOT / "skills" / "_shared" / "references"

    for name in sync.SHARED_REFERENCES:
        source = sync.REFERENCE_SOURCE_DIR / name
        assert source.exists()
        for skill in sync.SKILL_DIRS:
            target = REPO_ROOT / "skills" / skill / "references" / name
            assert filecmp.cmp(source, target, shallow=False)

    # Divergent files must NOT be in the shared set (would clobber per-platform text).
    assert "workflow.md" not in sync.SHARED_REFERENCES
    assert "vocabulary-map.md" not in sync.SHARED_REFERENCES
