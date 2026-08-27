#!/usr/bin/env python3
"""Safely rewrite the embedded `est_name` in an evo result archive.

Usage:
  python scripts/rename_result_estimate.py input.zip output.zip new_name
"""

from __future__ import annotations

import argparse
from pathlib import Path

from evo.tools import file_interface


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", type=Path)
    parser.add_argument("output_file", type=Path)
    parser.add_argument("new_name")
    args = parser.parse_args()

    result = file_interface.load_res_file(args.input_file, load_trajectories=True)
    result.info["est_name"] = args.new_name
    file_interface.save_res_file(args.output_file, result)
    print(f"ok: wrote renamed result archive to {args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
