#!/usr/bin/env python3
"""Convert TuSimple annotations into segmentation masks and list files.

This helper mirrors the repo's TuSimple conversion flow but exposes explicit
arguments and avoids hardcoded repository paths.

Example:
    python convert_tusimple_safe.py --root /path/to/TuSimple
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import cv2
import numpy as np
import tqdm

DEFAULT_TRAIN_LABELS = [
    "label_data_0601.json",
    "label_data_0531.json",
    "label_data_0313.json",
]
DEFAULT_TEST_LABELS = ["test_tasks_0627.json"]


def calc_k(line: Sequence[float]) -> float:
    line_x = np.asarray(line[::2], dtype=float)
    line_y = np.asarray(line[1::2], dtype=float)
    length = np.sqrt((line_x[0] - line_x[-1]) ** 2 + (line_y[0] - line_y[-1]) ** 2)
    if length < 90:
        return -10
    p = np.polyfit(line_x, line_y, deg=1)
    return float(np.arctan(p[0]))


def draw(mask: np.ndarray, line: Sequence[float], idx: int) -> None:
    line_x = [int(x) for x in line[::2]]
    line_y = [int(y) for y in line[1::2]]
    pt0 = (line_x[0], line_y[0])
    for i in range(len(line_x) - 1):
        cv2.line(mask, pt0, (line_x[i + 1], line_y[i + 1]), (idx,), thickness=16)
        pt0 = (line_x[i + 1], line_y[i + 1])


def read_training_json_lines(root: Path, label_files: Sequence[str]) -> Tuple[List[str], List[List[List[str]]]]:
    label_json_all = []
    for file_name in label_files:
        file_path = root / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"missing TuSimple JSON file: {file_path}")
        label_json_all.extend(json.loads(line) for line in file_path.read_text().splitlines())

    names = [item["raw_file"] for item in label_json_all]
    h_samples = [np.asarray(item["h_samples"]) for item in label_json_all]
    lanes = [np.asarray(item["lanes"]) for item in label_json_all]

    line_txt = []
    for i in range(len(lanes)):
        line_txt_i = []
        for j in range(len(lanes[i])):
            if np.all(lanes[i][j] == -2):
                continue
            valid = lanes[i][j] != -2
            line_txt_tmp = [None] * (len(h_samples[i][valid]) + len(lanes[i][j][valid]))
            line_txt_tmp[::2] = [str(v) for v in lanes[i][j][valid]]
            line_txt_tmp[1::2] = [str(v) for v in h_samples[i][valid]]
            line_txt_i.append(line_txt_tmp)
        line_txt.append(line_txt_i)
    return names, line_txt


def read_test_names(root: Path, label_files: Sequence[str]) -> List[str]:
    names = []
    for file_name in label_files:
        file_path = root / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"missing TuSimple test JSON file: {file_path}")
        for line in file_path.read_text().splitlines():
            item = json.loads(line)
            names.append(item["raw_file"])
    return names


def generate_segmentation_and_train_list(root: Path, line_txt: Sequence[Sequence[Sequence[str]]], names: Sequence[str]) -> None:
    train_gt_path = root / "train_gt.txt"
    with train_gt_path.open("w") as train_gt_fp:
        for i in tqdm.tqdm(range(len(line_txt))):
            tmp_line = line_txt[i]
            lines = [list(map(float, lane)) for lane in tmp_line]
            ks = np.array([calc_k(line) for line in lines])

            k_neg = ks[(ks < 0) & (ks != -10)].copy()
            k_pos = ks[(ks > 0) & (ks != -10)].copy()
            k_neg.sort()
            k_pos.sort()

            label_path = names[i][:-3] + "png"
            label = np.zeros((720, 1280), dtype=np.uint8)
            bin_label = [0, 0, 0, 0]

            if len(k_neg) == 1:
                which_lane = np.where(ks == k_neg[0])[0][0]
                draw(label, lines[which_lane], 2)
                bin_label[1] = 1
            elif len(k_neg) >= 2:
                which_lane = np.where(ks == k_neg[1])[0][0]
                draw(label, lines[which_lane], 1)
                which_lane = np.where(ks == k_neg[0])[0][0]
                draw(label, lines[which_lane], 2)
                bin_label[0] = 1
                bin_label[1] = 1

            if len(k_pos) == 1:
                which_lane = np.where(ks == k_pos[0])[0][0]
                draw(label, lines[which_lane], 3)
                bin_label[2] = 1
            elif len(k_pos) >= 2:
                which_lane = np.where(ks == k_pos[-1])[0][0]
                draw(label, lines[which_lane], 3)
                which_lane = np.where(ks == k_pos[-2])[0][0]
                draw(label, lines[which_lane], 4)
                bin_label[2] = 1
                bin_label[3] = 1

            out_path = root / label_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(out_path), label)
            train_gt_fp.write(names[i] + " " + label_path + " " + " ".join(map(str, bin_label)) + "\n")


def write_test_list(root: Path, names: Iterable[str]) -> None:
    test_path = root / "test.txt"
    with test_path.open("w") as fp:
        for name in names:
            fp.write(name + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert TuSimple JSON annotations into masks and list files.")
    parser.add_argument("--root", required=True, help="TuSimple dataset root containing the JSON labels")
    parser.add_argument(
        "--train-labels",
        nargs="+",
        default=DEFAULT_TRAIN_LABELS,
        help="Training JSON files relative to the root",
    )
    parser.add_argument(
        "--test-labels",
        nargs="+",
        default=DEFAULT_TEST_LABELS,
        help="Test JSON files relative to the root",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"TuSimple root does not exist: {root}")

    train_names, train_lines = read_training_json_lines(root, args.train_labels)
    generate_segmentation_and_train_list(root, train_lines, train_names)

    test_names = read_test_names(root, args.test_labels)
    write_test_list(root, test_names)

    print(f"wrote train_gt.txt and test.txt under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
