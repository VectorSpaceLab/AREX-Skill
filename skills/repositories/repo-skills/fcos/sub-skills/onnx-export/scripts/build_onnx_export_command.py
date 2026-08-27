#!/usr/bin/env python3
"""Build an FCOS ONNX export command without running export."""
from __future__ import annotations

import argparse
import shlex


def q(x: str) -> str:
    return shlex.quote(str(x))


def main() -> int:
    p = argparse.ArgumentParser(description="Print an FCOS ONNX export command")
    p.add_argument("--config-file", required=True)
    p.add_argument("--weights", help="MODEL.WEIGHT value")
    p.add_argument("--output", default="fcos.onnx")
    p.add_argument("--export-script", default="export_model_to_onnx.py", help="Path to a compatible FCOS ONNX export entry script")
    p.add_argument("--device", choices=["cpu", "cuda"], help="Optional MODEL.DEVICE override")
    p.add_argument("--override", nargs="*", default=[], help="Additional cfg merge_from_list tokens")
    args = p.parse_args()
    opts = list(args.override)
    if args.weights:
        opts += ["MODEL.WEIGHT", args.weights]
    if args.device:
        opts += ["MODEL.DEVICE", args.device]
    cmd = ["python", args.export_script, "--config-file", args.config_file, "--output", args.output] + opts
    print(" ".join(q(x) for x in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
