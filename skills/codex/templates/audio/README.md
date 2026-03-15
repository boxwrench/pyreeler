# Audio Templates

These templates are lightweight starters, not a full engine.

Use them when a film script needs a reusable audio backbone without turning the skill into a heavy framework.

## Files

- `sfx_gen.py`: procedural ambience, impacts, and shimmer
- `composer.py`: motif-to-MIDI helpers and optional SoundFont workflow
- `voice.py`: optional `edge-tts` helper for narration or machine voice
- `audio_engine.py`: stem placement, ducking, mastering, and WAV export

## Dependency Tiers

Core:

- `numpy`
- `ffmpeg`

Recommended for procedural filtering:

- `scipy`

Optional music:

- `midiutil`
- `fluidsynth` or `pyfluidsynth`
- a small SoundFont such as `TimGM6mb.sf2`

Optional voice:

- `edge-tts`

## Suggested Flow

1. Generate `ambience`, `pulse`, and `impacts` as arrays with `sfx_gen.py`.
2. Generate `score` events with `composer.py` if the piece needs melodic or harmonic motion.
3. Render `voice` only if speech materially helps the piece.
4. Place and mix stems with `audio_engine.py`.
5. Hand the final WAV to `ffmpeg`.

## Design Rule

Keep the film script focused on timing and structure.
Keep synthesis, voice rendering, and mixing logic in helper modules.
