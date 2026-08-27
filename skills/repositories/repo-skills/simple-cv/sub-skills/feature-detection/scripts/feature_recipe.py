#!/usr/bin/env python
"""Finite SimpleCV feature-detection recipes adapted from source examples."""
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


def save_rendered(img, path):
    rendered = img.applyLayers()
    rendered.save(path)
    print("wrote=%s size=%s" % (path, rendered.size()))


def require_features(features, name, fail_empty):
    count = len(features) if features else 0
    print("feature_count %s=%s" % (name, count))
    if count == 0:
        print("warning=no_%s_found; adjust thresholds, sample image, method, or optional OpenCV detector support" % name)
        if fail_empty:
            raise RuntimeError("no %s found" % name)
    return count


def run_recipe(args):
    from SimpleCV import Image, Color

    ensure_dir(args.output_dir)

    if args.recipe == "blobs":
        img = load_sample(Image, args.sample or "coins.jpg")
        features = img.invert().findBlobs(minsize=args.minsize)
        count = require_features(features, "blobs", args.fail_empty)
        if features:
            features.draw(color=Color.RED, width=2)
            largest = features[-1]
            img.drawText("count=%s radius=%0.1f" % (count, largest.radius()), largest.x, largest.y, color=Color.BLUE)
        save_rendered(img, os.path.join(args.output_dir, "blobs.png"))

    elif args.recipe == "corners":
        img = load_sample(Image, args.sample or "aerospace.jpg")
        features = img.findCorners(args.maxnum)
        count = require_features(features, "corners", args.fail_empty)
        if features:
            features.draw(color=Color.RED)
            img.drawText("corners=%s" % count, 10, 10, color=Color.BLUE)
        save_rendered(img, os.path.join(args.output_dir, "corners.png"))

    elif args.recipe == "lines":
        img = load_sample(Image, args.sample or "9dots4lines.png")
        features = img.findLines(threshold=args.threshold)
        count = require_features(features, "lines", args.fail_empty)
        if features:
            features.draw(color=Color.RED)
            img.drawText("lines=%s" % count, 10, 10, color=Color.BLUE)
        save_rendered(img, os.path.join(args.output_dir, "lines.png"))

    elif args.recipe == "template":
        source = load_sample(Image, args.source or "templatetest.png")
        template = load_sample(Image, args.template or "template.png")
        features = source.findTemplate(template, threshold=args.template_threshold, method=args.method)
        count = require_features(features, "template_matches", args.fail_empty)
        if features:
            features.draw(color=Color.RED)
            source.drawText("matches=%s method=%s" % (count, args.method), 10, 10, color=Color.BLUE)
        save_rendered(source, os.path.join(args.output_dir, "template_matches.png"))

    print("status=ok recipe=%s" % args.recipe)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run finite SimpleCV detector recipes on package samples.")
    parser.add_argument("--repo-root", help="Optional SimpleCV checkout to add to sys.path before import.")
    parser.add_argument("--recipe", choices=["blobs", "corners", "lines", "template"], default="blobs")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--sample", help="Override sample image/path for blobs, corners, or lines.")
    parser.add_argument("--source", help="Source image for template recipe.")
    parser.add_argument("--template", help="Template image for template recipe.")
    parser.add_argument("--minsize", type=int, default=200)
    parser.add_argument("--maxnum", type=int, default=25)
    parser.add_argument("--threshold", type=int, default=80)
    parser.add_argument("--template-threshold", type=float, default=5.0)
    parser.add_argument("--method", default="SQR_DIFF_NORM")
    parser.add_argument("--fail-empty", action="store_true", help="Exit nonzero when a recipe finds zero features.")
    args = parser.parse_args(argv)

    add_repo_root(args.repo_root)
    try:
        run_recipe(args)
        return 0
    except Exception as exc:
        print("status=failed error=%s: %s" % (exc.__class__.__name__, exc))
        print("hint=Check image availability, thresholds, and optional OpenCV detector support.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
