"""Generate soft, royalty-free ambient tracks for the music library.

Run:  python scripts/generate_music.py
The resulting WAV files live in static/audio/ and are copied into MEDIA_ROOT
by the `seed_love` management command.
"""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

SR = 22050
OUT = Path(__file__).resolve().parent.parent / "static" / "audio"
OUT.mkdir(parents=True, exist_ok=True)


def freq(note: str) -> float:
    """Convert scientific pitch notation (e.g. 'C4', 'F#3') to Hz."""
    names = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
             "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
    name = note[:-1]
    octave = int(note[-1])
    midi = 12 * (octave + 1) + names[name]
    return 440.0 * 2 ** ((midi - 69) / 12)


def envelope(i: int, n: int, attack: float, release: float, curve: float = 3.0) -> float:
    t = i / SR
    a = min(1.0, t / attack) if attack > 0 else 1.0
    remaining = (n - i) / SR
    r = min(1.0, remaining / release) if release > 0 else 1.0
    return (a * r) ** curve


def add_note(buf: list[float], start: float, note: str, duration: float,
             gain: float, harmonics=(1.0, 0.35, 0.14), decay: float = 2.0,
             vibrato: float = 0.0) -> None:
    f = freq(note)
    begin = int(start * SR)
    length = int(duration * SR)
    for i in range(length):
        idx = begin + i
        if idx >= len(buf):
            break
        t = i / SR
        env = math.exp(-decay * t) * min(1.0, t / 0.012)
        vib = 1.0 + vibrato * math.sin(2 * math.pi * 5.2 * t)
        sample = 0.0
        for h, amp in enumerate(harmonics, start=1):
            sample += amp * math.sin(2 * math.pi * f * h * vib * t)
        buf[idx] += gain * env * sample


def add_pad(buf: list[float], start: float, notes: list[str], duration: float,
            gain: float = 0.035) -> None:
    begin = int(start * SR)
    length = int(duration * SR)
    for i in range(length):
        idx = begin + i
        if idx >= len(buf):
            break
        t = i / SR
        env = min(1.0, t / 1.6) * min(1.0, max(0.0, (length - i) / (SR * 1.8)))
        for note in notes:
            f = freq(note)
            detune = 1.0 + 0.0018 * math.sin(2 * math.pi * 0.15 * t + f)
            buf[idx] += gain * env * (
                math.sin(2 * math.pi * f * detune * t)
                + 0.18 * math.sin(2 * math.pi * f * 2.01 * t)
            )


def echo(buf: list[float], delay: float = 0.38, feedback: float = 0.26) -> list[float]:
    out = list(buf)
    offset = int(delay * SR)
    for i in range(offset, len(buf)):
        out[i] += out[i - offset] * feedback
    return out


def normalize(buf: list[float], peak: float = 0.82) -> list[float]:
    top = max((abs(x) for x in buf), default=1.0) or 1.0
    scale = peak / top
    return [x * scale for x in buf]


def write(name: str, buf: list[float], fade: float = 2.0) -> None:
    fade_n = int(fade * SR)
    total = len(buf)
    for i in range(fade_n):
        g = i / fade_n
        buf[i] *= g
        buf[total - 1 - i] *= g
    path = OUT / name
    with wave.open(str(path), "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(SR)
        frames = bytearray()
        for sample in buf:
            s = max(-1.0, min(1.0, sample))
            frames += struct.pack("<h", int(s * 32767))
        fh.writeframes(bytes(frames))
    print(f"wrote {path.name} ({path.stat().st_size / 1_048_576:.2f} MB)")


def quiet_song() -> None:
    """Gentle piano arpeggio — Cmaj7 / Am7 / Fmaj7 / G."""
    duration = 32.0
    buf = [0.0] * (int(duration * SR) + 1)
    chords = [
        (["C3", "G3", "B3", "E4"], ["C4", "E4", "G4", "B4", "E5", "B4", "G4", "E4"]),
        (["A2", "E3", "G3", "C4"], ["A3", "C4", "E4", "G4", "C5", "G4", "E4", "C4"]),
        (["F2", "C3", "E3", "A3"], ["F3", "A3", "C4", "E4", "A4", "E4", "C4", "A3"]),
        (["G2", "D3", "G3", "B3"], ["G3", "B3", "D4", "G4", "B4", "G4", "D4", "B3"]),
    ]
    beat = 0.9
    t = 0.0
    for group in range(2):
        for pad_notes, arp in chords:
            add_pad(buf, t, pad_notes, beat * 8, gain=0.03)
            for i, note in enumerate(arp):
                add_note(buf, t + i * beat, note, 2.4, gain=0.105, decay=1.9)
            t += beat * 8
    write("quiet-song.wav", normalize(echo(buf)))


def moonlight() -> None:
    """A slow music-box waltz in A minor."""
    duration = 34.0
    buf = [0.0] * (int(duration * SR) + 1)
    progression = [
        ("Am", ["A3", "C4", "E4", "A4"]),
        ("F", ["F3", "A3", "C4", "F4"]),
        ("C", ["C3", "E3", "G3", "C4"]),
        ("G", ["G3", "B3", "D4", "G4"]),
        ("Dm", ["D3", "F3", "A3", "D4"]),
        ("E", ["E3", "G#3", "B3", "E4"]),
        ("Am", ["A3", "C4", "E4", "A4"]),
        ("E", ["E3", "G#3", "B3", "E4"]),
    ]
    beat = 1.05
    t = 0.0
    for _ in range(1):
        for _name, notes in progression:
            add_pad(buf, t, [n[:-1] + "3" for n in notes[:2]], beat * 6, gain=0.026)
            pattern = [notes[0], notes[2], notes[3], notes[1], notes[3], notes[2]]
            for i, note in enumerate(pattern):
                add_note(buf, t + i * beat, note, 3.0, gain=0.085,
                         harmonics=(1.0, 0.22, 0.42, 0.12), decay=1.35)
                add_note(buf, t + i * beat, note[:-1] + str(int(note[-1]) + 1),
                         2.4, gain=0.018, harmonics=(1.0, 0.1), decay=1.8)
            t += beat * 6
    write("moonlight-waltz.wav", normalize(echo(buf, 0.42, 0.32)))


def rose_petal() -> None:
    """Warm, slow string pad in F major."""
    duration = 36.0
    buf = [0.0] * (int(duration * SR) + 1)
    chords = [
        ["F2", "C3", "A3", "F4"],
        ["D2", "A2", "F3", "D4"],
        ["A#1", "F2", "D3", "A#3"],
        ["C2", "G2", "E3", "C4"],
        ["F2", "C3", "A3", "F4"],
        ["A#1", "F2", "D3", "A#3"],
    ]
    span = duration / len(chords)
    for i, notes in enumerate(chords):
        add_pad(buf, i * span, notes, span + 2.5, gain=0.055)
        lead = notes[-1]
        add_note(buf, i * span + 0.6, lead, span * 0.8, gain=0.045,
                 harmonics=(1.0, 0.2, 0.08), decay=0.55, vibrato=0.0025)
        add_note(buf, i * span + span * 0.55, notes[2], span * 0.5, gain=0.035,
                 harmonics=(1.0, 0.2), decay=0.7, vibrato=0.002)
    write("rose-petal-lullaby.wav", normalize(echo(buf, 0.55, 0.34), 0.72))


if __name__ == "__main__":
    random.seed(4)
    quiet_song()
    moonlight()
    rose_petal()
