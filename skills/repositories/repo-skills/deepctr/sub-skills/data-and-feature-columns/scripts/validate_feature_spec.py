#!/usr/bin/env python3
"""Validate a JSON description of DeepCTR feature columns.

The validator is intentionally standalone: it imports only the Python standard
library and does not import TensorFlow, DeepCTR, or the original source tree. It
catches common schema mistakes before a future agent builds real
``SparseFeat``, ``DenseFeat``, and ``VarLenSparseFeat`` objects.

Spec shape, abbreviated::

  {
    "features": [
      {"type": "SparseFeat", "name": "item_id", "vocabulary_size": 1001},
      {"type": "DenseFeat", "name": "price", "dimension": 1},
      {
        "type": "VarLenSparseFeat",
        "name": "hist_item_id",
        "maxlen": 4,
        "length_name": "seq_length",
        "valid_id_min": 1,
        "sparsefeat": {
          "name": "hist_item_id",
          "vocabulary_size": 1001,
          "embedding_dim": 8,
          "embedding_name": "item_id"
        }
      }
    ],
    "input_keys": ["item_id", "price", "hist_item_id", "seq_length"]
  }

Useful commands::

  python validate_feature_spec.py --emit-example movielens-varlen > spec.json
  python validate_feature_spec.py spec.json
  python validate_feature_spec.py spec.json --check-paths --json
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

VALID_TYPES = {"SparseFeat", "DenseFeat", "VarLenSparseFeat"}
TYPE_ALIASES = {
    "sparse": "SparseFeat",
    "sparsefeat": "SparseFeat",
    "SparseFeat": "SparseFeat",
    "dense": "DenseFeat",
    "densefeat": "DenseFeat",
    "DenseFeat": "DenseFeat",
    "varlen": "VarLenSparseFeat",
    "varlen_sparse": "VarLenSparseFeat",
    "varlensparsefeat": "VarLenSparseFeat",
    "VarLenSparseFeat": "VarLenSparseFeat",
}
VALID_COMBINERS = {"sum", "mean", "max"}
STRING_DTYPES = {"string", "str", "tf.string", "tensorflow.string"}


EXAMPLES: dict[str, dict[str, Any]] = {
    "basic": {
        "features": [
            {"type": "SparseFeat", "name": "user_id", "vocabulary_size": 1001, "embedding_dim": 8},
            {"type": "SparseFeat", "name": "item_id", "vocabulary_size": 5001, "embedding_dim": 8},
            {"type": "DenseFeat", "name": "pay_score", "dimension": 1},
        ],
        "input_keys": ["user_id", "item_id", "pay_score"],
    },
    "criteo-hash": {
        "features": [
            {
                "type": "SparseFeat",
                "name": "C1",
                "vocabulary_size": 100000,
                "embedding_dim": 4,
                "use_hash": True,
                "dtype": "string",
            },
            {
                "type": "SparseFeat",
                "name": "C2",
                "vocabulary_size": 100000,
                "embedding_dim": 4,
                "use_hash": True,
                "dtype": "string",
            },
            {"type": "DenseFeat", "name": "I1", "dimension": 1},
            {"type": "DenseFeat", "name": "I2", "dimension": 1},
        ],
        "input_shapes": {"C1": ["batch"], "C2": ["batch"], "I1": ["batch", 1], "I2": ["batch", 1]},
    },
    "movielens-varlen": {
        "features": [
            {"type": "SparseFeat", "name": "movie_id", "vocabulary_size": 4001, "embedding_dim": 4},
            {"type": "SparseFeat", "name": "user_id", "vocabulary_size": 6101, "embedding_dim": 4},
            {
                "type": "VarLenSparseFeat",
                "name": "genres",
                "maxlen": 5,
                "combiner": "mean",
                "valid_id_min": 1,
                "padding_value": 0,
                "sparsefeat": {"name": "genres", "vocabulary_size": 19, "embedding_dim": 4},
            },
        ],
        "input_shapes": {"movie_id": ["batch"], "user_id": ["batch"], "genres": ["batch", 5]},
    },
    "din-history": {
        "features": [
            {"type": "SparseFeat", "name": "item_id", "vocabulary_size": 1001, "embedding_dim": 8},
            {"type": "SparseFeat", "name": "cate_id", "vocabulary_size": 101, "embedding_dim": 4},
            {
                "type": "VarLenSparseFeat",
                "name": "hist_item_id",
                "maxlen": 50,
                "length_name": "seq_length",
                "valid_id_min": 1,
                "sparsefeat": {
                    "name": "hist_item_id",
                    "vocabulary_size": 1001,
                    "embedding_dim": 8,
                    "embedding_name": "item_id",
                },
            },
            {
                "type": "VarLenSparseFeat",
                "name": "hist_cate_id",
                "maxlen": 50,
                "length_name": "seq_length",
                "valid_id_min": 1,
                "sparsefeat": {
                    "name": "hist_cate_id",
                    "vocabulary_size": 101,
                    "embedding_dim": 4,
                    "embedding_name": "cate_id",
                },
            },
        ],
        "expected_feature_names": ["item_id", "cate_id", "hist_item_id", "seq_length", "hist_cate_id"],
    },
    "dsin-session": {
        "features": [
            {"type": "SparseFeat", "name": "item", "vocabulary_size": 1001, "embedding_dim": 4},
            {"type": "SparseFeat", "name": "cate_id", "vocabulary_size": 101, "embedding_dim": 4},
            {
                "type": "VarLenSparseFeat",
                "name": "sess_0_item",
                "maxlen": 4,
                "valid_id_min": 1,
                "sparsefeat": {
                    "name": "sess_0_item",
                    "vocabulary_size": 1001,
                    "embedding_dim": 4,
                    "embedding_name": "item",
                },
            },
            {
                "type": "VarLenSparseFeat",
                "name": "sess_0_cate_id",
                "maxlen": 4,
                "valid_id_min": 1,
                "sparsefeat": {
                    "name": "sess_0_cate_id",
                    "vocabulary_size": 101,
                    "embedding_dim": 4,
                    "embedding_name": "cate_id",
                },
            },
            {
                "type": "VarLenSparseFeat",
                "name": "sess_1_item",
                "maxlen": 4,
                "valid_id_min": 1,
                "sparsefeat": {
                    "name": "sess_1_item",
                    "vocabulary_size": 1001,
                    "embedding_dim": 4,
                    "embedding_name": "item",
                },
            },
            {
                "type": "VarLenSparseFeat",
                "name": "sess_1_cate_id",
                "maxlen": 4,
                "valid_id_min": 1,
                "sparsefeat": {
                    "name": "sess_1_cate_id",
                    "vocabulary_size": 101,
                    "embedding_dim": 4,
                    "embedding_name": "cate_id",
                },
            },
        ],
        "additional_inputs": [{"name": "sess_length", "shape": ["batch"], "dtype": "int32"}],
        "input_keys": [
            "item",
            "cate_id",
            "sess_0_item",
            "sess_0_cate_id",
            "sess_1_item",
            "sess_1_cate_id",
            "sess_length",
        ],
    },
    "bad-shared-embedding": {
        "features": [
            {"type": "SparseFeat", "name": "item_id", "vocabulary_size": 1001, "embedding_dim": 8},
            {
                "type": "VarLenSparseFeat",
                "name": "hist_item_id",
                "maxlen": 4,
                "sparsefeat": {
                    "name": "hist_item_id",
                    "vocabulary_size": 1002,
                    "embedding_dim": 8,
                    "embedding_name": "item_id",
                },
            },
        ]
    },
    "bad-padding": {
        "features": [
            {
                "type": "VarLenSparseFeat",
                "name": "genres",
                "maxlen": 5,
                "valid_id_min": 0,
                "sparsefeat": {"name": "genres", "vocabulary_size": 18, "embedding_dim": 4},
            }
        ]
    },
}


@dataclass
class Issue:
    level: str
    path: str
    message: str
    advice: str | None = None

    def as_dict(self) -> dict[str, str]:
        result = {"level": self.level, "path": self.path, "message": self.message}
        if self.advice:
            result["advice"] = self.advice
        return result


@dataclass
class ExpectedInput:
    name: str
    kind: str
    suffixes: list[list[int]]
    path: str


class Validator:
    def __init__(self, *, check_paths: bool = False) -> None:
        self.check_paths = check_paths
        self.issues: list[Issue] = []
        self.shared_embeddings: dict[str, dict[str, Any]] = {}
        self.feature_names: list[str] = []
        self.expected_inputs: dict[str, ExpectedInput] = {}
        self.main_feature_names: set[str] = set()
        self.additional_inputs: set[str] = set()

    def error(self, path: str, message: str, advice: str | None = None) -> None:
        self.issues.append(Issue("error", path, message, advice))

    def warning(self, path: str, message: str, advice: str | None = None) -> None:
        self.issues.append(Issue("warning", path, message, advice))

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(data, dict):
            self.error("$", "spec must be a JSON object")
            return self.result()

        features = data.get("features")
        if not isinstance(features, list) or not features:
            self.error("features", "top-level 'features' must be a non-empty list")
            return self.result()

        labels = data.get("labels", data.get("label_names", []))
        label_names = {labels} if isinstance(labels, str) else set(labels if isinstance(labels, list) else [])

        for idx, spec in enumerate(features):
            self._check_feature(spec, f"features[{idx}]", label_names)

        self._check_additional_inputs(data.get("additional_inputs"))
        self._check_expected_feature_names(data.get("expected_feature_names"))
        self._check_input_keys(data.get("input_keys"))
        self._check_input_shapes(data.get("input_shapes", data.get("inputs")))
        return self.result()

    def result(self) -> dict[str, Any]:
        errors = [i.as_dict() for i in self.issues if i.level == "error"]
        warnings = [i.as_dict() for i in self.issues if i.level == "warning"]
        return {
            "ok": not errors,
            "feature_names": self.feature_names,
            "required_input_keys": list(self.expected_inputs),
            "shared_embeddings": self.shared_embeddings,
            "errors": errors,
            "warnings": warnings,
        }

    def _check_feature(self, spec: Any, path: str, label_names: set[Any]) -> None:
        if not isinstance(spec, dict):
            self.error(path, "feature entry must be an object")
            return
        ftype = canonical_type(spec.get("type"))
        if ftype not in VALID_TYPES:
            self.error(path + ".type", f"type must be one of {sorted(VALID_TYPES)}")
            return
        if ftype == "SparseFeat":
            name = self._check_sparse(spec, path)
            if name:
                self._add_main_feature_name(name, path, label_names)
                self._add_feature_name(name)
                self._add_expected_input(name, "SparseFeat", [[], [1]], path)
        elif ftype == "DenseFeat":
            name, dim = self._check_dense(spec, path)
            if name:
                self._add_main_feature_name(name, path, label_names)
                self._add_feature_name(name)
                suffixes = [[], [1]] if dim == 1 else [[dim]]
                self._add_expected_input(name, "DenseFeat", suffixes, path)
        elif ftype == "VarLenSparseFeat":
            self._check_varlen(spec, path, label_names)

    def _add_main_feature_name(self, name: str, path: str, label_names: set[Any]) -> None:
        if name in label_names:
            self.error(path + ".name", f"feature name '{name}' is also listed as a label", "Keep labels outside DeepCTR feature columns.")
        if name in self.main_feature_names:
            self.error(path + ".name", f"duplicate feature name '{name}'", "Describe each unique DeepCTR input feature once in this spec.")
        self.main_feature_names.add(name)

    def _add_feature_name(self, name: str) -> None:
        if name not in self.feature_names:
            self.feature_names.append(name)

    def _add_expected_input(self, name: str, kind: str, suffixes: list[list[int]], path: str) -> None:
        if name in self.expected_inputs:
            old = self.expected_inputs[name]
            if old.suffixes != suffixes:
                self.error(path, f"input key '{name}' has conflicting expected shapes from {old.kind} and {kind}")
            return
        self.expected_inputs[name] = ExpectedInput(name=name, kind=kind, suffixes=suffixes, path=path)

    def _check_sparse(self, spec: dict[str, Any], path: str) -> str | None:
        name = self._name(spec, path)
        vocab = self._positive_int(spec.get("vocabulary_size"), path + ".vocabulary_size")
        emb_raw = spec.get("embedding_dim", 4)
        emb_dim = self._embedding_dim(emb_raw, vocab, path + ".embedding_dim")

        use_hash = spec.get("use_hash", False)
        if not isinstance(use_hash, bool):
            self.error(path + ".use_hash", "use_hash must be a boolean")
            use_hash = False

        dtype = str(spec.get("dtype", "int32")).lower()
        if dtype in STRING_DTYPES and use_hash is not True:
            self.error(
                path + ".dtype",
                "string SparseFeat inputs require use_hash=true",
                "Set use_hash=true for raw string ids, or pre-encode values to integer ids and use an integer dtype.",
            )

        vocab_path = spec.get("vocabulary_path")
        if vocab_path is not None:
            if not isinstance(vocab_path, str) or not vocab_path:
                self.error(path + ".vocabulary_path", "vocabulary_path must be a non-empty string when set")
            if use_hash is not True:
                self.error(
                    path + ".vocabulary_path",
                    "vocabulary_path is only used by DeepCTR's Hash lookup path when use_hash=true",
                    "Set use_hash=true and dtype='string', or remove vocabulary_path.",
                )
            if isinstance(vocab_path, str) and self.check_paths:
                self._check_vocabulary_file(vocab_path, path + ".vocabulary_path")

        group_name = spec.get("group_name", "default_group")
        if not isinstance(group_name, str) or not group_name:
            self.error(path + ".group_name", "group_name must be a non-empty string when set")

        trainable = spec.get("trainable", True)
        if not isinstance(trainable, bool):
            self.error(path + ".trainable", "trainable must be a boolean")
            trainable = True

        if name and vocab is not None and emb_dim is not None:
            key = str(spec.get("embedding_name") or name)
            current = {"vocabulary_size": vocab, "embedding_dim": emb_dim, "trainable": trainable}
            previous = self.shared_embeddings.get(key)
            if previous is not None and previous != current:
                diffs = ", ".join(
                    f"{k}: {previous[k]!r} vs {current[k]!r}" for k in current if previous.get(k) != current.get(k)
                )
                self.error(
                    path + ".embedding_name",
                    f"embedding_name '{key}' is shared with incompatible settings ({diffs})",
                    "Use the same vocabulary_size, embedding_dim, and trainable values for shared embeddings, or choose a different embedding_name.",
                )
            else:
                self.shared_embeddings.setdefault(key, current)

        max_id = self._optional_int(spec.get("max_id"), path + ".max_id")
        if max_id is not None and vocab is not None and max_id >= vocab:
            self.error(
                path + ".max_id",
                f"max_id {max_id} is outside vocabulary_size {vocab}",
                "Set vocabulary_size to at least max_id + 1.",
            )
        return name

    def _check_dense(self, spec: dict[str, Any], path: str) -> tuple[str | None, int]:
        name = self._name(spec, path)
        dim = self._positive_int(spec.get("dimension", 1), path + ".dimension") or 1
        dtype = str(spec.get("dtype", "float32")).lower()
        if dtype in STRING_DTYPES:
            self.error(path + ".dtype", "DenseFeat should not use a string dtype", "Use DenseFeat for numeric tensors only.")
        return name, dim

    def _check_varlen(self, spec: dict[str, Any], path: str, label_names: set[Any]) -> None:
        sparse = spec.get("sparsefeat")
        if sparse is None:
            sparse = {
                key: spec[key]
                for key in (
                    "name",
                    "vocabulary_size",
                    "embedding_dim",
                    "use_hash",
                    "vocabulary_path",
                    "dtype",
                    "embedding_name",
                    "group_name",
                    "trainable",
                    "max_id",
                )
                if key in spec
            }
        if not isinstance(sparse, dict):
            self.error(path + ".sparsefeat", "VarLenSparseFeat must include a nested sparsefeat object or sparse fields")
            return

        wrapper_name = spec.get("name")
        sparse_name = sparse.get("name")
        if wrapper_name is not None and sparse_name is not None and wrapper_name != sparse_name:
            self.error(path + ".name", "VarLenSparseFeat name should match sparsefeat.name", "DeepCTR exposes VarLenSparseFeat.name as the wrapped SparseFeat name.")
        name = str(wrapper_name or sparse_name) if (wrapper_name or sparse_name) else None

        maxlen = self._positive_int(spec.get("maxlen"), path + ".maxlen")
        combiner = spec.get("combiner", "mean")
        if combiner not in VALID_COMBINERS:
            self.error(path + ".combiner", f"combiner must be one of {sorted(VALID_COMBINERS)}")

        if name:
            self._add_main_feature_name(name, path, label_names)
        sparse_checked_name = self._check_sparse(sparse, path + ".sparsefeat")
        if name and sparse_checked_name and name != sparse_checked_name:
            self.error(path + ".sparsefeat.name", "wrapped SparseFeat name must match the VarLenSparseFeat input name")

        if name and maxlen is not None:
            self._add_feature_name(name)
            self._add_expected_input(name, "VarLenSparseFeat", [[maxlen]], path)

        padding_value = spec.get("padding_value", 0)
        if padding_value != 0:
            self.error(path + ".padding_value", "DeepCTR variable-length sparse features should use 0 as padding")

        valid_min = spec.get("valid_id_min")
        if valid_min is not None:
            valid_min_int = self._optional_int(valid_min, path + ".valid_id_min")
            if valid_min_int is not None and valid_min_int <= 0:
                self.error(
                    path + ".valid_id_min",
                    "valid ids for padded VarLenSparseFeat should start at 1",
                    "Shift valid categorical ids by +1 and reserve 0 for padding.",
                )
        for flag in ("uses_zero_as_valid_id", "zero_is_valid_id", "allow_zero_id"):
            if spec.get(flag) is True:
                self.error(
                    path + "." + flag,
                    "0 cannot safely be a real id in a padded VarLenSparseFeat",
                    "Reserve 0 for padding; remap real ids to start at 1.",
                )

        self._check_example_values(spec.get("example_values"), maxlen, path + ".example_values")

        weight_name = spec.get("weight_name")
        if weight_name is not None:
            if not isinstance(weight_name, str) or not weight_name:
                self.error(path + ".weight_name", "weight_name must be a non-empty string when set")
            elif maxlen is not None:
                if weight_name == name:
                    self.error(path + ".weight_name", "weight_name must not equal the sequence feature name")
                self._add_feature_name(weight_name)
                self._add_expected_input(weight_name, "VarLenSparseFeat.weight", [[maxlen, 1]], path)

        length_name = spec.get("length_name")
        if length_name is not None:
            if not isinstance(length_name, str) or not length_name:
                self.error(path + ".length_name", "length_name must be a non-empty string when set")
            else:
                if length_name == name:
                    self.error(path + ".length_name", "length_name must not equal the sequence feature name")
                self._add_feature_name(length_name)
                self._add_expected_input(length_name, "VarLenSparseFeat.length", [[], [1]], path)

        weight_norm = spec.get("weight_norm", True)
        if not isinstance(weight_norm, bool):
            self.error(path + ".weight_norm", "weight_norm must be a boolean")

    def _check_additional_inputs(self, additional: Any) -> None:
        if additional is None:
            return
        if not isinstance(additional, list):
            self.error("additional_inputs", "additional_inputs must be a list when provided")
            return
        for idx, item in enumerate(additional):
            path = f"additional_inputs[{idx}]"
            if not isinstance(item, dict):
                self.error(path, "additional input must be an object")
                continue
            name = self._name(item, path)
            if not name:
                continue
            self.additional_inputs.add(name)
            shape = shape_from_value(item)
            suffixes = suffixes_from_shape(shape) if shape is not None else [[], [1]]
            self._add_expected_input(name, "additional_input", suffixes, path)

    def _check_expected_feature_names(self, expected: Any) -> None:
        if expected is None:
            return
        if not isinstance(expected, list) or not all(isinstance(x, str) for x in expected):
            self.error("expected_feature_names", "expected_feature_names must be a list of strings")
            return
        if expected != self.feature_names:
            self.error(
                "expected_feature_names",
                f"expected_feature_names does not match DeepCTR get_feature_names order; expected {self.feature_names!r}",
            )

    def _check_input_keys(self, input_keys: Any) -> None:
        if input_keys is None:
            return
        if not isinstance(input_keys, list) or not all(isinstance(x, str) for x in input_keys):
            self.error("input_keys", "input_keys must be a list of strings")
            return
        expected = set(self.expected_inputs)
        actual = set(input_keys)
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing:
            self.error("input_keys", f"missing required model input keys: {missing}")
        if extra:
            self.warning("input_keys", f"extra input keys not produced by feature columns/additional_inputs: {extra}")

    def _check_input_shapes(self, inputs: Any) -> None:
        if inputs is None:
            return
        if not isinstance(inputs, dict):
            self.error("input_shapes", "input_shapes/inputs must be an object mapping names to shapes")
            return
        for name, expected in self.expected_inputs.items():
            if name not in inputs:
                self.error("input_shapes", f"missing shape for required model input '{name}'")
                continue
            shape = shape_from_value(inputs[name])
            if shape is None:
                self.error(f"input_shapes.{name}", "shape must be a list, or an object with a shape list")
                continue
            if not shape_matches(shape, expected.suffixes):
                self.error(
                    f"input_shapes.{name}",
                    f"shape {shape!r} does not match expected {expected.kind} suffixes {expected.suffixes!r}",
                    "Use full array shapes such as ['batch', maxlen] or per-sample shapes such as [maxlen].",
                )
        extra = sorted(set(inputs) - set(self.expected_inputs))
        if extra:
            self.warning("input_shapes", f"extra input shapes not produced by feature columns/additional_inputs: {extra}")

    def _check_example_values(self, values: Any, maxlen: int | None, path: str) -> None:
        if values is None:
            return
        if maxlen is None:
            return
        if not isinstance(values, list):
            self.error(path, "example_values must be a list of padded rows")
            return
        for row_idx, row in enumerate(values[:20]):
            if not isinstance(row, list):
                self.error(f"{path}[{row_idx}]", "each example row must be a list")
                continue
            if len(row) != maxlen:
                self.error(
                    f"{path}[{row_idx}]",
                    f"row length {len(row)} does not equal maxlen {maxlen}",
                    "Pass padded arrays of shape (batch_size, maxlen) to DeepCTR.",
                )

    def _check_vocabulary_file(self, raw_path: str, path: str) -> None:
        file_path = Path(raw_path).expanduser()
        if not file_path.exists():
            self.error(path, f"vocabulary file does not exist: {raw_path}")
            return
        if not file_path.is_file():
            self.error(path, f"vocabulary path is not a file: {raw_path}")
            return
        try:
            with file_path.open(newline="") as handle:
                reader = csv.reader(handle)
                saw_row = False
                for line_no, row in zip(range(1, 11), reader):
                    if not row or all(not cell.strip() for cell in row):
                        continue
                    saw_row = True
                    if len(row) < 2:
                        self.error(path, f"vocabulary row {line_no} must have at least two comma-separated columns: id,key")
                        continue
                    try:
                        value = int(row[0])
                    except ValueError:
                        self.error(path, f"vocabulary row {line_no} first column must be an integer id")
                        continue
                    if value == 0:
                        self.warning(path, f"vocabulary row {line_no} maps a key to 0", "Reserve 0 for missing/padding unless this is intentional unknown handling.")
                if not saw_row:
                    self.error(path, "vocabulary file is empty")
        except OSError as exc:
            self.error(path, f"could not read vocabulary file: {exc}")

    def _name(self, spec: dict[str, Any], path: str) -> str | None:
        name = spec.get("name")
        if not isinstance(name, str) or not name:
            self.error(path + ".name", "name must be a non-empty string")
            return None
        return name

    def _positive_int(self, value: Any, path: str) -> int | None:
        parsed = self._optional_int(value, path)
        if parsed is None:
            self.error(path, "must be a positive integer")
            return None
        if parsed <= 0:
            self.error(path, "must be greater than 0")
            return None
        return parsed

    def _optional_int(self, value: Any, path: str) -> int | None:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float) and math.isfinite(value) and value.is_integer():
            return int(value)
        self.error(path, "must be an integer value")
        return None

    def _embedding_dim(self, value: Any, vocab: int | None, path: str) -> int | None:
        if value == "auto":
            if vocab is None:
                self.error(path, "embedding_dim='auto' requires a valid vocabulary_size")
                return None
            return 6 * int(pow(vocab, 0.25))
        return self._positive_int(value, path)


def canonical_type(raw: Any) -> str | None:
    if raw in TYPE_ALIASES:
        return TYPE_ALIASES[raw]
    if isinstance(raw, str):
        return TYPE_ALIASES.get(raw.lower())
    return None


def shape_from_value(value: Any) -> list[Any] | None:
    if isinstance(value, list):
        return value
    if isinstance(value, dict) and isinstance(value.get("shape"), list):
        return value["shape"]
    return None


def dim_eq(actual: Any, expected: int) -> bool:
    if isinstance(actual, bool):
        return False
    if isinstance(actual, int):
        return actual == expected
    if isinstance(actual, float) and actual.is_integer():
        return int(actual) == expected
    return False


def suffix_matches(actual_suffix: Iterable[Any], expected_suffix: list[int]) -> bool:
    actual = list(actual_suffix)
    if len(actual) != len(expected_suffix):
        return False
    return all(dim_eq(a, e) for a, e in zip(actual, expected_suffix))


def shape_matches(shape: list[Any], expected_suffixes: list[list[int]]) -> bool:
    # Accept per-sample shape, e.g. [50], or full array shape, e.g. ['batch', 50]
    # or [batch_size, 50]. For scalar per-row values, [] and [batch] are both ok.
    for suffix in expected_suffixes:
        if suffix_matches(shape, suffix):
            return True
        if len(shape) >= 1 and suffix_matches(shape[1:], suffix):
            return True
    return False


def suffixes_from_shape(shape: list[Any]) -> list[list[int]]:
    # Convert an additional input's shape into accepted suffixes. If the first
    # item is a batch marker/string, drop it. If every item is numeric, keep both
    # the full shape and the no-batch suffix where meaningful.
    if not shape:
        return [[]]
    suffix = shape[1:] if isinstance(shape[0], str) and shape[0].lower() in {"batch", "none", "n"} else shape
    parsed: list[int] = []
    for dim in suffix:
        if isinstance(dim, int) and not isinstance(dim, bool):
            parsed.append(dim)
        elif isinstance(dim, float) and dim.is_integer():
            parsed.append(int(dim))
        else:
            return [[], [1]]
    return [parsed]


def load_spec(path: str) -> dict[str, Any]:
    with Path(path).open() as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("top-level JSON value must be an object")
    return data


def print_human(result: dict[str, Any]) -> None:
    if result["ok"]:
        print("Feature spec looks consistent for DeepCTR feature-column construction.")
    else:
        print("Feature spec is invalid.", file=sys.stderr)
    print("Computed feature_names:", ", ".join(result["feature_names"]) or "<none>")
    print("Required input keys:", ", ".join(result["required_input_keys"]) or "<none>")
    for issue in result["errors"]:
        print(f"ERROR {issue['path']}: {issue['message']}", file=sys.stderr)
        if issue.get("advice"):
            print(f"  advice: {issue['advice']}", file=sys.stderr)
    for issue in result["warnings"]:
        print(f"WARNING {issue['path']}: {issue['message']}", file=sys.stderr)
        if issue.get("advice"):
            print(f"  advice: {issue['advice']}", file=sys.stderr)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a JSON DeepCTR feature-column spec.")
    parser.add_argument("spec", nargs="?", help="Path to a JSON spec containing a top-level features list.")
    parser.add_argument(
        "--emit-example",
        choices=sorted(EXAMPLES),
        help="Print a built-in example spec and exit. Some examples intentionally fail validation.",
    )
    parser.add_argument("--example", action="store_true", help="Alias for --emit-example basic.")
    parser.add_argument("--check-paths", action="store_true", help="Check that vocabulary_path files exist and look like id,key CSV files.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON validation result.")
    parser.add_argument("--strict-warnings", action="store_true", help="Treat warnings as a non-zero exit status.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    example_name = "basic" if args.example else args.emit_example
    if example_name:
        print(json.dumps(EXAMPLES[example_name], indent=2, sort_keys=False))
        return 0
    if not args.spec:
        print("error: spec is required unless --emit-example or --example is used", file=sys.stderr)
        return 2
    try:
        data = load_spec(args.spec)
    except Exception as exc:  # JSONDecodeError and OSError should be human-readable here.
        print(f"error: could not read spec: {exc}", file=sys.stderr)
        return 2
    result = Validator(check_paths=args.check_paths).validate(data)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=False))
    else:
        print_human(result)
    if not result["ok"]:
        return 1
    if args.strict_warnings and result["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
