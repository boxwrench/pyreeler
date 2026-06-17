# Provider-Agnostic Skill Core — Design

**Date:** 2026-06-17
**Status:** Implemented — shared reference source landed through commit `9096383`
**Location of artifact:** `skills/_shared/`

---

## Purpose

Reduce duplicated skill content while preserving self-contained install folders for
Claude Code and Codex. PyReeler currently has two provider folders with mostly
shared templates and references, plus provider-specific invocation language,
metadata, and review guidance. `sync.py` already made root `templates/` canonical;
the next step is to stop treating one provider folder as the source of truth for
shared references.

## Non-goals

- Do not make installed skills depend on symlinks or parent folders.
- Do not generate full `SKILL.md` files in v1.
- Do not merge provider-specific `workflow.md`, `vocabulary-map.md`, `README.md`,
  or agent metadata.
- Do not change user-facing invocation (`$pyreeler` vs `/pyreeler`).

## Relationship to Existing Code

- Root `templates/` remains the canonical source for portable template code.
- `skills/claude/` and `skills/codex/` remain complete installable skills.
- `sync.py` currently copies byte-identical references from `skills/claude` to
  `skills/codex`. That source should become `skills/_shared/references/` instead.

## Shared Core Layout

```text
skills/_shared/
└── references/
    ├── audio-pipeline.md
    ├── creative-lenses.md
    └── three-d-and-lensing.md
```

The shared folder is a source tree, not an installable skill.

## Sync Behavior

`sync.py` should:

1. Copy root `templates/audio/*.py` and `templates/video/*.py` into every provider
   skill folder as it does today.
2. Copy `skills/_shared/references/*.md` into each provider skill folder for the
   shared reference set.
3. Leave provider-specific references (`workflow.md`, `vocabulary-map.md`) alone.
4. Keep `sync.py --check` as the CI guard.

## Testing

Update `tests/test_sync.py` to assert:

- shared reference source is `skills/_shared/references`
- shared references are copied into both provider skills
- provider-specific references are excluded
- templates remain copied from root `templates/`

## Documentation

README's Development section should describe:

- root `templates/` is canonical for template code
- `skills/_shared/references/` is canonical for shared reference docs
- provider folders remain installable copies after `sync.py`

## Future Directions

- Add shared Markdown fragments for common `SKILL.md` instruction sections.
- Add a small render/build script for provider wrappers if duplication grows.
- Add a third provider folder by supplying only metadata and invocation deltas.
