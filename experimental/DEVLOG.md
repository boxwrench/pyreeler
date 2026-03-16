# PyReeler Experimental Dev Log

Chronological log of experiments, findings, and technique development.

---

## 2026-03-16: ParameterSequence Demo Film COMPLETE ✓ MOVIE PRODUCED

**Changes:**
- Created `experiments/parameter-sequence-demo/` - full film demonstrating
  cross-domain parameter automation
  - 60 seconds, 4 techniques (Lorenz, Rössler, FM Bell, FM Drone)
  - Moderate complexity: 3 parameters per technique
  - ParameterSequence drives both visuals and audio simultaneously
  - Narrative arc: emergence → orbit → chaos → resolution
- Precomputation strategy for attractor trajectories (performance)
- Frame-by-frame audio generation synchronized to parameter curves
- Sequences exported as JSON for editing/sharing
- FFmpeg detection with graceful fallback
- **MOVIE ENCODED** using moviepy (FFmpeg not available, used Python alternative)

**Performance (Actual):**
- Precomputation: ~0.6s
- Video render (1440 frames): ~18s
- Audio render: ~0.3s
- Movie encoding: ~30s
- **Total: ~50s** (still faster than estimated!)

**Output Artifacts:**
- ✅ `output/demo_final.mp4` - **3.8 MB, 60 seconds, 24fps** with audio
- ✅ `output/audio.wav` - 5.5 MB, 60 seconds FM synthesis
- ✅ `output/frames/*.png` - 1440 individual frames
- ✅ `output/sequences/*.json` - 4 parameter sequence files

**Result:** Demo runs successfully. **Movie produced.** 1440 frames + 60s audio
generated from parameter sequences, encoded into final MP4. First film
demonstrating ParameterSequence's core value - one sequence file defining a
complete audio-visual experience.

**Files added:**
- NEW: `experiments/parameter-sequence-demo/main.py` (340 lines)
- NEW: `experiments/parameter-sequence-demo/README.md`
- NEW: `output/sequences/*.json` (4 parameter sequence files)
- NEW: `output/demo_final.mp4` (3.8 MB - binary, not committed)

**Note:** The MP4 is ~3.8MB. As a binary file, it's excluded from git via
.gitignore. Run `python main.py` locally to regenerate.

**Next:** Iterate on parameter curves, or move on to next technique.

---

## 2026-03-16: ParameterSequence Demo Film Created

---

## 2026-03-16: ParameterSequence Implementation

**Changes:**
- Created `tools/parameter_sequence.py` - full working implementation
  - `ParameterSequence` class with record/playback/interpolation
  - JSON serialization for shareable "recipes"
  - Utility presets: `ramp()`, `pulse()`, `hold()`
  - Time scaling and sequence copying operations
- Created `ROADMAP.md` - tracks decisions and future options
  - Documents the 4 options from Pixel Sorting planning
  - Decision log format for context preservation
  - Future technique and infrastructure categories

**Result:** Reproducible parameter automation now works across ALL
techniques. The infrastructure investment enables version-controlled
experiments and batch automation.

**Files added:**
- NEW: `tools/parameter_sequence.py` (260 lines, tested)
- NEW: `ROADMAP.md` (options tracking)

**Next:** Integrate ParameterSequence with existing tools (attractors,
fm_synth) to demonstrate parameter sequencing in action.

---

## 2026-03-16: Pixel Sorting Integration

**Changes:**
- Added Image Processing category with Pixel Sorting technique
  - Created `research/pixel-sorting.md` - full technique documentation
  - Added algorithm variants: threshold, interval, mask, angle sorts
  - Included AI Direction Vocabulary for glitch aesthetics
- Documented Parameter Sequencing pattern in GUIDE.md
  - `ParameterSequence` class for record/playback of parameter changes
  - Enables reproducible experiments and shareable "recipes"
- Added Pre/Post Processing Pipeline hybrid architecture
  - 4 documented patterns combining Pixel Sorting with existing techniques
  - Pre-process: RD → Pixel Sort → Particles, Attractor → Pixel Sort Mask
  - Post-process: Particles → Pixel Sort, Multi-layer Stacking

