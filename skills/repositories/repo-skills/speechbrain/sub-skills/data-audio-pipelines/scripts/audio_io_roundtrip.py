#!/usr/bin/env python3
"""Run a synthetic SpeechBrain audio_io roundtrip."""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from pathlib import Path


def run(sample_rate: int, duration: float) -> dict:
    import torch
    from speechbrain.dataio import audio_io

    frames = int(sample_rate * duration)
    t = torch.linspace(0, duration, frames)
    wave = torch.sin(2 * math.pi * 440.0 * t).unsqueeze(0)
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        audio_io.save(path, wave, sample_rate)
        loaded, sr = audio_io.load(path)
        info = audio_io.info(path)
        close = torch.allclose(loaded, wave, atol=1e-3)
        return {
            "path_suffix": Path(path).suffix,
            "sample_rate": sr,
            "shape": list(loaded.shape),
            "duration": info.duration,
            "channels": info.channels,
            "format": info.format,
            "roundtrip_close": bool(close),
        }
    finally:
        Path(path).unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-rate", type=int, default=16000)
    parser.add_argument("--duration", type=float, default=0.25)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run(args.sample_rate, args.duration)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result)


if __name__ == "__main__":
    main()
