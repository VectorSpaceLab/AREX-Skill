#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os
import sys

import tensorflow as tf


def _make_label_feature(raw_value, label_type):
  if label_type == "int":
    return tf.train.Feature(
        int64_list=tf.train.Int64List(value=[int(float(raw_value))]))
  return tf.train.Feature(
      float_list=tf.train.FloatList(value=[float(raw_value)]))


def convert_libsvm(input_path, output_path, label_type):
  record_count = 0
  output_dir = os.path.dirname(output_path)
  if output_dir and not os.path.isdir(output_dir):
    os.makedirs(output_dir)

  writer = tf.python_io.TFRecordWriter(output_path)
  try:
    with open(input_path, "r") as handle:
      for line_number, line in enumerate(handle, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
          continue

        tokens = stripped.split()
        if len(tokens) < 2:
          raise ValueError("row {} in {} needs at least one feature token".format(
              line_number, input_path))

        label_raw = tokens[0]
        ids = []
        values = []
        for token in tokens[1:]:
          if token.startswith("#"):
            break
          if ":" not in token:
            raise ValueError("row {} in {} has invalid token {!r}".format(
                line_number, input_path, token))
          feature_id, feature_value = token.split(":", 1)
          ids.append(int(feature_id))
          values.append(float(feature_value))

        example = tf.train.Example(
            features=tf.train.Features(
                feature={
                    "label": _make_label_feature(label_raw, label_type),
                    "ids": tf.train.Feature(
                        int64_list=tf.train.Int64List(value=ids)),
                    "values": tf.train.Feature(
                        float_list=tf.train.FloatList(value=values)),
                }))
        writer.write(example.SerializeToString())
        record_count += 1
  finally:
    writer.close()

  return record_count


def build_parser():
  parser = argparse.ArgumentParser(
      description="Convert a LIBSVM file into sparse TFRecords.")
  parser.add_argument("--input", required=True, help="Input LIBSVM file path.")
  parser.add_argument("--output",
                      required=True,
                      help="Output TFRecords file path.")
  parser.add_argument("--label-type",
                      choices=["int", "float"],
                      default="int",
                      help="How to store the label feature.")
  return parser


def main(argv=None):
  args = build_parser().parse_args(argv)
  try:
    record_count = convert_libsvm(args.input, args.output, args.label_type)
  except (OSError, ValueError) as exc:
    print("Conversion failed: {}".format(exc), file=sys.stderr)
    return 1
  print("Wrote {} records to {}".format(record_count, args.output))
  return 0


if __name__ == "__main__":
  sys.exit(main())
