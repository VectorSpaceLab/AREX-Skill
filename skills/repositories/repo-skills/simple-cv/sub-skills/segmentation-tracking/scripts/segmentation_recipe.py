#!/usr/bin/env python
"""Finite SimpleCV segmentation recipes using package sample images."""
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


def load_sample(Image, name):
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
    from SimpleCV import Image
    from SimpleCV.Segmentation import ColorSegmentation, DiffSegmentation, RunningSegmentation

    ensure_dir(args.output_dir)

    if args.recipe == "color":
        img = load_sample(Image, args.image)
        seg = ColorSegmentation()
        crop = img.crop(0, 0, min(args.crop_size, img.width), min(args.crop_size, img.height))
        seg.addToModel(crop)
        seg.addImage(img)
        mask = seg.getSegmentedImage()
        save_image(mask, os.path.join(args.output_dir, "color_mask.png"))
        blobs = seg.getSegmentedBlobs()
        print("segmented_blobs=%s" % (len(blobs) if blobs else 0))

    elif args.recipe == "diff":
        first = load_sample(Image, args.first)
        second = load_sample(Image, args.second)
        seg = DiffSegmentation(threshold=(args.threshold, args.threshold, args.threshold))
        seg.addImage(first)
        seg.addImage(second)
        if not seg.isReady():
            raise RuntimeError("DiffSegmentation is not ready after two frames")
        mask = seg.getSegmentedImage()
        save_image(mask, os.path.join(args.output_dir, "diff_mask.png"))
        blobs = seg.getSegmentedBlobs()
        print("segmented_blobs=%s" % (len(blobs) if blobs else 0))

    elif args.recipe == "running":
        first = load_sample(Image, args.first)
        second = load_sample(Image, args.second)
        seg = RunningSegmentation(alpha=args.alpha, thresh=(args.threshold, args.threshold, args.threshold))
        for img in [first, second, first, second]:
            seg.addImage(img)
        if not seg.isReady():
            raise RuntimeError("RunningSegmentation is not ready")
        mask = seg.getSegmentedImage()
        save_image(mask, os.path.join(args.output_dir, "running_mask.png"))

    print("status=ok recipe=%s" % args.recipe)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run finite SimpleCV segmentation recipes.")
    parser.add_argument("--repo-root", help="Optional SimpleCV checkout to add to sys.path before import.")
    parser.add_argument("--recipe", choices=["color", "diff", "running"], default="diff")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--image", default="greenscreen.png", help="Sample/path for color segmentation.")
    parser.add_argument("--first", default="tracktest0.jpg", help="First frame sample/path.")
    parser.add_argument("--second", default="tracktest1.jpg", help="Second frame sample/path.")
    parser.add_argument("--crop-size", type=int, default=40)
    parser.add_argument("--threshold", type=int, default=10)
    parser.add_argument("--alpha", type=float, default=0.7)
    args = parser.parse_args(argv)

    add_repo_root(args.repo_root)
    try:
        run_recipe(args)
        return 0
    except Exception as exc:
        print("status=failed error=%s: %s" % (exc.__class__.__name__, exc))
        print("hint=Check sample frames, segmentation thresholds, and whether a live camera workflow was accidentally required.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
