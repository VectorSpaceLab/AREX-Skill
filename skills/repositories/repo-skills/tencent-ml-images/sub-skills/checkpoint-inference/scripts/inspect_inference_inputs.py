#!/usr/bin/env python3
"""Validate Tencent ML-Images classification inputs and print a safe command.

This helper does not restore checkpoints or run inference. It checks the image
list, dictionary, and checkpoint shape, then prints a command the user can run
in a prepared TensorFlow 1.x/OpenCV runtime.
"""

import argparse
import glob
import shlex
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--images", required=True, help="Image list file with one image path per line.")
    p.add_argument("--dictionary", required=True, help="ImageNet dictionary file used by the classification script.")
    p.add_argument("--checkpoint", required=True, help="TensorFlow checkpoint prefix or directory.")
    p.add_argument("--result", default="label_pred.txt", help="Result output file.")
    p.add_argument("--top-k", type=int, default=5, help="Number of predictions to print.")
    p.add_argument("--class-num", type=int, default=1000, help="Expected number of classes for the checkpoint.")
    p.add_argument("--python", default="python2.7", help="Python executable or command to prefix the script with.")
    p.add_argument("--script", default="image_classification.py", help="Classification script path inside a Tencent ML-Images checkout.")
    p.add_argument("--visiable-gpu", default="0", help="GPU id string used by the source flag spelling.")
    return p.parse_args()


def checkpoint_exists(path: Path) -> bool:
    if path.is_dir():
        patterns = [str(path / "*.index"), str(path / "*.data-*"), str(path / "checkpoint")]
        return any(glob.glob(pattern) for pattern in patterns)
    if path.exists():
        return True
    prefix = str(path)
    return bool(glob.glob(prefix + ".index") or glob.glob(prefix + ".data-*"))


def count_dictionary_rows(path: Path) -> int:
    rows = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            if raw.strip():
                rows += 1
    return rows


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
    dictionary = Path(a.dictionary)
    checkpoint = Path(a.checkpoint)
    errors = []
    warnings = []

    errors.extend(validate_images(images))
    if not dictionary.exists():
        errors.append(f"dictionary does not exist: {dictionary}")
    else:
        rows = count_dictionary_rows(dictionary)
        if rows < a.class_num:
            warnings.append(f"dictionary has {rows} rows, fewer than class_num={a.class_num}")
    if a.top_k > a.class_num:
        errors.append(f"top_k={a.top_k} cannot exceed class_num={a.class_num}")
    if not checkpoint_exists(checkpoint):
        errors.append(f"checkpoint prefix or directory does not look complete: {checkpoint}")

    if errors:
        for msg in errors:
            print(f"ERROR: {msg}", file=sys.stderr)
        for msg in warnings:
            print(f"WARNING: {msg}", file=sys.stderr)
        return 1

    cmd = [
        a.python,
        a.script,
        f"--images={a.images}",
        f"--top_k_pred={a.top_k}",
        f"--model_dir={a.checkpoint}",
        f"--dictionary={a.dictionary}",
        f"--result={a.result}",
        f"--visiable_gpu={a.visiable_gpu}",
    ]
    print(" \\\n  ".join(shlex.quote(part) for part in cmd))
    for msg in warnings:
        print(f"# WARNING: {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
