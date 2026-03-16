# Reaction-Diffusion Sampler Film

**Organic pattern evolution through Gray-Scott parameter space.**

A 60-second journey through different reaction-diffusion pattern regimes: coral growth, fingerprint stripes, chaotic turbulence, and back again. Parameters morph via ParameterSequence, allowing the chemical simulation to transform organically between pattern types.

---

## Film Structure

| Time | Pattern Zone | Visual Character |
|------|--------------|------------------|
| 0-10s | **Coral Variations** | Oscillating F/k, branches pulse and shift |
| 10-20s | **Rapid Transition** | Quick morph through fingerprint to chaos edge |
| 20-35s | **Deep Chaos** | Wild parameter swings, turbulent patterns |
| 35-50s | **Return Journey** | Chaotic descent back toward coral stability |
| 50-60s | **Coral Finale** | Final oscillations, never static |

**Key Change:** Parameters oscillate every 2-5 seconds instead of holding. The pattern never stays still - even "coral" phases have visible variation.

**Total:** 60 seconds, 24fps, 256×256 simulation (512×512 output)

---

## Gray-Scott Model

Two chemicals (U = activator, V = inhibitor) react and diffuse:

```
dU/dt = Du·∇²U - U·V² + F·(1-U)
dV/dt = Dv·∇²V + U·V² - (F+k)·V
```

Where:
- **F (feed rate):** How much U is added
- **k (kill rate):** How fast V is removed
- **Du, Dv:** Diffusion rates (U diffuses faster than V)

The magic: Different (F, k) values produce radically different patterns from the same simple rules.

---

## Pattern Regimes

### Coral Growth (F=0.0545, k=0.062)
- Branching, tree-like structures
- Tips grow outward, splitting occasionally
- Resembles coral, lichen, neural tissue
- **Visual:** Black background, white branching lines

### Fingerprint/Stripes (F=0.037, k=0.060)
- Parallel lines that curve and intersect
- Self-organizing into labyrinth patterns
- Resembles fingerprints, zebra stripes, magnetic fields
- **Visual:** Dense parallel lines, organic flow

### Spots (F=0.025, k=0.060)
- Stable, localized dots
- Dots appear, grow, stabilize
- Resembles leopard spots, cell colonies
- **Visual:** Scattered dots on uniform background

### Chaos/Turbulence (F=0.026, k=0.051)
- No stable pattern
- Constant swirling, merging, splitting
- Resembles turbulent flow, boiling liquid
- **Visual:** Rendered in false color (cyan/magenta) for this segment

### Mitosis (F=0.022, k=0.051)
- Cells that divide and multiply
- Oscillating between states
- Resembles biological cell division
- **Visual:** Pulsating, rhythmic motion

---

## Parameter Sequences

The film uses ParameterSequence to smoothly interpolate F and k between pattern regimes:

```python
# Feed rate - rapid oscillations + transitions
F: 0.050 ↔ 0.058 ↔ 0.052 → 0.055 → 0.045 → 0.037 → 0.030
     (oscillating coral)   →  transition → fingerprint → chaos edge

# Kill rate - correlated oscillations
k: 0.060 ↔ 0.064 ↔ 0.061 → 0.063 → 0.062 → 0.060 → 0.056
```

This morphing creates smooth transitions where one pattern dissolves and another emerges from the same running simulation.

### Additional Parameters

| Parameter | Purpose |
|-----------|---------|
| `contrast` | Boost visual intensity (especially for chaos) |
| `mode` | 'V' (activator), 'U' (inhibitor), or 'both' (false color) |

---

## Running the Film

```bash
cd experiments/rd-sampler-film
python main.py
```

**Requirements:**
- NumPy, Pillow
- SciPy (optional - uses faster Laplacian)
- imageio, moviepy (for video encoding)

**Output:**
```
output/
├── rd_sampler_final.mp4   # Final movie with audio
├── rd_sampler.mp4         # Video only
├── audio.wav              # Generated drone audio
├── sequences/             # Parameter sequences
│   ├── feed_rate.json
│   ├── kill_rate.json
│   ├── contrast.json
│   └── render_mode.json
└── frames/                # Individual PNG frames
```

---

## Performance

| Phase | Time | Notes |
|-------|------|-------|
| Pre-warm | ~2s | 300 steps to establish initial pattern |
| Frame render | ~30-60s | 1440 frames × RD simulation |
| Audio | ~2s | FM synthesis |
| Encoding | ~30s | Video + audio muxing |
| **Total** | **~2-3 min** | Depends on CPU |

**Optimization:** If too slow:
- Reduce `SIZE` from 256 to 128 (4× faster)
- Reduce `TOTAL_FRAMES` from 1440 to 720 (half the length)
- Increase `DT` from 1.0 to 2.0 (fewer simulation steps per frame)

---

## Modifying Patterns

Edit the sequences in `main.py`:

```python
# Try different pattern transitions
f_seq.record(30 * FPS, 'F', 0.025)  # Spots instead of chaos
k_seq.record(30 * FPS, 'k', 0.060)
```

Or modify the JSON files and re-run just the encoding:

```python
from tools.parameter_sequence import ParameterSequence

f_seq = ParameterSequence.load("output/sequences/feed_rate.json")
f_seq.record(720, 'F', 0.022)  # Add mitosis segment
f_seq.save("output/sequences/feed_rate.json")

# Re-run main.py to generate new movie
```

---

## Audio Design

The audio is a simple FM drone that maps:
- **F (feed rate)** → Base frequency (20Hz to 100Hz)
- **k (kill rate)** → Modulation frequency ratio
- **Pattern complexity** → Modulation index

Result: Audio evolves with the visual pattern. Coral is low and stable, chaos is high and turbulent.

---

## Key Insight

Reaction-diffusion demonstrates **emergence** - complex global patterns from simple local rules. The same equations, just different parameters, create coral, fingerprints, spots, and chaos.

With ParameterSequence, we can smoothly morph between these regimes, watching one pattern dissolve and another crystallize from the same chemical soup.

---

*Pattern table from Pearson (1993), "Complex Patterns in a Simple System"*
