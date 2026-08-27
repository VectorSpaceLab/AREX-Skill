#!/usr/bin/env python3
"""Read-only preflight for the tensorrt_demos engine-build inputs.

This script never downloads, installs, compiles, creates links, patches files,
or writes a calibration cache/engine. It reports errors for malformed inputs and
warnings for optional or intentionally absent model artifacts.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


MODEL_NAMES = (
    "ssd_mobilenet_v1_coco",
    "ssd_mobilenet_v1_egohands",
    "ssd_mobilenet_v2_coco",
    "ssd_mobilenet_v2_egohands",
    "ssd_inception_v2_coco",
    "ssdlite_mobilenet_v2_coco",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only checks for TensorRT demo engine-build inputs."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="tensorrt_demos checkout (default: current directory)",
    )
    parser.add_argument(
        "--model",
        help="YOLO model stem or SSD model key to inspect specifically",
    )
    parser.add_argument(
        "--calib-dir",
        type=Path,
        help="YOLO INT8 JPEG directory (default: <repo>/yolo/calib_images)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="inspect source prerequisites and all known model families",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return nonzero for warnings as well as errors",
    )
    args = parser.parse_args()
    if not args.all and not args.model:
        parser.error("choose --all or --model MODEL")
    return args


def show(level: str, message: str) -> None:
    print(f"{level}: {message}")


def check_path(path: Path, label: str, required: bool = True) -> bool:
    if path.is_file():
        show("OK", f"{label}: {path}")
        return True
    level = "ERROR" if required else "WARN"
    show(level, f"{label} is missing: {path}")
    return False


def check_source_tree(root: Path) -> tuple[int, int]:
    errors = warnings = 0
    required_files = {
        "GoogLeNet prototxt": root / "googlenet/deploy.prototxt",
        "GoogLeNet Caffe weights": root / "googlenet/deploy.caffemodel",
        "GoogLeNet builder": root / "googlenet/create_engine.cpp",
        "MTCNN PNet prototxt": root / "mtcnn/det1_relu.prototxt",
        "MTCNN PNet weights": root / "mtcnn/det1_relu.caffemodel",
        "MTCNN RNet prototxt": root / "mtcnn/det2_relu.prototxt",
        "MTCNN RNet weights": root / "mtcnn/det2_relu.caffemodel",
        "MTCNN ONet prototxt": root / "mtcnn/det3_relu.prototxt",
        "MTCNN ONet weights": root / "mtcnn/det3_relu.caffemodel",
        "SSD builder": root / "ssd/build_engine.py",
        "MODNet ONNX converter": root / "modnet/onnx_to_tensorrt.py",
        "MODNet ONNX": root / "modnet/modnet.onnx",
        "YOLO DarkNet converter": root / "yolo/yolo_to_onnx.py",
        "YOLO TensorRT converter": root / "yolo/onnx_to_tensorrt.py",
        "YOLO custom plugin source": root / "plugins/yolo_layer.cu",
        "YOLO custom plugin header": root / "plugins/yolo_layer.h",
        "plugin Makefile": root / "plugins/Makefile",
        "CUDA architecture probe": root / "plugins/gpu_cc.py",
        "common Makefile config": root / "common/Makefile.config",
        "root Makefile": root / "Makefile",
        "Python extension setup": root / "setup.py",
    }
    for label, path in required_files.items():
        if not check_path(path, label):
            errors += 1
    return errors, warnings


def parse_cfg(path: Path) -> Tuple[Dict[str, str], List[Dict[str, str]], List[str]]:
    """Parse only the cfg fields needed for safe shape/metadata checks."""
    net: dict[str, str] = {}
    yolo: list[dict[str, str]] = []
    section = ""
    current: dict[str, str] | None = None
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return net, yolo, [f"cannot read {path}: {exc}"]
    for lineno, raw in enumerate(lines, 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            if section == "net":
                current = net
            elif section == "yolo":
                current = {}
                yolo.append(current)
            else:
                current = None
            continue
        if "=" not in line or current is None:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if not key or not value:
            errors.append(f"{path}:{lineno}: empty cfg key/value")
        else:
            current[key] = value
    return net, yolo, errors


def integer(value: Optional[str], label: str, errors: List[str]) -> Optional[int]:
    if value is None:
        errors.append(f"missing {label}")
        return None
    try:
        return int(value)
    except ValueError:
        errors.append(f"{label} is not an integer: {value!r}")
        return None


def check_yolo_cfg(root: Path, model: str) -> tuple[int, int]:
    errors = warnings = 0
    cfg = root / "yolo" / f"{model}.cfg"
    if not check_path(cfg, f"YOLO cfg for {model}", required=True):
        return 1, 0
    net, yolo, parse_errors = parse_cfg(cfg)
    h = integer(net.get("height"), f"{cfg} net.height", parse_errors)
    w = integer(net.get("width"), f"{cfg} net.width", parse_errors)
    channels = integer(net.get("channels", "3"), f"{cfg} net.channels", parse_errors)
    classes: List[int] = []
    masks: List[List[int]] = []
    for index, block in enumerate(yolo):
        c = integer(block.get("classes"), f"{cfg} yolo[{index}].classes", parse_errors)
        if c is not None:
            classes.append(c)
        raw_mask = block.get("mask")
        if raw_mask is None:
            parse_errors.append(f"{cfg} yolo[{index}] has no mask")
        else:
            try:
                values = [int(v.strip()) for v in raw_mask.split(",") if v.strip()]
                masks.append(values)
            except ValueError:
                parse_errors.append(f"{cfg} yolo[{index}].mask is not integer CSV")
    if h is not None and (h <= 0 or h % 32):
        parse_errors.append(f"{cfg} height must be positive and divisible by 32: {h}")
    if w is not None and (w <= 0 or w % 32):
        parse_errors.append(f"{cfg} width must be positive and divisible by 32: {w}")
    if channels is not None and channels <= 0:
        parse_errors.append(f"{cfg} channels must be positive: {channels}")
    if not 2 <= len(yolo) <= 4:
        parse_errors.append(f"{cfg} has {len(yolo)} [yolo] blocks; source expects 2, 3, or 4")
    if classes and len(set(classes)) != 1:
        parse_errors.append(f"{cfg} has inconsistent classes values: {classes}")
    if masks and any(not values for values in masks):
        parse_errors.append(f"{cfg} has an empty anchor mask")
    for message in parse_errors:
        show("ERROR", message)
    errors += len(parse_errors)

    weights = root / "yolo" / f"{model}.weights"
    onnx = root / "yolo" / f"{model}.onnx"
    if not check_path(weights, f"DarkNet weights for {model}", required=False):
        warnings += 1
    if not check_path(onnx, f"generated ONNX for {model}", required=False):
        warnings += 1
    plugin = root / "plugins" / "libyolo_layer.so"
    if not check_path(plugin, "built YOLO plugin", required=False):
        warnings += 1
    return errors, warnings


def check_ssd(root: Path, model: str, required_model: bool = True) -> tuple[int, int]:
    errors = warnings = 0
    pb = root / "ssd" / f"{model}.pb"
    if not check_path(pb, f"SSD frozen graph for {model}", required=required_model):
        if required_model:
            errors += 1
        else:
            warnings += 1
    if not check_path(root / "ssd/build_engine.py", "SSD builder", required=True):
        errors += 1
    # A versioned plugin may be present while the unversioned link is absent.
    versioned = sorted((root / "ssd").glob("libflattenconcat.so.*"))
    if versioned:
        show("OK", "SSD FlattenConcat versioned plugin(s): " + ", ".join(map(str, versioned)))
    else:
        show("WARN", "no versioned SSD libflattenconcat.so.* found")
        warnings += 1
    return errors, warnings


def check_calibration(root: Path, calib_dir: Path | None) -> tuple[int, int]:
    errors = warnings = 0
    directory = calib_dir or (root / "yolo/calib_images")
    if not directory.is_dir():
        show("WARN", f"YOLO INT8 calibration directory is absent: {directory}")
        return 0, 1
    jpgs = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".jpg")
    show("OK", f"calibration JPEGs: {len(jpgs)} in {directory}")
    if len(jpgs) < 500:
        show("WARN", "fewer than 500 JPEGs; repository README cites 500 as guidance")
        warnings += 1
    return errors, warnings


def check_model(root: Path, model: str, calib_dir: Path | None) -> tuple[int, int]:
    if model in MODEL_NAMES:
        errors, warnings = check_ssd(root, model)
    else:
        errors, warnings = check_yolo_cfg(root, model)
    if calib_dir is not None:
        e, w = check_calibration(root, calib_dir)
        errors += e
        warnings += w
    return errors, warnings


def main() -> int:
    args = parse_args()
    root = args.repo_root.expanduser().resolve()
    if not root.is_dir():
        show("ERROR", f"repository root is not a directory: {root}")
        return 2
    errors = warnings = 0
    if args.all:
        e, w = check_source_tree(root)
        errors += e
        warnings += w
        # Source artifacts are checked separately from model-specific downloads.
        primary_ssd = set(MODEL_NAMES[:4])
        for model in MODEL_NAMES:
            e, w = check_ssd(root, model, required_model=model in primary_ssd)
            errors += e
            warnings += w
        e, w = check_calibration(root, args.calib_dir)
        errors += e
        warnings += w
        yolo_cfgs = sorted((root / "yolo").glob("*.cfg"))
        if not yolo_cfgs:
            show("WARN", "no YOLO cfg files found; download/acquisition is intentionally not performed")
            warnings += 1
        for cfg in yolo_cfgs:
            e, w = check_yolo_cfg(root, cfg.stem)
            errors += e
            warnings += w
    else:
        e, w = check_model(root, args.model, args.calib_dir)
        errors += e
        warnings += w
    show("SUMMARY", f"errors={errors} warnings={warnings} root={root}")
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
