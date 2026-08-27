#!/usr/bin/env python3
"""Validate gaussian-splatting model and render-output directory layouts.

This helper is safe: it checks for expected files and folders but does not run
render.py, metrics.py, LPIPS, or full evaluation.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def note(level: str, msg: str) -> None:
    print(f"[{level}] {msg}")


def validate_model(model: Path) -> bool:
    ok = True
    required = ["cfg_args", "cameras.json", "input.ply"]
    for rel in required:
        present = (model / rel).is_file()
        note("PASS" if present else "FAIL", f"{rel} present")
        ok = ok and present
    point_cloud = model / "point_cloud"
    if point_cloud.is_dir():
        iterations = sorted(point_cloud.glob("iteration_*/point_cloud.ply"))
        if iterations:
            note("PASS", f"found {len(iterations)} point_cloud iteration(s); latest={iterations[-1].parent.name}")
        else:
            note("FAIL", "point_cloud exists but contains no iteration_*/point_cloud.ply")
            ok = False
    else:
        note("FAIL", "missing point_cloud directory")
        ok = False
    return ok


def validate_render_root(model: Path, iteration: int, splits: list[str]) -> bool:
    ok = True
    for split in splits:
        for leaf in ["renders", "gt"]:
            path = model / split / f"ours_{iteration}" / leaf
            if path.is_dir():
                pngs = list(path.glob("*.png"))
                note("PASS", f"{path.relative_to(model)} with {len(pngs)} PNG(s)")
            else:
                note("FAIL", f"missing {path.relative_to(model)}")
                ok = False
    return ok


def validate_metrics(model: Path) -> bool:
    ok = True
    for rel in ["results.json", "per_view.json"]:
        present = (model / rel).is_file()
        note("PASS" if present else "FAIL", f"{rel} present")
        ok = ok and present
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate gaussian-splatting model/render output layouts")
    parser.add_argument("--model-root", type=Path, required=True, help="Trained model directory to inspect.")
    parser.add_argument("--iteration", type=int, help="Rendered iteration number to check under train/test/ours_<N>/.")
    parser.add_argument("--skip-train", action="store_true", help="Do not require train/ours_<N> render folders.")
    parser.add_argument("--skip-test", action="store_true", help="Do not require test/ours_<N> render folders.")
    parser.add_argument("--check-metrics", action="store_true", help="Also require results.json and per_view.json.")
    args = parser.parse_args()

    model = args.model_root.resolve()
    if not model.is_dir():
        note("FAIL", f"model root does not exist: {model}")
        return 2

    ok = validate_model(model)
    if args.iteration is not None:
        splits = []
        if not args.skip_train:
            splits.append("train")
        if not args.skip_test:
            splits.append("test")
        if not splits:
            note("WARN", "both --skip-train and --skip-test were set; no render folders checked")
        else:
            ok = validate_render_root(model, args.iteration, splits) and ok
    if args.check_metrics:
        ok = validate_metrics(model) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
