#!/usr/bin/env python3
"""Run a SimpleDet entry point through an explicit checkout root.

This helper has no install, network, cleanup, or kill behavior. The selected
entry point may train, allocate GPUs, read data, or write experiments.
"""
from __future__ import annotations
import argparse
import os
import subprocess
import sys

ENTRYPOINTS = {"train":"detection_train.py", "test":"detection_test.py", "mask-test":"mask_test.py", "speed":"detection_infer_speed.py"}

def main():
    parser = argparse.ArgumentParser(description="Run a SimpleDet workflow from an explicit checkout root")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--entrypoint", choices=sorted(ENTRYPOINTS), required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--epoch", type=int, default=None)
    parser.add_argument("--shape", nargs=2, type=int, metavar=("SHORT", "LONG"))
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = os.path.abspath(os.path.expanduser(args.repo_root))
    script = os.path.join(root, ENTRYPOINTS[args.entrypoint])
    if not os.path.isfile(script):
        parser.error("entry point missing under --repo-root: %s" % script)
    command = [sys.executable, script, "--config", args.config]
    if args.entrypoint in {"test", "mask-test"} and args.epoch is not None:
        command += ["--epoch", str(args.epoch)]
    if args.entrypoint == "speed":
        if args.shape is None:
            parser.error("--shape SHORT LONG is required for speed")
        command += ["--shape", str(args.shape[0]), str(args.shape[1]), "--gpu", str(args.gpu), "--count", str(args.count)]
    print("command:", " ".join(command))
    print("cwd:", root)
    if args.dry_run:
        return 0
    return subprocess.call(command, cwd=root)

if __name__ == "__main__":
    raise SystemExit(main())
