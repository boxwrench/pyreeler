# Experimental Skill Guide

How to develop new techniques in the experimental sandbox and graduate them to the main PyReeler skill.

---

## Overview

The experimental folder is a **self-contained incubator**. Work here is:
- **Local** - tuned to your hardware
- **Exploratory** - may break, may fail
- **Documented** - lessons learned are the output

Graduation to the main skill happens when a technique proves **reliable, portable, and useful**.

---

## Directory Map

```
experimental/
├── skills/codex/          # Frozen skill copy (reference only)
├── experiments/           # Your film projects (stay here)
├── research/              # Technique documentation
├── tools/                 # Reusable code modules
├── notes/                 #
│   ├── hardware/          # Your machine-specific tuning
│   ├── examples/          # Proven combinations
│   └── scratch/           # Loose ideas, dead ends
├── GUIDE.md               # This file
├── DEVLOG.md              # Chronological log
└── README.md              # Philosophy & structure
```

---

## 1. Technique Overview (New)

Before choosing a technique, understand the landscape. See [research/INDEX.md](research/INDEX.md) for the complete categorized index.

### Quick Reference Table

| Category | Techniques | Status |
|----------|-----------|--------|
| **Chaotic Maps** | Lorenz, Rössler, Clifford, Hénon | Working |
| **Morphogenesis** | Gray-Scott RD, Differential Growth, SCA, DLA | Partial |
| **Physics** | Particles, Boids, Springs, Oscillations | Ready |
| **Spatial** | Poisson Disk, Voronoi, Flow Fields, Circle Packing | Ready |

### Technique Selection Guide

Match your creative goal to the right category:

| Creative Goal | Technique Category | Example |
|--------------|-------------------|---------|
| Organic growth | Morphogenesis | Differential Growth, SCA |
| Swarm intelligence | Physics | Boids |
| Crystalline structures | Chaotic Maps | Discrete attractors with histogram |
| Rhythmic motion | Physics | Oscillations, Springs |
| Emergent complexity | Cellular Automata | Game of Life, Rule 30 |
| Fluid dynamics | Spatial | Flow Fields |
| Biological patterns | Morphogenesis | Reaction-Diffusion |
| Cosmic/celestial | Chaotic Maps | Lorenz, Rössler orbit |
| Structured distribution | Spatial | Poisson Disk, Voronoi |
| Analog texture | Spatial | Sand Splines |

See [research/creative-lenses.md](research/creative-lenses.md) for guidance on artistic direction.

---

## 2. Research Phase (Expanded)

**Before writing code, document:**

Create `research/my-technique.md` using the template:
```bash
cp research/TEMPLATE.md research/my-technique.md
```

### Choosing a Technique Category

Consider these questions:

1. **What's the visual character?**
   - Flowing and organic → Morphogenesis or Physics
   - Geometric and precise → Chaotic Maps or Spatial
   - Emergent and chaotic → Physics agents or CA

2. **What's the temporal behavior?**
   - Continuous evolution → Differential equations (attractors, RD)
   - Discrete steps → Maps, CA, agents
   - Accumulation over time → Persistent buffers, trails

3. **What's the computational budget?**
   - Real-time constraint → Need spatial indexing (see Advanced Rendering)
   - Offline render → Can use O(n²) algorithms

### When to Combine Techniques

Single techniques produce good results. **Hybrids produce unique results.**

Consider combining when:
- You want organic motion guided by mathematical precision
- You want patterns to drive secondary algorithms
- You want emergent behavior from simple rules

See the Hybrid Architectures section below for concrete patterns.

**Example research docs:**
- `research/fm-synthesis.md`
- `research/strange-attractors.md`
- `research/reaction-diffusion.md`

---

## 3. Tool Phase

### 1. Research Phase

**Before writing code, document:**

Create `research/my-technique.md` with:
```markdown
# My Technique

## Overview
What it does, why it's interesting

## Dependencies
- Required: NumPy, Pillow
- Optional: SciPy (for filters)

## Algorithm
Brief explanation or pseudocode

## Parameters
| Param | Range | Effect |
|-------|-------|--------|
| foo | 0-1 | Controls bar |

## AI Direction Vocabulary
- "smooth" → low foo
- "chaotic" → high foo

## Status: Research / Working / Graduated
```

**Example research docs:**
- `research/fm-synthesis.md`
- `research/strange-attractors.md`
- `research/reaction-diffusion.md`

---

### 2. Tool Phase

**Implement as reusable module in `tools/`:**

