# Audio-Reactive Parameter Mapping Implementation Plan

> **For agentic workers:** implement task-by-task with focused tests before code.
> This plan intentionally exercises the template graduation gate when the new
> portable helper is added.

**Goal:** Add `templates/audio/audio_reactive.py`, a NumPy-only helper that turns a
mono audio signal into a normalized per-frame envelope and maps that envelope into
visual parameter values.

**Architecture:** Pure functions, no file I/O, no runtime dependencies beyond
NumPy. The helper lives in root `templates/audio/`, is synced into both skill
folders, and is declared in `template_graduation.toml`.

**Spec:** `docs/superpowers/specs/2026-06-17-audio-reactive-parameter-mapping-design.md`

---

## File Structure

- Create: `templates/audio/audio_reactive.py`
- Create: `tests/test_audio_reactive.py`
- Modify: `templates/audio/README.md`
- Modify: `README.md`
- Modify: `template_graduation.toml`
- Run: `python3 sync.py` to update `skills/claude/templates/audio/` and
  `skills/codex/templates/audio/`
- Modify: `docs/plans/2026-06-17-review-improvements.md`

---

## Task 1: Envelope extraction

**Files:**
- Create: `templates/audio/audio_reactive.py`
- Create: `tests/test_audio_reactive.py`

- [ ] **Step 1: Write failing tests**

Cover:

- silence returns zeros
- output length equals requested `frame_count`
- a loud second half produces larger envelope values than a quiet first half
- invalid `sample_rate`, `fps`, `frame_count`, or `window_sec` raises `ValueError`

- [ ] **Step 2: Implement `rms_envelope`**

Use local RMS around each frame's corresponding sample index. Normalize by the
maximum RMS value, then apply one-pole attack/release smoothing.

- [ ] **Step 3: Run focused tests**

```bash
python3 -m pytest tests/test_audio_reactive.py -q
```

- [ ] **Step 4: Commit**

```bash
git add templates/audio/audio_reactive.py tests/test_audio_reactive.py
git commit -m "feat(audio): add per-frame RMS envelope helper"
```

---

## Task 2: Mapping helpers

**Files:**
- Modify: `templates/audio/audio_reactive.py`
- Modify: `tests/test_audio_reactive.py`

- [ ] **Step 1: Write failing tests**

Cover:

- `map_range(np.array([0, 1]), 10, 20)` returns `[10, 20]`
- curve shaping keeps output inside range
- `reactive_value(..., mode="add")`
- `reactive_value(..., mode="multiply")`
- unknown mode raises `ValueError`

- [ ] **Step 2: Implement `map_range` and `reactive_value`**

Keep the API scalar/array friendly and deterministic. Clip normalized values to
`0..1` before mapping.

- [ ] **Step 3: Run focused tests**

```bash
python3 -m pytest tests/test_audio_reactive.py -q
```

- [ ] **Step 4: Commit**

```bash
git add templates/audio/audio_reactive.py tests/test_audio_reactive.py
git commit -m "feat(audio): map audio envelopes to visual parameters"
```

---

## Task 3: Graduation, sync, and docs

**Files:**
- Modify: `templates/audio/README.md`
- Modify: `README.md`
- Modify: `template_graduation.toml`
- Modify: synced skill template copies via `python3 sync.py`
- Modify: `docs/plans/2026-06-17-review-improvements.md`

- [ ] **Step 1: Run sync**

```bash
python3 sync.py
```

- [ ] **Step 2: Add graduation manifest entry**

Declare `templates/audio/audio_reactive.py` with:

- `tests = ["tests/test_audio_reactive.py"]`
- `examples = ["docs/superpowers/specs/2026-06-17-audio-reactive-parameter-mapping-design.md"]`

- [ ] **Step 3: Document the helper**

Add short entries to README's Template Layer and `templates/audio/README.md`.

- [ ] **Step 4: Mark the future direction as delivered**

Update `docs/plans/2026-06-17-review-improvements.md` item 3 to note that the
portable v1 helper is delivered; band-specific and beat-detection mappings remain
future work.

- [ ] **Step 5: Run full verification**

```bash
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```

- [ ] **Step 6: Commit**

```bash
git add README.md templates/audio/README.md template_graduation.toml \
  templates/audio/audio_reactive.py skills/claude/templates/audio/audio_reactive.py \
  skills/codex/templates/audio/audio_reactive.py \
  docs/plans/2026-06-17-review-improvements.md
git commit -m "docs: graduate audio-reactive parameter helper"
```

---

## Self-Review Notes

- **Spec coverage:** envelope extraction, range mapping, reactive scalar updates,
  sync, graduation manifest, and docs are all covered by tasks.
- **YAGNI boundary:** v1 is RMS energy only. FFT bands and beat detection are
  intentionally future work.
- **CI implication:** after Task 1 creates a new template, `graduation_check.py`
  should fail until Task 3 updates sync copies and the manifest. This is expected
  and proves the gate is doing useful work.
