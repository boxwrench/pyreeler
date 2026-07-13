"""Behavioral tests for the canonical audio mixing and WAV helpers."""
import wave

import numpy as np

from templates.audio import audio_engine


def test_place_stem_handles_offsets_and_clips_to_timeline():
    stem = np.array([1, 2, 3, 4], dtype=np.float32)

    delayed = audio_engine.place_stem(stem, total_samples=5, start_sec=0.2, sample_rate=10)
    early = audio_engine.place_stem(stem, total_samples=3, start_sec=-0.2, sample_rate=10)

    np.testing.assert_array_equal(delayed, [0, 0, 1, 2, 3])
    np.testing.assert_array_equal(early, [3, 4, 0])


def test_duck_under_voice_only_attenuates_active_voice_samples():
    stem = np.ones(4, dtype=np.float32)
    voice = np.array([0, 0.5, 1.0, 0], dtype=np.float32)

    ducked = audio_engine.duck_under_voice(stem, voice, amount=0.6, floor=0.5)

    np.testing.assert_allclose(ducked, [1.0, 0.7, 0.5, 1.0])


def test_mix_stems_aligns_lengths_applies_gains_and_bounds_output():
    stems = {
        "score": np.ones(4, dtype=np.float32),
        "voice": np.array([0.0, 1.0], dtype=np.float32),
    }

    mixed = audio_engine.mix_stems(stems, gains={"score": 0.5}, duck_voice=False)

    assert mixed.dtype == np.float32
    assert mixed.shape == (4,)
    assert np.max(np.abs(mixed)) <= 0.95
    assert mixed[1] > mixed[0]


def test_write_mono_wav_emits_clipped_pcm_with_requested_rate(tmp_path):
    path = tmp_path / "nested" / "mix.wav"
    signal = np.array([-2.0, 0.0, 2.0], dtype=np.float32)

    audio_engine.write_mono_wav(path, signal, sample_rate=8000)

    with wave.open(str(path), "rb") as handle:
        assert handle.getnchannels() == 1
        assert handle.getsampwidth() == 2
        assert handle.getframerate() == 8000
        assert handle.getnframes() == 3
        pcm = np.frombuffer(handle.readframes(3), dtype=np.int16)
    np.testing.assert_array_equal(pcm, [-32767, 0, 32767])
