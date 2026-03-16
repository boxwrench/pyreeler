# Technique Index

Categorized index of all available generative techniques. Use this to find the right algorithm for your creative goal.

---

## Quick Reference Table

| Category | Techniques | Status | Research Doc |
|----------|-----------|--------|--------------|
| **Chaotic Maps** | Lorenz, Rössler, Clifford, Hénon, Peter de Jong, Bedhead, Duffing | Working | [strange-attractors.md](strange-attractors.md), [generative-video-techniques.md](generative-video-techniques.md) |
| **Morphogenesis** | Gray-Scott RD, Differential Growth, Space Colonization, DLA | Partial | [reaction-diffusion.md](reaction-diffusion.md), [generative-video-techniques.md](generative-video-techniques.md) |
| **Physics** | Particles, Boids, Springs, Oscillations | Ready | [generative-video-techniques.md](generative-video-techniques.md) |
| **Spatial** | Poisson Disk, Voronoi, Flow Fields, Circle Packing | Ready | [generative-video-techniques.md](generative-video-techniques.md) |
| **Fractals** | Quaternion Julia Set | Research | [generative-video-techniques.md](generative-video-techniques.md) |
| **Audio** | FM Synthesis, Bytebeat | Working | [fm-synthesis.md](fm-synthesis.md), [bytebeat-audio.md](bytebeat-audio.md) |
| **Image Processing** | Pixel Sorting | Research | [pixel-sorting.md](pixel-sorting.md) |

**Status Legend:**
- **Research** - Concept documented, not yet implemented
- **Partial** - Basic implementation exists, needs refinement
- **Working** - Usable in experiments, documented
- **Ready** - Fully implemented, ready for use
- **Graduated** - Moved to main skill

---

## Technique Selection Matrix

Link creative goals to specific techniques:

| Creative Goal | Technique Category | Example Techniques |
|--------------|-------------------|-------------------|
| Organic growth | Morphogenesis | Differential Growth, Space Colonization, Gray-Scott Coral |
| Swarm intelligence | Physics | Boids, Particle Systems |
| Crystalline structures | Chaotic Maps | Discrete attractors with histogram rendering (Clifford, Hénon) |
| Rhythmic motion | Physics | Oscillations, Springs, Pendulums |
| Emergent complexity | Cellular Automata | Game of Life variants (not yet documented) |
| Fluid dynamics | Spatial | Flow Fields with particle traces |
| Biological patterns | Morphogenesis | Reaction-Diffusion (stripes, spots) |
| Cosmic/celestial | Chaotic Maps | Lorenz, Rössler with camera orbit |
| Structured distribution | Spatial | Poisson Disk, Voronoi tessellation |
| Analog texture | Spatial | Sand Splines, B-Spline layering |
| Glitch aesthetics | Image Processing | Pixel Sorting threshold masking |
| Data corruption beauty | Image Processing | Interval sort with noise |

See [creative-lenses.md](creative-lenses.md) for guidance on choosing creative direction.

---

## Chaotic Maps

Deterministic systems producing infinitely complex, non-repeating trajectories.

### Continuous Attractors (3D)

| Technique | Visual Character | Best For | Complexity |
|-----------|-----------------|----------|------------|
| **Lorenz** | Butterfly wings, dual lobes | Cosmic ribbons, meditative orbits | Medium |
| **Rössler** | Single folding band | Smoother, circular compositions | Low |
| **Duffing** | Oscillating spring | Audio-reactive turbulence | Medium |

### Discrete Maps (2D Histogram)

| Technique | Visual Character | Best For | Complexity |
|-----------|-----------------|----------|------------|
| **Clifford** | Triangles, moiré patterns | Topological transformations | Medium |
| **Hénon** | Arched Cantor lines | High-contrast geometric | Low |
| **Peter de Jong** | Swirling silk tendrils | Ambient, dreamlike visuals | Low |
| **Bedhead** | Chaotic hair tangles | Neural pathways, magnetic fluid | Medium |

**Implementation:** See [strange-attractors.md](strange-attractors.md) for core algorithms.

---

## Morphogenesis

Biological simulation algorithms that replicate natural growth processes.

| Technique | Process | Visual Output | Status |
|-----------|---------|---------------|--------|
| **Gray-Scott Reaction-Diffusion** | Chemical reaction simulation | Coral, fingerprints, spots, cells | Working |
| **Differential Growth** | Edge subdivision based on curvature | Organic tissue, leaf venation | Research |
| **Space Colonization** | Resource competition for growth | Trees, vascular systems, roads | Research |
| **Diffusion-Limited Aggregation** | Random walk + freeze on contact | Frost, crystals, lightning | Research |

