"""Pre-render quality audit: sample several arc frames, re-roll bad params.

When a renderer depends on a randomized parameter set (chaotic attractor
constants, noise seeds, palette selectors), a single bad draw can produce
a blank, low-contrast, or flat preview. This helper renders a small number
of sample frames spread across the piece's arc and re-rolls the random
inputs until every sample passes a configurable per-frame check.

The default check is contrast (np.mean of per-channel stddev). The threshold
can vary by sample point — for a three-act piece, act 1 is intentionally
sparse and gets a low minimum, act 2 is the bloom and gets the highest
minimum, act 3 is the collapse and gets a medium minimum.

Usage:

    auditor = SelfHealer(
        sample_times=[(4.0, 5.0), (15.0, 12.0), (27.0, 8.0)],
        try_params=lambda rng: (rng.uniform(-2.5, -1.0),
                                rng.uniform(1.2, 2.5)),
        render_with=lambda params, t: render_frame(int(t * FPS), {"params": params}),
    )
    params = auditor.find_good_params()
    if params is None:
        sys.exit(1)
"""
from __future__ import annotations

import numpy as np
from PIL import ImageStat


class SelfHealer:
    """Multi-sample-frame audit with parameter re-rolling.

    Parameters
    ----------
    sample_times : list of (float, float)
        Each (t_seconds, min_contrast) — render the piece at t_seconds and
        require contrast >= min_contrast.
    try_params : callable(rng) -> tuple
        A function taking a numpy Generator and returning a parameter tuple.
        Will be called once per attempt.
    render_with : callable(params, t) -> PIL.Image.Image
        Given a parameter tuple and a sample time, return a rendered frame.
    max_attempts : int
        Maximum number of re-roll attempts before giving up.
    metric : callable(PIL.Image.Image) -> float
        Optional custom quality metric. Defaults to mean per-channel stddev.
    rng : numpy.random.Generator, optional
        Defaults to numpy.random.default_rng() (system entropy seed).
    verbose : bool
        If True, prints each attempt's params and contrast values.
    """

    def __init__(self, sample_times, try_params, render_with,
                 max_attempts: int = 5, metric=None, rng=None,
                 verbose: bool = True) -> None:
        self.sample_times = sample_times
        self.try_params = try_params
        self.render_with = render_with
        self.max_attempts = max_attempts
        self.metric = metric or self._default_metric
        self.rng = rng if rng is not None else np.random.default_rng()
        self.verbose = verbose

    @staticmethod
    def _default_metric(frame) -> float:
        return float(np.mean(ImageStat.Stat(frame).stddev))

    def find_good_params(self):
        """Try up to max_attempts param rolls. Return the first passing tuple,
        or None if all attempts fail."""
        for attempt in range(1, self.max_attempts + 1):
            params = self.try_params(self.rng)
            if self.verbose:
                print(f"   [AUDIT] Attempt {attempt}: {params}")
            ok = True
            for t_sec, min_score in self.sample_times:
                frame = self.render_with(params, t_sec)
                score = float(self.metric(frame))
                if self.verbose:
                    print(f"     t={t_sec}s score={score:.2f} (min {min_score})")
                if score < min_score:
                    ok = False
                    break
            if ok:
                if self.verbose:
                    print(f">> AUDIT PASS on attempt {attempt}")
                return params
        if self.verbose:
            print(">> AUDIT FAILED after max attempts")
        return None
