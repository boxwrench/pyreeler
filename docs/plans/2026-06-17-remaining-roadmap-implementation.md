# Remaining Roadmap Implementation Plan

**Date:** 2026-06-17
**Status:** Drafted for implementation
**Source roadmap:** `experimental/ROADMAP.md`

## Goal

Turn the remaining roadmap into an ordered implementation backlog that can be
worked task-by-task without re-triaging the whole repository each time.

The priority is infrastructure first, then integration helpers, then new visual
techniques. That order gives each later technique better comparison, validation,
and reuse paths.

## Current Delivered Baseline

- Contact-sheet v1: single-axis parameter sweeps.
- Template graduation gate: manifest + CI validation.
- Audio-reactive v1: RMS envelope and scalar mapping helpers.
- GPU runtime hardening: import-safe local `wgpu` runtime helpers.
- Provider shared references: `skills/_shared/references/` feeds provider copies.

## Remaining Roadmap Items

### Technique Implementation

- 3D perspective projection polish around `geometry_3d.py`.
- Autonomous validation loop / smoke-test self-healing scripts.
- Retro terminal UI overlays.
- Differential growth.
- Space colonization algorithm.
- Diffusion-limited aggregation.
- Boids with full parameter exposure.
- L-system string rewriting.
- Granular synthesis audio.

### Infrastructure

- Batch rendering system using `ParameterSequence`.
- 2D contact-sheet grids and parallel variant rendering.
- Automated visual regression testing.
- Render farm distribution.

### Integration

- Hybrid RD -> Pixel Sort -> Particles pipeline.
- Multi-layer stacking system.
- Audio-reactive band-specific envelopes and beat detection.
- GPU frame synthesis shader render base class / benchmark output.
- Real-time preview mode.

## Implementation Order

## Task 1: ParameterSequence Batch Rendering

**Why first:** The roadmap already chose `ParameterSequence` as the core experiment
primitive. Batch rendering makes it useful across techniques and feeds contact
sheets, regression tests, and integration demos.

**Deliverables:**

- Add `experimental/tools/batch_render.py`.
- Provide a small API that loads or accepts a `ParameterSequence` and renders named
  variants into deterministic output folders.
- Support dry-run listing for CI-safe tests.
- Add tests under `experimental/tools/test_batch_render.py`.
- Document usage in `experimental/README.md` and `experimental/ROADMAP.md`.

**Verification:**

```bash
python3 -m pytest experimental/tools/test_batch_render.py -q
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```

## Task 2: Contact-Sheet v2

**Why next:** It extends the just-delivered contact-sheet tool and consumes batch
render output.

**Deliverables:**

- Extend `experimental/tools/contact_sheet.py` with a 2D grid helper for two
  parameter axes.
- Add optional parallel rendering for top-level picklable render functions.
- Preserve sequential behavior as the default for closure-heavy experiments.
- Add tests for 2D layout, axis labels, deterministic cell order, and parallel
  fallback behavior.
- Update `experimental/README.md` and `experimental/ROADMAP.md`.

**Verification:**

```bash
python3 -m pytest experimental/tools/test_contact_sheet.py -q
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```

## Task 3: Automated Visual Regression

**Why after contact sheets:** Regression snapshots need stable image generation and
comparison utilities before they can guard future visual techniques.

**Deliverables:**

- Add `experimental/tools/visual_regression.py`.
- Implement image difference metrics with tolerance thresholds.
- Support update/check modes for local baseline maintenance.
- Keep committed baselines tiny and deterministic.
- Add CI-safe tests with synthetic images.
- Document baseline policy and artifact exclusions.

**Verification:**

```bash
python3 -m pytest experimental/tools/test_visual_regression.py -q
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```

## Task 4: Audio-Reactive v2

**Why here:** It can now use batch/contact-sheet/regression tooling for parameter
exploration and proof points.

**Deliverables:**

- Extend `templates/audio/audio_reactive.py` with band-specific envelope helpers.
- Add onset/beat-style event detection with conservative, deterministic behavior.
- Keep dependencies NumPy-only.
- Sync provider copies and update `template_graduation.toml` if examples/tests
  change.
