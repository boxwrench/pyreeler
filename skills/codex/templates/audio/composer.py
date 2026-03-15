from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path


def hz_to_midi(freq_hz: float) -> int:
    return int(round(69 + 12 * math.log2(freq_hz / 440.0)))


def motif_to_note_events(motif_hz, beat_starts, beat_duration: float, velocity: int = 84):
    events = []
    if motif_hz is None:
        return events
    if hasattr(motif_hz, "size"):
        if int(motif_hz.size) == 0:
            return events
    elif len(motif_hz) == 0:
        return events

    for index, start in enumerate(beat_starts):
        freq = motif_hz[index % len(motif_hz)]
        events.append(
            {
                "midi_note": hz_to_midi(freq),
                "start": float(start),
                "duration": float(beat_duration),
                "velocity": int(velocity),
            }
        )
    return events


def write_midi(midi_path, note_events, tempo_bpm: int = 80, program: int = 89):
    try:
        from midiutil import MIDIFile
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Install midiutil to write score templates.") from exc

    midi = MIDIFile(1)
    midi.addTempo(0, 0, tempo_bpm)
    midi.addProgramChange(0, 0, 0, program)

    for event in note_events:
        midi.addNote(
            0,
            0,
            event["midi_note"],
            event["start"],
            event["duration"],
            event["velocity"],
        )

    midi_path = Path(midi_path)
    midi_path.parent.mkdir(parents=True, exist_ok=True)
    with open(midi_path, "wb") as handle:
        midi.writeFile(handle)


def render_with_fluidsynth(midi_path, sf2_path, wav_path, sample_rate: int = 44100):
    fluidsynth_bin = shutil.which("fluidsynth")
    if not fluidsynth_bin:
        raise RuntimeError("Install FluidSynth or render the MIDI with another SoundFont path.")

    cmd = [
        fluidsynth_bin,
        "-ni",
        str(sf2_path),
        str(midi_path),
        "-F",
        str(wav_path),
        "-r",
        str(sample_rate),
    ]
    subprocess.run(cmd, check=True)
    return Path(wav_path)
