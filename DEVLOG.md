# PyReeler Devlog

## Current Repo State

`C:\Github\pyreeler` is the working repository for both Codex and Claude variants of the PyReeler skill:

- `pyreeler-codex/` - OpenAI Codex skill (invoked as `$pyreeler`)
- `pyreeler-claude/` - Claude Code skill (invoked as `/pyreeler`)

Previous render outputs, frame dumps, smoke artifacts, temp skill copies, and scratch scripts were archived to `C:\Github\pyreeler_archive_20260313`.

There are three relevant locations for skill development:
- **Working repo**: `C:\Github\pyreeler` (this repository)
- **Portable source**: `C:\Users\wests\Downloads\pyreeler` (sharable package source)
- **Installed skill**: `C:\Users\wests\.codex\skills\pyreeler` (active Codex skill)

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

---

## Benchmark Methodology

### Fast Iteration Loop

Use `narrative_preview_smoke.py` for rapid inner-loop testing:

```powershell
python C:\Github\pyreeler\narrative_preview_smoke.py cpu short
python C:\Github\pyreeler\narrative_preview_smoke.py portable_auto_multi short
```

This verifies the installed portable code directly, avoiding fresh-session generation overhead.

### Full Benchmark Suite

```powershell
python C:\Github\pyreeler\narrative_preview_smoke.py cpu full
python C:\Github\pyreeler\narrative_preview_smoke.py portable_auto full
python C:\Github\pyreeler\narrative_preview_smoke.py portable_auto_multi full
python C:\Github\pyreeler\narrative_preview_smoke.py gpu full
python C:\Github\pyreeler\narrative_preview_smoke.py gpu_multi full
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
