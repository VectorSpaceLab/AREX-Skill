#!/usr/bin/env python3
"""Run a tiny deterministic check of GeoSeg's confusion-matrix metrics.

The helper contains the metric equations needed for a dependency-light smoke
check and does not import the source checkout. It is intended to verify that a
runtime environment can compute the reported OA, IoU, and F1-style values
before using a real dataset.
"""

import argparse
import numpy as np


def evaluate(num_class, ground_truth, prediction):
    confusion = np.zeros((num_class, num_class), dtype=np.float64)
    mask = (ground_truth >= 0) & (ground_truth < num_class)
    labels = num_class * ground_truth[mask].astype(int) + prediction[mask]
    confusion += np.bincount(labels, minlength=num_class ** 2).reshape(num_class, num_class)
    tp = np.diag(confusion)
    fp = confusion.sum(axis=0) - tp
    fn = confusion.sum(axis=1) - tp
    iou = tp / (tp + fp + fn)
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1 = (2 * precision * recall) / (precision + recall)
    oa = tp.sum() / (confusion.sum() + 1e-8)
    return confusion, iou, f1, oa


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="print the confusion matrix")
    args = parser.parse_args(argv)
    gt = np.array([[0, 1, 1], [1, 2, 2], [0, 2, 1]], dtype=np.int64)
    pred = np.array([[0, 1, 0], [1, 2, 1], [0, 0, 1]], dtype=np.int64)
    confusion, iou, f1, oa = evaluate(3, gt, pred)
    if args.verbose:
        print(confusion)
    assert confusion.sum() == gt.size
    assert 0.0 < oa < 1.0
    assert np.all((iou >= 0.0) & (iou <= 1.0))
    assert np.all((f1 >= 0.0) & (f1 <= 1.0))
    print("metric smoke passed: OA={:.6f}, mIoU={:.6f}".format(oa, float(np.nanmean(iou))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
