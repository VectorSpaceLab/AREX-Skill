#!/usr/bin/env python
"""Finite SimpleCV image-processing recipes adapted from interactive examples."""
from __future__ import print_function

import argparse
import os
import sys


def add_repo_root(path):
    if path:
        root = os.path.abspath(path)
        if root not in sys.path:
            sys.path.insert(0, root)
        print("added_repo_root=%s" % root)


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def load_image(Image, name):
    try:
        img = Image(name, sample=True)
        if hasattr(img, "isEmpty") and not img.isEmpty():
            return img
    except Exception:
        pass
    return Image(name)


def save_image(img, path):
    img.save(path)
    print("wrote=%s size=%s" % (path, img.size()))


def run_recipe(args):
    from SimpleCV import Image, Color

    ensure_dir(args.output_dir)
    img = load_image(Image, args.sample)
    if hasattr(img, "isEmpty") and img.isEmpty():
        raise RuntimeError("input image is empty; check sample name or package data")

    outputs = []
    if args.recipe in ("rotate", "all"):
        rot = img.rotate(args.angle)
        path = os.path.join(args.output_dir, "rotated.png")
        save_image(rot, path)
        outputs.append(path)

    if args.recipe in ("crop", "all"):
        w = min(args.crop_size, img.width)
        h = min(args.crop_size, img.height)
        crop = img.crop(0, 0, w, h).scale(args.scale_size, args.scale_size)
        path = os.path.join(args.output_dir, "crop_scaled.png")
        save_image(crop, path)
        outputs.append(path)

    if args.recipe in ("threshold", "all"):
        binary = img.grayscale().binarize()
        binary.drawText("binary", 5, 5, color=Color.RED)
        rendered = binary.applyLayers()
        path = os.path.join(args.output_dir, "binary.png")
        save_image(rendered, path)
        outputs.append(path)

    if args.recipe in ("histogram", "all"):
        hist = img.histogram(args.hist_bins)
        path = os.path.join(args.output_dir, "histogram.txt")
        with open(path, "w") as handle:
            handle.write("bins=%s\n" % args.hist_bins)
            handle.write("counts=%s\n" % list(hist))
        print("wrote=%s entries=%s" % (path, len(hist)))
        outputs.append(path)

    print("status=ok outputs=%s" % ",".join(outputs))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run finite SimpleCV Image/ImageSet smoke recipes.")
    parser.add_argument("--repo-root", help="Optional SimpleCV checkout to add to sys.path before import.")
    parser.add_argument("--sample", default="simplecv", help="SimpleCV sample name or image path; default: simplecv.")
    parser.add_argument("--recipe", choices=["rotate", "crop", "threshold", "histogram", "all"], default="all")
    parser.add_argument("--output-dir", required=True, help="Directory for generated outputs.")
    parser.add_argument("--angle", type=float, default=45.0)
    parser.add_argument("--crop-size", type=int, default=100)
    parser.add_argument("--scale-size", type=int, default=64)
    parser.add_argument("--hist-bins", type=int, default=16)
    args = parser.parse_args(argv)

    add_repo_root(args.repo_root)
    try:
        run_recipe(args)
        return 0
    except Exception as exc:
        print("status=failed error=%s: %s" % (exc.__class__.__name__, exc))
        print("hint=Verify SimpleCV import, sample image availability, and headless display settings before debugging transforms.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
