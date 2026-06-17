# Template Graduation Gate Implementation Plan

> **For agentic workers:** implement task-by-task. Use the repo's existing TDD
> style where code behavior is introduced. Keep docs-only status updates separate
> from functional commits.

**Goal:** Add a lightweight, verifiable graduation gate for portable templates:
`template_graduation.toml` declares each template's tests/examples, and
`graduation_check.py` validates the declaration plus `sync.py` coverage.

**Architecture:** A standalone stdlib-only checker. It reads TOML via
`tomllib` (Python 3.11+) or falls back to `tomli` only if already installed. If
Python 3.10 support must be strict with no optional dependency, use a constrained
line parser for the manifest format. The checker imports `sync.py` to reuse
`_file_pairs()` instead of duplicating sync rules.

**Spec:** `docs/superpowers/specs/2026-06-17-template-graduation-design.md`

---

## File Structure

- Create: `template_graduation.toml`
- Create: `graduation_check.py`
- Create: `tests/test_graduation_check.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `docs/plans/2026-06-17-review-improvements.md`

---

## Task 1: Manifest scaffold and parser

**Files:**
- Create: `template_graduation.toml`
- Create: `graduation_check.py`
- Create: `tests/test_graduation_check.py`

- [ ] **Step 1: Write failing parser tests**

Add tests that create a temporary manifest with one `[[template]]` entry and assert
the checker returns a parsed template record with `path`, `kind`, `status`, `tests`,
`examples`, and `notes`.

- [ ] **Step 2: Implement manifest loading**

Implement:

```python
def load_manifest(path: Path) -> list[TemplateEntry]:
    ...
```

Use a small dataclass for `TemplateEntry`. Keep validation separate from parsing so
tests can target each layer.

- [ ] **Step 3: Add initial manifest entries**

Declare every current Python template under:

- `templates/audio/*.py`
- `templates/video/*.py`

Use existing tests/examples where possible. `tests/test_sync.py` is acceptable as
baseline maintenance coverage for v1, but each entry should also list at least one
real example/demo path from `films/` or `experimental/experiments/` when available.

- [ ] **Step 4: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_graduation_check.py -q
```

- [ ] **Step 5: Commit**

```bash
git add template_graduation.toml graduation_check.py tests/test_graduation_check.py
git commit -m "feat(build): add template graduation manifest parser"
```

---

## Task 2: Validation rules

**Files:**
- Modify: `graduation_check.py`
- Modify: `tests/test_graduation_check.py`

- [ ] **Step 1: Write failing validation tests**

Cover:

- missing template path
- path outside `templates/`
- kind/path mismatch
- duplicate entries
- missing tests path
- missing examples path
- missing manifest entry for a template file
- template not covered by `sync.py` file pairs

- [ ] **Step 2: Implement validation**

Implement:

```python
def validate(entries: list[TemplateEntry], repo_root: Path) -> list[str]:
    ...
```

Return human-readable problem strings. Do not exit inside validation; keep CLI
behavior thin.

- [ ] **Step 3: Add CLI**

Implement:

```bash
python3 graduation_check.py
python3 graduation_check.py --manifest template_graduation.toml
```

Exit `0` if there are no problems, otherwise print all problems and exit `1`.

- [ ] **Step 4: Run checker and tests**

Run:

```bash
python3 graduation_check.py
python3 -m pytest tests/test_graduation_check.py -q
```

- [ ] **Step 5: Commit**

```bash
git add graduation_check.py tests/test_graduation_check.py
git commit -m "feat(build): validate graduated template declarations"
```

---

## Task 3: CI and docs

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `docs/plans/2026-06-17-review-improvements.md`

- [ ] **Step 1: Wire CI**

Add the graduation check after `sync.py --check` and before pytest:

```bash
python3 graduation_check.py
```

- [ ] **Step 2: Document the graduation gate**

In README's Development section, add the definition of a graduated template and the
local verification command sequence:

```bash
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```

- [ ] **Step 3: Mark future direction as specified**

Update `docs/plans/2026-06-17-review-improvements.md` item 1 to link to this spec
and plan.

- [ ] **Step 4: Run full verification**

Run:

```bash
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml README.md docs/plans/2026-06-17-review-improvements.md
git commit -m "ci: enforce template graduation gate"
```

---

## Self-Review Notes

- **Spec coverage:** manifest, checker, sync coverage, docs, and CI each map to a task.
- **Dependency risk:** avoid adding a hard TOML dependency unless the project has
  already moved to Python 3.11+. If strict Python 3.10 is required, implement a
  constrained parser for this manifest shape.
- **YAGNI boundary:** this verifies declared proof points; it does not judge
  artistic quality or generate examples.
