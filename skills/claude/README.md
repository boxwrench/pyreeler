<img src="../assets/logo/pyreeler_logo.png" width="100" align="right" alt="PyReeler logo">

# PyReeler for Claude Code

PyReeler is a portable Claude Code skill for designing and delivering short code-generated films, loops, and experimental motion pieces.

## Installation

Copy or symlink this folder to your Claude Code skills directory:

**macOS/Linux:**
```bash
ln -s $(pwd)/pyreeler-claude ~/.claude/skills/pyreeler
```

**Windows:**
```powershell
# Copy to Claude skills directory
copy-item -recurse .\pyreeler-claude $env:APPDATA\Claude\skills\pyreeler
```

## Usage

Invoke the skill with `/pyreeler`:

```text
/pyreeler make a 45 second code-generated ritual film that begins calm, becomes entrancing, and ends with a single rupture.
```

## Contents

- `SKILL.md`: core skill instructions
- `references/`: workflow and creative references
- `references/audio-pipeline.md`: code-first guidance for procedural sound, stem design, mixing, and FFmpeg handoff
- `templates/audio/`: starter modules for procedural foley, optional scoring, optional voice, and stem mixing
- `templates/video/`: starter modules for portable render-runtime selection, encoder validation, and worker defaults
- `agents/claude.yaml`: Claude Code skill metadata

## Examples

See root `examples/` folder for sample output media.

## Key Differences from Codex Version

- Invoke with `/pyreeler` (vs `$pyreeler` for Codex)
- Claude-specific agent configuration in `agents/claude.yaml`
- Claude can read rendered PNG frames directly for visual review of arc, pacing, and composition
- Includes `PYREEL_WORKERS_OVERRIDE` and `PYREEL_LOCAL_FFMPEG_CANDIDATES` environment variables for local overrides
- Additional `parallel_render.py` for multiprocess frame rendering

## License

MIT License. See [LICENSE](../LICENSE).

## Performance & File Size Notes

### The Interference Film Lesson
The **Interference** film (geometric moiré patterns) produced a 273MB file at CRF 18 — 10x larger than typical outputs. Why?

**Hard-to-compress content:**
- Fine line grids create high-frequency moiré patterns
- Each frame is visually noisy (hard for H.264 to compress)
- Constant motion (rotating grids) reduces temporal redundancy

**Mitigation:**
- Use **CRF 28** for web-friendly output (~60MB)
- Consider lower resolution for dense geometric patterns
- Add slight glow/blur to reduce high-frequency noise

### Encoding Guidelines
| Use Case | CRF | Size (60s 720p) |
|----------|-----|-----------------|
| Archive/master | 18 | 200-400 MB |
| High quality | 23 | 50-100 MB |
| Web sharing | 28 | 15-60 MB |

### Content Types & Compression
- **Simple shapes/colors**: Compress well (low frequency)
- **Particles/organic**: Moderate compression
- **Fine lines/grids/moiré**: Poor compression (high frequency)
- **Fast motion**: Poor compression (less redundancy)

## See Also

- Main repository README for shared philosophy and workflow
- `pyreeler/` for the OpenAI Codex version
