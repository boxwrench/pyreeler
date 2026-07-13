# Critical Helper Behavioral Proof

**Date:** 2026-07-12
**Status:** Complete

## Boundary

The audit selected three canonical helpers with current production or reusable
runtime importance:

- `templates/audio/audio_engine.py`, used by completed films;
- `templates/video/parallel_render.py`, the graduated ordered worker helper; and
- `templates/video/render_runtime.py`, used by the installed renderer and films.

Optional composition, voice, geometry, lensing, self-healing, and text-track
helpers remain sync-covered. Adding broad tests for those helpers without a
current film, failure, or requested change would freeze speculative behavior.

## Proof Added

Audio tests cover positive and negative stem placement, timeline clipping,
voice-driven ducking, gain/mix bounds, and mono PCM WAV metadata. Parallel
render tests cover sequential ordering without pool creation, ordered pool
mapping with computed chunksize, and worker-error propagation with pool cleanup.
Runtime tests cover validated profile assembly, encoder arguments, inherited
worker counts, and clamped explicit overrides.

The graduation manifest now links each selected helper to its direct behavioral
test while retaining `tests/test_sync.py` as distribution-integrity proof.

## Validation

Nine focused behavioral tests pass. Full-suite, graduation, sync, and diff
checks are required before commit.
