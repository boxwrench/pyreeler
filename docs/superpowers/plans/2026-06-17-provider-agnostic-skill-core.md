# Provider-Agnostic Skill Core Implementation Plan

> **For agentic workers:** keep provider install folders self-contained. The shared
> folder is a source tree used by sync, not something installed directly.

**Goal:** Add `skills/_shared/references/` as the canonical source for references
that are byte-identical across provider skills, and update `sync.py`/tests/docs to
use that source instead of treating `skills/claude` as the lead provider.

**Status:** Completed through commit `9096383`; generated provider wrappers remain
future work.

**Spec:** `docs/superpowers/specs/2026-06-17-provider-agnostic-skill-core-design.md`

---

## File Structure

- Create: `skills/_shared/references/audio-pipeline.md`
- Create: `skills/_shared/references/creative-lenses.md`
- Create: `skills/_shared/references/three-d-and-lensing.md`
- Modify: `sync.py`
- Modify: `tests/test_sync.py`
- Modify: `README.md`
- Modify: `docs/plans/2026-06-17-review-improvements.md`

---

## Task 1: Shared reference source

**Files:**
- Create: `skills/_shared/references/*.md`
- Modify: `sync.py`
- Modify: `tests/test_sync.py`

- [x] **Step 1: Write failing sync tests**

Add assertions that `sync.REFERENCE_SOURCE_DIR` points at
`skills/_shared/references` and that every shared reference is copied from there
into both provider folders.

- [x] **Step 2: Create shared reference files**

Copy the current byte-identical reference files into `skills/_shared/references/`.

- [x] **Step 3: Update sync.py**

Replace `REFERENCE_SOURCE = "claude"` with a concrete source path:

```python
REFERENCE_SOURCE_DIR = REPO_ROOT / "skills" / "_shared" / "references"
```

Copy each `SHARED_REFERENCES` file into every provider skill folder.

- [x] **Step 4: Run verification**

```bash
python3 sync.py --check
python3 -m pytest tests/test_sync.py -q
```

- [x] **Step 5: Commit**

```bash
git add skills/_shared/references sync.py tests/test_sync.py
git commit -m "feat(build): add shared reference source for provider skills"
```

---

## Task 2: Documentation and full gate

**Files:**
- Modify: `README.md`
- Modify: `docs/plans/2026-06-17-review-improvements.md`

- [x] **Step 1: Document shared core**

Update README's repository structure and Development section to mention
`skills/_shared/references/`.

- [x] **Step 2: Mark future direction as advanced**

Update review-improvements item 5 to note that shared reference source exists;
generated provider wrappers remain future work.

- [x] **Step 3: Run full verification**

```bash
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```

- [x] **Step 4: Commit**

```bash
git add README.md docs/plans/2026-06-17-review-improvements.md
git commit -m "docs: document provider-agnostic shared skill core"
```

---

## Self-Review Notes

- **Self-contained install folders:** preserved; sync still writes physical copies.
- **YAGNI boundary:** no generated `SKILL.md` yet.
- **Provider-specific files:** `workflow.md`, `vocabulary-map.md`, `README.md`, and
  `agents/` remain provider-owned.