**Implementation:** See [reaction-diffusion.md](reaction-diffusion.md) for Gray-Scott.

---

## Physics

Newtonian mechanics and autonomous agent behaviors.

| Technique | Core Mechanism | Visual Output | Use Case |
|-----------|---------------|---------------|----------|
| **Particle Systems** | Mass + velocity + forces | Smoke, fire, waterfalls, nebulas | Environmental effects |
| **Boids** | Separation, alignment, cohesion | Flocking, swarming, schooling | Life-like motion |
| **Spring Systems** | Hooke's Law (F = -kx) | Web structures, elastic networks | Connected dynamics |
| **Oscillations** | Sine/cosine harmonics | Pendulums, waves, rhythmic motion | Temporal patterns |

---

## Spatial

Algorithms for elegant distribution and tessellation.

| Technique | Guarantee | Visual Character | Use Case |
|-----------|-----------|------------------|----------|
| **Poisson Disk** | Minimum distance, no clumping | Blue noise distribution | Star fields, stippling |
| **Voronoi** | Proximity-based polygons | Cellular structures, foam | Organic partitions |
| **Flow Fields** | Noise-driven vectors | Fluid dynamics, wind currents | Liquid-like motion |
| **Circle Packing** | Non-overlapping growth | Filling patterns, bubbles | Coverage aesthetics |
| **Delaunay** | Triangle mesh from points | Mesh structures, crystal facets | Geometric frameworks |
| **Sand Splines** | Accumulated B-splines | Graphite shading, charcoal | Analog texture |

---

## Image Processing

Image manipulation techniques for glitch aesthetics and stylistic post-processing.

| Technique | Process | Visual Output | Status |
|-----------|---------|---------------|--------|
| **Pixel Sorting** | Threshold-based pixel displacement | Glitch streaks, data corruption, motion trails | Research |

See [pixel-sorting.md](pixel-sorting.md) for algorithm details.

---

## Hybrid Architectures

Advanced combinations documented in [generative-video-techniques.md](generative-video-techniques.md):

### Vector-Driven Morphogenesis
- **Components:** Strange attractor + Boid system
- **Mechanism:** Use attractor coordinates as vector field, drive agents through it
- **Result:** Volumetric sweeping vortexes, organic chaos

### Reaction-Diffusion Mapping
- **Components:** Gray-Scott RD + spatial algorithm
- **Mechanisms:**
  - **DLA constrained by RD:** Frost growing along chemical veins
  - **Circle packing modulated by RD:** Breathing alveoli, topographic foam
- **Result:** Living patterns that guide secondary algorithms

### Neuroevolutionary Control
- **Components:** Genetic algorithm + neural network + growth system
- **Mechanism:** Evolve network weights based on aesthetic fitness
- **Result:** Self-evolving digital organisms

---

## Audio Techniques

| Technique | Character | Best For | Status |
|-----------|-----------|----------|--------|
| **FM Synthesis** | Precise, crystalline | Bells, brass, drones | Working |
| **Bytebeat** | Glitchy, algorithmic | Rhythms, textures, retro | Working |

See [fm-synthesis.md](fm-synthesis.md) and [bytebeat-audio.md](bytebeat-audio.md).

---

## Combination Quick Reference

Proven pairings from [technique-use-cases.md](technique-use-cases.md):

| Visual | Audio | Result | Mood |
|--------|-------|--------|------|
| Attractor Orbit | FM Drone | "Mathematical Sublime" | Awe |
| RD Coral | FM Bells | "Electric Life" | Emergent |
| Particle Cloud | Bytebeat | "Alive Circuits" | Playful |
| Lorenz Drift | Brass Swell | "Cosmic Event" | Drama |

---

## Documentation Map

```
research/
├── INDEX.md                 # This file - categorized overview
├── TEMPLATE.md              # Template for new technique docs
├── creative-lenses.md       # Choosing artistic direction
├── technique-use-cases.md   # Top uses by technique
├── vocabulary-map.md        # Terminology reference
├── generative-video-techniques.md  # Comprehensive deep dive
├── strange-attractors.md    # Chaotic maps (working)
├── reaction-diffusion.md    # Gray-Scott RD (partial)
├── fm-synthesis.md          # FM audio (working)
├── bytebeat-audio.md        # Bytebeat audio (working)
├── audio-pipeline.md        # Audio architecture
├── pixel-sorting.md         # Image processing glitch art
└── workflow.md              # Process documentation
```

---

*Last updated: 2026-03-16*
