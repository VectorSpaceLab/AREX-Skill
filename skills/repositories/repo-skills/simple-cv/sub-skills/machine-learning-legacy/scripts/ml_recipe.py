#!/usr/bin/env python
"""Safe SimpleCV legacy ML dry-run helper.

The default mode validates feature extraction and Orange availability without
training on network data or opening displays.
"""
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


class MeanColorExtractor(object):
    def extract(self, img):
        values = img.meanColor("RGB")
        return [float(v) for v in values]

    def getFieldNames(self):
        return ["mean_r", "mean_g", "mean_b"]

    def getNumFields(self):
        return 3


def make_image(Image, np, rgb_tuple):
    arr = np.zeros((16, 16, 3), dtype=np.uint8)
    arr[:, :] = rgb_tuple
    return Image(arr)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Create a tiny SimpleCV feature table and report Orange availability.")
    parser.add_argument("--repo-root", help="Optional SimpleCV checkout to add to sys.path before import.")
    parser.add_argument("--output", help="Optional TSV output path for extracted features.")
    parser.add_argument("--require-orange", action="store_true", help="Exit nonzero if SimpleCV Orange integration is unavailable.")
    args = parser.parse_args(argv)

    add_repo_root(args.repo_root)

    try:
        import SimpleCV
        from SimpleCV import Image, np
        import SimpleCV.base as base
        from SimpleCV.MachineLearning import KNNClassifier, NaiveBayesClassifier, TreeClassifier, SVMClassifier
    except Exception as exc:
        print("status=failed error=%s: %s" % (exc.__class__.__name__, exc))
        print("hint=Check core SimpleCV import before ML workflow debugging.")
        return 1

    print("simplecv_version=%s" % getattr(SimpleCV, "__version__", "unknown"))
    print("orange_enabled=%s" % getattr(base, "ORANGE_ENABLED", False))
    print("classifier_classes=%s,%s,%s,%s" % (KNNClassifier, NaiveBayesClassifier, TreeClassifier, SVMClassifier))

    extractor = MeanColorExtractor()
    rows = []
    for label, color in [("redish", (220, 20, 20)), ("blueish", (20, 20, 220))]:
        img = make_image(Image, np, color)
        feats = extractor.extract(img)
        if len(feats) != extractor.getNumFields():
            print("status=failed reason=feature length mismatch")
            return 2
        rows.append([label] + feats)
        print("feature_row label=%s values=%s" % (label, feats))

    if args.output:
        parent = os.path.dirname(os.path.abspath(args.output))
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(args.output, "w") as handle:
            handle.write("class\t%s\n" % "\t".join(extractor.getFieldNames()))
            for row in rows:
                handle.write("%s\t%s\n" % (row[0], "\t".join([str(x) for x in row[1:]])))
        print("wrote=%s" % args.output)

    if args.require_orange and not getattr(base, "ORANGE_ENABLED", False):
        print("status=failed reason=Orange integration unavailable")
        return 3

    print("status=ok mode=dry-run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
