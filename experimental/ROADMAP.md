# Experimental Work Roadmap

Tracking decisions and options as the experimental work evolves.

---

## Decision Log

| Date | Decision | Context | Chosen Option |
|------|----------|---------|---------------|
| 2026-03-16 | Demo film scope | 3 complexity levels, multiple techniques | **Option C (All 4, Moderate)** - Maximum demonstration value with manageable complexity |
| 2026-03-16 | Pixel Sorting follow-up | 4 implementation paths available | **Option 3: ParameterSequence** - Enables reproducible experiments for ALL techniques |

### 2026-03-16: Demo Film Design Decisions

**Why all 4 techniques:** Cross-domain demonstration (visual + audio) shows ParameterSequence's real power better than single-domain examples.

**Why moderate complexity:** 3 parameters per technique is the sweet spot - enough to show rich curves, not so many that editing becomes overwhelming.

**Precomputation insight:** Attractor trajectories precompute once (~10-20s) then render with varying parameters. This pattern should be documented for future technique implementations.

**Performance notes:** Total render ~40-70s for 60s film at 854×480. Acceptable for experimentation. 1080p would need ~4x time or quality reduction.

---

## Current Options Inventory

### From Pixel Sorting Integration (2026-03-16)

#### Option 1: Implement Pixel Sorting Tool
**Status:** Available
**Effort:** Medium
**Impact:** Working code for glitch aesthetics
**Files to create:** `tools/pixel_sorting.py`

Core functions:
- `brightness_sort_row()` - core sorting function
- `pixel_sort()` - main entry point with all variants
- Demo `if __name__ == "__main__"` block

**When to choose:** Want visual glitch results quickly

---

#### Option 2: Create Pixel Sorting Experiment
**Status:** Available
**Effort:** Medium
**Impact:** Visual proof-of-concept film
**Files to create:**
- `experiments/pixel-sort-demo/main.py`
- Test all 4 algorithm variants
- Generate reference frames

**When to choose:** Want to see the technique in action in a complete film

---

#### Option 3: Implement ParameterSequence Class ✅ SELECTED
**Status:** IN PROGRESS
**Effort:** Low-Medium
**Impact:** Infrastructure for reproducible experiments
**Files to create:**
- ✅ `tools/parameter_sequence.py` - Core implementation
- Integration examples with existing techniques

**Benefits:**
- Unlocks reproducible experiments for ALL techniques, not just Pixel Sorting
- Shareable "recipes" as JSON files
- Version control friendly (text diffs)
- Batch automation support

**When to choose:** Want maximum leverage across entire experimental ecosystem

---

#### Option 4: Graduate Experimental Work
**Status:** Available
**Effort:** High
**Impact:** Production-ready capabilities in main skill
**Work involved:**
- Review which techniques meet graduation criteria
- Update main skill SKILL.md
- Create graduation proposals

**Graduation criteria:**
- Reliable across hardware
- Well-documented
- Has working example film
- Clean API

**When to choose:** Experimental techniques have matured and proven useful

---

## Future Option Categories

### Technique Implementation
- [ ] Differential Growth (from generative-video-techniques.md)
- [ ] Space Colonization Algorithm
- [ ] Diffusion-Limited Aggregation (DLA)
- [ ] Boids with full parameter exposure
- [ ] L-System string rewriting
- [ ] Granular synthesis audio

### Infrastructure
- [ ] Batch rendering system using ParameterSequence
- [ ] Experiment comparison tools
- [ ] Automated visual regression testing
- [ ] Render farm distribution

### Integration
- [ ] Hybrid RD → Pixel Sort → Particles pipeline
- [ ] Multi-layer stacking system
- [ ] Audio-reactive parameter mapping
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

*Last updated: 2026-03-16*
