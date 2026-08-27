#!/usr/bin/env python3
"""Extract a route/log fingerprint summary for car-port triage."""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import sys


def main() -> int:
  parser = argparse.ArgumentParser(description="Print CAN fingerprint, FW versions, and VIN from an openpilot route/log")
  parser.add_argument("source", help="route/segment/log path")
  parser.add_argument("--qlog", action="store_true", help="prefer qlog mode when a route is provided")
  parser.add_argument("--car-model", help="override the guessed car model label in the output")
  parser.add_argument("--repo-root", help="target openpilot checkout to add to sys.path when openpilot is not installed")
  args = parser.parse_args()

  if args.repo_root:
    root = Path(args.repo_root).resolve()
    sys.path.insert(0, str(root))
    for sub in ("msgq_repo", "opendbc_repo", "rednose_repo", "teleoprtc_repo", "tinygrad_repo"):
      sys.path.insert(0, str(root / sub))

  try:
    from openpilot.tools.lib.logreader import LogReader, ReadMode
  except Exception as exc:
    parser.error(f"openpilot LogReader is not importable: {exc}")

  source = args.source
  if not (Path(source).exists() or source.startswith(("http://", "https://", "cd:/")) or "|" in source or "/" in source):
    parser.error("source must be a route/segment/log path, URL, or local file")

  mode = ReadMode.QLOG if args.qlog else ReadMode.RLOG
  try:
    lr = LogReader(source, default_mode=mode)
  except Exception as exc:
    print(f"failed to open source: {exc}")
    return 2

  fw = None
  vin = None
  msgs: dict[int, int] = {}
  for msg in lr:
    which = msg.which()
    if which == "carParams":
      fw = msg.carParams.carFw
      vin = msg.carParams.carVin
    elif which == "can":
      for c in msg.can:
        if c.src % 0x80 == 0 and c.address < 0x800 and c.address not in (0x7DF, 0x7E0, 0x7E8):
          msgs[c.address] = len(c.dat)

  label = args.car_model or getattr(getattr(lr.first("carParams"), "carParams", None), "carFingerprint", None) or "UNKNOWN"
  print(f"platform={label}")
  print(f"can_messages={len(msgs)}")
  print(", ".join(f"{addr:#x}: {size}" for addr, size in sorted(msgs.items())))
  if fw:
    print("fw_versions=")
    for item in fw:
      sub = None if item.subAddress == 0 else item.subAddress
      print(f"  - ({item.ecu}, {hex(item.address)}, {sub}) -> {item.fwVersion}")
  print(f"vin={vin}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