```python
# tools/my_technique.py
"""My technique for PyReeler experimental.

Usage:
    from experimental.tools.my_technique import generate, render
"""
import numpy as np
from PIL import Image

def generate(params):
    """Precompute/cache expensive data."""
    pass

def render(data, frame_num, width, height):
    """Render single frame."""
    pass
```

**Requirements:**
- Pure NumPy/PIL when possible
- No global state
- Document performance characteristics
- Include `if __name__ == "__main__":` demo

**Example tools:**
- `tools/fm_synth.py` - FM synthesis from scratch
- `tools/attractors.py` - Strange attractors (vectorized)

---

## 4. Film Phase

**Create experiment in `experiments/my-film/`:**

```
experiments/my-film/
├── main.py              # Main render script
├── NOTES.md             # Your specific tuning
└── ref_frame_*.jpg      # Reference frames
```

**NOTES.md template:**
```markdown
# My Film

## Hardware
- CPU/GPU:
- Render time:
- File size:

## Parameters Used
- Visual:
- Audio:

## What Worked

## What Didn't

## Would Try Next Time
```

---

## 5. Hybrid Architectures (New)

Advanced combinations documented in [research/generative-video-techniques.md](research/generative-video-techniques.md).

### Vector-Driven Morphogenesis

**Concept:** Use strange attractor coordinates as a vector field to drive autonomous agents.

**How it works:**
1. Generate Lorenz or Clifford attractor trajectory
2. Use (x, y, z) coordinates as force vectors at each grid location
3. Inject Boids/particles into this field
4. Agents attempt flocking behaviors but are pulled by attractor currents

**Result:** Volumetric sweeping vortexes where agents spiral through chaotic eddies. The motion feels organic but follows mathematical precision.

**Pseudocode:**
```python
# Precompute attractor field
attractor = generate_lorenz(n_points=10000)
vector_field = build_spatial_hash(attractor)

# Initialize agents
boids = [Boid(random_position()) for _ in range(500)]

# Simulation loop
for frame in frames:
    for boid in boids:
        # Standard flocking
        separation = boid.separate(boids)
        alignment = boid.align(boids)
        cohesion = boid.cohesion(boids)
        
        # Add attractor force
        attractor_force = vector_field.lookup(boid.position)
        
        # Blend forces
        boid.apply_force(separation + alignment + cohesion + attractor_force * 2)
        boid.update()
        boid.draw()
```

---

### Reaction-Diffusion Mapping

**Concept:** Use RD concentration matrix as a dynamic density map to constrain other algorithms.

**How it works:**
1. Run Gray-Scott simulation (U and V chemical grids)
2. Use V (activator) concentration as density/permission map
3. Secondary algorithm queries RD state before acting

**Variants:**

| Secondary Algorithm | Integration | Visual Result |
|--------------------|-------------|---------------|
| **DLA** | Sample RD matrix to dictate freeze zones | Frost growing along chemical veins |
| **Circle Packing** | Query concentration to set max radius | Breathing alveoli, foam topography |
| **Particle Spawn** | Birth rate proportional to concentration | Living dust, pollen on wind |

**Example - RD-Constrained DLA:**
```python
# Run RD simulation
U, V = gray_scott_init(size=256)
for _ in range(100):
    U, V = gray_scott_step(U, V)

# DLA that only freezes where V > threshold
while particle.moving:
    particle.random_walk()
    if V[particle.y, particle.x] > 0.5:
        particle.freeze()
        # Frost grows only along RD patterns
```

**Example - RD-Modulated Circle Packing:**
```python
for circle in growing_circles:
    # Query chemical concentration at circle center
    concentration = V[circle.y, circle.x]
    
    # Growth rate and max size depend on concentration
    max_radius = 10 + concentration * 50
    growth_rate = 0.1 + concentration * 0.5
    
    if circle.radius < max_radius:
        circle.grow(growth_rate)
```

---

### Multi-Layered Systems

**Concept:** Stack multiple algorithms with different temporal scales.

**Pattern:**
- **Slow layer:** RD or Attractor (evolves over minutes)
- **Medium layer:** Flow field or Boids (evolves over seconds)
- **Fast layer:** Particles or noise (evolves per frame)

Each layer influences the next, creating depth and emergent behavior.

---

### Pre/Post Processing Pipeline

**Concept:** Use image processing techniques (like Pixel Sorting) as either pre-processing (modifying input) or post-processing (modifying output) in the generative pipeline.

