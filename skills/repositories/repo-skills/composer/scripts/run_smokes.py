#!/usr/bin/env python3
"""Run Composer skill bundled smoke scripts with the current Python."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SMOKES = {
    "training": [
        ("sub-skills/training", ["scripts/train_smoke.py", "--batches", "2", "--eval-batches", "1", "--predict"]),
        ("sub-skills/training", ["scripts/checkpoint_smoke.py", "--mode", "both"]),
    ],
    "methods": [
        ("sub-skills/methods", ["scripts/functional_smoke.py"]),
    ],
    "observability": [
        ("sub-skills/observability", ["scripts/logger_smoke.py"]),
        ("sub-skills/observability", ["scripts/profiler_smoke.py"]),
    ],
    "distributed": [
        ("sub-skills/distributed", ["scripts/device_probe.py"]),
        ("sub-skills/distributed", ["scripts/launcher_help.py"]),
    ],
    "inference-export": [
        ("sub-skills/inference-export", ["scripts/export_torchscript_smoke.py"]),
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run selected smoke scripts bundled with the Composer skill.")
    parser.add_argument(
        "--only",
        action="append",
        choices=sorted(SMOKES),
        help="Run only a sub-skill smoke group. May be repeated. Defaults to all groups.",
    )
    parser.add_argument("--timeout", type=float, default=120.0, help="Timeout per smoke command in seconds.")
    parser.add_argument("--json", action="store_true", help="Print only JSON summary.")
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parents[1]
    selected = args.only or list(SMOKES)
    results = []
    ok = True

    for group in selected:
        for cwd_rel, cmd in SMOKES[group]:
            cwd = skill_root / cwd_rel
            full_cmd = [sys.executable, *cmd]
            try:
                proc = subprocess.run(
                    full_cmd,
                    cwd=str(cwd),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=args.timeout,
                    check=False,
                )
                status = "PASS" if proc.returncode == 0 else "FAIL"
                ok = ok and proc.returncode == 0
                results.append({
                    "group": group,
                    "cwd": cwd_rel,
                    "command": full_cmd,
                    "status": status,
                    "returncode": proc.returncode,
                    "stdout_tail": proc.stdout[-1200:],
                    "stderr_tail": proc.stderr[-1200:],
                })
            except subprocess.TimeoutExpired as exc:
                ok = False
                results.append({
                    "group": group,
                    "cwd": cwd_rel,
                    "command": full_cmd,
                    "status": "TIMEOUT",
                    "timeout": args.timeout,
                    "stdout_tail": (exc.stdout or "")[-1200:] if isinstance(exc.stdout, str) else "",
                    "stderr_tail": (exc.stderr or "")[-1200:] if isinstance(exc.stderr, str) else "",
                })

    summary = {"ok": ok, "python": sys.executable, "results": results}
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        for item in results:
            print(f"[{item['status']}] {item['group']} :: {' '.join(item['command'])}")
            if item.get("stdout_tail"):
                print(item["stdout_tail"].rstrip())
            if item.get("stderr_tail"):
                print(item["stderr_tail"].rstrip(), file=sys.stderr)
        print(json.dumps({"ok": ok, "count": len(results)}, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
