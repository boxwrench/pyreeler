"""Combine two recipes via overlay or sequence."""
from __future__ import annotations

from .base import Param, Recipe, register, get, list_recipes

def _prepare(p):
    ra = get(p["recipe_a"])
    rb = get(p["recipe_b"])
    
    from .params import resolve_params
    shared = {
        "width": p.get("width", 854), 
        "height": p.get("height", 480), 
        "trail": p.get("trail", 10000), 
        "thickness": p.get("thickness", 1), 
        "palette": p.get("palette", "phosphor")
    }
    
    pa = resolve_params(ra, shared)
    pb = resolve_params(rb, shared)
    
    prep_a = ra.prepare(pa)
    prep_b = rb.prepare(pb)
    return (p["recipe_a"], pa, prep_a, p["recipe_b"], pb, prep_b)

def _make_frame(prepared, p, frame_idx, total):
    ra_name, pa, prep_a, rb_name, pb, prep_b = prepared
    ra = get(ra_name)
    rb = get(rb_name)
    if p["mode"] == "overlay":
        img_a = ra.make_frame(prep_a, pa, frame_idx, total)
        
        pb_mod = dict(pb)
        if pb_mod["palette"] == p.get("palette", "phosphor"):
            from .base import PALETTES
            others = [k for k in PALETTES if k != pb_mod["palette"]]
            if others:
                pb_mod["palette"] = others[0]
                
        img_b = rb.make_frame(prep_b, pb_mod, frame_idx, total)
        
        from PIL import ImageChops
        return ImageChops.screen(img_a, img_b)
        
    elif p["mode"] == "sequence":
        half = max(1, total // 2)
        if frame_idx < half:
            return ra.make_frame(prep_a, pa, frame_idx * 2, total)
        else:
            return rb.make_frame(prep_b, pb, (frame_idx - half) * 2, total)

def make_combo_recipe() -> Recipe:
    names = tuple(r.name for r in list_recipes() if r.name != "combo")
    if not names:
        names = ("lorenz", "rossler", "aizawa", "thomas", "chen", "halvorsen")

    params = (
        Param("recipe_a", str, names[0], choices=names, help="First recipe to combine"),
        Param("recipe_b", str, names[1] if len(names) > 1 else names[0], choices=names, help="Second recipe to combine"),
        Param("mode", str, "overlay", choices=("overlay", "sequence"), help="How to combine them"),
    )

    return Recipe(
        name="combo",
        summary="Combine two recipes together.",
        description=(
            "Overlays two attractors or plays them in sequence. "
            "In overlay mode, the second attractor automatically uses a contrasting color. "
            "In sequence mode, the first plays for the first half of the film, "
            "followed by the second attractor."
        ),
        params=params, prepare=_prepare, make_frame=_make_frame,
    )

RECIPE = register(make_combo_recipe())
