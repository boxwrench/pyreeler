<div align="center">
  <img src="assets/readme/banner.svg" alt="PyReeler — code-generated cinema, conjured from math" width="100%">
</div>

<div align="center">

[**🎞️ Step into the Showcase Gallery →**](https://boxwrench.github.io/pyreeler/)

</div>

# PyReeler

> *Give an AI a render farm and it makes a music video. Give it a few hundred lines of NumPy and a sense of restraint, and it makes a **film**.*

**PyReeler turns an AI assistant into a director of short, code-generated cinema** — loops, rituals, glitch-poems, and experimental motion pieces conjured entirely from math, pixels, and procedural sound. No model weights. No stock footage. No "prompt and pray." Just code that knows how to *pace itself*.

It runs as a portable skill for both **OpenAI Codex** and **Claude Code**. Skill-first, not framework-first: the whole package stays lightweight, readable, and stubborn about working on the hardware you already own.

### The House Rules

PyReeler believes a film is an *arc*, not a wallpaper. So it follows a small creed:

- 🎬 **Preview the whole thing first** — full duration, every time. A great 5 seconds is not a film.
- 🪶 **Cheap previews, fast iterations** — drop fidelity before you drop runtime. See the shape, then make it pretty.
- 🎭 **Judge it like a critic** — arc, motif, pacing, and *the landing*. Does it end, or does it just stop?
- ✨ **Only upscale what earns it** — pixels are a reward for a piece that already works.

<div align="center"><img src="assets/readme/wave-divider.svg" alt="" width="100%"></div>

## The Beauty of Math, Rendered

PyReeler's whole thesis fits in two pictures. A few equations, integrated frame by frame, become something you'd hang on a wall. *(Both of these were drawn by `assets/readme/generate_readme_art.py` — the README art is code-generated too, naturally.)*

<div align="center">
  <table>
    <tr>
      <td align="center"><img src="assets/readme/lissajous.svg" alt="Lissajous curve" width="360"></td>
      <td align="center"><img src="assets/readme/lorenz.svg" alt="Lorenz attractor" width="360"></td>
    </tr>
    <tr>
      <td align="center"><em>A Lissajous figure — two sine waves at right angles, dancing.</em></td>
      <td align="center"><em>The Lorenz attractor — chaos that never repeats, yet never escapes.</em></td>
    </tr>
  </table>
</div>

This is the feeling PyReeler chases: not "render a thing," but *make the math perform.*

<div align="center"><img src="assets/readme/wave-divider.svg" alt="" width="100%"></div>

## Available Versions

PyReeler has three ways to use it:

| Version | What It Is | Location | Start With |
|---------|------------|----------|------------|
| **Local CLI + TUI** | Offline recipe renderer with an animated terminal UI | `pyreeler/` | `python3 -m pyreeler` |
| **Claude Code skill** | AI-assisted film workflow for Claude Code | `skills/claude/` | `/pyreeler` |
| **OpenAI Codex skill** | AI-assisted film workflow for Codex | `skills/codex/` | `$pyreeler` |

The two AI skill versions share the same core workflow and templates, including
the reusable PYREELER terminal banner template. The local CLI/TUI is the
deterministic recipe browser and renderer you can run without an AI.

## Quick Start

Talk to it like a director talks to a cinematographer — give it a feeling and an arc, not a parameter dump.

### Install the AI Skill

From the repository root:

```bash
./install.sh          # installs the Claude Code skill, invoked with /pyreeler
./install.sh codex    # installs the Codex skill, invoked with $pyreeler
```

Install both if you use both assistants.

### For Codex Users
```text
Use $pyreeler to make a 45 second code-generated ritual film that begins calm, becomes entrancing, and ends with a single rupture.
```

### For Claude Users
```text
/pyreeler make a 45 second code-generated ritual film that begins calm, becomes entrancing, and ends with a single rupture.
```

Then watch it sweat the pacing for you.

<div align="center"><img src="assets/readme/wave-divider.svg" alt="" width="100%"></div>

## Use It Without an AI (CLI)

PyReeler also ships a deterministic command-line renderer — no AI, no API cost,
fully offline. Pick a recipe, turn the knobs, render:

```bash
python3 -m pyreeler list                                   # see available recipes
python3 -m pyreeler render lorenz --duration 30 -o butterfly.mp4
python3 -m pyreeler render rossler --c 5.7 --palette amber -o scroll.mp4
```

Every recipe exposes typed, range-checked flags (`--rho`, `--fps`, `--palette`, …) —
run `python3 -m pyreeler render <recipe> -h` to see them. Core deps are just
`numpy` + `pillow` + FFmpeg.

Prefer it interactive? `pip install -r requirements-tui.txt` then run **`python3 -m pyreeler`**
with no arguments for the full TUI — a phosphor PYREELER banner, a recipe browser, a
live parameter form (with `[-]`/`[+]` steppers, a `‹ ›` palette cycler, and a
recipe filter box — press `p` to play the finished render), and a render progress
bar with a Sparkline. Renders land in
`~/Videos` with auto-incrementing names (`lorenz.mp4`, `lorenz-2.mp4`, …), so a new
render never overwrites an earlier one.

## Featured Films

Every frame below was born from a script you can read, run, and remix:

- `films/interference/` — *geometric moiré, breathing in and out of resonance.* 60s
- `films/sentient-weather/` — *particle systems that seem to have moods.* 60s
- `films/what-the-light-kept/` — *an AI sifting its own memory fragments.* 45s
- `films/dungeon-emergence/` — *a world assembling itself out of ASCII.* 45s

**Note:** A small set of low-bitrate showcase clips is committed under `assets/showcase/` to power the gallery above. Full-resolution finals and preview renders are *not* tracked — `.gitignore` excludes `*.mp4`/`*.mov`/`*.avi` by default, so generate those locally and export approved finals to `~/Videos`.

## Repository Structure

```
pyreeler/
├── skills/                  # AI assistant skills
│   ├── _shared/             # Canonical shared reference docs used by sync.py
│   ├── claude/              # Claude Code skill
│   └── codex/               # OpenAI Codex skill
│
├── films/                   # Complete film projects
│   ├── interference/
│   ├── sentient-weather/
│   ├── what-the-light-kept/
│   └── dungeon-emergence/
│
├── research/                # [Research Index](research/INDEX.md) — Effects, timelines, inspiration
│
├── templates/               # Shared audio/video starter modules
│   ├── audio/               # sfx_gen.py, composer.py, audio_engine.py, voice.py
│   └── video/               # ffmpeg_utils.py, render_runtime.py, parallel_render.py
│
├── docs/
│   ├── specs/               # Design specifications
│   ├── plans/               # Implementation plans
│   └── benchmarks/          # Performance benchmarks
│
├── assets/                  # Logo and static media
├── tests/                   # Test suite (run with `pytest`)
├── sync.py                  # Distributes canonical templates into the skill folders
└── DEVLOG.md                # Development history
```

## Development

`templates/` (repo root) is the single source of truth for template code.
`skills/_shared/references/` is the source for reference docs that are
byte-identical across providers. Each skill must ship self-contained, so these
files are physical copies in `skills/claude/` and `skills/codex/`. After editing
either source tree, redistribute the copies:

```bash
python3 sync.py          # copy canonical files into skills/claude and skills/codex
python3 sync.py --check  # verify nothing has drifted (used in CI)
python3 graduation_check.py  # verify graduated templates are declared/tested/proven
python3 -m pytest -q     # run the test suite
```

A graduated template is a portable helper whose canonical source lives in
`templates/`, is declared in `template_graduation.toml`, is distributed into both
skill folders by `sync.py`, has at least one test path, and has at least one
example film/demo or documented usage path.

## Using This Skill With Other AI Models

The PyReeler skill is documented in human-readable Markdown and YAML files. Other AI models can:

- **Read and adapt** the skill files (`skills/*/SKILL.md`, `templates/`, `research/`) for their own skill systems
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
- `audio_reactive.py`: per-frame RMS envelopes for audio-driven visual parameters
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

### War Stories: Things That Bit Us So They Won't Bite You

Every number in these tables was paid for in render time and disk space. The **Interference** film — all those gorgeous moiré patterns — once weighed **273MB for 60 seconds at 720p**. That's 10× heavier than it had any right to be. Here's what we learned dragging it back down to earth.

#### Content That Bloats File Size
| Content Type | Why It Bloats | Mitigation |
|--------------|----------------|------------|
| **Fine line patterns** (grids, moiré) | High-frequency noise, hard to compress | CRF 28, add slight blur/glow, lower resolution |
| **Film grain / noise** | Random data, no temporal redundancy | Use consistent seed, reduce noise amplitude |
| **Fast motion** | Less frame-to-frame similarity | Lower FPS (18-24), motion blur |
| **High contrast edges** | Sharp transitions | Slight anti-aliasing, glow effects |
| **Alpha channels** | Extra data per pixel | Pre-composite, don't render transparency |
| **Lossless codecs** | No compression | Use H.264 with CRF 23-28 |

#### Render Time Killers
| Issue | Why It Slows Down | Fix |
|-------|-------------------|-----|
| **Sequential frame rendering** | 1 CPU core only | Use `parallel_render.py` with `runtime.workers` |
| **Canvas larger than output** | Drawing pixels you don't see | Match canvas to viewport when possible |
| **Recalculating every frame** | Same math 1440 times | Cache quantized values, precompute static layers |
| **Python loops over pixels** | Python is slow at pixel-level work | Use NumPy vectorization, PIL operations |
| **Writing temp frame files** | Disk I/O bottleneck | Pipe frames directly to FFmpeg |

#### Encoding Guidelines (60s @ 720p)
| CRF | Quality | Typical Size | Use For |
|-----|---------|--------------|---------|
| 18 | Visually lossless | 150-400 MB | Archive masters |
| 20 | Excellent | 80-150 MB | High-quality delivery |
| 23 | Very good | 40-80 MB | Default balance |
| 28 | Good | 15-40 MB | Web sharing, previews |

**Rule of thumb:**
- **Geometric/line-heavy films**: CRF 25-28
- **Organic/particle films**: CRF 20-23
- **Simple shapes/colors**: CRF 23

#### The Interference Film Optimizations
| Issue | Fix | Result |
|-------|-----|--------|
| CRF 18 | Use CRF 28 | 273MB → 99MB |
| 1920x1080 canvas | Use 1600x900 | Faster render, less memory |
| Recalculating lines | Cache quantized angles | Faster + consistent |
| Combined | All above | 273MB → 61MB (78% smaller)

<div align="center"><img src="assets/readme/wave-divider.svg" alt="" width="100%"></div>

## Installing

**Requires Python 3.10+ and FFmpeg on your `PATH`.** (`numpy` + `pillow` are installed for you; FFmpeg is the one external tool you must install yourself — see Prerequisites below.)

**Tested on Windows and Ubuntu Linux.**
**macOS support is expected** (the code handles Apple Silicon and `h264_videotoolbox`) but has not been personally verified.

### macOS/Linux: AI Skills

```bash
git clone https://github.com/boxwrench/pyreeler.git && cd pyreeler
./install.sh          # Claude Code skill -> ~/.claude/skills/pyreeler
./install.sh codex    # Codex skill      -> ~/.codex/skills/pyreeler
```

Run one or both installer commands depending on which assistant you use. The
installer checks for FFmpeg, runs `pip install -r requirements.txt` (just `numpy`
+ `pillow`), and symlinks the selected skill into place. The only thing it can't
install for you is **FFmpeg itself** — see Prerequisites below.

After install:

```text
/pyreeler     # Claude Code
$pyreeler     # OpenAI Codex
```

Optional capabilities (music, voice, SciPy filters) live in
`requirements-extras.txt`:

```bash
python3 -m pip install -r requirements-extras.txt
```

### Local CLI + Animated TUI

The local renderer is separate from the AI skill invocation. It needs **Python
3.10+** and **FFmpeg** on your `PATH` (the `render` step shells out to it). From
the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 -m pyreeler list
python3 -m pyreeler render lorenz --duration 30 -o butterfly.mp4
```

Pass `-o` to choose the exact output path (it's written as-is). Without `-o`,
renders land in `~/Videos` with auto-incrementing names (`lorenz.mp4`,
`lorenz-2.mp4`, …) — the same no-overwrite policy the TUI uses.

For the animated terminal UI:

```bash
python3 -m pip install -r requirements-tui.txt
python3 -m pyreeler
```

### Windows: Manual Skill Install

Windows users should install FFmpeg, run Python deps from the repository root,
then copy the desired skill folder:

```powershell
python -m pip install -r requirements.txt

# Claude Code
Copy-Item -Recurse .\skills\claude $env:APPDATA\Claude\skills\pyreeler

# OpenAI Codex
Copy-Item -Recurse .\skills\codex $env:USERPROFILE\.codex\skills\pyreeler
```

For the local animated TUI on Windows:

```powershell
python -m pip install -r requirements-tui.txt
python -m pyreeler
```

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
Copy or symlink `skills/codex/` to your Codex skills directory:
- **macOS/Linux**: `~/.codex/skills/`
- **Windows**: `%USERPROFILE%\.codex\skills\`

### Claude Code
Copy or symlink `skills/claude/` to your Claude Code skills directory:
- **macOS/Linux**: `~/.claude/skills/`
- **Windows**: `%USERPROFILE%\.claude\skills\` (i.e. `~/.claude/skills/`). Native symlinks need admin or Developer Mode; a directory junction works without elevation: `mklink /J "%USERPROFILE%\.claude\skills\pyreeler" "<repo>\skills\claude"`

See the individual skill folders for detailed installation instructions:
`skills/claude/README.md` and `skills/codex/README.md`.

## License

MIT License. See [LICENSE](LICENSE).

If you adapt or redistribute PyReeler, please preserve the original copyright and license notice.

---

<div align="center">

*Made for people who think a `for` loop can be a camera move.*

**Now go make something that ends well.** 🎬

</div>
