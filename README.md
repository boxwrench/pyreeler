<img src="assets/logo/pyreeler_logo.png" width="120" align="right" alt="PyReeler logo">

# PyReeler

PyReeler is a portable skill for designing and delivering short code-generated films, loops, and experimental motion pieces. Available for both **OpenAI Codex** and **Claude Code**.

It is intentionally skill-first rather than framework-first. The portable package stays lightweight, readable, and dependable across common modern hardware.

It is built around a simple rule set:
- Make a full-duration preview first
- Keep previews cheap by lowering fidelity before lowering runtime
- Judge the piece on arc, motif development, pacing, and landing
- Only upscale after preview approval

## Available Versions

| Version | Location | Invoke With |
|---------|----------|-------------|
| **OpenAI Codex** | `pyreeler-codex/` | `$pyreeler` |
| **Claude Code** | `pyreeler-claude/` | `/pyreeler` |

Both versions share the same core philosophy and workflow, adapted for each AI's capabilities.

## Quick Start

### For Codex Users
```text
Use $pyreeler to make a 45 second code-generated ritual film that begins calm, becomes entrancing, and ends with a single rupture.
```

### For Claude Users
```text
/pyreeler make a 45 second code-generated ritual film that begins calm, becomes entrancing, and ends with a single rupture.
```

## Featured Example: PyReeler Emergence

[![PyReeler Emergence](assets/showcase/pyreeler-emergence.mp4)](assets/showcase/pyreeler-emergence.mp4)

A code-generated experimental motion piece created with PyReeler.

### More Examples

See [`assets/showcase/`](assets/showcase/) for additional films:
- `ascii-cosmic-dragon-720p.mp4`
- `pyreel_ghost_in_the_machine_720p_final.mp4`
- `terminal_genesis_pro_preview.mp4`

## Repository Structure

```
pyreeler/
├── assets/                # Logo and showcase media
│   ├── logo/              # PyReeler branding assets
│   └── showcase/          # Featured example films
│
├── examples/              # Example films and outputs
│
├── pyreeler-codex/        # OpenAI Codex skill
│   ├── SKILL.md           # Core skill instructions
│   ├── agents/openai.yaml # Codex skill metadata
│   ├── references/        # Workflow & creative guides
│   └── templates/         # Audio/video starter modules
│
├── pyreeler-claude/       # Claude Code skill
│   ├── SKILL.md           # Core skill instructions
│   ├── agents/claude.yaml # Claude skill metadata
│   ├── references/        # Workflow & creative guides
│   └── templates/         # Audio/video starter modules
│
├── local_nvidia/          # NVIDIA GPU experiments (optional)
└── DEVLOG.md              # Development history
```

## Using This Skill With Other AI Models

The PyReeler skill is documented in human-readable Markdown and YAML files. Other AI models can:

- **Read and adapt** the skill files (`SKILL.md`, `references/`, `templates/`) for their own skill systems
- **Implement as a prompt** by reading the workflow guidance and creative references directly into context

The skill is intentionally code-first and framework-agnostic. The core principles (preview-first, hardware-aware rendering, stem-based audio) can be applied regardless of the AI platform.

## Core Principles

### Audio Direction
PyReeler treats audio as a first-class part of the film structure:
- **Default**: procedural foley and ambience
- **Optional music**: compact SoundFont workflow
- **Optional voice**: `edge-tts`
- **Structure**: `ambience`, `pulse`, `impacts`, `score`, and `voice` as separate conceptual stems

### Template Layer
The `templates/` folder provides lightweight starters, not a full framework:
- `sfx_gen.py`: procedural ambience, impacts, and shimmer
- `composer.py`: motif-to-MIDI helpers and optional SoundFont rendering path
- `voice.py`: optional `edge-tts` helper
- `audio_engine.py`: simple stem placement, ducking, mastering, and WAV export
- `ffmpeg_utils.py`: host-profile detection, encoder smoke tests, and conservative worker heuristics
- `render_runtime.py`: one-call portable render defaults for encoder, ffmpeg path, and worker count
- `parallel_render.py`: multiprocess frame rendering with ordered output (Claude version)

### Dependency Approach
PyReeler uses a tiered dependency model:
- **Core path**: `ffmpeg`, `numpy`, and standard Python
- **Recommended audio**: add `scipy` when filtering materially improves the result
- **Optional score**: add `midiutil` and `fluidsynth`/`pyfluidsynth`, plus a small SoundFont
- **Optional voice**: add `edge-tts` only when needed

### Workflow Notes
- **Preview**: full-duration piece for artistic review
- **Test pass**: technical/debugging render (not shown as preview)
- Always make a preview version first
- Never present a partial-duration render as the preview
- Surface the preview to the user before committing to an upscale
- Export approved finals to `~/Videos`

### Portability Policy
The portable package stays conservative:
- Prefer hardware-aware defaults over machine-specific hardcoding
- Validate hardware encoders before assuming they work
- Keep fallbacks reliable, especially `libx264`
- Avoid requiring heavy dependencies for the default path

### Modern Hardware Defaults
PyReeler has a portable path for common modern hardware:
- **NVIDIA**: prefer `h264_nvenc` after validation
- **Apple Silicon**: prefer `h264_videotoolbox` after validation
- **Intel / Quick Sync**: prefer `h264_qsv` after validation
- **AMD**: prefer `h264_amf` after validation
- **Unknown/unsupported**: fall back to `libx264`

## GitHub Media Notes

GitHub supports images in Markdown and uploaded media files (`.mp4`, `.mov`, `.webm`), but browser and codec behavior can vary.

For a repository `README`, the safest presentation is an image or GIF that links to an MP4 in the repo, or to an external host such as YouTube or Vimeo.

## Installing

**Tested on Windows and Ubuntu Linux.**  
**macOS support is expected** (the code handles Apple Silicon and `h264_videotoolbox`) but has not been personally verified.

### Prerequisites

**macOS** (untested):
```bash
brew install ffmpeg
# Optional: brew install fluidsynth
```

**Linux** (Ubuntu tested):
```bash
sudo apt-get install ffmpeg
# Optional: sudo apt-get install fluidsynth
```

**Windows** (tested):
- Install [FFmpeg](https://ffmpeg.org/download.html) and add to PATH
- Optional: Install [FluidSynth](https://github.com/FluidSynth/fluidsynth/releases)

### Codex
Copy or symlink `pyreeler-codex/` to your Codex skills directory:
- **macOS/Linux**: `~/.codex/skills/`
- **Windows**: `%USERPROFILE%\.codex\skills\`

### Claude Code
Copy or symlink `pyreeler-claude/` to your Claude Code skills directory:
- **macOS/Linux**: `~/.claude/skills/`
- **Windows**: `%APPDATA%\Claude\skills\`

See the individual skill folders for detailed installation instructions.

## License

MIT License. See [LICENSE](LICENSE).

If you adapt or redistribute PyReeler, please preserve the original copyright and license notice.
