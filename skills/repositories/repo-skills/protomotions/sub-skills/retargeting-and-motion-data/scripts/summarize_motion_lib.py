#!/usr/bin/env python3
"""Summarize a packaged ProtoMotions MotionLib .pt file without simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import torch


def describe_value(value: Any) -> Any:
    if torch.is_tensor(value):
        return {"type": "tensor", "dtype": str(value.dtype), "shape": list(value.shape)}
    if isinstance(value, (list, tuple)):
        return {"type": type(value).__name__, "length": len(value), "sample": list(value[:3])}
    return {"type": type(value).__name__, "repr": repr(value)[:200]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("motion_lib", help="Packaged MotionLib .pt file")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = Path(args.motion_lib)
    data = torch.load(path, map_location="cpu", weights_only=False)
    summary = {"path": str(path), "fields": {key: describe_value(value) for key, value in sorted(data.items())}}
    if "motion_num_frames" in data:
        frames = data["motion_num_frames"]
        summary["num_motions"] = int(len(frames))
        summary["total_frames"] = int(frames.sum().item()) if torch.is_tensor(frames) else None
    if "contacts" in data and torch.is_tensor(data["contacts"]):
        contacts = data["contacts"]
        summary["contacts_any"] = bool(contacts.any().item())
        summary["contacts_dtype"] = str(contacts.dtype)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