**Result:** Experimental folder now covers image-processing-based glitch aesthetics
and reproducible parameter automation - filling gaps in the technique taxonomy.

**Files added/modified:**
- NEW: `research/pixel-sorting.md`
- MOD: `research/INDEX.md` (Image Processing category)
- MOD: `GUIDE.md` (Parameter Sequencing + Hybrid Pipelines)
- MOD: `research/TEMPLATE.md` (Parameter Sequencing section)

---

## 2026-03-16: Research Documentation Consolidated

**Changes:**
- Copied ALL main skill references to `experimental/research/`
  - `creative-lenses.md`
  - `workflow.md`
  - `audio-pipeline.md`
  - `vocabulary-map.md`
- Added advanced research: `generative-video-techniques.md`
  - Turing patterns, Boids, DLA, flow fields
  - Circle packing, Voronoi, Poisson disk sampling
  - Hybrid architectures

**Result:** Experimental folder now contains complete reference documentation.
All research lives in one place - no need to reference main skill docs separately.

---

## 2026-03-15: Sampler Render - SUCCESS

**Attempt 4:** 480p disk-based - **SUCCESS!**

**What worked:**
- Precompute ALL trajectories at startup (separate simulation from rendering)
- Write PNG frames to disk, then FFmpeg encode (avoid stdin pipe issues on Windows)
- 854×480, 30 particles, 3000 points

**Result:**
- `experimental_sampler.mp4` - 50 seconds, 5.5MB
- 10 segments × 5 seconds of FM synthesis + strange attractors
- Render time: ~90 seconds total

**Issues to debug separately:**
- FFmpeg stdin piping hangs at 83% on Windows
- Particle cloud segment causes issues at frame 1200 (50s mark)

**Deliverable:** Working 50s sampler demonstrating all experimental techniques

## 2026-03-16: FULL 60S SAMPLER SUCCESS - Vectorized Renderer

**Problem solved:** Vectorized `render_frame()` + reduced particle count (200→100)

**Changes:**
1. **NumPy vectorization** - Replaced nested Python loops with array operations
   - 10x faster: ~3.6ms/frame vs ~50ms/frame
   - Uses `np.add.at()` for accumulation
2. **Safety monitoring** - `RenderMonitor` class with 120s timeout
3. **Pre-render estimation** - `estimate_render_time()` + `check_render_safety()`
4. **Particle cloud fix** - 100 particles instead of 200

**Result:**
- **60 seconds, 1440 frames, 6.3MB**
- **Render time: ~21 seconds** (was hanging indefinitely)
- **All 12 segments working**

**Performance:**
| Segment | Particles | Trail | Time |
|---------|-----------|-------|------|
| Lorenz Orbit | 30 | 400 | ~3s |
| RD Coral | N/A | N/A | ~2s |
| Rössler | 30 | 400 | ~3s |
| Lorenz Drift | 20 | 200 | ~2s |
| Particle Cloud | 100 | 100 | ~4s |
| **Total** | - | - | **~21s** |

**Documentation Updated:**
- `sampler-film/README.md` - Technical improvements section
- `sampler-film/VISUAL_REFERENCE.md` - Frame analysis with difficulty ratings
- `tools/attractors.py` - Vectorized renderer + safety utilities
- `notes/scratch/2026-03-15-sampler-render-attempts.md` - Complete debug log

## 2026-03-16: Visual Reference Frames Extracted

**Reference frames captured:** 6s, 18s, 39s, 43s

**Visual Quality Findings:**
- **6s (Lorenz):** Excellent - clear butterfly wings, readable structure
- **18s (RD Coral):** Good - surprisingly organic from sine approximation
- **39s (Rössler):** Okay - dim but visible band structure
- **43s (Lorenz Drift):** Weak - too sparse with rho=33.6

**Render Difficulty Ratings:**
| Technique | Difficulty | Precompute Time |
|-----------|------------|-----------------|
| Lorenz Orbit | ★★☆☆☆ | ~15s (30p/3000pt) |
| RD Coral | ★☆☆☆☆ | None (math only) |
| Rössler | ★★☆☆☆ | ~15s |
| Lorenz Drift | ★★★☆☆ | ~30s (6 trajectories) |

