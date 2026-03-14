# PyReeler Devlog

## Current Repo State

`C:\Github\pyreeler` has been cleaned down to the current skill packages only:

- `pyreeler-codex`
- `pyreeler-claude`

Previous render outputs, frame dumps, smoke artifacts, temp skill copies, and scratch scripts were moved out of the working folder to:

- `C:\Github\pyreeler_archive_20260313`

## Context

This workspace contains both:

- the local working repo at `C:\Github\pyreeler`
- the sharable portable skill package at `C:\Users\wests\Downloads\pyreeler`
- the installed Codex skill copy at `C:\Users\wests\.codex\skills\pyreeler`

Recent work has focused on making the portable package faster by default while keeping it safe and cross-machine compatible.

## Current Portable Direction

The portable skill should default to:

- validated hardware-aware encoder selection
- conservative multicore frame generation
- direct piping to FFmpeg over stdin
- clean fallback to `libx264`

The portable package should not depend on machine-specific hardcoding. Local installs can still tune more aggressively.

## Current Guidance Added

The current portable and installed guidance now requires:

- a pre-render hardware gate for portable Python renderers
- `detect_render_runtime()` for runtime selection
- validated encoder selection instead of hardcoded hardware encoder assumptions
- `runtime.workers` to drive actual frame generation, not just FFmpeg settings
- piped FFmpeg when practical
- a short worker-path smoke test before the first full render when `runtime.workers > 1`
- Windows-safe multiprocessing structure
  - top-level worker functions
  - picklable worker inputs
  - `if __name__ == "__main__":`
  - `multiprocessing.freeze_support()` when needed

## Implemented In Portable Package

Added or updated in the portable package:

- `templates/video/ffmpeg_utils.py`
  - lightweight host detection
  - encoder smoke tests
  - conservative worker heuristics
- `templates/video/render_runtime.py`
  - one-call runtime selection for:
    - ffmpeg path
    - encoder
    - worker count
    - video args
- `templates/video/parallel_render.py`
  - ordered multiprocessing helper for frame generation
- `README.md`
  - benchmark note
  - modern hardware defaults
- `SKILL.md`
  - explicit instruction to use `detect_render_runtime()` in portable Python renderers
- `references/workflow.md`
  - reinforced portable runtime guidance

These changes were synced into:

- `C:\Users\wests\.codex\skills\pyreeler`

## Audio Fixes Applied

The new audio layer in the portable package had several correctness fixes applied:

- negative stem offsets now trim correctly
- NumPy motif arrays no longer break empty checks
- zero-length signals no longer crash the low-pass fallback
- MIDI and TTS output helpers create parent directories before writing

Files updated:

- `templates/audio/audio_engine.py`
- `templates/audio/composer.py`
- `templates/audio/sfx_gen.py`
- `templates/audio/voice.py`

## Benchmark Method

### Fast Iteration Loop

Use the fixed harness:

- `C:\Github\pyreeler\narrative_preview_smoke.py`

This harness imports from the installed portable skill and is the preferred inner-loop benchmark target.

Run:

```powershell
python C:\Github\pyreeler\narrative_preview_smoke.py cpu short
python C:\Github\pyreeler\narrative_preview_smoke.py portable_auto_multi short
```

Purpose:

- verify the installed portable code directly
- avoid fresh-session skill generation for every iteration
- get a result in a few seconds

The harness prints:

- selected ffmpeg path
- encoder
- worker count
- `verify_runtime_helper`
- `verify_frame_parallelism`
- `verify_ffmpeg_pipe`

### Full Benchmark

Run:

```powershell
python C:\Github\pyreeler\narrative_preview_smoke.py cpu full
python C:\Github\pyreeler\narrative_preview_smoke.py portable_auto full
python C:\Github\pyreeler\narrative_preview_smoke.py portable_auto_multi full
python C:\Github\pyreeler\narrative_preview_smoke.py gpu full
python C:\Github\pyreeler\narrative_preview_smoke.py gpu_multi full
```

Purpose:

- compare end-to-end preview runtime on the same deterministic scene
- separate encoder effects from frame-generation effects

### Acceptance Test

Only after the fast loop looks right:

1. Open a fresh Codex session.
2. Invoke `$pyreeler`.
3. Inspect the generated renderer script.
4. Confirm it actually uses:
   - `detect_render_runtime()`
   - real frame parallelism
   - piped FFmpeg
5. Run the full render and compare wall-clock time.

## Benchmark Findings So Far

### 30-second Narrative Harness

Representative numbers measured during this development pass:

- `cpu`
  - about `5.9s` to `6.3s`
- `gpu`
  - about `6.0s`
- `gpu_multi`
  - about `3.8s`
- `portable_auto_multi`
  - about `3.8s` to `4.3s`
- `local_specific_multi`
  - about `3.7s` to `4.2s`

Meaning:

- hardware encoding alone did not materially help this CPU-bound preview
- multicore frame generation was the meaningful speedup
- once portable used both validated hardware encode and multicore rendering, it came close to the local-specific path

### Short Harness

Measured:

- `cpu short`
  - `2.88s`
- `portable_auto_multi short`
  - `2.38s`

This is the current preferred iteration path.

## Benchmark Interpretation

Recent clean-room testing suggests:

- helper adoption is now happening by default
- worker-backed rendering can be selected and verified before full render
- some scenes may still render slowly because the frame function itself is expensive
- heavy full-frame procedural fields and bloom are a separate performance problem from worker-path correctness

## Important Interpretation

Current `gpu` mode means:

- hardware-assisted video encoding

It does **not** mean:

- GPU-based frame synthesis

Today the visual rendering is still CPU-side Python/Pillow. The GPU is only helping on the FFmpeg encode side when available.

## Generated Script Findings

In a fresh generated script run for:

- `C:\Github\pyreeler\space_dragon_pyreeler_preview.py`

initial findings were:

- `render_runtime.py`: not used at first
- detected encoder: not used at first
- worker count: not used at first
- piped FFmpeg: yes
- temp frame trees: no

The script was then patched to use `render_runtime.py`, but the timing stayed essentially flat because `runtime.workers` was only being used as FFmpeg thread count, not for actual parallel frame generation.

Conclusion:

- portable runtime integration alone is not enough
- the generated script must use worker count for frame production itself

## Current Known Gap

`space_dragon_pyreeler_preview.py` still needs a careful refactor if it is going to benefit from portable multicore defaults.

Reason:

- the renderer is stateful frame-to-frame
- frame generation must be separated into:
  - precomputed simulation state
  - independent per-frame drawing

Only then can `parallel_render.py` or a worker pool be used correctly.

## Recommended Development Workflow

1. Patch the portable package in `C:\Users\wests\Downloads\pyreeler`.
2. Sync it into `C:\Users\wests\.codex\skills\pyreeler`.
3. Benchmark with `narrative_preview_smoke.py` in `short` mode.
4. Re-run in `full` mode when needed.
5. Only then validate with a fresh session and a newly generated script.

## Immediate Next Step

Patch `space_dragon_pyreeler_preview.py` so it:

- keeps `detect_render_runtime()`
- uses `parallel_render.py`
- uses worker count for actual frame generation
- preserves piped FFmpeg output

That is the next meaningful performance test for generated-script realism.
