# Interference — Film Design Spec

## Concept
A 60-second code-generated film exploring geometric interference patterns created by multiple overlapping line grids. The piece combines fixed grids with a moving viewpoint (moiré patterns shift as the eye drifts) and an accumulating density arc (sparse to saturated).

## Visual Arc

### 0-10s: Seed
- Single sparse vertical line grid
- Slow, almost imperceptible eye movement
- Thin white lines on deep black (#000000)
- 20-30 lines across the canvas

### 10-25s: Layering
- Add diagonal grid at +15° (10s)
- Add diagonal grid at -15° (20s)
- Moiré patterns begin to emerge
- Eye movement becomes more noticeable
- Lines: white (#FFFFFF) and subtle cyan (#00FFFF) tint on alternate grids

### 25-40s: Density Build
- Add horizontal grid (25s)
- Add grid at +30° (32s)
- Complex interference zones: diamonds, waves, beat patterns
- Eye sweeps across field to reveal different pattern zones
- Line count: 40-60 lines per grid

### 40-55s: Saturation
- Add grids at +45° and +60°
- Dense field of intersecting lines
- Moiré creates organic emergent shapes: tunnels, spirals, beats
- Occasional "breathing" zooms amplify interference
- Line count: 80-100 lines per grid

### 55-60s: Hold and Release
- Eye slows to a stop
- Full dense pattern holds for 2 seconds
- Smooth zoom out reveals entire field
- Cut to black

## Technical Specifications

### Resolution & Format
- Output: 1280x720 (720p)
- FPS: 24
- Duration: 60 seconds (1440 frames)
- Codec: H.264 with yuv420p pixel format

### Rendering Approach
- NumPy arrays for frame buffers
- PIL (Pillow) for line rendering via ImageDraw
- Virtual canvas larger than viewport (1920x1080) for eye movement
- Smooth camera position interpolation
- Direct piping to FFmpeg (no temp frames)

### Grid System
- 7 total grid layers added sequentially
- Each grid: lines at fixed angle, evenly spaced
- Density increases per layer (20 → 100 lines)
- Line thickness: 1px, antialiased

### Camera/Eye Movement
- Slow drift across virtual canvas
- Sinusoidal path with gentle curves
- Occasional zoom breathing (scale 0.9x to 1.1x)

## Audio Direction

### Drone Layer
- Sustained low sine waves: 80-120Hz
- Subtle pitch shifts as visual density increases
- Volume: -12dB, gradually rising to -6dB

### Interference Tones
- High harmonics (800-2000Hz) when moiré beats are strong
- Ringing quality against drone
- Triggered by visual beat frequency moments

### Pulse Layer
- Soft 4/4 heartbeat emerges at 30s
- Strengthens toward end (55s)
- Frequency: 60-80 BPM

## Color Palette
- Background: #000000 (pure black)
- Grid lines: #FFFFFF (white), #E0FFFF (light cyan alternate)
- Optional: subtle alpha blending for depth

## Success Criteria
- Moiré patterns are clearly visible and evolve throughout
- Eye movement feels smooth and intentional
- Density build creates satisfying visual arc
- Audio complements without overwhelming
- Final render plays cleanly in standard video players

## Dependencies
- numpy
- Pillow (PIL)
- FFmpeg (with H.264 encoder)
- Optional: scipy for audio synthesis