**Why it works:** Image processing operations create stylistic effects that are computationally efficient and artistically distinct from simulation-based techniques. Using them as pipeline stages allows controlled corruption and stylistic unity.

---

**Pre-processing patterns:**

1. **RD → Pixel Sort → Particles**
   - Run Gray-Scott to generate organic texture
   - Pixel sort the texture along flow lines (horizontal or angled)
   - Use sorted result as particle spawn mask or texture
   - **Result:** Glitchy organic motion where particles emerge from corrupted chemical patterns

2. **Attractor → Pixel Sort Mask**
   - Generate Lorenz trajectory over time
   - Create binary mask from attractor density (high density = sort region)
   - Apply pixel sort only within masked regions
   - **Result:** Chaotic glitch focused on attractor shape, clean background

```python
# Pre-processing example: RD → Pixel Sort → Particle Mask
U, V = gray_scott_init(size=256)
for _ in range(200):
    U, V = gray_scott_step(U, V)

# Convert V channel to image and sort
rd_image = (V * 255).astype(np.uint8)
sorted_rd = pixel_sort(rd_image, threshold=100, direction='horizontal')

# Use as particle spawn probability
for frame in range(frames):
    for y in range(height):
        for x in range(width):
            if random() < sorted_rd[y, x] / 255 * 0.1:
                spawn_particle(x, y)
```

---

**Post-processing patterns:**

1. **Particles → Pixel Sort**
   - Render particle system to buffer (trails, accumulation)
   - Apply interval sort for motion streaks
   - **Result:** Motion blur via sorting, creates "speed lines" effect

2. **Multi-layer Stacking**
   - Layer 1: Base render (RD or Particles)
   - Layer 2: Pixel Sort with threshold A, direction horizontal
   - Layer 3: Pixel Sort with threshold B, direction vertical
   - Composite with blend modes (screen, multiply, overlay)
   - **Result:** Complex glitch aesthetic with controlled chaos

```python
# Post-processing example: Particles → Pixel Sort
particle_buffer = render_particles(frame)  # RGB array

# Multiple sort passes with different parameters
layer1 = pixel_sort(particle_buffer, threshold=150, direction='horizontal')
layer2 = pixel_sort(particle_buffer, threshold=100, direction='vertical', interval=2)

# Blend layers
final = blend_screen(layer1, layer2)
```

---

**Combination benefits:**
- **Efficiency:** Image processing is fast (O(n) per pixel)
- **Controllability:** Parameters map directly to visual output
- **Reproducibility:** Same parameters = same corruption pattern
- **Versatility:** Works with any technique that produces image output

**Techniques that work well in pipeline:**
- **Pixel Sorting** - Glitch, streaks, data corruption
- **Dithering** - Retro aesthetic, bit reduction
- **Edge Detection** - Contour extraction for vectorization
- **Convolution filters** - Blur, sharpen, emboss effects

---

## 6. Example Phase (Renumbered)

**If the combination is proven, document in `notes/examples/`:**

```markdown
# Example: X + Y Combination

**Contributor:** @yourname
**Date:** YYYY-MM-DD

## Ingredients
- Visual: [technique + params]
- Audio: [technique + params]

## Why It Worked

## Files
- `experiments/my-film/`
```

---

## 7. Advanced Rendering (New)

Techniques from research for professional-quality output.

### Persistent Dual-Buffer Rendering

**Technique:** Never fully clear the background between frames. Draw with slight fade/low alpha.

**How it works:**
```python
# Instead of clearing to black:
# screen.fill((0, 0, 0))  # Don't do this

# Fade the existing buffer slightly:
screen = screen * 0.99  # 1% fade per frame
# Then draw new elements at full opacity
```

**Effects achieved:**
- **Motion blur:** Moving objects leave fading trails
- **Accumulation:** Static elements build up density
- **Light interference:** Additive blending creates glow
- **Temporal coherence:** Frame-to-frame stability

**Essential for:**
- Sand Splines aesthetic (layered B-splines)
- Strange attractor trails
- Particle systems with history

### Spatial Indexing

**Problem:** Morphogenetic algorithms need constant proximity checks. O(n²) collision detection fails at scale.

**Solution:** Partition space to only check local neighbors.

| Structure | Complexity | Best For |
|-----------|-----------|----------|
| **Uniform Grid** | O(1) lookup | Evenly distributed particles |
| **Quadtree** | O(log n) | Hierarchical spatial queries |
| **BVH** | O(log n) | Dynamic objects, ray tracing |
| **Spatial Hash** | O(1) | Large numbers of small objects |

