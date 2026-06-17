# Template Graduation Gate — Design

**Date:** 2026-06-17
**Status:** Drafted — ready for implementation plan
**Location of artifact:** `graduation_check.py` + `template_graduation.toml`

---

## Purpose

Make template graduation a verifiable process instead of a manual copy ritual.
When experimental code is promoted into the portable PyReeler skill, the repo
should be able to answer three questions automatically:

1. Does the promoted template live in the canonical `templates/` tree?
2. Is it covered by the sync model that copies templates into both skill folders?
3. Is there a documented proof point: tests and an example film or demo that uses it?

This implements future direction 1 from the project review: "Formalize template
graduation" as passing tests + an example film + `sync.py`.

## Non-goals

- No package publishing or installer changes.
- No automatic code migration from `experimental/` into `templates/`.
- No quality scoring for visual output.
- No deep import graph analysis. The gate checks declared files and proof points.
- No new runtime dependencies.

## Relationship to Existing Code

`sync.py` already makes root `templates/` the canonical source of truth and copies
template files into `skills/claude/` and `skills/codex/`. The graduation gate sits
one level above that:

- `sync.py --check` verifies copied files are in sync.
- `graduation_check.py` verifies promoted templates are declared, present,
  covered by sync, tested, and backed by an example.

The gate should not replace `sync.py`; it should run alongside it in CI.

## Data Model

Use a small TOML manifest in the repo root:

```toml
[[template]]
path = "templates/video/parallel_render.py"
kind = "video"
status = "graduated"
tests = ["tests/test_sync.py"]
examples = ["films/what-the-light-kept/render_preview.py"]
notes = "Multiprocess ordered frame rendering used by generated scripts."
```

### Fields

- `path`: canonical template path under `templates/audio/` or `templates/video/`.
- `kind`: `audio` or `video`.
- `status`: `graduated` for active portable templates. Future values may include
  `candidate` or `deprecated`, but v1 only enforces `graduated`.
- `tests`: one or more test files or test directories that prove the template is
  maintained.
- `examples`: one or more example scripts, films, or demos that prove the template
  has been used in context.
- `notes`: short human-readable rationale.

## Command API

Add a script with a simple CLI:

```bash
python3 graduation_check.py
python3 graduation_check.py --manifest template_graduation.toml
```

The command exits `0` when every check passes and `1` otherwise. Output should name
each failed template and the exact missing or invalid field.

## Checks

For each `[[template]]` entry:

1. `path` exists and is below `templates/`.
2. `kind` matches the path segment (`templates/audio/` or `templates/video/`).
3. `status` is `graduated`.
4. Every `tests` path exists.
5. Every `examples` path exists.
6. The template is covered by `sync.py`'s managed file pairs, meaning it has target
   copies in both skill folders.

For the manifest as a whole:

1. Every `.py` file under `templates/audio/` and `templates/video/` has one
   manifest entry.
2. No manifest entry points outside the repo.
3. No duplicate `path` entries.

## CI Integration

The default CI order should become:

```bash
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```

`sync.py --check` remains first because graduation assumes the copy model is clean.

## Documentation

README's Development section should define "graduated template" as:

- canonical source in `templates/`
- declared in `template_graduation.toml`
- distributed by `sync.py`
- covered by at least one test path
- backed by at least one example film/demo path

## Future Directions

- Add `candidate` status for experimental items being evaluated for graduation.
- Generate a Markdown report of graduated templates.
- Add a helper that scaffolds a manifest entry for a new template.
- Require template-specific smoke tests once more templates have focused tests.
