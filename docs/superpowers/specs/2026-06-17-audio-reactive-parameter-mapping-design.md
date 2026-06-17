# Audio-Reactive Parameter Mapping — Design

**Date:** 2026-06-17
**Status:** Drafted — ready for implementation plan
**Location of artifact:** `templates/audio/audio_reactive.py` (+ synced skill copies)

---

## Purpose

Let audio energy drive visual parameters without each film hand-rolling its own
envelope extraction. PyReeler already recommends a shared `arc_state(t)` timeline
for synchronized visual/audio structure; this helper adds the missing bridge from
actual audio stems or mixes back into frame-indexed visual modulation curves.

The core question is: "At frame N, how much should this visual parameter react to
the audio?" The answer should be a normalized, deterministic scalar that can be
mixed into `arc_state(t)` or a render loop.

## Non-goals

- No real-time microphone or streaming input.
- No beat detection, pitch tracking, FFT bands, or onset classification in v1.
- No dependency beyond NumPy.
- No replacement for `arc_state(t)`. This augments the timeline; it does not
  become the timeline source of truth.
- No automatic choice of which visual parameter should be mapped. Callers decide.

## Relationship to Existing Code

- `templates/audio/audio_engine.py` already mixes named stems into a mono signal.
  This helper consumes those same NumPy arrays.
- `templates/video/text_track.py` exposes discrete event times for audio sync.
  This helper covers continuous energy curves rather than discrete events.
- `experimental/experiments/cosmic_collapse.py` already samples
  `arc_state(t)["audio_intensity"]` for audio. This helper supports the inverse
  direction: sample audio energy and feed it into visual state.

## Public API

```python
def rms_envelope(
    signal: np.ndarray,
    sample_rate: int,
    fps: float,
    frame_count: int,
    *,
    window_sec: float = 0.05,
    attack: float = 0.45,
    release: float = 0.12,
) -> np.ndarray:
    """Return a normalized 0..1 RMS envelope, one value per video frame."""


def map_range(
    values: np.ndarray,
    out_min: float,
    out_max: float,
    *,
    curve: float = 1.0,
) -> np.ndarray:
    """Map normalized envelope values into a target parameter range."""


def reactive_value(
    base: float,
    amount: float,
    envelope_value: float,
    *,
    mode: str = "add",
) -> float:
    """Apply one envelope sample to a scalar base parameter."""
```

### Contract Details

- `signal` is mono float-like audio. Stereo callers should mix down before calling.
- Output length from `rms_envelope` is exactly `frame_count`.
- Envelope values are clipped/normalized to `0..1`.
- `window_sec` determines local RMS window width.
- `attack` and `release` are smoothing factors in `0..1`; higher attack follows
  rising energy faster, higher release follows falling energy faster.
- `map_range` accepts normalized values and supports simple curve shaping:
  `curve > 1` emphasizes peaks, `curve < 1` lifts quiet motion.
- `reactive_value` supports `mode="add"` and `mode="multiply"` in v1.

## Example Usage

```python
from templates.audio.audio_reactive import rms_envelope, reactive_value

mix = mix_stems(stems)
env = rms_envelope(mix, SAMPLE_RATE, FPS, N_FRAMES)

def render_frame(frame_idx, ctx):
    t = frame_idx / FPS
    state = arc_state(t)
    state["particle_density"] = reactive_value(
        state["particle_density"],
        amount=0.35,
        envelope_value=float(env[frame_idx]),
    )
    ...
```

## Testing

Unit tests should cover deterministic synthetic signals:

1. Silence returns all zeros.
2. Constant-amplitude tone returns a stable high envelope after smoothing.
3. A later loud section produces higher frame values than an earlier quiet section.
4. Output length always equals `frame_count`.
5. `map_range` maps `0` to `out_min` and `1` to `out_max`.
6. `reactive_value` supports additive and multiplicative modes and rejects unknown
   modes with `ValueError`.

## Graduation and Sync

Because this is a portable helper, adding it requires:

- root canonical file: `templates/audio/audio_reactive.py`
- synced copies under both skill folders via `python3 sync.py`
- `template_graduation.toml` entry
- tests in the default suite
- README Template Layer mention

The existing graduation gate should fail until the manifest and sync copies are
updated, which is intentional.

## Future Directions

- Band-limited envelopes with FFT or simple filters.
- Beat/onset impulse extraction.
- Stem-specific named envelope maps.
- A declarative mapping helper for multiple parameters at once.
