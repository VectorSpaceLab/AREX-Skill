#!/usr/bin/env python3
"""Dry-run-first launcher for SiamMask checkout-local data-preparation scripts.

The original preprocessing scripts download or process very large datasets. This
bundled helper centralizes the working directory, PYTHONPATH, and command
composition so future agents do not have to navigate the source tree. It prints
commands by default; add --run only after reviewing network, disk, and runtime
side effects.
"""
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path

ENTRYPOINTS = {
    "vot-json-native": ("data", "data/create_json.py", "Create VOT metadata JSON from an existing local VOT directory."),
    "coco-crop": ("data/coco", "data/coco/par_crop.py", "Crop COCO images/masks into crop511-style training data; CPU-heavy."),
    "coco-json": ("data/coco", "data/coco/gen_json.py", "Generate COCO training JSON indexes after crop preparation."),
    "det-crop": ("data/det", "data/det/par_crop.py", "Crop ImageNet DET images; CPU-heavy and large-data dependent."),
    "det-json": ("data/det", "data/det/gen_json.py", "Generate DET training JSON index."),
    "vid-parse": ("data/vid", "data/vid/parse_vid.py", "Parse ImageNet VID annotations into raw vid.json."),
    "vid-crop": ("data/vid", "data/vid/par_crop.py", "Crop ImageNet VID frames; CPU-heavy and large-data dependent."),
    "vid-json": ("data/vid", "data/vid/gen_json.py", "Generate VID train/val JSON indexes from vid.json."),
    "ytb-parse": ("data/ytb_vos", "data/ytb_vos/parse_ytb_vos.py", "Parse YouTube-VOS annotations into instances_train/val JSON files."),
    "ytb-crop": ("data/ytb_vos", "data/ytb_vos/par_crop.py", "Crop YouTube-VOS frames and masks; CPU-heavy and large-data dependent."),
    "ytb-json": ("data/ytb_vos", "data/ytb_vos/gen_json.py", "Generate YouTube-VOS train.json from parsed instance annotations."),
}

HEAVY = {"coco-crop", "det-crop", "vid-crop", "ytb-crop", "ytb-parse", "vid-parse"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compose or run SiamMask data-preparation commands against a checkout.")
    p.add_argument("--repo-root", default=".", help="Path to a SiamMask checkout. Defaults to current directory.")
    p.add_argument("--python", default=sys.executable, help="Python executable to use for checkout-local scripts.")
    p.add_argument("--run", action="store_true", help="Execute the command. Omit for safe dry-run command printing.")
    p.add_argument("--list", action="store_true", help="List known entry points and exit.")
    p.add_argument("entry", nargs="?", choices=sorted(ENTRYPOINTS), help="Data-preparation entry point to compose/run.")
    p.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed after -- to the selected checkout-local script.")
    return p.parse_args()


def list_entries() -> None:
    for name, (_, _, desc) in sorted(ENTRYPOINTS.items()):
        mark = "heavy" if name in HEAVY else "local"
        print(f"{name:16s} [{mark}] {desc}")


def main() -> int:
    args = parse_args()
    if args.list:
        list_entries()
        return 0
    if not args.entry:
        raise SystemExit("choose an entry point or pass --list")
    root = Path(args.repo_root).expanduser().resolve()
    if not (root / "data").exists():
        raise SystemExit(f"repo root does not look like SiamMask: {root}")
    work_rel, script_rel, desc = ENTRYPOINTS[args.entry]
    cwd = root / work_rel
    script = root / script_rel
    if not script.exists():
        raise SystemExit(f"missing checkout-local script: {script}")
    passthrough = list(args.args)
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]
    cmd = [args.python, str(script)] + passthrough
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root) + os.pathsep + str(cwd) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    print("entry:", args.entry)
    print("description:", desc)
    print("cwd:", cwd)
    print("cmd:", shlex.join(cmd))
    print("PYTHONPATH prepends:", os.pathsep.join([str(root), str(cwd)]))
    if args.entry in HEAVY:
        print("warning: this entry point can process large datasets and may run for minutes to hours")
    if not args.run:
        print("dry-run: add --run before the entry name to execute")
        return 0
    return subprocess.call(cmd, cwd=str(cwd), env=env)


if __name__ == "__main__":
    raise SystemExit(main())
