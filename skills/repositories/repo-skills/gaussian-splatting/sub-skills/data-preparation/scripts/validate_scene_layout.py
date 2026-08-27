#!/usr/bin/env python3
"""Validate gaussian-splatting scene and model directory layouts.

This is a safe structural checker: it does not run COLMAP, training, rendering,
or metrics. Use it before building train.py/render.py commands.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def emit(level: str, msg: str) -> None:
    print(f"[{level}] {msg}")


def has_images(folder: Path) -> bool:
    return folder.is_dir() and any(p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES for p in folder.iterdir())


def validate_colmap(root: Path, images: str, depths: str | None) -> bool:
    ok = True
    sparse0 = root / "sparse" / "0"
    if not sparse0.is_dir():
        emit("FAIL", "COLMAP scene missing sparse/0 directory")
        ok = False
    else:
        cams = (sparse0 / "cameras.bin").is_file() or (sparse0 / "cameras.txt").is_file()
        imgs = (sparse0 / "images.bin").is_file() or (sparse0 / "images.txt").is_file()
        pts = (sparse0 / "points3D.bin").is_file() or (sparse0 / "points3D.txt").is_file() or (sparse0 / "points3D.ply").is_file()
        for label, present in [("cameras", cams), ("images", imgs), ("points3D", pts)]:
            emit("PASS" if present else "FAIL", f"COLMAP {label} file present")
            ok = ok and present
    image_dir = root / images
    if has_images(image_dir):
        emit("PASS", f"image directory contains images: {images}")
    else:
        emit("FAIL", f"image directory missing or empty: {images}")
        ok = False
    if depths:
        depth_dir = root / depths
        if depth_dir.is_dir():
            emit("PASS", f"depth directory exists: {depths}")
        else:
            emit("FAIL", f"depth directory missing: {depths}")
            ok = False
        if (sparse0 / "depth_params.json").is_file():
            emit("PASS", "depth_params.json exists under sparse/0")
        else:
            emit("FAIL", "depth regularization needs sparse/0/depth_params.json for real COLMAP scenes")
            ok = False
    return ok


def validate_blender(root: Path, depths: str | None) -> bool:
    ok = True
    for name in ["transforms_train.json", "transforms_test.json"]:
        path = root / name
        if not path.is_file():
            emit("FAIL", f"missing {name}")
            ok = False
            continue
        try:
            data = json.loads(path.read_text())
            frames = data.get("frames", [])
            emit("PASS", f"{name} has {len(frames)} frame(s)")
            if "camera_angle_x" not in data:
                emit("FAIL", f"{name} missing camera_angle_x")
                ok = False
        except Exception as exc:
            emit("FAIL", f"could not parse {name}: {exc}")
            ok = False
    if depths and not (root / depths).is_dir():
        emit("FAIL", f"depth directory missing: {depths}")
        ok = False
    return ok


def validate_model(root: Path) -> bool:
    ok = True
    if (root / "cfg_args").is_file():
        emit("PASS", "cfg_args present")
    else:
        emit("WARN", "cfg_args missing; render.py will need explicit source/model options")
    point_cloud = root / "point_cloud"
    iterations = sorted(point_cloud.glob("iteration_*/point_cloud.ply")) if point_cloud.is_dir() else []
    if iterations:
        emit("PASS", f"found {len(iterations)} point_cloud iteration(s); latest={iterations[-1].parent.name}")
    else:
        emit("FAIL", "missing point_cloud/iteration_*/point_cloud.ply")
        ok = False
    if (root / "cameras.json").is_file():
        emit("PASS", "cameras.json present")
    else:
        emit("WARN", "cameras.json missing; model may be incomplete or from an older run")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate gaussian-splatting scene/model layouts")
    parser.add_argument("--scene-root", type=Path, help="Scene directory to validate as COLMAP or Blender/NeRF synthetic.")
    parser.add_argument("--model-root", type=Path, help="Trained model directory to validate.")
    parser.add_argument("--images", default="images", help="Image subdirectory used for COLMAP scenes (default: images).")
    parser.add_argument("--depths", default="", help="Optional depth-map subdirectory used with train.py -d/--depths.")
    args = parser.parse_args()

    if not args.scene_root and not args.model_root:
        parser.error("provide --scene-root, --model-root, or both")

    ok = True
    if args.scene_root:
        scene = args.scene_root.resolve()
        if not scene.is_dir():
            emit("FAIL", f"scene root does not exist: {scene}")
            ok = False
        elif (scene / "sparse").exists():
            emit("INFO", "detected COLMAP-style scene")
            ok = validate_colmap(scene, args.images, args.depths or None) and ok
        elif (scene / "transforms_train.json").exists():
            emit("INFO", "detected Blender/NeRF synthetic scene")
            ok = validate_blender(scene, args.depths or None) and ok
        else:
            emit("FAIL", "unrecognized scene: expected sparse/ or transforms_train.json")
            ok = False
    if args.model_root:
        model = args.model_root.resolve()
        if not model.is_dir():
            emit("FAIL", f"model root does not exist: {model}")
            ok = False
        else:
            ok = validate_model(model) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
