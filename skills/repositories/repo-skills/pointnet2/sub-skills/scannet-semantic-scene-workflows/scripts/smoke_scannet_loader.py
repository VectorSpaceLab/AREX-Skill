#!/usr/bin/env python3
"""Smoke-test an adapted ScanNet loader contract for PointNet2.

The original repository loader is Python 2-era code. This helper exercises the
same public data contract in Python 3: two-object split pickles, random block
sampling, class-weight lookup, and whole-scene tiling. It can create a tiny
fixture so the skill can be validated without downloading ScanNet.
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

try:
    import numpy as np
except Exception as exc:  # pragma: no cover
    sys.stderr.write("ERROR: numpy is required for ScanNet loader smoke: %s\n" % exc)
    sys.exit(2)

NUM_CLASSES = 21


def pickle_load(fp):
    try:
        return pickle.load(fp, encoding="latin1")
    except TypeError:  # pragma: no cover - Python 2 compatibility if reused manually
        return pickle.load(fp)


def write_split(root: Path, split: str, points_list: List[np.ndarray], labels_list: List[np.ndarray]) -> None:
    with (root / ("scannet_%s.pickle" % split)).open("wb") as fp:
        pickle.dump(points_list, fp, protocol=2)
        pickle.dump(labels_list, fp, protocol=2)


def make_fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    grid = []
    labels = []
    # Build a small but spatially non-degenerate scene with foreground labels.
    for ix in range(5):
        for iy in range(5):
            for iz in range(2):
                grid.append([ix * 0.45, iy * 0.45, iz * 0.6])
                labels.append((ix + iy + iz) % 5)  # includes 0..4
    points = np.asarray(grid, dtype=np.float32)
    semantic = np.asarray(labels, dtype=np.int32)
    points2 = points + np.asarray([0.1, 0.2, 0.0], dtype=np.float32)
    semantic2 = np.asarray([(int(x) % 4) + 1 for x in semantic], dtype=np.int32)
    write_split(root, "train", [points, points2], [semantic, semantic2])
    write_split(root, "test", [points2], [semantic2])


def load_split(root: Path, split: str) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    path = root / ("scannet_%s.pickle" % split)
    with path.open("rb") as fp:
        points = pickle_load(fp)
        labels = pickle_load(fp)
    return [np.asarray(p, dtype=np.float32) for p in points], [np.asarray(l, dtype=np.int32) for l in labels]


def validate_basic(points_list: Sequence[np.ndarray], labels_list: Sequence[np.ndarray]) -> None:
    if len(points_list) != len(labels_list):
        raise ValueError("points/labels scene count mismatch: %d vs %d" % (len(points_list), len(labels_list)))
    if not points_list:
        raise ValueError("split has no scenes")
    for idx, (points, labels) in enumerate(zip(points_list, labels_list)):
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError("scene %d points must be N x 3, got %s" % (idx, points.shape))
        if labels.ndim != 1:
            raise ValueError("scene %d labels must be 1-D, got %s" % (idx, labels.shape))
        if len(points) != len(labels):
            raise ValueError("scene %d length mismatch: %d points vs %d labels" % (idx, len(points), len(labels)))
        if len(points) == 0:
            raise ValueError("scene %d has no points" % idx)
        if labels.min() < 0 or labels.max() >= NUM_CLASSES:
            raise ValueError("scene %d labels outside 0..%d: min=%s max=%s" % (idx, NUM_CLASSES - 1, labels.min(), labels.max()))


def compute_labelweights(labels_list: Sequence[np.ndarray], split: str) -> np.ndarray:
    if split == "train":
        hist = np.zeros(NUM_CLASSES, dtype=np.float64)
        for labels in labels_list:
            hist += np.histogram(labels, range(NUM_CLASSES + 1))[0]
        if hist.sum() == 0:
            raise ValueError("training label histogram is empty")
        freq = hist / hist.sum()
        return 1.0 / np.log(1.2 + freq)
    return np.ones(NUM_CLASSES, dtype=np.float64)


def random_block(points: np.ndarray, labels: np.ndarray, labelweights: np.ndarray, npoints: int, rng: np.random.RandomState) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    coordmax = np.max(points, axis=0)
    coordmin = np.min(points, axis=0)
    selected_points = points
    selected_labels = labels
    selected_mask = np.ones(len(labels), dtype=bool)

    for _ in range(10):
        center = points[rng.choice(len(labels)), :]
        curmin = center - np.asarray([0.75, 0.75, 1.5], dtype=np.float32)
        curmax = center + np.asarray([0.75, 0.75, 1.5], dtype=np.float32)
        curmin[2] = coordmin[2]
        curmax[2] = coordmax[2]
        curchoice = np.sum((points >= (curmin - 0.2)) & (points <= (curmax + 0.2)), axis=1) == 3
        if not np.any(curchoice):
            continue
        candidate_points = points[curchoice, :]
        candidate_labels = labels[curchoice]
        inner_mask = np.sum((candidate_points >= (curmin - 0.01)) & (candidate_points <= (curmax + 0.01)), axis=1) == 3
        labeled_ratio = float(np.sum(candidate_labels > 0)) / float(len(candidate_labels))
        occupancy_ratio = float(np.sum(inner_mask)) / float(max(len(inner_mask), 1))
        selected_points = candidate_points
        selected_labels = candidate_labels
        selected_mask = inner_mask
        if labeled_ratio >= 0.7 and occupancy_ratio >= 0.02:
            break

    choice = rng.choice(len(selected_labels), npoints, replace=True)
    sampled_points = selected_points[choice, :]
    sampled_labels = selected_labels[choice]
    sampled_mask = selected_mask[choice]
    sampled_weights = labelweights[sampled_labels] * sampled_mask.astype(np.float64)
    return sampled_points, sampled_labels, sampled_weights


def whole_scene_tiles(points: np.ndarray, labels: np.ndarray, labelweights: np.ndarray, npoints: int, rng: np.random.RandomState) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    coordmax = np.max(points, axis=0)
    coordmin = np.min(points, axis=0)
    nsubvolume_x = max(1, int(np.ceil((coordmax[0] - coordmin[0]) / 1.5)))
    nsubvolume_y = max(1, int(np.ceil((coordmax[1] - coordmin[1]) / 1.5)))
    point_sets = []
    semantic_sets = []
    weight_sets = []
    for i in range(nsubvolume_x):
        for j in range(nsubvolume_y):
            curmin = coordmin + np.asarray([i * 1.5, j * 1.5, 0.0], dtype=np.float32)
            curmax = coordmin + np.asarray([(i + 1) * 1.5, (j + 1) * 1.5, coordmax[2] - coordmin[2]], dtype=np.float32)
            curchoice = np.sum((points >= (curmin - 0.2)) & (points <= (curmax + 0.2)), axis=1) == 3
            if not np.any(curchoice):
                continue
            candidate_points = points[curchoice, :]
            candidate_labels = labels[curchoice]
            inner_mask = np.sum((candidate_points >= (curmin - 0.001)) & (candidate_points <= (curmax + 0.001)), axis=1) == 3
            choice = rng.choice(len(candidate_labels), npoints, replace=True)
            sampled_points = candidate_points[choice, :]
            sampled_labels = candidate_labels[choice]
            sampled_mask = inner_mask[choice]
            if float(np.sum(sampled_mask)) / float(len(sampled_mask)) < 0.01:
                continue
            point_sets.append(sampled_points[np.newaxis, :, :])
            semantic_sets.append(sampled_labels[np.newaxis, :])
            weight_sets.append((labelweights[sampled_labels] * sampled_mask.astype(np.float64))[np.newaxis, :])
    if not point_sets:
        raise ValueError("whole-scene tiling produced no valid tiles")
    return np.concatenate(point_sets, axis=0), np.concatenate(semantic_sets, axis=0), np.concatenate(weight_sets, axis=0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke-test PointNet2 ScanNet pickle loading and block/whole-scene sampling.")
    parser.add_argument("--pickle-root", help="Existing directory containing scannet_<split>.pickle files.")
    parser.add_argument("--make-fixture", help="Create a tiny valid fixture at this directory and smoke-test it.")
    parser.add_argument("--split", default="train", choices=["train", "test"], help="Split to smoke after fixture creation/loading. Default: train.")
    parser.add_argument("--npoints", type=int, default=16, help="Points sampled per block/tile for the smoke. Default: 16.")
    parser.add_argument("--seed", type=int, default=0, help="Random seed. Default: 0.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.pickle_root and not args.make_fixture:
        parser.error("provide --pickle-root or --make-fixture")
    root = Path(args.make_fixture or args.pickle_root)
    if args.make_fixture:
        make_fixture(root)
        print("created fixture: %s" % root)
    rng = np.random.RandomState(args.seed)
    points_list, labels_list = load_split(root, args.split)
    validate_basic(points_list, labels_list)
    labelweights = compute_labelweights(labels_list, args.split)
    block_points, block_labels, block_weights = random_block(points_list[0], labels_list[0], labelweights, args.npoints, rng)
    whole_points, whole_labels, whole_weights = whole_scene_tiles(points_list[0], labels_list[0], labelweights, args.npoints, rng)

    print("loaded split=%s scenes=%d" % (args.split, len(points_list)))
    print("random block: points=%s labels=%s weights=%s positive_weight=%d" % (block_points.shape, block_labels.shape, block_weights.shape, int(np.sum(block_weights > 0))))
    print("whole scene: points=%s labels=%s weights=%s tiles=%d" % (whole_points.shape, whole_labels.shape, whole_weights.shape, whole_points.shape[0]))
    print("observed block labels: %s" % sorted(int(x) for x in np.unique(block_labels)))
    print("OK: ScanNet loader smoke passed")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
