#!/usr/bin/env python3
"""Generate YOLOP drivable-area mask PNGs from BDD-style polygon JSON labels.

This is an argument-driven adaptation of YOLOP's gen_bdd_seglabel.py. It does
not assume hard-coded bdd/ paths and is safe to test with a tiny fixture.

Example:
  python generate_drivable_masks.py --labels-dir /data/bdd100k/labels/100k/train \
    --output-dir /data/bdd_seg_gt/train --limit 10
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402
from tqdm import tqdm  # noqa: E402


def poly2patch(poly2d: list[list[object]], closed: bool = False, alpha: float = 1.0, color=None):
    moves = {"L": MplPath.LINETO, "C": MplPath.CURVE4}
    points = [p[:2] for p in poly2d]
    codes = [moves.get(str(p[2]), MplPath.LINETO) for p in poly2d]
    if not points:
        raise ValueError("empty poly2d")
    codes[0] = MplPath.MOVETO
    if closed:
        points.append(points[0])
        codes.append(MplPath.CLOSEPOLY)
    return mpatches.PathPatch(
        MplPath(points, codes),
        facecolor=color if closed else "none",
        edgecolor=color,
        lw=1 if closed else 2,
        alpha=alpha,
        antialiased=False,
        snap=True,
    )


def _area_objects(objects: Iterable[dict]) -> list[dict]:
    return [obj for obj in objects if "poly2d" in obj and str(obj.get("category", "")).startswith("area")]


def render_mask(label: dict, output_path: Path, image_width: int, image_height: int, dpi: int, skip_empty: bool) -> bool:
    objects = label.get("frames", [{}])[0].get("objects", [])
    areas = _area_objects(objects)
    has_drivable = any(obj.get("category") == "area/drivable" for obj in areas)
    if skip_empty and not has_drivable:
        return False

    fig = plt.figure(figsize=(image_width / dpi, image_height / dpi), dpi=dpi)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], frameon=False)
    ax.set_xlim(0, image_width - 1)
    ax.set_ylim(0, image_height - 1)
    ax.invert_yaxis()
    ax.axis("off")
    ax.add_patch(
        poly2patch(
            [[0, 0, "L"], [0, image_height - 1, "L"], [image_width - 1, image_height - 1, "L"], [image_width - 1, 0, "L"]],
            closed=True,
            alpha=1.0,
            color=(0, 0, 0),
        )
    )
    for obj in areas:
        if obj.get("category") == "area/drivable":
            color = (1, 1, 1)
        else:
            color = (0, 0, 0)
        ax.add_patch(poly2patch(obj["poly2d"], closed=True, alpha=1.0, color=color))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate drivable-area PNG masks from BDD-style label JSONs")
    parser.add_argument("--labels-dir", required=True, help="Directory containing BDD JSON label files for one split")
    parser.add_argument("--output-dir", required=True, help="Directory where PNG masks should be written")
    parser.add_argument("--image-width", type=int, default=1280, help="Annotation coordinate width")
    parser.add_argument("--image-height", type=int, default=720, help="Annotation coordinate height")
    parser.add_argument("--dpi", type=int, default=80, help="Matplotlib DPI; width/dpi and height/dpi define figure size")
    parser.add_argument("--limit", type=int, default=0, help="Only process the first N JSON files; 0 means all")
    parser.add_argument("--skip-empty", action="store_true", help="Do not write all-black masks for labels without area/drivable")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing PNG files")
    args = parser.parse_args()

    labels_dir = Path(args.labels_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    if not labels_dir.is_dir():
        print(f"ERROR: labels dir does not exist: {labels_dir}", file=sys.stderr)
        return 2
    files = sorted(labels_dir.glob("*.json"))
    if args.limit > 0:
        files = files[: args.limit]
    if not files:
        print(f"ERROR: no JSON files found in {labels_dir}", file=sys.stderr)
        return 3

    written = 0
    skipped = 0
    failed: list[str] = []
    for path in tqdm(files, desc="drivable masks"):
        try:
            label = json.loads(path.read_text())
            name = label.get("name") or path.stem
            output_path = output_dir / f"{name}.png"
            if output_path.exists() and not args.overwrite:
                skipped += 1
                continue
            if render_mask(label, output_path, args.image_width, args.image_height, args.dpi, args.skip_empty):
                written += 1
            else:
                skipped += 1
        except Exception as exc:  # pragma: no cover - diagnostic path
            failed.append(f"{path.name}: {exc}")

    print(f"written={written} skipped={skipped} failed={len(failed)} output_dir={output_dir}")
    if failed:
        for item in failed[:20]:
            print(f"ERROR: {item}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
