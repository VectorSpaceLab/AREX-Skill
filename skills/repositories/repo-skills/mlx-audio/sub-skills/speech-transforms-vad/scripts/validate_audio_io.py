from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import numpy as np

from mlx_audio.audio_io import read, write


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate MLX Audio I/O on a tiny fixture")
    parser.add_argument("--format", default="wav")
    parser.add_argument("--sample-rate", type=int, default=16000)
    parser.add_argument("--duration-seconds", type=float, default=0.25)
    parser.add_argument("--target-sample-rate", type=int, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    n = max(1, int(args.sample_rate * args.duration_seconds))
    t = np.linspace(0.0, args.duration_seconds, n, endpoint=False)
    audio = (0.1 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / f"fixture.{args.format}"
        write(path, audio, args.sample_rate, format=args.format)
        loaded, loaded_rate = read(
            path,
            dtype="float32",
            sample_rate=args.target_sample_rate,
            nchannels=1,
        )
        payload = {
            "path": str(path.name),
            "written_sample_rate": args.sample_rate,
            "read_sample_rate": int(loaded_rate),
            "loaded_shape": list(np.asarray(loaded).shape),
            "loaded_dtype": str(np.asarray(loaded).dtype),
        }
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
