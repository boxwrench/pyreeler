<img src="../assets/logo/pyreeler_logo.png" width="100" align="right" alt="PyReeler logo">

# PyReeler for OpenAI Codex

PyReeler is a portable OpenAI Codex skill for designing and delivering short code-generated films, loops, and experimental motion pieces.

## Installation

**Easiest:** from the repository root, run `./install.sh codex` — it checks for
FFmpeg, installs the core Python deps, and symlinks this skill for you.

**Manual** — copy or symlink this folder to your Codex skills directory. Run these
from the repository root:

**macOS/Linux:**
```bash
ln -s "$(pwd)/skills/codex" ~/.codex/skills/pyreeler
```

**Windows (PowerShell):**
```powershell
Copy-Item -Recurse .\skills\codex $env:USERPROFILE\.codex\skills\pyreeler
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

## Examples

See root `examples/` folder for sample output media.

## License

MIT License. See [LICENSE](../LICENSE).

## See Also

- Main repository README for shared philosophy and workflow
- `pyreeler-claude/` for the Claude Code version
