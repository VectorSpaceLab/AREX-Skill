#!/usr/bin/env python3
"""Create a tiny Open3D-ML visualization fixture.

The script does not open a GUI or download demo data. It only writes a small
point-cloud/labels/predictions/bounding-box fixture that future agents can use
for smoke tests or examples.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_fixture(points: int = 8):
    pts = [[float(i), float(i % 3), float((i * 2) % 5)] for i in range(points)]
    labels = [i % 4 for i in range(points)]
    preds = [(i + 1) % 4 for i in range(points)]
    bboxes = [
        {
            "center": [1.0, 1.0, 1.0],
            "front": [1.0, 0.0, 0.0],
            "up": [0.0, 1.0, 0.0],
            "left": [0.0, 0.0, 1.0],
            "size": [1.5, 1.0, 2.0],
            "label_class": 1,
            "confidence": 0.99,
            "meta": "fixture-box",
        }
    ]
    return {"name": "fixture_cloud", "points": pts, "labels": labels, "pred": preds, "bounding_boxes": bboxes}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Write a tiny visualization fixture.")
    parser.add_argument("--out", required=True, help="Output path without extension or with .npz/.json.")
    parser.add_argument("--points", type=int, default=8, help="Number of synthetic points to generate.")
    parser.add_argument("--format", choices=["npz", "json"], default="npz", help="Fixture format to write.")
    args = parser.parse_args(argv)

    fixture = build_fixture(args.points)
    out = Path(args.out)
    if out.suffix != f".{args.format}":
        out = out.with_suffix(f".{args.format}")
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "json":
        out.write_text(json.dumps(fixture, indent=2, sort_keys=True))
    else:
        try:
            import numpy as np
        except Exception as exc:
            raise SystemExit(f"NumPy is required for npz output: {type(exc).__name__}: {exc}")
        np.savez(
            out,
            name=fixture["name"],
            points=np.asarray(fixture["points"], dtype="float32"),
            labels=np.asarray(fixture["labels"], dtype="int32"),
            pred=np.asarray(fixture["pred"], dtype="int32"),
            bounding_boxes=json.dumps(fixture["bounding_boxes"]),
        )
    print(json.dumps({"written": str(out), "format": args.format, "points": args.points}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
