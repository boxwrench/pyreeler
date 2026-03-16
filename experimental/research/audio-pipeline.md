# Audio Pipeline

Use this reference when the piece's sound needs to do more than fill space.

## Goals

- Keep the audio pipeline lightweight, code-first, and hardware-agnostic.
- Prefer procedural synthesis and algorithmic composition over large sample libraries.
- Treat audio as part of the film's structure, not as a last-step overlay.
- Keep the LLM focused on timing, motif, and scene function rather than raw DSP details.

## Golden Path

When building or extending a Python film generator, prefer this stack:

1. Generate ambience and foley procedurally with `numpy` and `scipy`.
2. Generate score events as MIDI or note logic rather than raw sample edits.
3. Use a small SoundFont with `pyfluidsynth` when real instrument timbre materially helps.
4. Mix stems in memory with simple gain staging first. Add `pedalboard` or equivalent DSP tooling only when it materially improves the result.
5. Hand mastered audio directly to `ffmpeg` instead of writing unnecessary temporary WAV files.

## Stem Model

Prefer separate stems with distinct narrative jobs:

- `ambience`: wind, hum, rumble, room tone, environmental beds
- `pulse`: rhythmic propulsion, gated motion, entrainment
- `impacts`: hits, swells, accents, transitions, scene punctuation
- `score`: harmonic or melodic development
- `voice`: speech, machine readouts, narration, whispers

Use the brief or timeline to control when stems enter, thin out, collide, or disappear.

## Procedural Foley

Use simple building blocks first:

- white, pink, or brown noise for weather, hiss, rustle, or rumble
- sine, square, or triangle oscillators for drones, tones, and body resonance
- short noise bursts for transients
- exponential or curved envelopes for impacts, swells, and fades
- low-pass filtering and resonance for wind, pressure, and cinematic weight

Typical mappings:

- wind or atmosphere: filtered brown or pink noise with slowly changing cutoff
- impacts or thumps: low-frequency tone plus short noise transient
- glitches or ticks: short bright bursts with sharp decay
- shimmer: high-frequency partials with a long fade

## Music Strategy

Default to procedural or rule-based music before reaching for heavier tooling.

When the piece benefits from more instrumental color:

- use `MIDIUtil` or compact note logic to describe score events
- render with `pyfluidsynth`
- prefer a compact SoundFont such as `TimGM6mb.sf2`

Do not introduce large audio asset packs unless the concept genuinely requires them.

## Mixing Rules

- Mix by stem, not by one monolithic waveform.
- Keep gain staging simple and intentional.
- Duck score under voice or critical impacts when clarity matters.
- Use compression lightly to glue stems together.
- Keep preview mixes readable rather than polished to death.

For short-film previews, simple balances often beat elaborate mastering chains.

## LLM Interface

Prefer high-level audio macros or helper functions over repeated handwritten DSP:

- `gen_ambience(kind, level, start, end)`
- `trigger_sfx(kind, time, intensity)`
- `set_score(style, tempo, motif)`
- `mix_master()`

The model should mostly decide structure and timing. Reusable modules should handle synthesis, rendering, and mixing details.

## Preview Policy

- Audio must be present in the preview if the final piece depends on it.
- Keep the full runtime even when preview fidelity is low.
- Lower complexity before removing structure: fewer layers, simpler filters, shorter effect tails.
- Preserve key cues that carry the arc: voids, impacts, transitions, and the final move.

## Hardware Notes

- Prefer vectorized `numpy` operations over Python loops.
- Use `float32` or `int16` where appropriate to control memory use.
- Keep stems memory-resident when practical.
- Let `ffmpeg` handle final encoding rather than overbuilding custom export logic.

## Avoid

- giant sample folders as a default dependency
- single-function audio generators that cannot separate stems
- music beds that ignore scene timing
- temp-file-heavy pipelines when in-memory handoff is practical
- complex DSP code in the main film script when helper modules can encapsulate it
