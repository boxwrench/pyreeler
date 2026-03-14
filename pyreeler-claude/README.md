# PyReeler

PyReeler is a portable Claude Code skill for designing and delivering short code-generated films, loops, and experimental motion pieces.

It is built around a simple rule set:
- make a full-duration preview first
- keep previews cheap by lowering fidelity before lowering runtime
- judge the piece on arc, motif development, pacing, and landing
- only upscale after preview approval

## Contents

- `SKILL.md`: core skill instructions
- `references/`: workflow and creative references
- `references/audio-pipeline.md`: code-first guidance for procedural sound, stem design, mixing, and FFmpeg handoff
- `templates/audio/`: starter modules for procedural foley, optional scoring, optional voice, and stem mixing
- `templates/video/`: starter modules for portable render-runtime selection, encoder validation, and worker defaults
- `agents/claude.yaml`: Claude Code skill metadata
- `examples/`: sample output media for the repository page

## Usage

Install the skill into your Claude Code skills directory and invoke it with `/pyreeler`.

Example prompt:

```text
/pyreeler make a 45 second code-generated ritual film that begins calm, becomes entrancing, and ends with a single rupture.
```

## Audio Direction

PyReeler treats audio as a first-class part of the film structure.

- Default audio direction: procedural foley and ambience
- Optional music layer: compact SoundFont workflow
- Optional voice layer: `edge-tts`
- Preferred structure: `ambience`, `pulse`, `impacts`, `score`, and `voice` as separate conceptual stems

## Template Layer

The `templates/audio/` folder provides lightweight starters, not a full framework.

- `sfx_gen.py`: procedural ambience, impacts, and shimmer
- `composer.py`: motif-to-MIDI helpers and optional SoundFont rendering path
- `voice.py`: optional `edge-tts` helper
- `audio_engine.py`: simple stem placement, ducking, mastering, and WAV export

The `templates/video/` folder provides lightweight runtime helpers for portable FFmpeg decisions.

- `ffmpeg_utils.py`: host-profile detection, encoder smoke tests, and conservative worker heuristics
- `render_runtime.py`: one-call portable render defaults for encoder, ffmpeg path, and worker count
- `parallel_render.py`: multiprocess frame rendering with ordered output

## Dependency Approach

PyReeler uses a tiered dependency model.

- Core path: keep things working with small, common tools such as `ffmpeg`, `numpy`, and standard Python
- Recommended procedural audio path: add `scipy` when filtering materially improves the result
- Optional score path: add `midiutil` and `fluidsynth` or `pyfluidsynth`, plus a small SoundFont such as `TimGM6mb.sf2`
- Optional voice path: add `edge-tts` only when the piece actually needs voice

## Workflow Notes

- `Preview` means a full-duration piece for artistic review.
- `Test pass` means a technical or debugging render and should not be shown as the preview.
- If the chosen renderer cannot actually support the planned brief fields or behaviors, patch the implementation or narrow the brief before rendering.
- Prefer scripting deterministic work such as validation, render orchestration, sampling, and cleanup when it improves efficiency without reducing quality.
- Claude can read rendered PNG frames directly for visual review of arc, pacing, and composition.

## Portability Policy

The portable `pyreeler-claude` package should stay conservative.

- Prefer hardware-aware defaults over machine-specific hardcoding
- Validate hardware encoders before assuming they work
- Keep fallbacks reliable, especially `libx264`
- Avoid requiring heavy dependencies for the default path
- For local worker override, set `PYREEL_WORKERS_OVERRIDE` in the environment
- For local FFmpeg candidates, set `PYREEL_LOCAL_FFMPEG_CANDIDATES` (path-separator-delimited list)

## Modern Hardware Defaults

PyReeler has a portable path for common modern hardware profiles:

- NVIDIA: prefer `h264_nvenc` after validation
- Apple Silicon: prefer `h264_videotoolbox` after validation
- Intel graphics / Quick Sync: prefer `h264_qsv` after validation
- AMD graphics: prefer `h264_amf` after validation
- Unknown or unsupported environments: fall back to `libx264`

## Example Output

[![PyReeler Emergence poster](examples/pyreeler-emergence-poster.png)](examples/pyreeler-emergence.mp4)

Example film:
- `examples/pyreeler-emergence.mp4`

## GitHub Media Notes

GitHub supports images in Markdown and supports uploaded media files including `.mp4`, `.mov`, and `.webm`, but browser and codec behavior can still vary.

For a repository `README`, the safest presentation is still an image or GIF that links to an MP4 in the repo, or to an external host such as YouTube or Vimeo.

## Also Available For

PyReeler is also available as an OpenAI Codex skill. See the companion package.

## Publishing Notes

- This portable package is licensed under `MIT`. See `LICENSE`.
- If you adapt or redistribute PyReeler, please preserve the original copyright and license notice.
- If the skill name changes, update `SKILL.md`, `agents/claude.yaml`, and the enclosing folder name together.
