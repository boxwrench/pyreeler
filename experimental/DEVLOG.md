# PyReeler Experimental Dev Log

Chronological log of experiments, findings, and technique development.

---

## 2026-03-17: Main Skill Demo RUN SUCCESSFULLY ✓ MOVIE PRODUCED

**Changes:**
- Fixed `main_skill_demo.py` to handle missing FFmpeg gracefully
  - Added fallback to `imageio-ffmpeg` when FFmpeg not in PATH
  - Fixed type error in `render_frame_build()` (float vs array)
  - Improved error handling for runtime detection
- Successfully executed complete 30-second demo film

**Film Output:**
- ✅ `C:\Users\wests\Videos\main_skill_demo.mp4` - **46.6 MB, 30 seconds**

**Demonstration Coverage:**
| Reference Document | Concepts Shown |
|-------------------|----------------|
| `creative-lenses.md` | Ritual mode, returning circle motif, rupture at peak |
| `workflow.md` | Hardware gate, worker smoke test, preview, cleanup |
| `audio-pipeline.md` | 4-stem model (ambience, pulse, score, impacts) |
| `vocabulary-map.md` | Particles/swarm, flow fields, symmetry, phosphor glow |

**All Templates Used:**
- `render_runtime.py` - Runtime detection (with fallback)
- `parallel_render.py` - Frame rendering
- `audio_engine.py` - Audio generation
- `sfx_gen.py` - Procedural foley
- `composer.py` - Musical structure

**Technical Notes:**
- FFmpeg detection fails on Windows without explicit PATH
- `imageio-ffmpeg` works as fallback (bundles FFmpeg binary)
- H.264 requires dimensions divisible by 16 (imageio auto-resizes 854→864)
- Render time: ~30s for 720 frames (single worker fallback mode)

**Files Modified:**
- MOD: `experiments/main-skill-demo/main_skill_demo.py`
  - FFmpeg fallback logic
  - Bug fix for float array assignment
  - Graceful degradation when templates unavailable

---

## 2026-03-16: Pixel Sort Sampler Film COMPLETE ✓ MOVIE PRODUCED

**Changes:**
- Created `tools/pixel_sorting.py` - core pixel sorting implementation
  - Threshold sort (brightness-based)
  - Interval sort (row spacing)
  - Masked sort (selective application)
  - Angle support (horizontal/vertical)
- Created `experiments/pixel-sort-sampler/` - glitch aesthetic film
  - 60 seconds, 4 segments with different sorting variants
  - ParameterSequence drives threshold, interval, angle parameters
  - Generates source images with animated gradients and shapes
  - Audio: glitchy FM synthesis mapped to sorting intensity

**Film Structure:**
- 0-15s: Threshold intensification (more sorting over time)
- 15-30s: Interval/rhythm patterns (every Nth row)
- 30-45s: Masked/glitch bursts (selective sorting)
- 45-60s: Angle morphing (vertical ↔ horizontal)

**Technical Notes:**
- Pixel sorting is slower than RD (~5-10 fps vs ~250 fps)
- Horizontal sorting (angle=0) had dimension issues - fixed with resize
- Source image generation is key - needs high contrast for visible sorting

**Performance:**
- Frame render: ~2-3 minutes for 1440 frames
- Audio render: ~2s
- Total: ~3-4 minutes

**Output:**
- ✅ `output/pixel_sort_final.mp4` - **9.9 MB, 60 seconds**

**Files:**
- NEW: `tools/pixel_sorting.py`
- NEW: `experiments/pixel-sort-sampler/main.py`
- NEW: `experiments/pixel-sort-sampler/` (film directory)

---

## 2026-03-16: Reaction-Diffusion Sampler Film COMPLETE ✓ MOVIE PRODUCED (v3)

**Changes:**
- Created `experiments/rd-sampler-film/` - Gray-Scott pattern evolution
  - 60 seconds, continuous parameter oscillation (no static holds)
  - ParameterSequence morphs F (feed) and k (kill) rates every 2-5 seconds
  - Pattern never stays still - coral phases have visible variation
  - False color rendering at 15s and 50s for visual contrast
  - Audio: FM drone mapped to RD parameters

**v2 Update:** Increased rate of change significantly
- Parameters oscillate instead of holding (e.g., F: 0.050 ↔ 0.058 ↔ 0.052)
- Transitions faster (2-3s instead of 5s)
- More render mode switches (V → U → both → V → both → V)
- Contrast pulses with the action for visual punch

**v3 Update:** DRAMATIC early changes (feedback: not visible until 20s)
- First 10s: BIG jumps between coral (F=0.0545) and fingerprint (F=0.040)
- Parameters change every 2 seconds (not 3)
- Mode switches at 4s and 8s (U view and false color)
- Contrast swings: 1.0 → 1.8 → 0.8 (dramatic dips and peaks)
- Opposing k swings for maximum pattern disruption

**Key Finding:** RD patterns have "inertia" - they take time to respond to parameter changes. Solution: combine parameter drift with instant post-processing (mode switches, contrast) for immediate visual feedback.

**Performance:**
- Total render: ~22s for 60s film
- Grid: 256×256 at ~250 fps

**Files:**
- MOD: `experiments/rd-sampler-film/main.py`
- NEW: `experiments/rd-sampler-film/NOTES.md` - production learnings

---

## 2026-03-16: ParameterSequence Demo Film COMPLETE ✓ MOVIE PRODUCED

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
