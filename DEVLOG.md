# PyReeler Devlog

> **Historical note:** This devlog records development as it happened on the
> original Windows authoring machine, so historical local paths and the
> `narrative_preview_smoke.py` benchmark harness
> are **not part of this repository**. The benchmark numbers are kept for
> reference; they are not reproducible from a fresh clone. For the current,
> runnable workflow see the **Development** section of `README.md`
> (`python3 sync.py`, `pytest`).

## Current Repo State

The working repository contains both Codex and Claude variants of the PyReeler skill:

- `pyreeler-codex/` - OpenAI Codex skill (invoked as `$pyreeler`)
- `pyreeler-claude/` - Claude Code skill (invoked as `/pyreeler`)

Previous render outputs, frame dumps, smoke artifacts, temp skill copies, and scratch scripts were archived outside this repository.

There are three relevant locations for skill development:
- **Working repo**: this repository
- **Portable source**: local package checkout
- **Installed skill**: local assistant skill directory

Development workflow: edit portable source → sync to installed skill → benchmark → validate in fresh session.

---

## Project Direction

The portable skill targets:
- Validated hardware-aware encoder selection
- Conservative multicore frame generation
- Direct piping to FFmpeg over stdin
- Clean fallback to `libx264`

The portable package avoids machine-specific hardcoding. Local installs can tune more aggressively.

---

## Implementation History

### Video Runtime & Encoding

Added `templates/video/` modules for portable rendering:

- `ffmpeg_utils.py` - host detection, encoder smoke tests, worker heuristics
- `render_runtime.py` - one-call runtime selection (ffmpeg path, encoder, workers, video args)
- `parallel_render.py` - ordered multiprocessing for frame generation

Guidance now requires:
- Pre-render hardware gate for portable Python renderers
- `detect_render_runtime()` for runtime selection
- Validated encoder selection (no hardcoded hardware assumptions)
- `runtime.workers` for actual frame generation, not just FFmpeg settings
- Piped FFmpeg when practical
- Worker-path smoke test before first render when `runtime.workers > 1`
- Windows-safe multiprocessing (top-level workers, picklable inputs, `if __name__ == "__main__"`, `freeze_support()`)

### Audio Layer Fixes

Correctness fixes applied to the audio templates:
- Negative stem offsets now trim correctly
- NumPy motif arrays no longer break empty checks
- Zero-length signals no longer crash low-pass fallback
- MIDI and TTS helpers create parent directories before writing

Files: `audio_engine.py`, `composer.py`, `sfx_gen.py`, `voice.py`

### Documentation Updates

- `README.md` - added benchmark notes, modern hardware defaults
- `SKILL.md` - explicit `detect_render_runtime()` instruction
- `references/workflow.md` - reinforced portable runtime guidance

### Cosmic Collapse — 3D, Lensing, Self-Healing, Text Track (2026-05-10)

Produced `experimental/experiments/cosmic_collapse.py` (30s three-act piece) and extracted its reusable patterns into the main skill:

- `templates/video/geometry_3d.py` — `get_rotation_matrix`, `project_points`, and `find_coeffs` for PIL.PERSPECTIVE. Documents the `find_coeffs(target_pb, src_pa)` direction convention. (Older `cosmic_experiment.py` calls it with reversed arguments; that bug produces tiny corner-clipped textures.)
- `templates/video/lensing.py` — `apply_lensing` Schwarzschild-style radial warp. Pure NumPy, ~200ms per 1280×720 frame.
- `templates/video/text_track.py` — terminal-style narration timeline with typed lines, scrolling, isolated punchline, and `keystroke_events()` for audio sync.
- `templates/video/self_healing.py` — multi-sample-frame contrast audit with parameter re-rolling. Generic replacement for the per-renderer `SelfHealer` pattern.

New reference: `references/three-d-and-lensing.md` — lean-3D math, perspective per-face texturing recipe, lensing usage, and the find_coeffs gotcha.

Workflow additions (`references/workflow.md`):
- Section 9 (Timeline-driven structure): one `arc_state(t)` consumed by both visuals and audio, so peaks are guaranteed in sync.
- Section 10 (Pre-render quality audit): use `self_healing.py` with samples spread across the arc before committing to a full render.