**Example - Grid-Based Spatial Hash:**
```python
class SpatialHash:
    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.grid = {}
    
    def _key(self, x, y):
        return (int(x // self.cell_size), int(y // self.cell_size))
    
    def insert(self, obj):
        key = self._key(obj.x, obj.y)
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append(obj)
    
    def query_neighbors(self, obj):
        """Get objects in same and adjacent cells."""
        cx, cy = self._key(obj.x, obj.y)
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                key = (cx + dx, cy + dy)
                if key in self.grid:
                    neighbors.extend(self.grid[key])
        return neighbors

# Usage: 100x speedup for 10k particles
spatial_hash = SpatialHash(cell_size=10)
for obj in objects:
    spatial_hash.insert(obj)

# Collision detection: O(n) instead of O(n²)
for obj in objects:
    neighbors = spatial_hash.query_neighbors(obj)
    for other in neighbors:
        if collides(obj, other):
            resolve_collision(obj, other)
```

**Required for real-time:**
- Particle systems (10k+ particles)
- Boid flocking (neighbor queries)
- DLA (freeze detection)
- Circle packing (collision)
- Differential growth (node proximity)

### Performance Characteristics

| Technique | Without Spatial Index | With Spatial Index | Speedup |
|-----------|----------------------|-------------------|---------|
| Boids (1k) | 1 fps | 60 fps | 60x |
| Circle Packing | 10s/frame | 0.1s/frame | 100x |
| DLA (10k particles) | Hours | Minutes | 1000x |

### Parameter Sequencing

**Pattern:** Record parameter changes over time as (frame, parameter, value) tuples for reproducible, version-controlled experiments.

**Concept:** Instead of hardcoding parameter values or using random changes, record explicit keyframes that can be replayed, shared, and versioned. This enables:
- Reproducible experiments (same sequence = same output)
- Version control friendly (text sequences vs binary outputs)
- Shareable parameter "recipes"
- Batch processing with different sequences

**Implementation:**
```python
import json
from typing import List, Tuple, Any

class ParameterSequence:
    """Record and replay parameter changes over time."""

    def __init__(self):
        self.keyframes: List[Tuple[int, str, Any]] = []  # [(frame, param, value), ...]

    def record(self, frame: int, param: str, value: Any):
        """Record a parameter change at a specific frame."""
        self.keyframes.append((frame, param, value))

    def get_value(self, frame: int, param: str, default: Any = None) -> Any:
        """Get interpolated parameter value at frame."""
        # Get all keyframes for this parameter
        relevant = [(f, v) for f, p, v in self.keyframes if p == param]

        if not relevant:
            return default

        # Find surrounding keyframes
        before = [(f, v) for f, v in relevant if f <= frame]
        after = [(f, v) for f, v in relevant if f > frame]

        if not before:
            return relevant[0][1]  # Before first keyframe
        if not after:
            return before[-1][1]   # After last keyframe

        # Linear interpolation between keyframes
        f1, v1 = before[-1]
        f2, v2 = after[0]
        t = (frame - f1) / (f2 - f1)
        return v1 + (v2 - v1) * t

    def save(self, path: str):
        """Export sequence to JSON."""
        with open(path, 'w') as f:
            json.dump(self.keyframes, f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'ParameterSequence':
        """Import sequence from JSON."""
        seq = cls()
        with open(path, 'r') as f:
            seq.keyframes = json.load(f)
        return seq

# Usage example
sequence = ParameterSequence()
sequence.record(0, 'threshold', 200)     # Start subtle
sequence.record(30, 'threshold', 100)    # Increase effect
sequence.record(60, 'threshold', 200)    # Fade out
sequence.save('glitch_sequence.json')

# Replay in render loop
for frame in range(60):
    threshold = sequence.get_value(frame, 'threshold', default=128)
    result = pixel_sort(image, threshold=threshold)
    save_frame(result, frame)
```

**Benefits:**
- **Reproducibility:** Exact parameter curves every time
- **Shareability:** Text files can be shared, forked, improved
- **Version control:** Git diffs show parameter evolution
- **Batch automation:** Apply same sequence to different inputs
- **Non-linear:** Parameters can change discretely or smoothly

**Techniques supporting sequencing:**
- Pixel Sorting (threshold, interval, angle)
- FM Synthesis (carrier/modulator frequencies, index)
- Strange Attractors (step size, camera orbit)
- Reaction-Diffusion (feed/kill rates over time)

