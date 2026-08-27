#!/usr/bin/env python3
"""Scale timestamps in a TUM trajectory file and write the result elsewhere.

Usage:
  python scripts/scale_tum_timestamps.py input.tum 0.5 out.tum
"""

from __future__ import annotations

import argparse
from pathlib import Path

from evo.tools import file_interface


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", type=Path)
    parser.add_argument("factor", type=float)
    parser.add_argument("output_file", type=Path)
    args = parser.parse_args()

    trajectory = file_interface.read_tum_trajectory_file(args.input_file)
    trajectory.timestamps = trajectory.timestamps * args.factor
    file_interface.write_tum_trajectory_file(args.output_file, trajectory)
    print(f"ok: wrote scaled TUM trajectory to {args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
