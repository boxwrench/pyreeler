# PyReeler for OpenAI Codex

PyReeler is a portable OpenAI Codex skill for designing and delivering short code-generated films, loops, and experimental motion pieces.

## Installation

Copy or symlink this folder to your Codex skills directory:

**macOS/Linux:**
```bash
ln -s $(pwd)/pyreeler ~/.codex/skills/pyreeler
```

**Windows:**
```powershell
# Copy to Codex skills directory
copy-item -recurse .\pyreeler $env:USERPROFILE\.codex\skills\pyreeler
```

## Usage

Invoke the skill with `$pyreeler`:

```text
Use $pyreeler to make a 45 second code-generated ritual film that begins calm, becomes entrancing, and ends with a single rupture.
```

## Contents

- `SKILL.md`: core skill instructions
- `references/`: workflow and creative references
- `references/audio-pipeline.md`: code-first guidance for procedural sound, stem design, mixing, and FFmpeg handoff
- `templates/`: lightweight starter modules for reusable audio structure
- `agents/openai.yaml`: UI metadata for skill lists and chips
- `examples/`: sample output media for the repository page

## Key Differences from Claude Version

- Invoke with `$pyreeler` (vs `/pyreeler` for Claude)
- Codex-specific agent configuration in `agents/openai.yaml`
- Same core workflow and templates

## License

MIT License. See [LICENSE](../LICENSE).

## See Also

- Main repository README for shared philosophy and workflow
- `pyreeler-claude/` for the Claude Code version