---

## 8. Graduation Criteria (Renumbered)

A technique graduates to the main skill when **ALL** are true:

| Criterion | Test |
|-----------|------|
| **Portable** | Works on Windows & Linux without modification |
| **Reliable** | 10 consecutive renders without failure |
| **Documented** | Full research doc with AI vocabulary |
| **Minimal deps** | NumPy/PIL only, or optional deps handled gracefully |
| **Bounded** | `check_render_safety()` passes for reasonable params |
| **Useful** | Produces results distinct from existing techniques |

---

## Graduation Process

### Step 1: Prepare

In your experiment folder:
```bash
# 1. Final test at production settings
python main.py

# 2. Extract reference frames
ffmpeg -i output.mp4 -ss 00:00:05 -vframes 1 ref_05s.jpg

# 3. Document final parameters in NOTES.md
```

### Step 2: Propose

Create a proposal in `notes/scratch/graduation-proposal-my-technique.md`:

```markdown
# Graduation Proposal: My Technique

## Technique
Brief description

## Files to Graduate
- `research/my-technique.md` → `skills/claude/references/`
- `tools/my_technique.py` → root `templates/`

## Test Results
- Renders: 10/10 successful
- Platforms tested: Windows 11, Ubuntu 22.04
- Dependencies: NumPy only

## Proven Combinations
- With FM synthesis (see examples/lorenz-fm-drone.md)
- With bytebeat (see experiments/my-film/)

## Maintenance
I will maintain this for 3 months post-graduation.
```

### Step 3: Review

Self-review checklist:
- [ ] Works on clean Python install (no local hacks)
- [ ] Documentation complete
- [ ] Safety utilities implemented
- [ ] No hardcoded paths
- [ ] Graceful degradation (if optional deps missing)

### Step 4: Graduate

Copy to main skill:

```bash
# 1. Research doc
cp research/my-technique.md ../skills/claude/references/

# 2. Tool module
cp tools/my_technique.py ../templates/

# 3. Update main skill SKILL.md
# Add technique to the toolkit section

# 4. Update main README
# Add to feature list
```

### Step 5: Verify

Test from main skill context:
```bash
cd ..
python -c "from templates.my_technique import generate; print('OK')"
```

---

## Flow Diagram

```
┌─────────────────┐
│  Research Doc   │ ← Start here: Document the technique
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Tool Module   │ ← Implement reusable code
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Film Project   │ ← Make something with it
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Example Doc    │ ← If combination is proven
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Meet Criteria? │────→│   Graduation    │
└─────────────────┘ Yes └─────────────────┘
         │ No
         ▼
┌─────────────────┐
│  Stays in Exp.  │ ← Still valid, just not graduated
└─────────────────┘
```

---

## Special Cases

### Hardware-Specific Techniques

Some techniques are inherently hardware-bound (GPU shaders, specific encoders).

**Handle by:**
- Document in `notes/hardware/[your-machine].md`
- Mark as "Experimental Only - Hardware Bound"
- Do not graduate

### Failed Experiments

Not everything works. Document the failure:

```markdown
# Attempt: Granular Synthesis

**Status:** ABANDONED

**Why:** Too heavy for real-time, dependencies complex

**Lesson:** Need 10MB+ sample libraries, defeats "small deps" goal

**Archive:** `notes/scratch/2026-03-16-granular-abandoned.md`
```

---

## Maintenance Responsibilities

| Location | Who Maintains | Lifespan |
|----------|--------------|----------|
| `research/` | Author | Until graduated or abandoned |
| `tools/` | Author | Until graduated |
| `experiments/` | Author | Permanent (your films) |
| `notes/examples/` | Community | Permanent (reference) |
| `notes/hardware/` | Individual | Personal reference |
| `notes/scratch/` | No one | Ephemeral (clean up occasionally) |

---

## Quick Reference

**Start new technique:**
```bash
cp research/TEMPLATE.md research/my-technique.md
cp tools/TEMPLATE.py tools/my_technique.py
mkdir experiments/my-film
cp experiments/TEMPLATE/NOTES.md experiments/my-film/
```

**Test safety:**
```python
from attractors import check_render_safety
is_safe, est, rec = check_render_safety(
    n_frames=1440, n_particles=50, trail_length=500
)
```

**Extract reference frames:**
```bash
ffmpeg -i film.mp4 -ss 00:00:05 -vframes 1 ref_05s.jpg
```

---

*Last updated: 2026-03-16*
