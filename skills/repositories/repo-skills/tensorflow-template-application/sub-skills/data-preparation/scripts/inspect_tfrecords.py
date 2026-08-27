#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import sys

import tensorflow as tf


class SchemaMismatch(RuntimeError):
  pass


def _value_list(feature):
  if feature.int64_list.value:
    return "int64", list(feature.int64_list.value)
  if feature.float_list.value:
    return "float", list(feature.float_list.value)
  if feature.bytes_list.value:
    return "bytes", list(feature.bytes_list.value)
  return "empty", []


def _require_feature(feature_map, name):
  if name not in feature_map:
    raise SchemaMismatch("missing required field {!r}".format(name))
  return feature_map[name]


def _inspect_dense(example, feature_size=None):
  feature_map = example.features.feature
  label_kind, label_values = _value_list(_require_feature(feature_map, "label"))
  if not label_values:
    raise SchemaMismatch("field 'label' is empty")

  features_feature = _require_feature(feature_map, "features")
  feature_kind, features = _value_list(features_feature)
  if feature_kind != "float":
    raise SchemaMismatch("field 'features' must be a float list")

  unexpected = [name for name in ("ids", "values") if name in feature_map]
  if unexpected:
    raise SchemaMismatch("dense schema saw sparse fields: {}".format(
        ", ".join(sorted(unexpected))))

  if feature_size is not None and len(features) != feature_size:
    raise SchemaMismatch("dense feature length {} does not match expected {}".format(
        len(features), feature_size))

  return "label({})={} features(len={})={}".format(label_kind, label_values,
                                                   len(features), features)


def _inspect_sparse(example, feature_size=None):
  feature_map = example.features.feature
  label_kind, label_values = _value_list(_require_feature(feature_map, "label"))
  if not label_values:
    raise SchemaMismatch("field 'label' is empty")

  ids_feature = _require_feature(feature_map, "ids")
  values_feature = _require_feature(feature_map, "values")
  ids_kind, ids = _value_list(ids_feature)
  values_kind, values = _value_list(values_feature)
  if ids_kind != "int64":
    raise SchemaMismatch("field 'ids' must be an int64 list")
  if values_kind != "float":
    raise SchemaMismatch("field 'values' must be a float list")
  if len(ids) != len(values):
    raise SchemaMismatch("ids/value length mismatch: {} vs {}".format(
        len(ids), len(values)))

  if feature_size is not None:
    bad_ids = [feature_id for feature_id in ids
               if feature_id < 0 or feature_id >= feature_size]
    if bad_ids:
      raise SchemaMismatch("ids outside expected feature_size {}: {}".format(
          feature_size, bad_ids))

  unexpected = [name for name in ("features",) if name in feature_map]
  if unexpected:
    raise SchemaMismatch("sparse schema saw dense fields: {}".format(
        ", ".join(sorted(unexpected))))

  return "label({})={} ids(len={})={} values(len={})={}".format(
      label_kind, label_values, len(ids), ids, len(values), values)


def inspect_tfrecords(input_path, schema, max_records, feature_size=None):
  record_count = 0
  for serialized_example in tf.python_io.tf_record_iterator(input_path):
    example = tf.train.Example()
    example.ParseFromString(serialized_example)
    if schema == "dense":
      summary = _inspect_dense(example, feature_size)
    else:
      summary = _inspect_sparse(example, feature_size)
    print("Record {}: {}".format(record_count, summary))
    record_count += 1
    if record_count >= max_records:
      break

  if record_count == 0:
    raise RuntimeError("no TFRecords found in {}".format(input_path))

  return record_count


def build_parser():
  parser = argparse.ArgumentParser(
      description="Inspect a TFRecord file using a dense or sparse schema.")
  parser.add_argument("--input", required=True, help="Input TFRecords file.")
  parser.add_argument("--schema",
                      required=True,
                      choices=["dense", "sparse"],
                      help="Expected TFExample schema.")
  parser.add_argument("--max-records",
                      type=int,
                      default=10,
                      help="Maximum number of records to print.")
  parser.add_argument("--feature-size",
                      type=int,
                      default=None,
                      help="Optional expected dense width or sparse id bound.")
  return parser


def main(argv=None):
  args = build_parser().parse_args(argv)
  try:
    record_count = inspect_tfrecords(args.input, args.schema, args.max_records,
                                     args.feature_size)
  except (SchemaMismatch, RuntimeError, ValueError) as exc:
    print("Schema mismatch: {}".format(exc), file=sys.stderr)
    return 1

  print("Inspected {} records from {}".format(record_count, args.input))
  return 0


if __name__ == "__main__":
  sys.exit(main())
