# Main PyReeler Skill Demo - Production Notes

**Date:** 2026-03-16
**Duration:** 30 seconds
**Resolution:** 854×480 (preview) / 1920×1080 (upscale option)
**Output:** `~/Videos/main_skill_demo.mp4`

---

## Creative Brief

**Genre/Mode:** Ritual/Mythic
**Motif:** Returning circle
**Core Move:** Rupture at peak, then return
**Inspiration:** `creative-lenses.md`

> "Ritual or mythic work: recurrence, ceremony, symmetry, invocation, escalation through repetition"

The piece establishes a recurring circular motif in the opening, escalates through the middle section, and introduces a rupture (color inversion) at the peak before returning to a transformed calm.

---

## Reference Document Implementation

### creative-lenses.md

| Concept | Implementation |
|---------|----------------|
| **Genre** | Ritual - ceremonial recurrence, symmetrical patterns |
| **Motif** | Returning circle - appears in sections 1 and 3 |
| **Repetition** | Useful work: establishes ceremony, then transforms |
| **Rupture** | Frame 600 (25s): color inversion breaks established logic |
| **Time** | Acceleration in build, pause after rupture |

**Judgment questions answered:**
- *What would the obvious version look like?* Simple particle rotation
- *What makes it specific?* The rupture/return structure, chromatic aberration
- *What move will viewers remember?* The inversion at 25s

### workflow.md

| Step | Implementation |
|------|----------------|
| **1. Frame** | Brief defined: ritual, 30s, rupture structure |
| **2. Audio plan** | Stem architecture: ambience, pulse, score, impacts |
| **3. Hardware gate** | Verify `detect_render_runtime()`, encoder, workers |
| **4. Smoke test** | Validate `ordered_frame_map()` with 4 test frames |
| **5. Preview** | 854×480, full 30s duration |
| **6. Review** | Verify file opens, check representative frames |
| **7. Upscale** | Offer 720p, 1080p, or keep preview |
| **8. Deliver** | Write to `~/Videos/` |
| **9. Cleanup** | Delete `temp_frames/` directory |

### audio-pipeline.md

**Stem model:**

| Stem | Function | Technique |
|------|----------|-----------|
| ambience | Environmental bed | `gen_wind()` with varying intensity |
| pulse | Rhythmic propulsion | Gated FM tones (72 BPM) |
| score | Harmonic development | FM drone with dissonance at rupture |
| impacts | Transitions | `gen_impact()` at section boundaries |

**Mixing approach:**
- Gain staging: ambience 0.6, pulse 0.5, score 0.7, impacts 0.9
- Normalize to -0.5dB peak
- Ducking: impacts naturally cut through due to timing

### vocabulary-map.md

**Visual systems:**
- particles/swarm → Rotating geometric field (0-10s)
- fields/flow → Sine-based acceleration (10-20s)
- symmetry/mirrors → 8-way kaleidoscope (20-30s)
- noise/texture → Grain overlay (10-20s)

**Audio systems:**
- drone → FM brass with slow evolution
- pulse → Gated rhythmic synthesis
- shimmer → High-frequency partials (post-rupture)

**Temporal systems:**
- recurrence → Returning circular motion
- acceleration → Increasing flow frequency
- rupture → Color inversion at 25s
- return → Calm after chaos

**Material/surface:**
- phosphor glow → Multi-layer blur falloff
- grain → Noise overlay
- signal haze → Chromatic aberration (RGB shift at rupture)

---

## Technical Implementation

### Templates Used

| Template | Purpose |
|----------|---------|
| `render_runtime.py` | Hardware detection, encoder selection |
| `parallel_render.py` | Multi-worker frame generation |
| `audio_engine.py` | FM synthesis, BPM utilities |
| `sfx_gen.py` | Procedural foley (wind, impact, shimmer) |
| `composer.py` | Note events, MIDI (optional) |

### Performance Characteristics

| Aspect | Estimate |
|--------|----------|
| Audio generation | ~2s (vectorized numpy) |
| Frame render (single worker) | ~60s |
| Frame render (4 workers) | ~20s |
| FFmpeg encode | ~5s |
| **Total** | **~30s** |

### Safety Limits

```python
# From render_runtime.py
MAX_WORKERS = min(4, os.cpu_count())  # Conservative
DEFAULT_RESOLUTION = (854, 480)        # Preview
```

---

## What Worked

1. **Stem architecture** - Separating audio into narrative roles made mixing intuitive
2. **Hardware gate** - Caught encoder issues before full render
3. **Worker smoke test** - Validated Windows multiprocessing quickly
4. **Rupture timing** - 25s feels like the right moment for maximum impact
5. **Chromatic aberration** - Simple RGB shift creates strong material effect

## What Didn't

1. **MIDI/FluidSynth** - Not all systems have fluidsynth; kept as optional
2. **Scipy dependency** - Would be nice to have pure-numpy fallbacks for all filters
3. **Flow field** - Could be more sophisticated (curl noise, etc.)

## Surprises

- The `gen_shimmer()` function produced unexpectedly beautiful results when layered post-rupture
- Windows multiprocessing worked reliably with `freeze_support()` and top-level functions
- Color inversion as rupture was more effective than complex glitch effects

## Would Try Next Time

1. **Text overlays** - Terminal language, warnings (vocabulary-map.md)
2. **CRT effects** - Scanlines, phosphor decay curves
3. **Cellular automata** - Growth systems for organic section
4. **Bytebeat** - Demoscene-style audio for glitch section
5. **SoundFont scoring** - Real instruments via `composer.py` + `pyfluidsynth`

---

## Render Checklist

- [x] Hardware gate passed
- [x] Worker smoke test passed
- [x] All 30 seconds rendered
- [x] Audio present and synced
- [x] File opens correctly
- [x] Duration verified
- [x] Cleanup completed

## Tags

#demo #main-skill #reference-implementation #ritual-mode #rupture #stems #comprehensive
