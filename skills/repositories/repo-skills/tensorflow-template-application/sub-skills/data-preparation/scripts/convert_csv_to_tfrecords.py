#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import csv
import os
import sys

import tensorflow as tf


def _make_label_feature(raw_value, label_type):
  if label_type == "int":
    return tf.train.Feature(
        int64_list=tf.train.Int64List(value=[int(float(raw_value))]))
  return tf.train.Feature(
      float_list=tf.train.FloatList(value=[float(raw_value)]))


def _convert_row(row, label_position, label_type):
  if label_position == "last":
    label_raw = row[-1]
    feature_values = row[:-1]
  else:
    label_raw = row[0]
    feature_values = row[1:]

  features = [float(value) for value in feature_values]
  example = tf.train.Example(
      features=tf.train.Features(
          feature={
              "label": _make_label_feature(label_raw, label_type),
              "features": tf.train.Feature(
                  float_list=tf.train.FloatList(value=features)),
          }))
  return example


def convert_csv(input_path, output_path, label_position, label_type):
  record_count = 0
  output_dir = os.path.dirname(output_path)
  if output_dir and not os.path.isdir(output_dir):
    os.makedirs(output_dir)

  writer = tf.python_io.TFRecordWriter(output_path)
  try:
    with open(input_path, "r", newline="") as handle:
      reader = csv.reader(handle)
      for line_number, row in enumerate(reader, start=1):
        if not row:
          continue
        row = [cell.strip() for cell in row]
        if not row or all(cell == "" for cell in row):
          continue
        if len(row) < 2:
          raise ValueError("row {} in {} needs at least 2 columns".format(
              line_number, input_path))
        try:
          example = _convert_row(row, label_position, label_type)
        except ValueError as exc:
          raise ValueError("failed to parse row {} in {}: {}".format(
              line_number, input_path, exc))
        writer.write(example.SerializeToString())
        record_count += 1
  finally:
    writer.close()

  return record_count


def build_parser():
  parser = argparse.ArgumentParser(
      description="Convert a dense CSV file into TFRecords.")
  parser.add_argument("--input", required=True, help="Input CSV file path.")
  parser.add_argument("--output",
                      required=True,
                      help="Output TFRecords file path.")
  parser.add_argument("--label-position",
                      choices=["first", "last"],
                      default="last",
                      help="Where the label column lives.")
  parser.add_argument("--label-type",
                      choices=["int", "float"],
                      default="int",
                      help="How to store the label feature.")
  return parser


def main(argv=None):
  args = build_parser().parse_args(argv)
  try:
    record_count = convert_csv(args.input, args.output, args.label_position,
                               args.label_type)
  except (OSError, ValueError) as exc:
    print("Conversion failed: {}".format(exc), file=sys.stderr)
    return 1
  print("Wrote {} records to {}".format(record_count, args.output))
  return 0


if __name__ == "__main__":
  sys.exit(main())
