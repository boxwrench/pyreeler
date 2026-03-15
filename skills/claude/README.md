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

### Common File Size Killers
| Content Type | Why It Bloates | Quick Fix |
|--------------|----------------|-----------|
| **Fine line patterns / moiré** | High-frequency noise, hard to compress | CRF 28, add slight blur/glow |
| **Film grain / noise** | Random data, no temporal redundancy | Consistent seed, reduce amplitude |
| **Fast motion** | Less frame-to-frame similarity | Lower FPS (18-24), motion blur |
| **High contrast edges** | Sharp transitions | Anti-aliasing, glow effects |
| **Alpha channels** | Extra data per pixel | Pre-composite before encoding |
| **CRF 18 or lower** | Visually lossless, huge files | Use CRF 23-28 |

### Common Render Time Killers
| Issue | Why It Slows Down | Fix |
|-------|-------------------|-----|
| **Sequential rendering** | 1 CPU core only | Use `parallel_render.py` with `runtime.workers` |
| **Canvas > output size** | Drawing pixels you don't see | Match canvas to viewport |
| **Recalculating per frame** | Same math 1440 times | Cache quantized values |
| **Python pixel loops** | Python is slow at pixel-level | Use NumPy vectorization |
| **Temp frame files** | Disk I/O bottleneck | Pipe directly to FFmpeg |

### The Interference Film Lesson
The **Interference** film (geometric moiré patterns) produced a 273MB file at CRF 18 — 10x larger than typical.

**Optimization results:**
- CRF 18 → CRF 28: 273MB → 99MB
- 1920x1080 canvas → 1600x900: Faster render
- Add angle caching: Faster + consistent
- **Combined**: 273MB → 61MB (78% smaller)

### Encoding Guidelines (60s @ 720p)
| Use Case | CRF | Typical Size |
|----------|-----|--------------|
| Archive/master | 18 | 200-400 MB |
| High quality | 20 | 80-150 MB |
| Default balance | 23 | 40-80 MB |
| Web sharing | 28 | 15-40 MB |

**Rule of thumb:**
- **Geometric/line-heavy**: CRF 25-28
- **Organic/particles**: CRF 20-23
- **Simple shapes**: CRF 23

## See Also

- Main repository README for shared philosophy and workflow
- `pyreeler/` for the OpenAI Codex version
