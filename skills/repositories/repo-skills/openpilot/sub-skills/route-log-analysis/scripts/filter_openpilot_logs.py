#!/usr/bin/env python3
"""Filter openpilot logMessage/errorLogMessage/operatingSystemLog records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
OS_LOG_SOURCE = {0: "MAIN", 1: "RADIO", 2: "EVENTS", 3: "SYSTEM", 4: "CRASH", 5: "KERNEL"}


def print_log(t: float, payload: str, min_level: int) -> None:
  try:
    item = json.loads(payload)
    if int(item.get("levelnum", 0)) >= min_level:
      loc = f"{item.get('filename', '?')}:{item.get('lineno', '')}".rstrip(":")
      print(f"[{t:.6f}] {loc} {item.get('funcname', '')}: {item.get('msg', payload)}")
      if item.get("exc_info"):
        print(item["exc_info"])
  except Exception:
    if min_level <= LEVELS["DEBUG"]:
      print(f"[{t:.6f}] decode-error: {payload}")


def print_os(t: float, msg) -> None:
  source = msg.tag or OS_LOG_SOURCE.get(msg.id, "SYSTEM")
  try:
    text = json.loads(msg.message)["MESSAGE"]
  except Exception:
    text = msg.message
  print(f"[{t:.6f}] {source} {msg.pid} {msg.tag} - {text}")


def main() -> int:
  parser = argparse.ArgumentParser(description="Filter openpilot route log messages")
  parser.add_argument("route", nargs="+", help="route/segment/range, URL, or local log file")
  parser.add_argument("--level", choices=sorted(LEVELS), default="DEBUG")
  parser.add_argument("--absolute", action="store_true", help="print absolute monotonic seconds instead of route-relative")
  parser.add_argument("--repo-root", help="target openpilot checkout to add to sys.path when openpilot is not installed")
  args = parser.parse_args()

  if args.repo_root:
    root = Path(args.repo_root).resolve()
    sys.path.insert(0, str(root))
    for sub in ("msgq_repo", "opendbc_repo", "rednose_repo", "teleoprtc_repo", "tinygrad_repo"):
      sys.path.insert(0, str(root / sub))

  try:
    from openpilot.tools.lib.logreader import LogReader
  except Exception as exc:
    parser.error(f"openpilot LogReader is not importable: {exc}")

  min_level = LEVELS[args.level]
  start = None if not args.absolute else 0
  for route in args.route:
    try:
      for msg in LogReader(route, sort_by_time=True, only_union_types=True):
        if start is None:
          start = msg.logMonoTime
        t = (msg.logMonoTime - (start or 0)) / 1e9
        which = msg.which()
        if which == "logMessage":
          print_log(t, msg.logMessage, min_level)
        elif which == "errorLogMessage":
          print_log(t, msg.errorLogMessage, min_level)
        elif which == "operatingSystemLog":
          print_os(t, msg.operatingSystemLog)
    except Exception as exc:
      print(f"failed to read {route}: {exc}")
      return 2
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
