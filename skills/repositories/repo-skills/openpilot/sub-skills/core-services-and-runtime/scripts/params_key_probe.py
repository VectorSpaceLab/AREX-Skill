#!/usr/bin/env python3
"""Probe known Params keys without writing values."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main() -> int:
  parser = argparse.ArgumentParser(description="Inspect Params keys and defaults from an openpilot checkout")
  parser.add_argument("key", nargs="*", help="specific keys to probe")
  parser.add_argument("--repo-root", help="target openpilot checkout to add to sys.path when openpilot is not installed")
  args = parser.parse_args()

  if args.repo_root:
    root = Path(args.repo_root).resolve()
    sys.path.insert(0, str(root))
    for sub in ("msgq_repo", "opendbc_repo", "rednose_repo", "teleoprtc_repo", "tinygrad_repo"):
      sys.path.insert(0, str(root / sub))

  try:
    from openpilot.common.params import Params
  except Exception as exc:
    parser.error(f"openpilot Params are not importable: {exc}")

  p = Params()
  keys = args.key or ["CarParams", "DongleId", "IsOffroad", "IsMetric", "LongitudinalPersonality", "LiveParametersV2"]
  for key in keys:
    try:
      value = p.get(key)
      default = p.get(key, return_default=True)
      print(f"{key}: value={value!r} default={default!r} type={type(default).__name__ if default is not None else 'None'}")
    except Exception as exc:
      print(f"{key}: ERROR {exc}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
