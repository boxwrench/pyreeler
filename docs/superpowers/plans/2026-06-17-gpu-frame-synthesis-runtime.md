# GPU Frame Synthesis Runtime Implementation Plan

> **For agentic workers:** keep GPU code local-only. CI tests must not require
> `wgpu` or a physical GPU.

**Goal:** Harden `docs/hardware-experiments/wgpu_runtime.py` so the local GPU frame
synthesis path is import-safe, testable, and clearly distinct from portable
encoding/runtime helpers.

**Architecture:** Lazy optional import for `wgpu`, fake-adapter tests for selection
logic, and docs that clarify current status. Actual shader demos stay in
`docs/hardware-experiments/`.

**Spec:** `docs/superpowers/specs/2026-06-17-gpu-frame-synthesis-runtime-design.md`

---

## File Structure

- Modify: `docs/hardware-experiments/wgpu_runtime.py`
- Create: `tests/test_wgpu_runtime.py`
- Modify: `docs/hardware-experiments/README.md`
- Modify: `docs/plans/2026-06-17-review-improvements.md`

---

## Task 1: Import-safe optional `wgpu`

**Files:**
- Modify: `docs/hardware-experiments/wgpu_runtime.py`
- Create: `tests/test_wgpu_runtime.py`

- [ ] **Step 1: Write failing tests**

Cover:

- importing `wgpu_runtime.py` succeeds in CI without installing `wgpu`
- `is_wgpu_available()` returns a bool
- `pick_discrete_adapter(wgpu_module=None)` raises a clear install message when
  `wgpu` is missing

- [ ] **Step 2: Implement lazy import**

Remove module-level `import wgpu`. Add:

```python
def _load_wgpu():
    ...

def is_wgpu_available() -> bool:
    ...
```

- [ ] **Step 3: Run tests**

```bash
python3 -m pytest tests/test_wgpu_runtime.py -q
```

- [ ] **Step 4: Commit**

```bash
git add docs/hardware-experiments/wgpu_runtime.py tests/test_wgpu_runtime.py
git commit -m "test(gpu): make local wgpu runtime import-safe"
```

---

## Task 2: Adapter and FFmpeg candidate behavior

**Files:**
- Modify: `docs/hardware-experiments/wgpu_runtime.py`
- Modify: `tests/test_wgpu_runtime.py`

- [ ] **Step 1: Write failing tests**

Cover:

- `resolve_local_ffmpeg_candidates(extra_candidates=[...])` returns only existing
  paths
- adapter picking prefers NVIDIA discrete adapters
- adapter picking falls back to any discrete adapter
- adapter picking can fall back to any adapter with `require_discrete=False`

- [ ] **Step 2: Implement behavior**

Update:

```python
def resolve_local_ffmpeg_candidates(extra_candidates=None):
    ...

def pick_discrete_adapter(wgpu_module=None, *, require_discrete=True):
    ...
```

Keep existing local Windows candidate paths as defaults, but make overrides
possible for tests and future local tuning.

- [ ] **Step 3: Run tests**

```bash
python3 -m pytest tests/test_wgpu_runtime.py -q
```

- [ ] **Step 4: Commit**

```bash
git add docs/hardware-experiments/wgpu_runtime.py tests/test_wgpu_runtime.py
git commit -m "feat(gpu): harden local shader runtime selection"
```

---

## Task 3: Docs and full verification

**Files:**
- Modify: `docs/hardware-experiments/README.md`
- Modify: `docs/plans/2026-06-17-review-improvements.md`

- [ ] **Step 1: Document current GPU synthesis status**

Clarify:

- hardware encoding vs frame synthesis
- local-only `wgpu` requirement
- no portable skill dependency yet
- how to run the shader demo locally

- [ ] **Step 2: Mark future direction as advanced**

Update review-improvements item 4 to note that the local runtime is import-safe and
test-covered; portable graduation remains future work.

- [ ] **Step 3: Run full verification**

```bash
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```

- [ ] **Step 4: Commit**

```bash
git add docs/hardware-experiments/README.md docs/plans/2026-06-17-review-improvements.md
git commit -m "docs: clarify local GPU frame synthesis path"
```

---

## Self-Review Notes

- **Safety:** no CI test should touch real GPU hardware.
- **Scope:** this remains a hardware experiment, not a graduated template.
- **Portability:** the portable skill should continue to describe GPU mode honestly
  as encoder acceleration unless a script explicitly uses this local shader path.
