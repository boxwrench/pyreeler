# PyReeler Experimental

A self-contained sandbox for developing new PyReeler techniques, tools, and workflows. **Experimental films live here permanently**—this is not just a staging area, it's a habitat for work that may never graduate.

## Philosophy

The main PyReeler skill prioritizes stability, portability, and reproducibility. This space prioritizes **exploration, hardware-specific tuning, and surprising results**. Some techniques may be too niche, too hardware-dependent, or too personally tuned to ever leave. That's not failure—that's the point.

**What Belongs Here:**
- Films that depend on specific hardware (GPU shaders, CPU-specific optimizations)
- Techniques requiring heavy dependencies (SciPy, Numba, PyTorch)
- Personal parameter sets tuned to your machine's performance characteristics
- Explorations that are interesting but not generalizable
- Wild experiments that might fail

**Graduation Criteria (if you want to graduate something):**
- Works reliably across Windows/Linux without hardware-specific tuning
- Dependencies are small or optional
- Technique produces compelling results
- AI can direct it intuitively
- Render time reasonable relative to duration

## Structure

```
experimental/
├── skills/codex/          # Base skill copy (working foundation)
│   ├── SKILL.md
│   ├── references/
│   └── templates/
│
├── experiments/           # Film projects live HERE permanently
│   ├── sampler-film/      # 60s technique demonstration
│   ├── main-skill-demo/   # Comprehensive reference implementation
│   └── your-film-name/    # Your self-contained film projects
│       ├── main.py
│       ├── render.sh      # Hardware-tuned render command
│       └── NOTES.md       # Your specific tuning and findings
│
├── research/              # ALL reference documentation
│   ├── creative-lenses.md         # (from main skill)
│   ├── workflow.md                # (from main skill)
│   ├── audio-pipeline.md          # (from main skill)
│   ├── vocabulary-map.md          # (from main skill)
│   ├── generative-video-techniques.md  # Advanced algorithms research
│   ├── fm-synthesis.md            # Experimental techniques
│   ├── strange-attractors.md
│   └── ...
│
├── tools/                 # Reusable experimental utilities
│   ├── fm_synth.py
│   ├── attractors.py
│   └── TEMPLATE.py
│
├── notes/                 # Three types of notes (see below)
│   ├── hardware/          # Machine-specific tuning
│   ├── examples/          # Cool ways others used these tools
│   └── scratch/           # Loose observations, dead ends
│
├── GUIDE.md               # How to develop & graduate techniques
├── DEVLOG.md              # Chronological experiment log
└── README.md              # This file
```

## Notes Directory Explained

### notes/hardware/
**Hardware-specific tuning and performance notes.** What works on *your* machine.

Example entries:
- `ryzen-9-7950x-rtx4070.md` - Your workstation tuning
- `m3-macbook-pro.md` - Apple Silicon specific paths
- `intel-i5-integrated.md` - Low-end fallback settings

Content:
- Optimal worker counts for your CPU
- Encoder performance (NVENC vs QSV vs libx264 on your hardware)
- Memory limits that cause swapping
- Fastest resolution/CRF combinations for preview iteration

### notes/examples/
**Cool ways people have used these tools.** Inspiration and proven combinations.

Example entries:
- `lorenz-with-fm-bass.md` - Attractor visuals + FM audio combination
- `bytebeat-rhythm-layer.md` - Using bytebeat as percussion
- `reaction-diffusion-palette.md` - Color strategies for RD patterns

