# GPU Frame Synthesis Runtime — Design

**Date:** 2026-06-17
**Status:** Implemented — local runtime hardening landed through commit `5025e3d`
**Location of artifact:** `docs/hardware-experiments/wgpu_runtime.py`

---

## Purpose

Move the "GPU mode" story from encoding-only toward actual GPU-backed frame
synthesis, while keeping the portable PyReeler skill conservative. The existing
hardware experiment already proves shader-backed frame generation on a local
machine, but the runtime is not import-safe without `wgpu` and still carries
machine-specific assumptions.

The v1 goal is to make the local shader runtime explicit, testable, and honest:

- importing `wgpu_runtime.py` must not require `wgpu`
- CI can test non-GPU behavior
- GPU adapter selection remains local-only and opt-in
- docs clearly distinguish shader synthesis from hardware video encoding

## Non-goals

- No portable skill dependency on `wgpu`.
- No CI GPU rendering.
- No shader framework abstraction beyond the existing local helper.
- No automatic installation of GPU drivers or `wgpu`.
- No promotion into `templates/` yet.

## Relationship to Existing Code

- `docs/hardware-experiments/render_shader_terminal_preview.py` and
  `pyreel_ghost_machine_shader.py` already perform offscreen shader rendering.
- `docs/hardware-experiments/wgpu_runtime.py` provides adapter/runtime detection
  but imports `wgpu` immediately and has hardcoded Windows FFmpeg candidates.
- `templates/video/render_runtime.py` remains the portable encoder/runtime helper.

This design keeps GPU synthesis in `docs/hardware-experiments/` until the API and
dependency story are stable.

## Public API

```python
def is_wgpu_available() -> bool:
    """Return True when the optional wgpu package can be imported."""


def resolve_local_ffmpeg_candidates(extra_candidates=None) -> list[str]:
    """Return existing local FFmpeg candidate paths, including optional overrides."""


def pick_discrete_adapter(wgpu_module=None):
    """Return the preferred discrete adapter, raising a clear RuntimeError if absent."""


def detect_local_shader_runtime(
    *,
    ffmpeg_candidates=None,
    require_discrete: bool = True,
) -> tuple[LocalShaderRuntime, Any]:
    """Return runtime metadata and adapter for local shader rendering."""
```

## Behavior

- Importing `wgpu_runtime.py` succeeds even if `wgpu` is missing.
- Calling GPU-dependent functions without `wgpu` raises
  `RuntimeError("Install wgpu to use local shader rendering.")`.
- FFmpeg candidate resolution accepts caller-provided paths and only returns paths
  that exist.
- Adapter picking prefers discrete NVIDIA adapters when present, then any discrete
  adapter, then optionally any adapter when `require_discrete=False`.
- The local shader demos continue to call `detect_local_shader_runtime()` and fail
  clearly on machines without the dependency/hardware.

## Testing

Use CI-safe unit tests with fake `wgpu` modules and fake adapters:

1. module imports when `wgpu` is absent
2. `is_wgpu_available()` returns a boolean
3. missing `wgpu` produces a clear `RuntimeError`
4. adapter picking prefers NVIDIA discrete adapters
5. adapter picking can fall back to non-discrete adapters when requested
6. FFmpeg candidate resolver filters missing paths

No test should require actual GPU hardware.

## Documentation

Update `docs/hardware-experiments/README.md` to define:

- GPU encoding: FFmpeg/hardware codec acceleration
- GPU frame synthesis: shader/GPU generation of pixel frames
- current status: local-only, optional `wgpu`, not portable skill behavior

Update `docs/plans/2026-06-17-review-improvements.md` item 4 to note that the
runtime has been hardened once implementation lands.

## Future Directions

- Extract a tiny shader-render base class if more demos converge.
- Add optional benchmark output for GPU readback time and encode time.
- Add a CPU fallback demo for machines without `wgpu`.
- Consider graduation only after dependency, platform, and examples are stable.
