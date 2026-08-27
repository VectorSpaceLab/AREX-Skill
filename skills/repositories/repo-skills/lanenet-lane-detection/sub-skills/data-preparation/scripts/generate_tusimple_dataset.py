#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert raw TuSimple labels into LaneNet training masks and index files.

This bundled wrapper mirrors the upstream output layout but adds:
- explicit path validation,
- clearer JSON/image errors,
- write checks for OpenCV.
"""
from __future__ import annotations

import argparse
import glob
import json
import logging
import os
import shutil
from pathlib import Path

import cv2
import numpy as np

LOG = logging.getLogger("generate_tusimple_dataset")


def init_args():
    """
    Parse the raw TuSimple dataset root.
    """
    parser = argparse.ArgumentParser(
        description="Convert an unzipped TuSimple dataset into LaneNet training masks."
    )
    parser.add_argument(
        "--src_dir",
        required=True,
        help="Path to the unzipped TuSimple dataset root.",
    )
    return parser.parse_args()


def _ensure(condition, message):
    if not condition:
        raise ValueError(message)


def _read_png_count(dst_dir):
    return sum(1 for _ in Path(dst_dir).glob("*.png"))


def process_json_file(json_file_path, src_dir, ori_dst_dir, binary_dst_dir, instance_dst_dir):
    """
    Process one TuSimple label JSON file.

    :param json_file_path: Label JSON path.
    :param src_dir: Root of the unzipped TuSimple archive.
    :param ori_dst_dir: Output folder for copied source images.
    :param binary_dst_dir: Output folder for binary lane masks.
    :param instance_dst_dir: Output folder for lane-instance masks.
    :return: Number of usable samples written from this JSON file.
    """
    json_file_path = Path(json_file_path)
    src_dir = Path(src_dir)
    ori_dst_dir = Path(ori_dst_dir)
    binary_dst_dir = Path(binary_dst_dir)
    instance_dst_dir = Path(instance_dst_dir)

    _ensure(json_file_path.is_file(), f"{json_file_path} not exist")

    image_nums = _read_png_count(ori_dst_dir)
    if image_nums:
        LOG.info("Existing PNGs detected in %s; appending after index %d", ori_dst_dir, image_nums)

    written = 0
    with json_file_path.open("r", encoding="utf-8") as file:
        for line_index, line in enumerate(file):
            line = line.strip()
            if not line:
                continue

            try:
                info_dict = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in {json_file_path} line {line_index + 1}: {exc}"
                ) from exc

            for key in ("raw_file", "h_samples", "lanes"):
                _ensure(key in info_dict, f"{json_file_path} line {line_index + 1} missing key: {key}")

            raw_file = info_dict["raw_file"]
            image_path = Path(raw_file)
            if not image_path.is_absolute():
                image_path = src_dir / image_path
            _ensure(image_path.exists(), f"{image_path} not exist")

            h_samples = info_dict["h_samples"]
            lanes = info_dict["lanes"]

            src_image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
            _ensure(src_image is not None, f"Failed to read image: {image_path}")

            image_name_new = "{:04d}.png".format(line_index + image_nums)
            dst_binary_image = np.zeros([src_image.shape[0], src_image.shape[1]], np.uint8)
            dst_instance_image = np.zeros([src_image.shape[0], src_image.shape[1]], np.uint8)

            for lane_index, lane in enumerate(lanes):
                _ensure(len(h_samples) == len(lane),
                        f"{json_file_path} line {line_index + 1}: h_samples and lane length mismatch")
                lane_x = []
                lane_y = []
                for sample_index, lane_x_value in enumerate(lane):
                    if lane_x_value == -2:
                        continue
                    lane_x.append(lane_x_value)
                    lane_y.append(h_samples[sample_index])
                if not lane_x:
                    continue
                lane_pts = np.vstack((lane_x, lane_y)).transpose()
                lane_pts = np.array([lane_pts], np.int64)

                cv2.polylines(dst_binary_image, lane_pts, isClosed=False, color=255, thickness=5)
                cv2.polylines(dst_instance_image, lane_pts, isClosed=False,
                              color=lane_index * 50 + 20, thickness=5)

            dst_binary_image_path = binary_dst_dir / image_name_new
            dst_instance_image_path = instance_dst_dir / image_name_new
            dst_rgb_image_path = ori_dst_dir / image_name_new

            if not cv2.imwrite(str(dst_binary_image_path), dst_binary_image):
                raise IOError(f"OpenCV failed to write {dst_binary_image_path}")
            if not cv2.imwrite(str(dst_instance_image_path), dst_instance_image):
                raise IOError(f"OpenCV failed to write {dst_instance_image_path}")
            if not cv2.imwrite(str(dst_rgb_image_path), src_image):
                raise IOError(f"OpenCV failed to write {dst_rgb_image_path}")

            written += 1
            LOG.info("Process %s success -> %s", raw_file, image_name_new)

    return written


def gen_train_sample(src_dir, b_gt_image_dir, i_gt_image_dir, image_dir):
    """
    Generate the LaneNet training index file.
    """
    src_dir = Path(src_dir)
    b_gt_image_dir = Path(b_gt_image_dir)
    i_gt_image_dir = Path(i_gt_image_dir)
    image_dir = Path(image_dir)

    train_file = src_dir / "training" / "train.txt"
    written = 0

    with train_file.open("w", encoding="utf-8") as file:
        for image_name in sorted(os.listdir(b_gt_image_dir)):
            if not image_name.endswith(".png"):
                continue

            binary_gt_image_path = b_gt_image_dir / image_name
            instance_gt_image_path = i_gt_image_dir / image_name
            image_path = image_dir / image_name

            _ensure(image_path.exists(), f"{image_path} not exist")
            _ensure(binary_gt_image_path.exists(), f"{binary_gt_image_path} not exist")
            _ensure(instance_gt_image_path.exists(), f"{instance_gt_image_path} not exist")

            b_gt_image = cv2.imread(str(binary_gt_image_path), cv2.IMREAD_COLOR)
            i_gt_image = cv2.imread(str(instance_gt_image_path), cv2.IMREAD_COLOR)
            image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)

            if b_gt_image is None or image is None or i_gt_image is None:
                LOG.warning("Skip corrupt image pair: %s", image_name)
                continue

            info = f"{image_path} {binary_gt_image_path} {instance_gt_image_path}"
            file.write(info + "\n")
            written += 1

    _ensure(written > 0, f"No usable samples were written into {train_file}")
    LOG.info("Wrote %d rows to %s", written, train_file)
    return written


def process_tusimple_dataset(src_dir):
    """
    Convert a raw TuSimple archive in place.
    """
    src_dir = Path(src_dir).expanduser().resolve()
    _ensure(src_dir.is_dir(), f"{src_dir} is not a directory")

    traing_folder_path = src_dir / "training"
    testing_folder_path = src_dir / "testing"

    traing_folder_path.mkdir(parents=True, exist_ok=True)
    testing_folder_path.mkdir(parents=True, exist_ok=True)

    label_json_paths = sorted(glob.glob(str(src_dir / "label*.json")))
    test_json_paths = sorted(glob.glob(str(src_dir / "test*.json")))
    _ensure(label_json_paths, f"No label*.json files found in {src_dir}")

    for json_label_path in label_json_paths:
        json_label_name = Path(json_label_path).name
        shutil.copyfile(json_label_path, str(traing_folder_path / json_label_name))

    if test_json_paths:
        for json_label_path in test_json_paths:
            json_label_name = Path(json_label_path).name
            shutil.copyfile(json_label_path, str(testing_folder_path / json_label_name))
    else:
        LOG.warning("No test*.json files found under %s", src_dir)

    gt_image_dir = traing_folder_path / "gt_image"
    gt_binary_dir = traing_folder_path / "gt_binary_image"
    gt_instance_dir = traing_folder_path / "gt_instance_image"

    gt_image_dir.mkdir(parents=True, exist_ok=True)
    gt_binary_dir.mkdir(parents=True, exist_ok=True)
    gt_instance_dir.mkdir(parents=True, exist_ok=True)

    total_written = 0
    for json_label_path in sorted(glob.glob(str(traing_folder_path / "*.json"))):
        total_written += process_json_file(json_label_path, src_dir, gt_image_dir, gt_binary_dir, gt_instance_dir)

    _ensure(total_written > 0, f"No lane masks were generated under {traing_folder_path}")
    gen_train_sample(src_dir, gt_binary_dir, gt_instance_dir, gt_image_dir)
    return


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = init_args()
    process_tusimple_dataset(args.src_dir)


if __name__ == "__main__":
    main()
