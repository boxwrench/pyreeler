"""Unit tests for cosmic_collapse film generator."""
import math
import numpy as np
import pytest
from PIL import Image

import cosmic_collapse as cc


def test_arc_state_at_t0_is_void():
    s = cc.arc_state(0.0)
    assert s["cube_alpha"] == 0.0
    assert s["lens_K"] == 0.0
    assert s["particle_density"] == 0.0
    assert s["infall"] == 0.0
    assert s["text_alpha"] == 1.0
    assert 0.0 <= s["audio_intensity"] <= 0.3


def test_arc_state_act2_peak():
    s = cc.arc_state(15.0)
    assert s["cube_alpha"] == 1.0
    assert 0.4 <= s["lens_K"] <= 0.6
    assert s["particle_density"] == 1.0
    assert s["infall"] == 0.0
    assert s["text_alpha"] == 1.0


def test_arc_state_collapse_end():
    s = cc.arc_state(29.0)
    assert s["cube_alpha"] == 1.0
    assert 0.85 <= s["lens_K"] <= 1.0
    assert s["infall"] >= 0.95
    assert s["text_alpha"] == 0.0


def test_arc_state_text_fade_window():
    s_before = cc.arc_state(24.9)
    s_mid = cc.arc_state(26.25)
    s_after = cc.arc_state(27.5)
    assert s_before["text_alpha"] == 1.0
    assert 0.3 < s_mid["text_alpha"] < 0.7
    assert s_after["text_alpha"] == 0.0
