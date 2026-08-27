#!/usr/bin/env python3
"""Compute YOLO-style anchors from COCO detection annotations.

Outputs anchors in pixel width,height order sorted by descending area.
"""
import argparse
import json
import numpy as np
from pathlib import Path


def iou(box, clusters):
    x = np.minimum(clusters[:, 0], box[0])
    y = np.minimum(clusters[:, 1], box[1])
    intersection = x * y
    box_area = box[0] * box[1]
    cluster_area = clusters[:, 0] * clusters[:, 1]
    denom = box_area + cluster_area - intersection
    return intersection / np.maximum(denom, 1e-9)


def kmeans(boxes, k, seed=0, reducer=np.median):
    if len(boxes) < k:
        raise SystemExit(f"need at least {k} valid boxes, got {len(boxes)}")
    rng = np.random.default_rng(seed)
    clusters = boxes[rng.choice(len(boxes), k, replace=False)]
    last = np.full((len(boxes),), -1)
    while True:
        distances = np.array([1 - iou(box, clusters) for box in boxes])
        nearest = np.argmin(distances, axis=1)
        if np.array_equal(last, nearest):
            return clusters
        for idx in range(k):
            members = boxes[nearest == idx]
            if len(members):
                clusters[idx] = reducer(members, axis=0)
        last = nearest


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute anchors from a COCO annotation JSON.")
    parser.add_argument("json", help="COCO annotation JSON path.")
    parser.add_argument("--clusters", type=int, default=9)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    data = json.loads(Path(args.json).read_text(encoding="utf-8"))
    boxes = []
    for ann in data.get("annotations", []):
        bbox = ann.get("bbox")
        if isinstance(bbox, list) and len(bbox) == 4 and bbox[2] > 0 and bbox[3] > 0:
            boxes.append([float(bbox[2]), float(bbox[3])])
    boxes = np.asarray(boxes, dtype=float)
    anchors = kmeans(boxes, args.clusters, args.seed)
    order = np.argsort(anchors[:, 0] * anchors[:, 1])[::-1]
    anchors = np.rint(anchors[order]).astype(int)
    avg = np.mean([np.max(iou(box, anchors.astype(float))) for box in boxes])
    print("anchors:", anchors.tolist())
    print(f"average_iou: {avg * 100:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
