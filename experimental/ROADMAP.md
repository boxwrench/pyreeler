# Experimental Work Roadmap

Tracking decisions and options as the experimental work evolves.

Current implementation backlog:
`docs/plans/2026-06-17-remaining-roadmap-implementation.md`.

---

## Decision Log

| Date | Decision | Context | Chosen Option |
|------|----------|---------|---------------|
| 2026-03-16 | Next sampler film | 5 options for next film | **Option 2: Reaction-Diffusion** - Organic pattern evolution, distinct from previous attractor/sampler |
| 2026-03-16 | Demo film scope | 3 complexity levels, multiple techniques | **Option C (All 4, Moderate)** - Maximum demonstration value with manageable complexity |
| 2026-03-16 | Pixel Sorting follow-up | 4 implementation paths available | **Option 3: ParameterSequence** - Enables reproducible experiments for ALL techniques |
| 2026-06-17 | Experiment comparison tooling | Project review future directions | **Single-axis contact sheet delivered** - `contact_sheet.sweep()` compares one parameter across values |
| 2026-06-17 | Template graduation gate | Project review future directions | **Graduation manifest + CI gate delivered** - `template_graduation.toml` and `graduation_check.py` define proof points |
| 2026-06-17 | Audio-reactive mapping | Project review future directions | **Portable v1 delivered** - `templates/audio/audio_reactive.py` maps RMS envelopes to visual parameters |
| 2026-06-17 | Local GPU frame synthesis | Project review future directions | **Runtime hardening delivered** - `docs/hardware-experiments/wgpu_runtime.py` is import-safe and CI-covered without GPU hardware |
| 2026-06-17 | Provider skill core | Project review future directions | **Shared reference source delivered** - `skills/_shared/references/` feeds self-contained provider skill copies |

### 2026-03-16: Demo Film Design Decisions

**Why all 4 techniques:** Cross-domain demonstration (visual + audio) shows ParameterSequence's real power better than single-domain examples.

**Why moderate complexity:** 3 parameters per technique is the sweet spot - enough to show rich curves, not so many that editing becomes overwhelming.

**Precomputation insight:** Attractor trajectories precompute once (~10-20s) then render with varying parameters. This pattern should be documented for future technique implementations.

**Performance notes:** Total render ~40-70s for 60s film at 854×480. Acceptable for experimentation. 1080p would need ~4x time or quality reduction.

---

## Current Options Inventory

### From Pixel Sorting Integration (2026-03-16)

#### Option 1: Implement Pixel Sorting Tool
**Status:** Done
**Effort:** Medium
**Impact:** Working code for glitch aesthetics
**Files created:** `tools/pixel_sorting.py`

Core functions:
- `brightness_sort_row()` - core sorting function
- `pixel_sort()` - main entry point with all variants
- Demo `if __name__ == "__main__"` block

**When to choose:** Want visual glitch results quickly

---

#### Option 2: Create Pixel Sorting Experiment
**Status:** Done
**Effort:** Medium
**Impact:** Visual proof-of-concept film
**Files created:**
- `experiments/pixel-sort-sampler/main.py`
- `experiments/pixel-sort-sampler/output/sequences/*.json`

**When to choose:** Want to see the technique in action in a complete film

---

#### Option 3: Implement ParameterSequence Class ✅ SELECTED
**Status:** Done
**Effort:** Low-Medium
**Impact:** Infrastructure for reproducible experiments
**Files created:**
- ✅ `tools/parameter_sequence.py` - Core implementation
- ✅ `experiments/parameter-sequence-demo/` - Cross-domain demo film
- ✅ `experiments/rd-sampler-film/` - Reaction-diffusion integration
- ✅ `experiments/pixel-sort-sampler/` - Pixel-sorting integration

**Benefits:**
- Unlocks reproducible experiments for ALL techniques, not just Pixel Sorting
- Shareable "recipes" as JSON files
- Version control friendly (text diffs)
- Batch automation support

**When to choose:** Want maximum leverage across entire experimental ecosystem

---

#### Option 4: Graduate Experimental Work
**Status:** Partially implemented — graduation is now gated by manifest + CI
**Effort:** High
**Impact:** Production-ready capabilities in main skill
**Work involved:**
- Review which techniques meet graduation criteria
- Add or update `template_graduation.toml` entries
- Keep `sync.py --check` and `graduation_check.py` clean
- Update main skill docs and provider copies

**Graduation criteria:**
- Reliable across hardware
- Well-documented
- Has working example film
- Clean API
- Declared in `template_graduation.toml` with test/example proof points

**When to choose:** Experimental techniques have matured and proven useful

---

## Future Option Categories

### Technique Implementation
- [ ] 3D Perspective Projection (geometry_3d.py) - from [demoscene_inspiration.md](../research/demoscene_inspiration.md)
- [ ] Autonomous Validation Loop (smoke_test) - self-healing scripts
- [ ] Retro Terminal UI Overlays (scanlines, terminal text)
- [ ] Differential Growth (from generative-video-techniques.md)
- [ ] Space Colonization Algorithm
- [ ] Diffusion-Limited Aggregation (DLA)
- [ ] Boids with full parameter exposure
- [ ] L-System string rewriting
- [ ] Granular synthesis audio

### Infrastructure
- [ ] Batch rendering system using ParameterSequence
- [x] Experiment comparison tools — `tools/contact_sheet.py` supports single-axis sweeps
- [ ] 2D contact-sheet grids and parallel variant rendering
- [x] Template graduation gate — `template_graduation.toml` + `graduation_check.py` enforce proof points in CI
- [x] Provider-agnostic shared references — `skills/_shared/references/` is synced into provider skill folders
- [ ] Automated visual regression testing
- [ ] Render farm distribution

### Integration
- [ ] Hybrid RD → Pixel Sort → Particles pipeline
- [ ] Multi-layer stacking system
- [x] Audio-reactive parameter mapping — portable RMS envelope/scalar mapping helper delivered
- [ ] Audio-reactive band-specific envelopes and beat detection
- [ ] GPU frame synthesis shader render base class / benchmark output
- [ ] Real-time preview mode

---

## How to Use This Document

**When deciding what to work on:**
1. Check the Decision Log for context on past choices
2. Review the Options Inventory for available paths
3. Consider the "When to choose" guidance for each option
4. Add your decision to the log with rationale

**When adding new options:**
- Add to the appropriate category (or create new)
- Include effort, impact, and decision criteria
- Link to any related research docs or experiments

---

*Last updated: 2026-06-17*
