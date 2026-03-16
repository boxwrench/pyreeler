# Main PyReeler Skill - Comprehensive Demo

A demonstration film that exercises **ALL** main skill reference documents and templates.

## What This Demonstrates

### Reference Documents

| Document | Location | Concepts Demonstrated |
|----------|----------|----------------------|
| `creative-lenses.md` | `experimental/research/` | Genre/mode (ritual), motif (returning circle), repetition/rupture, time as material |
| `workflow.md` | `experimental/research/` | Hardware gate, worker smoke test, preview/upscale, cleanup |
| `audio-pipeline.md` | `experimental/research/` | Stem model (ambience, pulse, score, impacts), procedural foley, mixing |
| `vocabulary-map.md` | `experimental/research/` | Visual systems (particles, flow, symmetry), audio systems (drone, pulse, shimmer), material (grain, phosphor) |

### Templates Used

| Template | Location | Purpose |
|----------|----------|---------|
| `render_runtime.py` | Main skill + `skills/codex/` | Hardware-aware encoder/worker detection |
| `parallel_render.py` | Main skill + `skills/codex/` | Multi-worker frame generation |
| `audio_engine.py` | Main skill + `skills/codex/` | FM synthesis (`FMSynth`, `bpm_to_ms`) |
| `sfx_gen.py` | Main skill + `skills/codex/` | Procedural foley (`gen_wind`, `gen_impact`, `gen_shimmer`) |
| `composer.py` | Main skill + `skills/codex/` | Note events, MIDI writing (optional) |

**Note:** All reference docs are now in `experimental/research/`. Templates are imported from the main skill installation but copied to `skills/codex/` for offline reference.

## Quick Start

```bash
cd experimental/experiments/main-skill-demo
python main_skill_demo.py
```

Output: `~/Videos/main_skill_demo.mp4`

## Film Structure

```
0-10s:  ┊ RITUAL    ┊ recurrence + drone + phosphor glow
10-20s: ┊ BUILD     ┊ escalation + pulse + grain
20-25s: ┊ PEAK      ┊ symmetry + shimmer
25-30s: ┊ RUPTURE   ┊ inversion + chromatic aberration + return
```

### Creative Implementation

**creative-lenses.md:**
- **Genre**: Ritual/mythic mode
- **Motif**: Returning circle (recurs throughout, deepens meaning)
- **Repetition**: Establishes ceremony in first section
- **Rupture**: Frame 600 (25s) - color inversion breaks established logic
- **Time as material**: Acceleration in build section, pause after rupture

## Audio Pipeline

**Stem architecture** (audio-pipeline.md):

```python
stems = {
    'ambience': gen_wind(),      # Section-varying intensity
    'pulse': gated_tones(),       # Only in build section
    'score': fm_drone(),          # Slow evolution + rupture
    'impacts': gen_impact(),      # Transitions + punctuation
}
mixed = sum(stem * gain for stem, gain in stems.items())
```

| Stem | Technique | Narrative Role |
|------|-----------|----------------|
| ambience | `gen_wind()` | Environmental bed, builds tension |
| pulse | Gated FM sine | Rhythmic propulsion in build |
| score | `FMSynth.fm_sample()` | Harmonic evolution, dissonance at rupture |
| impacts | `gen_impact()` + `gen_shimmer()` | Transitions at section boundaries |

## Workflow Implementation

**workflow.md steps implemented:**

1. **Frame the piece**: Genre/mode, motif, duration defined
2. **Plan audio architecture**: Stem-based design
3. **Hardware gate**: Verify `detect_render_runtime()`, encoder, workers
4. **Worker smoke test**: Validate multiprocessing before full render
5. **Build preview**: 854×480, full duration
6. **Verify**: Output integrity check
7. **Upscale offer**: 720p, 1080p, or keep preview
8. **Deliver**: Write to `~/Videos/`
9. **Cleanup**: Delete frame directory

## Vocabulary Map Mapping

| Category | Concept | Implementation |
|----------|---------|----------------|
| **Visual** | particles/swarm | Rotating geometric field |
| **Visual** | fields/flow | Sine-based flow with acceleration |
| **Visual** | symmetry/mirrors | 8-way kaleidoscope |
| **Visual** | noise/texture | Grain overlay (np.random) |
| **Audio** | drone | FM brass with slow evolution |
| **Audio** | pulse | Gated rhythmic synthesis |
| **Audio** | shimmer | High-frequency partials |
| **Temporal** | recurrence | Returning circular motion |
| **Temporal** | build | Intensifying flow + pulse |
| **Temporal** | rupture | Color inversion at 25s |
| **Temporal** | return | Calm after rupture |
| **Material** | phosphor glow | Multi-layer blur falloff |
| **Material** | grain | Noise overlay |
| **Material** | signal haze | Chromatic aberration (RGB shift) |

## Key Code Patterns

### Hardware-Aware Rendering

```python
from templates.video.render_runtime import detect_render_runtime

runtime = detect_render_runtime()
print(runtime.ffmpeg_path)   # Auto-detected
print(runtime.encoder)       # Best available
print(runtime.workers)       # Conservative default
```

### Worker Smoke Test

```python
from templates.video.parallel_render import ordered_frame_map

def smoke_test(runtime):
    def test(i): return i * i
    results = list(ordered_frame_map(
        range(4), test, workers=runtime.workers
    ))
    return results == [0, 1, 4, 9]
```

### Procedural Foley

```python
from templates.audio.sfx_gen import gen_wind, gen_impact, gen_shimmer

ambience = gen_wind(duration=10, intensity=0.5)
impact = gen_impact(duration=0.35, fundamental_hz=62)
shimmer = gen_shimmer(duration=3)
```

### FM Synthesis

```python
from templates.audio.audio_engine import FMSynth

synth = FMSynth(sample_rate=44100)
sample = synth.fm_sample(carrier=440, modulator=220, index=2.0)
```

## Extending

To add a new section using the main skill's vocabulary:

1. Pick a concept from `references/vocabulary-map.md`
2. Create a `render_frame_*()` function
3. Add audio stem generation
4. Register in `render_frame()` router

Example:
```python
def render_frame_cellular(frame_idx: int) -> Image.Image:
    """Cellular growth system (vocabulary-map: cellular systems)."""
    # Implement cellular automata growth
    pass
```

## Dependencies

- NumPy
- Pillow
- SciPy (optional, for advanced filtering)
- midiutil (optional, for MIDI score export)
- FFmpeg (auto-detected by render_runtime)

## Relationship to Main Skill

This lives in `experimental/` because:
- It's a reference implementation, not a core template
- It demonstrates integration of multiple templates
- It serves as educational documentation

The main skill's `examples/` folder is currently empty—this could graduate there as a canonical example.
