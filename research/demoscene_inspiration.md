# Research: 3D Demoscene & Autonomous Generation

## Inspiration Source
- **Project**: [auto_demo_scener](https://github.com/RowanUnderwood/auto_demo_scener)
- **Author**: Rowan Underwood
- **Core Concept**: An autonomous "kiosk" that generates Three.js 3D effects in a retro-hacker terminal interface.

## Key Elements to "Steal" for PyReeler

### 1. 3D Perspective Projection (The "Lean" 3D)
While `auto_demo_scener` uses a full 3D engine (Three.js), PyReeler can achieve similar visual depth by implementing pure-math 3D projections in NumPy.
- **Implementation**: Create a `geometry_3d.py` helper that handles rotation matrices and $(x, y, z) \to (u, v)$ projection.
- **Benefit**: 3D wireframes, starfields, and particle clouds without the Three.js dependency.

### 2. Autonomous Validation Loop (Self-Healing)
`auto_demo_scener` has a loop that catches errors and asks the LLM to fix the code.
- **Implementation**: Add a `smoke_test` phase to the PyReeler skill. After generating code, the AI runs a 1-second render and inspects the FFmpeg logs/output for errors or blank frames.
- **Benefit**: Higher success rate for complex "ritual" films.

### 3. Retro Terminal "Wrappers"
The visual identity of `auto_demo_scener` is heavily tied to its "Mock-OS" UI.
- **Implementation**: Create a `templates/video/ui_overlay.py` that can draw CRT scanlines, terminal text, and diagnostic metadata over the film.
- **Benefit**: Instant "aesthetic" upgrade for experimental and narrative pieces.

### 4. Shaders & SDFs (Signed Distance Fields)
The most impressive visuals in the demoscene often come from GLSL fragment shaders.
- **Implementation**: Explore using `ModernGL` or vectorizing SDF math in NumPy.
- **Benefit**: "Shadertoy" quality visuals (blobs, tunnels, fractal surfaces) with PyReeler's high-fidelity video encoding.

## Architectural Trade-offs: PyReeler vs. Three.js

| Feature | PyReeler (Pre-rendered) | Three.js (Real-time) |
| :--- | :--- | :--- |
| **Viewer Reach** | Universal (MP4 works everywhere) | Variable (limited by viewer's GPU) |
| **Complexity** | Unlimited (can spend 10s/frame) | Restricted (must hit 16ms/frame) |
| **Sync** | Guaranteed Audio/Video sync | Prone to drift/stutter |
| **Longevity** | High (Videos last forever) | Medium (Web APIs change) |