- Add focused tests for band separation, event thresholds, and invalid parameters.
- Update `templates/audio/README.md`, root `README.md`, and roadmap docs.

**Verification:**

```bash
python3 sync.py
python3 -m pytest tests/test_audio_reactive.py -q
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```

## Task 5: Multi-Layer Stacking System

**Why before hybrid pipelines:** Hybrid work needs a shared composition model, not
one-off render loops.

**Deliverables:**

- Add an experimental layer-composition helper that accepts named render layers,
  blend modes, opacity curves, and deterministic ordering.
- Reuse existing Pillow/NumPy patterns; avoid new dependencies.
- Add tests for alpha compositing, ordering, disabled layers, and shape handling.
- Add a small demo in `experimental/experiments/`.
- Document how this relates to graduated `templates/video/` helpers.

**Verification:**

```bash
python3 -m pytest experimental/tools/test_layer_stack.py -q
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```

## Task 6: Hybrid RD -> Pixel Sort -> Particles Pipeline

**Why after stacking:** This is an integration demo that should use the stacking
and batch tooling rather than inventing local orchestration.

**Deliverables:**

- Add an experiment under `experimental/experiments/`.
- Compose existing reaction-diffusion, pixel-sorting, and particle ideas into a
  short deterministic demo or smoke-render path.
- Expose main parameters through `ParameterSequence`.
- Add a quick smoke test that validates output shape and deterministic metadata,
  not a long render.
- Document the experiment and update the roadmap.

**Verification:**

```bash
python3 -m pytest experimental/experiments/test_hybrid_pipeline.py -q
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```

## Task 7: GPU Frame Synthesis v2

**Why later:** GPU work is local-only and should not block portable tool progress.

**Deliverables:**

- Add a local shader render base class or protocol in `docs/hardware-experiments/`.
- Add benchmark output for adapter selection, shader readback, and encode timing.
- Define a CPU fallback contract for examples that can run without `wgpu`.
- Keep CI tests fake-adapter or CPU-only.
- Update hardware experiment docs and roadmap status.

**Verification:**

```bash
python3 -m pytest tests/test_wgpu_runtime.py -q
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```

## Task 8: Real-Time Preview Mode

**Why after render primitives settle:** Preview depends on stable render functions,
layer composition, and performance choices.

**Deliverables:**

- Add a small preview runner for experiments with frame stepping and low-resolution
  render settings.
- Prefer stdlib/Pillow-compatible output first; add optional richer UI only if the
  repo already has the dependency path.
- Add tests for preview configuration and frame selection without opening a GUI.
- Document local-only limitations.

**Verification:**

```bash
python3 -m pytest experimental/tools/test_preview.py -q
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```

## Task 9: New Technique Pack

**Why last:** New techniques are best added once exploration and validation tooling
is stronger.

**Recommended order:**

1. Retro terminal UI overlays.
2. L-system string rewriting.
3. Boids with full parameter exposure.
4. Diffusion-limited aggregation.
5. Space colonization.
6. Differential growth.
7. Granular synthesis audio.
8. 3D perspective polish, if existing `geometry_3d.py` gaps remain after demos.

**Per-technique deliverables:**

- Research note or existing research doc link.
- Minimal experimental implementation.
- `ParameterSequence` exposure for meaningful controls.
- Smoke test or visual regression baseline.
- Contact sheet showing at least one parameter sweep.
- Roadmap update describing status: research, working, ready, or graduated.

## Task 10: Render Farm Distribution

**Why last:** Distribution adds operational complexity and should wait until batch
rendering, visual regression, and artifact policy are stable.

**Deliverables:**

- Specify a small job manifest format.
- Implement local multi-process execution first.
- Define artifact layout and resumability.
- Add CI-safe unit tests for scheduling and manifest parsing.
- Defer remote execution until local semantics are proven.

## Commit And Review Discipline

For each task:

1. Write or update the spec if behavior is not already obvious.
2. Add failing focused tests where practical.
3. Implement the smallest useful v1.
4. Run focused tests and the full gate.
5. Update `experimental/ROADMAP.md` and any relevant README.
6. Commit with a task-specific message.

Full gate:

```bash
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```
