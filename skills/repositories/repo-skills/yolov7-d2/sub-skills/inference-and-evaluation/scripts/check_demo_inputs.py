#!/usr/bin/env python3
"""Preflight YOLOv7-d2 demo inputs without importing Detectron2 or running inference."""
import argparse
from pathlib import Path


def is_probably_url(value: str) -> bool:
    return value.startswith(("http://", "https://", "detectron2://"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check demo config/input/weight/output paths.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--weights", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    errors = []
    if not Path(args.config).is_file():
        errors.append(f"config file not found: {args.config}")
    inp = Path(args.input)
    if not (inp.exists() or any(Path().glob(args.input))):
        errors.append(f"input path/glob matched nothing: {args.input}")
    if not is_probably_url(args.weights) and not Path(args.weights).is_file():
        errors.append(f"weights file not found: {args.weights}")
    if args.output:
        out = Path(args.output)
        parent = out if out.suffix == "" else out.parent
        if parent and not parent.exists():
            print(f"output parent does not exist yet: {parent}")
    else:
        print("warning: no output path; OpenCV display may fail in headless sessions")

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        raise SystemExit(1)
    print("demo inputs look usable for a launch preflight")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
