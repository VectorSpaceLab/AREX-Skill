#!/usr/bin/env python3
"""Quickly validate that a MIDI file exists and is parseable.

This helper is safe: it only reads the MIDI file and prints a small summary.
Example:
    python sub-skills/media-minigames/scripts/check_midi_file.py songs/example.mid
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    import mido
except Exception as exc:  # optional dependency
    mido = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("midi_file", type=Path)
    args = parser.parse_args(argv)

    if mido is None:
        print(f"missing optional dependency: mido ({type(_IMPORT_ERROR).__name__}: {_IMPORT_ERROR})")
        return 2

    path = args.midi_file.expanduser()
    if not path.exists():
        print(f"missing file: {path}")
        return 2
    try:
        midi = mido.MidiFile(path)
    except Exception as exc:
        print(f"invalid MIDI: {type(exc).__name__}: {exc}")
        return 2

    track_count = len(midi.tracks)
    msg_count = sum(len(track) for track in midi.tracks)
    print(f"OK: {path} | ticks_per_beat={midi.ticks_per_beat} | tracks={track_count} | messages={msg_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
