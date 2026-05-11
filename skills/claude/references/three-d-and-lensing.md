# 3D, Perspective, and Lensing

Use this reference when a piece needs perceived depth without taking on a real-time 3D engine. The PyReeler approach is "lean 3D": pure-NumPy math that we can spend seconds-per-frame on, instead of being capped at 16 ms.

## When to reach for 3D

- The piece's motif rotates, drifts in z, or otherwise relies on parallax.
- You want perspective-warped face textures (e.g. a rotating cube with a different texture on each face).
- You want the starfield, particle nebula, or background to feel volumetric rather than flat.

If the piece is happy as 2D layers, stay 2D. 3D is a tool, not a default.

## Module map

- `templates/video/geometry_3d.py` — `get_rotation_matrix`, `project_points`, `find_coeffs`
- `templates/video/lensing.py` — `apply_lensing` (Schwarzschild-style radial warp)

Both are pure NumPy + Pillow. No new dependencies, no GPU required.

## The `find_coeffs` direction gotcha

PIL's `Image.transform(size, Image.PERSPECTIVE, coeffs, ...)` interprets `coeffs` as an **output → input** (inverse) mapping. For each pixel in the output, PIL inverts the transform to find the source pixel.

Therefore, to paint a source rectangle `src_pa` onto a target quadrilateral `target_pb`:

```python
from templates.video.geometry_3d import find_coeffs

coeffs = find_coeffs(target_pb, src_pa)   # target first, source second
warped = src_img.transform((W, H), Image.PERSPECTIVE, coeffs, Image.BILINEAR)
```

Reversing the arguments produces a tiny, clipped texture in the corner of the output rather than filling the target polygon. This bug exists in some older PyReeler experiments — when reading older code, check the call order before copying patterns.

## Per-face texturing recipe

To render a rotating cube with a textured face per side:

1. Build the cube (8 vertices, 6 faces).
2. Each frame: rotate vertices, perspective-project to 2D.
3. Depth-sort faces by mean z, back-to-front.
4. Backface-cull: skip any face whose surface normal points away from camera.
5. For each remaining face: compute `find_coeffs(target_face_corners, texture_corners)`, transform the texture into the frame's coordinate space, then paste through a polygon mask of the face corners.
6. (Optional) Compute a per-face directional-lighting intensity from the dot product of the face normal with a virtual light direction; multiply the warped RGB by that intensity for volumetric weight.

This is the pattern `experimental/experiments/cosmic_collapse.py:render_cube_layer` follows.

## Gravitational lensing

`apply_lensing(layer, lens_centers, K)` warps an RGBA layer (typically a starfield, optionally with backgrounds) so pixels near each lens center are pulled inward by a `1/r²` term, capped by an event-horizon limit.

Key choices:

- Lens centers are **screen-space**. Couple them to the projected positions of in-scene singularities (e.g. each visible cube face's center) so they track motion automatically.
- `K` is a time-varying scalar — drive it from your `arc_state(t)` so the warp ramps in and spikes on cue.
- Each lens carries a per-instance `strength` in `[0, 1]`. Set it from how directly the face is facing the camera (e.g. `-normal_z`), so off-axis faces lens less.
- `k_scale` (default 4000) sets the lens "size" in pixel-area units. Raise to widen the warp, lower to tighten it.

The displacement composes additively across multiple centers, which is physically rough but visually convincing for "gravity wells on each cube face."

## Performance budget

- 1280×720 starfield render: tens of milliseconds.
- Lensing pass at 1280×720 with 3 lens centers: 200–400 ms on a modern CPU.
- Cube face passes (6 PIL `transform` calls + composites): ~100 ms.

For a 900-frame piece this lands in the 5–15 minute total range. If a piece's per-frame cost climbs above ~2 s, downscale the lensing displacement to half-resolution and upsample, or reduce `STAR_COUNT`.

## Reference implementation

`experimental/experiments/cosmic_collapse.py` is the canonical example combining geometry_3d, lensing, a perspective-warped per-face texture, particles, and a god's-CLI text overlay against a single `arc_state(t)` timeline.
