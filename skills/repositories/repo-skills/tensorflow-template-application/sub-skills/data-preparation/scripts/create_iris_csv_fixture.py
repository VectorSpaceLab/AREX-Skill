#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import csv
import os
import random
import sys

from sklearn import datasets


def _format_row(features, label, label_position):
  feature_cells = ["{:g}".format(float(value)) for value in features]
  label_cell = str(int(label))
  if label_position == "last":
    return feature_cells + [label_cell]
  return [label_cell] + feature_cells


def _select_class_rows(target, train_per_class, test_per_class, seed):
  indices_by_class = {}
  for index, label in enumerate(target):
    indices_by_class.setdefault(int(label), []).append(index)

  rng = random.Random(seed)
  train_indices = []
  test_indices = []
  required = train_per_class + test_per_class

  for class_id in sorted(indices_by_class):
    class_indices = list(indices_by_class[class_id])
    rng.shuffle(class_indices)
    if len(class_indices) < required:
      raise ValueError("class {} only has {} samples; need {}".format(
          class_id, len(class_indices), required))
    train_indices.extend(class_indices[:train_per_class])
    test_indices.extend(class_indices[train_per_class:required])

  rng.shuffle(train_indices)
  rng.shuffle(test_indices)
  return train_indices, test_indices


def _write_rows(path, data, target, indices, label_position):
  with open(path, "w", newline="") as handle:
    writer = csv.writer(handle)
    for index in indices:
      writer.writerow(_format_row(data[index], target[index], label_position))


def create_fixture(output_dir, train_per_class, test_per_class, seed,
                   label_position):
  iris = datasets.load_iris()
  train_indices, test_indices = _select_class_rows(iris.target, train_per_class,
                                                   test_per_class, seed)

  if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

  train_path = os.path.join(output_dir, "iris_train.csv")
  test_path = os.path.join(output_dir, "iris_test.csv")
  _write_rows(train_path, iris.data, iris.target, train_indices,
              label_position)
  _write_rows(test_path, iris.data, iris.target, test_indices,
              label_position)
  return train_path, test_path, len(train_indices), len(test_indices)


def build_parser():
  parser = argparse.ArgumentParser(
      description="Create a tiny deterministic iris CSV fixture from sklearn.")
  parser.add_argument("--output-dir",
                      required=True,
                      help="Directory that will receive iris_train.csv and iris_test.csv.")
  parser.add_argument("--train-per-class",
                      type=int,
                      default=2,
                      help="Training rows to keep from each iris class.")
  parser.add_argument("--test-per-class",
                      type=int,
                      default=1,
                      help="Test rows to keep from each iris class.")
  parser.add_argument("--seed",
                      type=int,
                      default=13,
                      help="Deterministic shuffle seed.")
  parser.add_argument("--label-position",
                      choices=["first", "last"],
                      default="last",
                      help="Where to write the label column.")
  return parser


def main(argv=None):
  parser = build_parser()
  args = parser.parse_args(argv)
  if args.train_per_class < 1 or args.test_per_class < 1:
    parser.error("train-per-class and test-per-class must both be positive")

  try:
    train_path, test_path, train_rows, test_rows = create_fixture(
        args.output_dir, args.train_per_class, args.test_per_class, args.seed,
        args.label_position)
  except (OSError, ValueError) as exc:
    print("Fixture generation failed: {}".format(exc), file=sys.stderr)
    return 1
  print("Wrote {} rows to {}".format(train_rows, train_path))
  print("Wrote {} rows to {}".format(test_rows, test_path))
  return 0


if __name__ == "__main__":
  sys.exit(main())