**Files:**
- `sampler-film/ref_frame_*.jpg` - Reference frames
- `sampler-film/VISUAL_REFERENCE.md` - Detailed analysis

---

## 2026-03-15: Sampler Film Created

**Deliverable:**
- `experiments/sampler-film/` - Complete 60-second demonstration
- `sampler_demo.py` - Runnable script demonstrating all techniques
- `README.md` - Detailed breakdown of structure and parameters

**Structure:**
- 12 segments × 5 seconds = 60 seconds
- 4 visual techniques (Lorenz, Rössler, RD, Particle Cloud)
- 4 audio techniques (FM Bell, Brass, Drone, Woodwind + Bytebeat variants)
- Audio/video interleaved for efficiency (not strictly paired)

**Key Design Decisions:**
- Lorenz runs 0-15s while audio changes (efficiency)
- FM Drone layers 15-25s to bridge visual transitions
- Build arc: calm → glitch → organic → climax → chaos

**Next:** Test render, document actual performance on hardware

---

## 2026-03-16: Comprehensive Main Skill Demo Created

**Deliverable:**
- `experiments/main-skill-demo/` - Complete reference implementation
- `main_skill_demo.py` - Demonstrates ALL 4 reference documents + ALL templates
- `NOTES.md` - Full production documentation

**Reference Documents Covered:**
| Document | Concepts Demonstrated |
|----------|----------------------|
| `creative-lenses.md` | Genre/mode (ritual), motif, repetition/rupture, time |
| `workflow.md` | Hardware gate, worker smoke test, preview, upscale, cleanup |
| `audio-pipeline.md` | Stem model (4 stems), procedural foley, mixing |
| `vocabulary-map.md` | Visual/audio/temporal/material systems |

**Templates Used (ALL):**
- `templates/video/render_runtime.py` - Hardware detection
- `templates/video/parallel_render.py` - Multi-worker rendering
- `templates/audio/audio_engine.py` - FM synthesis
- `templates/audio/sfx_gen.py` - Wind, impact, shimmer generation
- `templates/audio/composer.py` - Note events, MIDI (optional)

**Film Structure:**
- 0-10s: RITUAL - recurrence + drone + phosphor glow
- 10-20s: BUILD - escalation + pulse + grain
- 20-25s: PEAK - symmetry + shimmer
- 25-30s: RUPTURE - inversion + chromatic aberration + return

**Key Achievement:** First film to demonstrate complete main skill workflow including hardware gate and worker smoke test.

---

## 2026-03-15: Experimental Skill Sandbox Created

**Setup:**
- Cloned Codex skill as stable foundation
- Established directory structure (experiments/, research/, notes/, tools/)
- Created initial research stub documents
- Set up notes/ subdirectories (hardware/, examples/, scratch/)
- Created technique use-case taxonomy

**Immediate Priorities:**
1. FM synthesis proof-of-concept (no SoundFont dependency)
2. Strange attractor particle systems
3. Document render time/file size characteristics of each technique

**Hypotheses:**
- FM synthesis will produce more "electronic" sounds than SoundFont
- Strange attractors render faster than equivalent particle systems
- Bytebeat audio is fun but musically limited

---

## Template Entry

**Date:** YYYY-MM-DD

**Experiment:** Name/technique being tested

**What was tried:**
- Specific parameters, approaches, variations

**Results:**
- Render time:
- File size:
- Visual/audio quality:
- Issues encountered:

**Findings:**
- What worked
- What didn't
- Surprises

**Next steps:**
- What to try next
- Whether to graduate, iterate, or abandon

---

## Pending Research Docs

- [ ] FM Synthesis from Scratch
- [ ] Strange Attractors (Lorenz, Rössler, custom)
- [ ] Reaction-Diffusion Patterns
- [ ] Bytebeat Audio
- [ ] L-System String Rewriting
- [ ] Additive Synthesis
- [ ] Granular Synthesis (maybe - heavier dependency)

---

## Technique Graduation Candidates

None yet. First experiments in progress.

---

*Format: Add new entries at the top (reverse chronological). Use the template entry as a guide.*