Content:
- What was tried
- Why it worked (or didn't)
- Parameter values that produced good results
- Render settings used

### notes/scratch/
**Loose observations, half-ideas, dead ends.** The notebook you don't have to organize.

- Random parameter combinations tried
- "What if..." musings
- Failed experiments and why they failed
- Links to inspiration sources

## Current Techniques

### Audio
| Technique | Dependencies | Status | Notes |
|-----------|-------------|--------|-------|
| FM Synthesis | NumPy | Ready | Bell, brass, woodwind presets |
| Bytebeat | NumPy | Ready | Demoscene-style bitwise audio |
| Additive Synthesis | NumPy | Planned | Sine wave stacking |

### Visual
| Technique | Dependencies | Status | Notes |
|-----------|-------------|--------|-------|
| Strange Attractors | NumPy, Pillow | **Ready** | Lorenz, Rössler - **vectorized 14x speedup** |
| Reaction-Diffusion | NumPy, SciPy | Ready | Gray-Scott patterns |
| L-Systems | NumPy | Planned | String rewriting growth |

### Completed Films

**`experimental_sampler.mp4`** (60s, 6.3MB)
- Demonstrates all 4 visual + 4 audio techniques
- 12 segments × 5 seconds
- **Render time: ~21 seconds** with vectorized renderer
- See `experiments/sampler-film/`

**`main_skill_demo.mp4`** (30s)
- **Comprehensive reference implementation** of main PyReeler skill
- Demonstrates ALL 4 reference docs + ALL templates
- Includes: hardware gate, worker smoke test, stem architecture
- creative-lenses, workflow, audio-pipeline, vocabulary-map
- See `experiments/main-skill-demo/`

## Reference Documentation (All Included)

The `research/` folder now contains **complete reference documentation** - both from the main skill and experimental research:

**Main Skill References (copied for convenience):**
- `creative-lenses.md` - Genre/mode, motif, repetition/rupture, time
- `workflow.md` - Production loop, preview/upscale, hardware gate
- `audio-pipeline.md` - Stem model, procedural foley, mixing
- `vocabulary-map.md` - Visual/audio/temporal/material systems

**Experimental Research:**
- `fm-synthesis.md` - FM synthesis from scratch
- `strange-attractors.md` - Lorenz, Rössler, vectorization
- `generative-video-techniques.md` - Advanced algorithms (Turing patterns, Boids, DLA, etc.)
- `reaction-diffusion.md` - Gray-Scott patterns
- `technique-use-cases.md` - When to use each technique

## Using This Skill

**Invoke pattern:**
```
Use the experimental PyReeler skill to make a 30s film using strange attractor visuals and FM synthesis audio. Read the research docs first, check hardware notes for render tuning.
```

**Before rendering:**
1. Check `notes/hardware/` for your machine's optimal settings
2. Review `notes/examples/` for proven combinations
3. Start with research doc's default parameters
4. Tune based on your hardware capabilities

## Creating an Experimental Film

1. **Create folder:** `experiments/my-film-name/`
2. **Copy templates:** From `tools/` or `skills/codex/templates/`
3. **Develop:** Iterate on your machine with your tuning
4. **Document:** Create `NOTES.md` in your film folder with:
   - Hardware used
   - Render times at different settings
   - Parameter evolution
   - Why specific choices were made
5. **Contribute:** If you find something cool, add to `notes/examples/`

## Dependencies

**Base:**
- Python 3.10+
- NumPy
- Pillow
- FFmpeg

**Experimental add-ons:**
- SciPy (for reaction-diffusion, filters)
- Numba (for JIT acceleration)
- Moderngl (for shader experiments)

Check technique-specific docs for requirements.

## Relationship to Main Skill

```
User request
     │
     ▼
┌─────────────────┐     ┌──────────────────┐
│  Use standard   │────▶│ Main PyReeler    │──▶ Portable output
│  techniques?    │     │ (skills/claude/) │    to ~/Videos
└─────────────────┘     └──────────────────┘
     │
     │ No, use experimental
     ▼
┌─────────────────┐     ┌──────────────────┐
│  Experimental   │────▶│ Stays in         │──▶ Hardware-tuned
│  techniques?    │     │ experiments/     │    local output
└─────────────────┘     └──────────────────┘
```

Experimental work is valid final output. Not everything needs to graduate.

---

*Last updated: 2026-03-15*
