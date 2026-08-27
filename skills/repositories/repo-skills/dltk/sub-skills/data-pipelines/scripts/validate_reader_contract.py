#!/usr/bin/env python3
"""Validate a small DLTK-style nested Reader contract without TensorFlow.

The legacy Reader delegates dtype/shape enforcement to TensorFlow 1.x. This
bounded checker catches the same structural mistakes early and exercises a
PREDICT-only branch plus synchronized multimodal synthetic data. It performs no
I/O and does not import repository files.
"""
from __future__ import print_function

import argparse
import sys

import numpy as np


class ContractError(ValueError):
    pass


def clean_to_spec(value, spec, path="root"):
    """Model the legacy recursive dict cleanup and reject structural errors."""
    if isinstance(spec, dict):
        if not isinstance(value, dict):
            raise ContractError("{} must be a dictionary".format(path))
        value = dict(value)
        for key in list(value):
            if key not in spec:
                del value[key]
        for key, child_spec in spec.items():
            if key not in value:
                raise ContractError("missing {}".format(path + "." + key))
            value[key] = clean_to_spec(value[key], child_spec,
                                       path + "." + key)
        return value

    # A dtype leaf must describe a TensorFlow-visible scalar/array, not another
    # mapping or a Python list structure that the declared tree does not have.
    if isinstance(value, (dict, list, tuple)):
        raise ContractError("{} has a dict/list where a dtype leaf is expected"
                            .format(path))
    return value


def check_shape(value, expected, path):
    actual = np.asarray(value).shape
    expected = tuple(expected)
    if len(actual) != len(expected):
        raise ContractError("{} has shape {}, expected {}".format(
            path, actual, expected))
    for index, (got, want) in enumerate(zip(actual, expected)):
        if want is not None and got != want:
            raise ContractError(
                "{} dimension {} is {}, expected {}".format(
                    path, index, got, want))


def check_dtype(value, dtype_name, path):
    actual = np.asarray(value).dtype
    wanted = np.dtype(dtype_name)
    if actual != wanted:
        raise ContractError("{} has dtype {}, expected {}".format(
            path, actual, wanted))


def validate_leaf_contract(value, dtype_spec, shape_spec, path="root"):
    if isinstance(dtype_spec, dict):
        for key in dtype_spec:
            validate_leaf_contract(value[key], dtype_spec[key],
                                   shape_spec[key], path + "." + key)
        return
    check_dtype(value, dtype_spec, path)
    check_shape(value, shape_spec, path)


def valid_case():
    dtypes = {
        "features": {"x": "float32"},
        "labels": {"y": "int32"},
    }
    shapes = {
        "features": {"x": [4, 5, 6, 2]},
        "labels": {"y": []},
    }
    image = np.zeros((4, 5, 6, 2), dtype=np.float32)
    label = np.int32(1)
    record = {
        "features": {"x": image},
        "labels": {"y": label},
        "metadata": {"subject_id": "synthetic"},
    }
    cleaned = clean_to_spec(record, dtypes)
    if "metadata" in cleaned:
        raise ContractError("undeclared metadata was not removed")
    validate_leaf_contract(cleaned, dtypes, shapes)


def malformed_case():
    dtypes = {"features": {"x": {"channel": "float32"}}}
    shapes = {"features": {"x": {"channel": []}}}
    record = {"features": {"x": np.zeros((2, 2), dtype=np.float32)}}
    try:
        clean_to_spec(record, dtypes)
    except ContractError:
        return
    raise ContractError("malformed nested dtype map was accepted")


def predict_case():
    def reader(file_references, mode, params=None):
        for subject_id in file_references:
            image = np.zeros((2, 3, 4, 1), dtype=np.float32)
            if mode == "PREDICT":
                # The real reader must return here/continue before label or
                # params access. This branch intentionally accepts params=None.
                yield {"features": {"x": image}, "subject_id": subject_id}
                continue
            yield {"features": {"x": image},
                   "labels": {"y": np.int32(0)}}

    records = list(reader(["synthetic-1"], "PREDICT", params=None))
    if len(records) != 1 or "labels" in records[0]:
        raise ContractError("PREDICT did not emit exactly one feature record")


def multimodal_case():
    label = (np.arange(4 * 5 * 6).reshape(4, 5, 6) % 2).astype(np.int32)
    image = np.stack([label, label + 100], axis=-1).astype(np.float32)
    patch = (slice(1, 3), slice(1, 4), slice(0, 4))
    image_patch = image[patch + (slice(None),)]
    label_patch = label[patch]
    if image_patch.shape != (2, 3, 4, 2):
        raise ContractError("multimodal patch has the wrong image shape")
    if label_patch.shape != (2, 3, 4):
        raise ContractError("multimodal patch has the wrong label shape")

    # One spatial decision must be shared by every modality and the label.
    flipped_image = np.flip(image_patch, axis=1)
    flipped_label = np.flip(label_patch, axis=1)
    if not np.array_equal(flipped_image[..., 0].astype(np.int32),
                          flipped_label):
        raise ContractError("image and label lost spatial synchronization")
    classes, counts = np.unique(label_patch, return_counts=True)
    if set(classes.tolist()) != {0, 1} or np.min(counts) == 0:
        raise ContractError("synthetic patch does not contain both classes")


def run(case):
    cases = {
        "valid": valid_case,
        "malformed": malformed_case,
        "predict": predict_case,
        "multimodal": multimodal_case,
    }
    selected = list(cases) if case == "all" else [case]
    for name in selected:
        cases[name]()
        print("reader contract case passed: {}".format(name))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run bounded synthetic DLTK Reader contract checks.")
    parser.add_argument("--case", choices=["all", "valid", "malformed",
                                            "predict", "multimodal"],
                        default="all",
                        help="run one fixture or all fixtures (default: all)")
    args = parser.parse_args(argv)
    try:
        return run(args.case)
    except (AssertionError, ContractError, KeyError, TypeError) as exc:
        print("reader contract validation failed: {}".format(exc),
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
