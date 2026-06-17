"""Tests for audio-reactive parameter mapping helpers."""
import numpy as np
import pytest

from templates.audio.audio_reactive import map_range, reactive_value, rms_envelope


def test_rms_envelope_silence_returns_zeros():
    env = rms_envelope(np.zeros(1000, dtype=np.float32), 1000, 10, 10)

    assert np.allclose(env, 0.0)


def test_rms_envelope_output_length_matches_frame_count():
    signal = np.ones(1000, dtype=np.float32)

    env = rms_envelope(signal, 1000, 24, 37)

    assert env.shape == (37,)


def test_rms_envelope_loud_second_half_is_higher_than_quiet_first_half():
    quiet = np.full(1000, 0.1, dtype=np.float32)
    loud = np.full(1000, 0.8, dtype=np.float32)
    signal = np.concatenate([quiet, loud])

    env = rms_envelope(signal, 1000, 10, 20, window_sec=0.05, attack=1.0, release=1.0)

    assert float(np.mean(env[12:18])) > float(np.mean(env[2:8])) * 3.0


@pytest.mark.parametrize(
    ("sample_rate", "fps", "frame_count", "window_sec"),
    [
        (0, 10, 10, 0.05),
        (1000, 0, 10, 0.05),
        (1000, 10, 0, 0.05),
        (1000, 10, 10, 0.0),
    ],
)
def test_rms_envelope_rejects_invalid_parameters(sample_rate, fps, frame_count, window_sec):
    with pytest.raises(ValueError):
        rms_envelope(
            np.ones(100, dtype=np.float32),
            sample_rate,
            fps,
            frame_count,
            window_sec=window_sec,
        )


def test_map_range_maps_normalized_extremes():
    mapped = map_range(np.array([0.0, 1.0], dtype=np.float32), 10.0, 20.0)

    assert np.allclose(mapped, [10.0, 20.0])


def test_map_range_curve_shaping_stays_inside_output_range():
    mapped = map_range(np.array([0.0, 0.5, 1.0], dtype=np.float32), -2.0, 2.0, curve=2.0)

    assert float(np.min(mapped)) >= -2.0
    assert float(np.max(mapped)) <= 2.0
    assert mapped[1] < 0.0


def test_reactive_value_add_mode():
    assert reactive_value(10.0, 4.0, 0.25, mode="add") == pytest.approx(11.0)


def test_reactive_value_multiply_mode():
    assert reactive_value(10.0, 0.5, 0.5, mode="multiply") == pytest.approx(12.5)


def test_reactive_value_rejects_unknown_mode():
    with pytest.raises(ValueError):
        reactive_value(10.0, 1.0, 0.5, mode="unknown")
