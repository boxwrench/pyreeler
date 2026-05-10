# Cosmic Collapse — 30s Design Spec

**Date:** 2026-05-10
**Target file:** `experimental/experiments/cosmic_collapse.py`
**Output:** `experimental/cosmic_collapse.mp4` — 30s, 1280×720, 30fps, H.264 + AAC
**Lineage:** evolves `experimental/experiments/cosmic_experiment.py`; that file is preserved as reference.

## Goal

Upgrade the existing 10-second cosmic piece into a 30-second, three-act generative film with a single headline visual upgrade (gravitational lensing) and a synchronized "god's CLI" text track that narrates creation as the film unfolds. Audio is event-driven so visual and sonic peaks share one source of truth.

## Three-Act Arc

900 frames total (30s × 30fps). All `t` values below are seconds.

| Act | Window | Visual beats | Text-track beats | Audio beats |
|---|---|---|---|---|
| 1 — Genesis | 0–8 | Black screen → starfield fades in (~3000 stars). Cube wireframe ghosts in at t=4 as faint cyan edges. No lensing. | `$ universe.init(...)`, `> and there was void.`, star/cube spawn lines. | Sub drone fades in (38Hz FM, low index). Sparse soft-keystroke clicks on each `$` line. |
| 2 — Bloom | 8–22 | Cube solidifies (textured faces, directional shading). Black-hole accretion textures ignite on cube faces (each face's texture rotates per-frame). Particle nebula floods in (Clifford attractor, full density). **Lensing strength `K(t)` ramps from 0 → 0.55**, visibly bending the starfield around each black-hole face. | `$ ignite singularities --faces=6`, `> and the shape consumed light.`, `$ bend space --k=...`. | Drone modulation index rises. Granular shimmer pad joins (filtered noise + 220Hz FM partial). Lens-driven pitch-bend bursts on each `K(t)` peak. |
| 3 — Collapse | 22–30 | Particle positions interpolate toward cube's projected center (gravitational infall). `K(t)` spikes to 0.95, lensing tears the starfield. Cube edges distort. Everything shrinks toward a single point at t=29. Final 1s: black with a single lingering pixel. HUD/text fades out by t=25. | `$ collapse --target=center`, `> and the form fell inward.`, `$ kill light`, `> and it was good.`, `$ exit` (typed at t=28, final char lands with sub-bass). | Reverse-FM swell from t=22. **30Hz sub-bass impact at t=28** synced to `$ exit` keystroke. 1.5s decay tail to silence. |

## Visual Pipeline

### New: Starfield + Gravitational Lensing (the headline)

Replaces the old per-pixel particle-cloud-only approach.

- **Starfield generation**: ~3000 stars distributed in a 3D shell (radius 8–25 from origin), generated once at start with fixed seed for reproducibility. Each star has (xyz, brightness, color temp).
- **Per-frame projection**: same `project_points()` math already in `cosmic_experiment.py`. Produces an `(N, 2)` array of screen coords + depths.
- **Render starfield to a base layer** (RGBA): each star drawn as a 1–3px point with brightness scaled by depth.
- **Lensing displacement pass**: for each cube face that is camera-facing (uses existing backface check), compute its 2D projected center `c_face`. Build a NumPy meshgrid of pixel coords, then for each lens center compute radial offset:
  ```
  dx = x - c_face.x; dy = y - c_face.y
  r2 = dx² + dy² + ε
  scale = 1 - K(t) * face_strength / r2
  scale = clip(scale, lower=0)   # event-horizon clamp
  src_x = c_face.x + dx * scale
  src_y = c_face.y + dy * scale
  ```
  Multiple lens centers compose by accumulating displacements (sum in screen space).
- **Resample**: bilinear sample of the un-lensed starfield layer at displaced coordinates. Pure NumPy (`np.clip` + integer indexing for nearest, or 4-tap bilinear). No new dependencies.
- **Cost target**: lensing pass ≤ 200ms/frame at 1280×720 on a modern CPU. If profiling shows it's slower, fall back to half-res displacement map upsampled.

### Cube + Black-Hole Faces (kept, refined)

- Existing perspective-warp pipeline retained.
- **Accretion texture animates**: rotate the texture by `t * 30°/s` before warping, so each face shimmers.
- Directional shading kept.
- Cube alpha follows arc: 0 in act 1 until t=4, ramps to 1 by t=8.

### Particle Nebula (Clifford, kept and modulated)

- 15,000 attractor points, generated per-render after self-healing chooses params.
- **Density schedule**: 0% (act 1) → 100% by t=12 (act 2) → infall by act 3.
- **Infall (act 3)**: each particle's projected position is lerped toward the cube's projected center using `infall(t) = smoothstep(22, 29, t)`. Particle alpha also ramps down.

### God's-CLI Text Track (new — replaces old static HUD)

- **Position**: lower-left, 32px from edge, monospace (Consolas 22pt, fallback default).
- **Style**: terminal-like, scrolling upward. Last ~10 lines visible. Older lines fade out.
- **Color**: `$ command` lines in `(0, 220, 200)` cyan; `> response` lines in `(180, 240, 200)` dim mint.
- **Typing effect**: ~30 chars/sec reveal, then settles, then scrolls when next line appears.
- **Cursor**: blinking block cursor on the active line.
- **Timeline (concrete script — lines staged at these times):**

  ```
  t=0.4   $ universe.init(seed=0xDEADBEEF)
  t=1.2   > and there was void.
  t=2.5   $ spawn stars --n=3000
  t=3.4   > and the dark was given points.
  t=5.0   $ alloc cube --dim=3
  t=6.6   > and a shape was given form.
  t=8.0   $ ignite singularities --faces=6
  t=9.6   > and the shape consumed light.
  t=12.0  $ bend space --k=0.4
  t=13.2  > and the heavens curved.
  t=16.0  $ summon nebula --particles=15000
  t=17.6  > and the void was filled.
  t=20.0  $ tune gravity --k=0.8
  t=22.0  $ collapse --target=center
  t=23.0  > and the form fell inward.
  t=25.5  $ kill light
  t=26.5  > and it was good.
  t=28.0  $ exit
  ```

- **Fadeout**: at t=25 the scrolling text block begins a 2.5-second alpha fade to 0, completing at t=27.5. The final `$ exit` (t=28) is **not** part of the faded block — it appears as a single isolated cyan line at full alpha, types in 0.5s, holds for 1s under the sub-bass, then cuts to black at t=29.5.
- **Sync to audio**: each `$` line emits a soft keystroke click sample (procedural — short noise burst with bandpass filter). The `$ exit` keystrokes at t=28 are the trigger for the 30Hz sub-bass impact.

## Audio Pipeline (event-driven, ~30s)

Single mixer, three sources:

1. **Drone** — 38Hz FM carrier. Modulation index follows arc curve: `index(t) = 1.5 + 4.0 * arc_intensity(t)`. Always present, low gain in act 1, full gain by act 2.
2. **Shimmer pad (act 2 onward)** — filtered noise + 220Hz FM partial. Envelope opens at t=8, peaks t=18, ducks during collapse.
3. **Event layer** (sample-accurate, driven by shared timeline):
   - Keystroke clicks on each `$` text line.
   - Lens-pitch bursts at fixed event times t ∈ {12.0, 14.5, 17.0, 19.5, 21.0} — each a 250ms ring-modulated FM blip alternating 110Hz/220Hz. These match the `$ bend space`, `$ summon nebula`, `$ tune gravity` lines and fill the gaps between.
   - **Reverse-FM swell** starts t=22, duration 6s, rising pitch + filter sweep.
   - **Sub-bass impact at t=28** — 30Hz sine with 50ms attack, 1.5s exponential decay. Clipped at -3dBFS.

The same `K(t)` curve and the same text-track timeline are shared between the visual and audio modules, so events are guaranteed in sync.

## Self-Healing (extended)

The existing `SelfHealer` is kept but its audit is upgraded:

- Render **three sample frames** at t=4 (act 1), t=15 (act 2), t=27 (act 3) instead of a single frame.
- For each, compute `contrast = mean(stddev_per_channel)`.
- **Pass criterion**: act-2 frame contrast > 12 AND act-3 frame contrast > 8 (act 1 is intentionally sparse).
- Re-roll Clifford `(a, b, c, d)` parameters up to 5 times. Star seed and lens parameters are deterministic and not re-rolled.
- Failure mode unchanged: exit code 1 with diagnostic.

## Implementation Strategy

1. **New file** `experimental/experiments/cosmic_collapse.py`. Do not modify `cosmic_experiment.py` — keep it as the reference 10s baseline.
2. **Reuse from `cosmic_experiment.py`** (copy, not import — the experiments dir is intentionally self-contained):
   - `get_rotation_matrix`, `project_points`, `find_coeffs`
   - `create_black_hole_texture`, `create_cube`, `clifford_attractor`
   - `fm_wave` and the audio scaffolding
3. **New modules within the file**:
   - `arc_state(t) -> dict` — single source of truth: returns `cube_alpha`, `lens_K`, `particle_density`, `infall`, `text_alpha`, `audio_intensity` for a given time.
   - `render_starfield(stars, width, height) -> RGBA Image` — un-lensed base layer.
   - `apply_lensing(layer, lens_centers, K) -> RGBA Image` — meshgrid + bilinear sample.
   - `TextTrack` class — owns the timeline, types lines char-by-char, renders the scrolling block, exposes `keystroke_events()` for audio sync.
   - `compose_audio(arc_curve, text_keystrokes) -> int16 array` — replaces the single `generate_cosmic_audio` with the layered/event-driven mixer.
4. **`render_frame` signature**: `render_frame(frame_num, fps, ctx) -> (Image, persistence_buffer)` where `ctx` bundles starfield, cube data, attractor cloud, text-track, font, light direction, persistence buffer. Removes the long parameter list and threads `arc_state(t)` through one place.
5. **Render budget**: full HD, single pass. Expect 8–20 minutes wall-clock on a modern CPU. No preview pass — the user accepted the wait. Self-healing audits 3 sample frames before committing to the full 900-frame render.

## File / Module Layout

```
experimental/experiments/cosmic_collapse.py        # the new piece
experimental/cosmic_collapse.mp4                    # final output (gitignored)
docs/specs/2026-05-10-cosmic-collapse-design.md    # this file
docs/plans/2026-05-10-cosmic-collapse-plan.md      # next step (writing-plans)
```

## Out of Scope

- Real-time interactive version (this is offline rendering by design).
- Replacing `cosmic_experiment.py`.
- New external dependencies (must work with current `numpy`, `Pillow`, `ffmpeg` setup).
- Full opencv / scipy / moderngl integration.
- Any 4K render pass.

## Success Criteria

1. `python experimental/experiments/cosmic_collapse.py` produces `experimental/cosmic_collapse.mp4`, exactly 30.0s long, 1280×720, with audio.
2. Lensing is visibly bending the starfield around at least one cube face during act 2, on inspection of any frame in [12, 22].
3. The god's-CLI text is readable, typed in real time, and lines appear at the timestamps specified in this spec (±1 frame).
4. Sub-bass impact at t=28 is audible and synced with the final `$ exit` keystroke.
5. Self-healing audit passes within ≤5 attempts on a fresh run.
6. No new pip dependencies introduced.
