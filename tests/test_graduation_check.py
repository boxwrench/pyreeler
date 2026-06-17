"""Tests for the template graduation manifest checker."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from graduation_check import TemplateEntry, load_manifest  # noqa: E402


def test_load_manifest_parses_template_entries(tmp_path):
    manifest = tmp_path / "template_graduation.toml"
    manifest.write_text(
        """
[[template]]
path = "templates/video/parallel_render.py"
kind = "video"
status = "graduated"
tests = ["tests/test_sync.py"]
examples = ["experimental/experiments/main-skill-demo/main_skill_demo.py"]
notes = "Ordered multiprocess frame rendering."
""".strip(),
        encoding="utf-8",
    )

    entries = load_manifest(manifest)

    assert entries == [
        TemplateEntry(
            path="templates/video/parallel_render.py",
            kind="video",
            status="graduated",
            tests=["tests/test_sync.py"],
            examples=["experimental/experiments/main-skill-demo/main_skill_demo.py"],
            notes="Ordered multiprocess frame rendering.",
        )
    ]


def test_load_repo_manifest_includes_current_python_templates():
    entries = load_manifest(REPO_ROOT / "template_graduation.toml")
    declared = {entry.path for entry in entries}
    current_templates = {
        str(path.relative_to(REPO_ROOT))
        for path in (REPO_ROOT / "templates").glob("*/*.py")
    }

    assert declared == current_templates
