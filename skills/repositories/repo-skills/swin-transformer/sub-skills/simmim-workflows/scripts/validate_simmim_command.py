#!/usr/bin/env python3
"""Validate SimMIM command shape without running training."""
from __future__ import annotations

import argparse
import shlex
import sys


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate a SimMIM command shape.")
    ap.add_argument("command", nargs=argparse.REMAINDER, help="Use -- before the command to validate.")
    args = ap.parse_args()
    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if len(cmd) == 1:
        cmd = shlex.split(cmd[0])
    script = next((x for x in cmd if x.endswith(("main_simmim_pt.py", "main_simmim_ft.py"))), None)
    if not script:
        print("ERROR: command must target main_simmim_pt.py or main_simmim_ft.py", file=sys.stderr)
        return 1
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("script")
    p.add_argument("--cfg")
    p.add_argument("--data-path")
    p.add_argument("--pretrained")
    p.add_argument("--resume")
    p.add_argument("--eval", action="store_true")
    p.add_argument("--batch-size")
    p.add_argument("--enable-amp", action="store_true")
    p.add_argument("--disable-amp", action="store_true")
    # Keep tokens from the selected script onward.
    argv = cmd[cmd.index(script):]
    ns, unknown = p.parse_known_args(argv)
    errors = []
    warnings = []
    if not ns.cfg:
        errors.append("missing --cfg")
    if not ns.data_path:
        errors.append("missing --data-path")
    if script.endswith("main_simmim_pt.py") and (ns.pretrained or ns.eval):
        warnings.append("pretraining script does not use --pretrained/--eval in normal workflows")
    if script.endswith("main_simmim_ft.py") and not (ns.pretrained or ns.resume):
        warnings.append("fine-tune/eval usually needs --pretrained or --resume")
    if ns.eval and not ns.resume:
        warnings.append("evaluation usually uses --resume <fine-tuned-checkpoint>")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    for w in warnings:
        print(f"WARNING: {w}")
    if unknown:
        print("INFO: unparsed flags:", " ".join(unknown))
    if not errors:
        print("SimMIM command shape looks plausible; this did not run training")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
