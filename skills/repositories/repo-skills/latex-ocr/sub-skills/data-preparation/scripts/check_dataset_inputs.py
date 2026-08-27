#!/usr/bin/env python3
"""Validate pix2tex dataset-builder inputs without creating a pickle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median

from PIL import Image


def main() -> int:
    parser = argparse.ArgumentParser(description="Check pix2tex image/equation dataset inputs")
    parser.add_argument("--equations", "-e", required=True, type=Path, help="formula text file, one formula per line")
    parser.add_argument("--images", "-i", required=True, type=Path, help="directory of integer-named PNG files")
    parser.add_argument("--sample", type=int, default=10, help="number of images to open for size checks")
    args = parser.parse_args()

    equations = args.equations.read_text(encoding="utf-8", errors="replace").splitlines()
    pngs = sorted(args.images.glob("*.png"))
    report = {"equation_lines": len(equations), "png_files": len(pngs), "errors": [], "warnings": [], "sample_sizes": []}
    indices: list[int] = []
    for p in pngs:
        try:
            idx = int(p.stem)
            indices.append(idx)
        except ValueError:
            report["errors"].append(f"non-integer PNG basename: {p.name}")
    if indices:
        report["min_index"] = min(indices)
        report["max_index"] = max(indices)
        missing = [idx for idx in indices if idx < 0 or idx >= len(equations)]
        if missing:
            report["errors"].append(f"{len(missing)} PNG indices are outside equation line range; first={missing[:5]}")
    blank = sum(1 for line in equations if not line.strip())
    if blank:
        report["warnings"].append(f"{blank} blank equation lines")
    for p in pngs[: max(args.sample, 0)]:
        try:
            with Image.open(p) as img:
                report["sample_sizes"].append({"file": p.name, "size": list(img.size), "mode": img.mode})
        except Exception as exc:  # noqa: BLE001
            report["errors"].append(f"cannot open {p.name}: {type(exc).__name__}: {exc}")
    if report["sample_sizes"]:
        widths = [item["size"][0] for item in report["sample_sizes"]]
        heights = [item["size"][1] for item in report["sample_sizes"]]
        report["sample_median_size"] = [median(widths), median(heights)]
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
