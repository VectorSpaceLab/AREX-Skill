#!/usr/bin/env python3
"""Validate and normalize openpilot route/segment/range identifiers without downloading logs."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main() -> int:
  parser = argparse.ArgumentParser(description="Validate an openpilot route, segment, or segment range string")
  parser.add_argument("identifier")
  parser.add_argument("--show-segments", action="store_true", help="print seg_idxs; avoid open-ended ranges offline")
  parser.add_argument("--repo-root", help="target openpilot checkout to add to sys.path when openpilot is not installed")
  args = parser.parse_args()

  if args.repo_root:
    root = Path(args.repo_root).resolve()
    sys.path.insert(0, str(root))
    for sub in ("msgq_repo", "opendbc_repo", "rednose_repo", "teleoprtc_repo", "tinygrad_repo"):
      sys.path.insert(0, str(root / sub))

  try:
    from openpilot.tools.lib.route import SegmentRange, SegmentName, RouteName
  except Exception as exc:
    parser.error(f"openpilot route APIs are not importable: {exc}")

  try:
    if "--" in args.identifier.rsplit("|", 1)[-1] or "/" in args.identifier.rsplit("|", 1)[-1]:
      try:
        sr = SegmentRange(args.identifier)
        print(f"segment_range={sr}")
        print(f"route_name={sr.route_name}")
        print(f"selector={sr.selector or 'default-rlog'}")
        if args.show_segments:
          print(f"segment_indexes={list(sr.seg_idxs)}")
        return 0
      except Exception:
        sn = SegmentName(args.identifier, allow_route_name=True)
        print(f"segment_name={sn}")
        print(f"route_name={sn.route_name}")
        print(f"segment_num={sn.segment_num}")
        return 0
    rn = RouteName(args.identifier)
    print(f"route_name={rn}")
    print(f"dongle_id={rn.dongle_id}")
    print(f"log_id={rn.log_id}")
    return 0
  except Exception as exc:
    print(f"invalid openpilot route identifier: {exc}")
    return 2


if __name__ == "__main__":
  raise SystemExit(main())
