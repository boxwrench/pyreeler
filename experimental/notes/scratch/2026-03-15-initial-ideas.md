# Initial Experiment Ideas

Just dumping thoughts as they come.

## FM Synthesis

- Try cascading 3 operators like DX7 algorithm 1
- Feedback FM (operator modulates itself) - sharpens sound
- Percussive FM: pitch envelope dropping quickly for "punch"
- Metallic ratios: 1:1.41 (sqrt 2), 1:1.618 (phi) - inharmonic

## Attractors

- Coupled Lorenz systems? Each particle is its own attractor, weakly coupled to neighbors
- Would need n-dimensional array, might be slow
- Try Aizawa attractor - different shape, more spherical
- Thomas attractor - "cyclical" behavior

## Reaction-Diffusion

- Multiple passes per frame for faster evolution
- Use as displacement map for other content
- Feed rate as audio amplitude mapping

## Bytebeat

- Actually pretty limited musically
- Better as rhythmic texture layer under FM synthesis
- Try: `t & (t >> 8)` as hi-hat pattern

## Wild Ideas

- Render attractor in 3D with depth of field blur
- Use audio waveform as seed for RD initial conditions
- Film grain via Perlin noise overlay (but check compression!)
- Chromatic aberration: RGB channels slightly offset

## Performance Notes

Precomputing trajectory is WAY faster than integrating per frame. Like 100x faster. Always precompute.

FM synthesis is nearly free. Could generate per-frame audio variations without issue.

---

*Don't overthink it. Make something.*
