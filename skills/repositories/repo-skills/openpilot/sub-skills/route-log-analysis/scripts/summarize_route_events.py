#!/usr/bin/env python3
"""Summarize events, alerts, cameras, and duration from openpilot logs."""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import json
import math
from pathlib import Path
import sys


def main() -> int:
  parser = argparse.ArgumentParser(description="Summarize an openpilot route/log using LogReader")
  parser.add_argument("route_or_log", help="route/segment/range, URL, or local log file")
  parser.add_argument("--qlog", action="store_true", help="prefer qlog mode for route identifiers")
  parser.add_argument("--limit", type=int, default=0, help="maximum messages to inspect; 0 means all")
  parser.add_argument("--repo-root", help="target openpilot checkout to add to sys.path when openpilot is not installed")
  args = parser.parse_args()

  if args.repo_root:
    root = Path(args.repo_root).resolve()
    sys.path.insert(0, str(root))
    for sub in ("msgq_repo", "opendbc_repo", "rednose_repo", "teleoprtc_repo", "tinygrad_repo"):
      sys.path.insert(0, str(root / sub))

  try:
    from openpilot.cereal.services import SERVICE_LIST
    from openpilot.tools.lib.logreader import LogReader, ReadMode
    from openpilot.selfdrive.test.process_replay.migration import migrate_all
  except Exception as exc:
    parser.error(f"openpilot log APIs are not importable: {exc}")

  mode = ReadMode.QLOG if args.qlog else ReadMode.AUTO
  counters: Counter[str] = Counter()
  events: Counter[str] = Counter()
  alerts: list[tuple[float, str]] = []
  cameras = {s: 0 for s in SERVICE_LIST if s.endswith("CameraState")}
  start = math.inf
  end = -math.inf

  try:
    iterator = migrate_all(LogReader(args.route_or_log, default_mode=mode, only_union_types=True))
    for idx, msg in enumerate(iterator):
      if args.limit and idx >= args.limit:
        break
      which = msg.which()
      counters[which] += 1
      start = min(start, msg.logMonoTime)
      end = max(end, msg.logMonoTime)
      t = 0.0 if start == math.inf else (msg.logMonoTime - start) / 1e9
      if which == "onroadEvents":
        for event in msg.onroadEvents:
          events[str(event.name)] += 1
      elif which == "selfdriveState":
        at = msg.selfdriveState.alertType
        if at and (not alerts or alerts[-1][1] != at):
          alerts.append((t, at))
      elif which in cameras:
        cameras[which] += 1
  except Exception as exc:
    print(f"failed to read logs: {exc}")
    return 2

  duration = 0 if end < start else (end - start) / 1e9
  output = {
    "duration": str(dt.timedelta(seconds=round(duration, 2))),
    "message_counts_top": counters.most_common(30),
    "events": events.most_common(),
    "alerts": alerts[:50],
    "camera_counts": {k: v for k, v in cameras.items() if v},
  }
  print(json.dumps(output, indent=2))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
