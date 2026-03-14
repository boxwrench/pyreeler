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

## See Also

- Main repository README for shared philosophy and workflow
- `pyreeler/` for the OpenAI Codex version
