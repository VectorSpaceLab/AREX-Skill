#!/usr/bin/env python3
"""Print openpilot service frequencies and logging flags."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main() -> int:
  parser = argparse.ArgumentParser(description="Inspect SERVICE_LIST entries from an openpilot checkout")
  parser.add_argument("--filter", help="substring filter for service names")
  parser.add_argument("--repo-root", help="target openpilot checkout to add to sys.path when openpilot is not installed")
  args = parser.parse_args()

  if args.repo_root:
    root = Path(args.repo_root).resolve()
    sys.path.insert(0, str(root))
    for sub in ("msgq_repo", "opendbc_repo", "rednose_repo", "teleoprtc_repo", "tinygrad_repo"):
      sys.path.insert(0, str(root / sub))

  try:
    from openpilot.cereal.services import SERVICE_LIST
  except Exception as exc:
    parser.error(f"openpilot services are not importable: {exc}")

  rows = []
  for name, svc in SERVICE_LIST.items():
    if args.filter and args.filter.lower() not in name.lower():
      continue
    rows.append((name, getattr(svc, "frequency", None), getattr(svc, "decimation", None), getattr(svc, "should_log", None)))
  for name, freq, dec, should_log in sorted(rows):
    print(f"{name:30} freq={freq!s:>6} decimation={dec!s:>4} should_log={should_log}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
