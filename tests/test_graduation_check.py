"""Tests for the template graduation manifest checker."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from graduation_check import TemplateEntry, load_manifest, validate  # noqa: E402


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
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "templates").glob("*/*.py")
    }

    assert declared == current_templates


def _valid_entry(**overrides):
    data = {
        "path": "templates/video/parallel_render.py",
        "kind": "video",
        "status": "graduated",
        "tests": ["tests/test_sync.py"],
        "examples": ["experimental/experiments/main-skill-demo/main_skill_demo.py"],
        "notes": "Ordered multiprocess frame rendering.",
    }
    data.update(overrides)
    return TemplateEntry(**data)


def test_validate_accepts_repo_manifest():
    entries = load_manifest(REPO_ROOT / "template_graduation.toml")

    assert validate(entries, REPO_ROOT) == []


def test_validate_reports_missing_template_path():
    problems = validate([_valid_entry(path="templates/video/missing.py")], REPO_ROOT)

    assert "templates/video/missing.py does not exist" in problems


def test_validate_reports_path_outside_templates():
    problems = validate([_valid_entry(path="README.md")], REPO_ROOT)

    assert (
        "README.md is not under templates/audio, templates/video, or templates/tui"
        in problems
    )


def test_validate_reports_kind_path_mismatch():
    problems = validate([_valid_entry(kind="audio")], REPO_ROOT)

    assert "templates/video/parallel_render.py kind audio does not match video path" in problems


def test_validate_reports_duplicate_entries():
    entry = _valid_entry()

    problems = validate([entry, entry], REPO_ROOT)

    assert "duplicate template entry: templates/video/parallel_render.py" in problems


def test_validate_reports_missing_tests_path():
    problems = validate([_valid_entry(tests=["tests/missing_test.py"])], REPO_ROOT)

    assert "templates/video/parallel_render.py test path missing: tests/missing_test.py" in problems


def test_validate_reports_missing_examples_path():
    problems = validate([_valid_entry(examples=["films/missing.py"])], REPO_ROOT)

    assert "templates/video/parallel_render.py example path missing: films/missing.py" in problems


def test_validate_reports_missing_manifest_entry_for_template_file():
    entries = [
        entry
        for entry in load_manifest(REPO_ROOT / "template_graduation.toml")
        if entry.path != "templates/video/text_track.py"
    ]

    problems = validate(entries, REPO_ROOT)

    assert "missing manifest entry for template: templates/video/text_track.py" in problems


def test_validate_reports_template_not_covered_by_sync_pairs(tmp_path):
    repo = tmp_path
    template = repo / "templates" / "video" / "orphan.py"
    template.parent.mkdir(parents=True)
    template.write_text("# orphan\n", encoding="utf-8")
    test_path = repo / "tests" / "test_orphan.py"
    test_path.parent.mkdir()
    test_path.write_text("# test\n", encoding="utf-8")
    example_path = repo / "examples" / "orphan_demo.py"
    example_path.parent.mkdir()
    example_path.write_text("# demo\n", encoding="utf-8")

    problems = validate(
        [
            TemplateEntry(
                path="templates/video/orphan.py",
                kind="video",
                status="graduated",
                tests=["tests/test_orphan.py"],
                examples=["examples/orphan_demo.py"],
                notes="Temporary orphan.",
            )
        ],
        repo,
    )

    assert "templates/video/orphan.py is not covered by sync.py targets" in problems
