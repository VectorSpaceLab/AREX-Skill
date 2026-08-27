#!/usr/bin/env python3
"""Validate Tencent ML-Images feature-extraction inputs and print a safe command.

This helper does not restore checkpoints or extract features. It checks the
image list, checkpoint shape, and result path before printing a command the user
can run in a prepared TensorFlow 1.x/OpenCV runtime.
"""

import argparse
import glob
import shlex
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--images", required=True, help="Image list file with one image path per line.")
    p.add_argument("--checkpoint", required=True, help="TensorFlow checkpoint prefix or directory.")
    p.add_argument("--result", default="features.txt", help="Output file path for extracted features.")
    p.add_argument("--python", default="python2.7", help="Python executable or command to prefix the script with.")
    p.add_argument("--script", default="extract_feature.py", help="Feature extraction script path inside a Tencent ML-Images checkout.")
    p.add_argument("--visiable-gpu", default="0", help="GPU id string used by the source flag spelling.")
    p.add_argument("--resnet-size", type=int, default=101, choices=[50, 101, 152], help="ResNet depth used by the checkpoint.")
    p.add_argument("--data-format", default="NCHW", choices=["NCHW", "NHWC"], help="TensorFlow data format string.")
    return p.parse_args()


def checkpoint_exists(path: Path) -> bool:
    if path.is_dir():
        patterns = [str(path / "*.index"), str(path / "*.data-*"), str(path / "checkpoint")]
        return any(glob.glob(pattern) for pattern in patterns)
    if path.exists():
        return True
    prefix = str(path)
    return bool(glob.glob(prefix + ".index") or glob.glob(prefix + ".data-*"))


def validate_images(path: Path):
    errors = []
    if not path.exists():
        return [f"image list does not exist: {path}"]
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for lineno, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            image_path = line.split("\t", 1)[0].split()[0]
            if not image_path:
                errors.append(f"line {lineno}: empty image path")
            elif not Path(image_path).expanduser().exists():
                errors.append(f"line {lineno}: missing image file {image_path}")
    return errors


def main() -> int:
    a = parse_args()
    images = Path(a.images)
    checkpoint = Path(a.checkpoint)
    result = Path(a.result)
    errors = []

    errors.extend(validate_images(images))
    if not checkpoint_exists(checkpoint):
        errors.append(f"checkpoint prefix or directory does not look complete: {checkpoint}")
    if result.exists() and result.is_dir():
        errors.append(f"result path is an existing directory, not a file: {result}")

    if errors:
        for msg in errors:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 1

    cmd = [
        a.python,
        a.script,
        f"--resnet_size={a.resnet_size}",
        f"--data_format={a.data_format}",
        f"--visiable_gpu={a.visiable_gpu}",
        f"--pretrain_ckpt={a.checkpoint}",
        f"--result={a.result}",
        f"--images={a.images}",
    ]
    print(" \\\n  ".join(shlex.quote(part) for part in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
