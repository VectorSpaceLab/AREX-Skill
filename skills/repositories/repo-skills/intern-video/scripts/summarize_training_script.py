#!/usr/bin/env python3
"""Summarize an InternVideo-style shell launcher without executing it."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ASSIGN_RE = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
PLACEHOLDER_RE = re.compile(r"your_[A-Za-z0-9_]+|train_1\.1M\.csv|/path/to/[^\s'\"]+")


def summarize(text: str) -> dict:
    env = {}
    for line in text.splitlines():
        stripped = line.strip()
        m = ASSIGN_RE.match(stripped)
        if m:
            env[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    python_entries = re.findall(r"(?:python(?:\s+-u)?|tasks/[A-Za-z0-9_./-]+\.py)\s+([^\\\n]*)", text)
    return {
        "variables": env,
        "resource_hints": {
            "partition": env.get("PARTITION"),
            "gpus": env.get("GPUS") or env.get("NUM_GPUS"),
            "gpus_per_node": env.get("GPUS_PER_NODE") or env.get("NUM_GPUS"),
            "nodes": env.get("NNODE") or env.get("NNODES"),
            "cpus_per_task": env.get("CPUS_PER_TASK") or env.get("NUM_CPU"),
        },
        "uses_srun": "srun" in text,
        "uses_torchrun": "torchrun" in text or "torchrun.sh" in text,
        "uses_deepspeed": "deepspeed" in text.lower() or "--enable_deepspeed" in text,
        "python_entry_fragments": python_entries,
        "placeholders": sorted(set(PLACEHOLDER_RE.findall(text))),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize a local InternVideo shell launcher without running it.")
    parser.add_argument("--script", required=True, help="Path to a shell script supplied by the user/current checkout.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()
    path = Path(args.script)
    text = path.read_text(encoding="utf-8", errors="replace")
    report = summarize(text)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Variables:")
        for key, value in sorted(report["variables"].items()):
            print(f"  {key}={value}")
        print("Resource hints:", report["resource_hints"])
        print("Uses srun:", report["uses_srun"])
        print("Uses torchrun:", report["uses_torchrun"])
        print("Uses DeepSpeed:", report["uses_deepspeed"])
        if report["placeholders"]:
            print("Placeholders needing replacement:", ", ".join(report["placeholders"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