Vocabulary additions (`references/vocabulary-map.md`):
- Visual: 3D geometry / perspective projection, gravitational lensing, chaotic attractors, accretion-disk textures.
- Temporal: multi-act arc with shared timeline.
- Textual: god's-CLI / creation-log narration; typewriter-revealed lines synced to events.

Mirrored to `skills/codex/` and top-level `templates/`.

---

## Benchmark Methodology

> The `narrative_preview_smoke.py` harness referenced below lived on the
> original authoring machine and is not committed here. Treat this section as a
> record of the methodology used to produce the benchmark numbers, not as
> instructions runnable from this repo.

### Fast Iteration Loop

Use `narrative_preview_smoke.py` for rapid inner-loop testing:

```powershell
python narrative_preview_smoke.py cpu short
python narrative_preview_smoke.py portable_auto_multi short
```

This verifies the installed portable code directly, avoiding fresh-session generation overhead.

### Full Benchmark Suite

```powershell
python narrative_preview_smoke.py cpu full
python narrative_preview_smoke.py portable_auto full
python narrative_preview_smoke.py portable_auto_multi full
python narrative_preview_smoke.py gpu full
python narrative_preview_smoke.py gpu_multi full
```

Purpose: compare end-to-end preview runtime, separate encoder effects from frame-generation effects.

### Acceptance Test

After fast loop passes:
1. Open fresh Codex session
2. Invoke `$pyreeler`
3. Inspect generated renderer for:
   - `detect_render_runtime()` usage
   - Real frame parallelism
   - Piped FFmpeg
4. Run full render and compare wall-clock time

---

## Benchmark Results

### 30-Second Narrative Harness

| Mode | Time |
|------|------|
| `cpu` | ~5.9s - 6.3s |
| `gpu` (encode only) | ~6.0s |
| `gpu_multi` | ~3.8s |
| `portable_auto_multi` | ~3.8s - 4.3s |
| `local_specific_multi` | ~3.7s - 4.2s |

**Key finding**: Hardware encoding alone did not materially help this CPU-bound preview. Multicore frame generation was the meaningful speedup. Portable multicore came close to local-specific performance.

### Short Harness

| Mode | Time |
|------|------|
| `cpu short` | 2.88s |
| `portable_auto_multi short` | 2.38s |

Preferred iteration path.

### What "GPU Mode" Actually Means

Current `gpu` mode = hardware-assisted **video encoding** only. It does **not** mean GPU-based frame synthesis. Visual rendering remains CPU-side (Python/Pillow). The GPU only accelerates FFmpeg encoding when available.

### Correctness Learnings

- Helper adoption now happens by default
- Worker-backed rendering can be verified before full render
- Slow scenes are usually expensive frame functions, not render-path issues
- Heavy procedural fields and bloom are separate from worker-path correctness

---

## Generated Script Analysis

Tested with `space_dragon_pyreeler_preview.py`:

**Initial findings**:
- `render_runtime.py`: not used
- Detected encoder: not used
- Worker count: not used (only as FFmpeg thread count)
- Piped FFmpeg: yes ✓
- Temp frame trees: no ✓

**After patching to use `render_runtime.py`**:
- Timing stayed flat because `runtime.workers` wasn't driving actual parallel frame generation

**Conclusion**: Portable runtime integration alone is insufficient. Generated scripts must use worker count for frame production itself.

---

## Known Gaps

### `space_dragon_pyreeler_preview.py`

Still needs refactor to benefit from portable multicore defaults:
- Renderer is stateful frame-to-frame
- Must separate: precomputed simulation state + independent per-frame drawing
- Then `parallel_render.py` or worker pools can work correctly

### Next Steps

Patch `space_dragon_pyreeler_preview.py` to:
1. Keep `detect_render_runtime()`
2. Use `parallel_render.py`
3. Use worker count for actual frame generation
4. Preserve piped FFmpeg output

This is the next meaningful performance test for generated-script realism.

---

## Development Workflow Summary

1. Edit portable package in Downloads folder
2. Sync to installed Codex skill
3. Benchmark with `narrative_preview_smoke.py short`
4. Run `full` mode when needed
5. Validate with fresh session and newly generated script
