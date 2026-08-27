#!/usr/bin/env python3
"""Validate DeepCTR-Torch feature-column specs and model_input arrays.

Default mode runs a tiny self-contained demo. Pass --spec to validate JSON like:

{
  "features": [
    {"type": "sparse", "name": "user_id", "vocabulary_size": 4, "input": [0, 1, 2]},
    {"type": "dense", "name": "profile_vec", "dimension": 2,
     "input": [[0.1, 0.9], [0.2, 0.8], [0.3, 0.7]]},
    {"type": "varlen_sparse", "name": "hist_item_id", "vocabulary_size": 5,
     "embedding_dim": 8, "embedding_name": "item_id", "maxlen": 3,
     "length_name": "hist_len", "input": [[1, 2, 0], [2, 3, 4], [4, 0, 0]],
     "length_input": [2, 3, 1]}
  ],
  "labels": [1, 0, 1]
}

Feature input may also be supplied under a top-level "model_input" mapping instead of
per-feature "input" fields.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message=r"The pynvml package is deprecated.*",
)

try:
    from deepctr_torch.inputs import DenseFeat, SparseFeat, VarLenSparseFeat, get_feature_names
except Exception as exc:  # pragma: no cover - environment-specific
    print(
        "ERROR: cannot import deepctr_torch.inputs. Install deepctr-torch in the active Python environment. "
        f"Original error: {exc}",
        file=sys.stderr,
    )
    sys.exit(1)


VALID_COMBINERS = {"sum", "mean", "max"}
FEATURE_TYPE_ALIASES = {
    "sparse": "sparse",
    "sparsefeat": "sparse",
    "sparse_feat": "sparse",
    "dense": "dense",
    "densefeat": "dense",
    "dense_feat": "dense",
    "varlen_sparse": "varlen_sparse",
    "varlensparsefeat": "varlen_sparse",
    "var_len_sparse": "varlen_sparse",
    "sequence": "varlen_sparse",
    "seq": "varlen_sparse",
}


class ValidationResult:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.notes: List[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)


# ---------------------------------------------------------------------------
# Demo and spec loading
# ---------------------------------------------------------------------------


def default_demo_spec() -> Dict[str, Any]:
    """A tiny demo adapted from DeepCTR-Torch examples/tests, with no files."""
    return {
        "features": [
            {
                "type": "sparse",
                "name": "user_id",
                "vocabulary_size": 4,
                "embedding_dim": 4,
                "input": [0, 1, 2, 3],
            },
            {
                "type": "sparse",
                "name": "item_id",
                "vocabulary_size": 5,
                "embedding_dim": 8,
                "input": [1, 2, 3, 4],
            },
            {
                "type": "dense",
                "name": "profile_vec",
                "dimension": 2,
                "input": [[0.1, 0.9], [0.2, 0.8], [0.4, 0.6], [0.5, 0.5]],
            },
            {
                "type": "varlen_sparse",
                "name": "hist_item_id",
                "vocabulary_size": 5,
                "embedding_dim": 8,
                "embedding_name": "item_id",
                "maxlen": 3,
                "combiner": "mean",
                "length_name": "hist_len",
                "input": [[1, 2, 0], [2, 3, 4], [4, 0, 0], [1, 3, 2]],
                "length_input": [2, 3, 1, 3],
            },
            {
                "type": "varlen_sparse",
                "name": "genres",
                "vocabulary_size": 6,
                "embedding_dim": 4,
                "maxlen": 3,
                "combiner": "mean",
                "input": [[1, 2, 0], [3, 0, 0], [4, 5, 0], [1, 0, 0]],
            },
        ],
        "labels": [1, 0, 1, 0],
    }


def load_spec(path: Optional[str]) -> Dict[str, Any]:
    if path is None:
        return default_demo_spec()
    with open(path, "r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise ValueError("top-level JSON spec must be an object")
    return loaded


# ---------------------------------------------------------------------------
# Construction helpers
# ---------------------------------------------------------------------------


def normalize_feature_type(raw: Any) -> str:
    key = str(raw or "").strip().lower().replace("-", "_")
    if key not in FEATURE_TYPE_ALIASES:
        raise ValueError(f"unsupported feature type {raw!r}; expected sparse, dense, or varlen_sparse")
    return FEATURE_TYPE_ALIASES[key]


def positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a positive integer, got bool")
    try:
        number = int(value)
    except Exception as exc:
        raise ValueError(f"{field} must be a positive integer, got {value!r}") from exc
    if number < 1:
        raise ValueError(f"{field} must be >= 1, got {number}")
    return number


def optional_embedding_dim(value: Any) -> Any:
    if value == "auto":
        return value
    return positive_int(value, "embedding_dim")


def build_column(feature: Dict[str, Any]) -> Any:
    ftype = normalize_feature_type(feature.get("type"))
    name = str(feature.get("name", "")).strip()
    if not name:
        raise ValueError("each feature requires a non-empty name")

    if ftype == "sparse":
        return SparseFeat(
            name=name,
            vocabulary_size=positive_int(feature.get("vocabulary_size"), f"{name}.vocabulary_size"),
            embedding_dim=optional_embedding_dim(feature.get("embedding_dim", 4)),
            use_hash=bool(feature.get("use_hash", False)),
            dtype=str(feature.get("dtype", "int32")),
            embedding_name=feature.get("embedding_name"),
            group_name=str(feature.get("group_name", "default_group")),
        )

    if ftype == "dense":
        return DenseFeat(
            name=name,
            dimension=positive_int(feature.get("dimension", 1), f"{name}.dimension"),
            dtype=str(feature.get("dtype", "float32")),
        )

    if ftype == "varlen_sparse":
        combiner = str(feature.get("combiner", "mean"))
        sparse = SparseFeat(
            name=name,
            vocabulary_size=positive_int(feature.get("vocabulary_size"), f"{name}.vocabulary_size"),
            embedding_dim=optional_embedding_dim(feature.get("embedding_dim", 4)),
            use_hash=bool(feature.get("use_hash", False)),
            dtype=str(feature.get("dtype", "int32")),
            embedding_name=feature.get("embedding_name"),
            group_name=str(feature.get("group_name", "default_group")),
        )
        length_name = feature.get("length_name")
        if length_name in ("", None):
            length_name = None
        else:
            length_name = str(length_name)
        return VarLenSparseFeat(
            sparse,
            maxlen=positive_int(feature.get("maxlen"), f"{name}.maxlen"),
            combiner=combiner,
            length_name=length_name,
        )

    raise AssertionError("unreachable")


# ---------------------------------------------------------------------------
# Array validation helpers
# ---------------------------------------------------------------------------


def get_feature_value(spec: Dict[str, Any], feature: Dict[str, Any], name: str) -> Tuple[bool, Any]:
    if "input" in feature:
        return True, feature["input"]
    model_input = spec.get("model_input", {})
    if isinstance(model_input, dict) and name in model_input:
        return True, model_input[name]
    return False, None


def get_length_value(spec: Dict[str, Any], feature: Dict[str, Any], length_name: str) -> Tuple[bool, Any]:
    if "length_input" in feature:
        return True, feature["length_input"]
    model_input = spec.get("model_input", {})
    if isinstance(model_input, dict) and length_name in model_input:
        return True, model_input[length_name]
    return False, None


def as_array(value: Any, name: str, result: ValidationResult) -> Optional[np.ndarray]:
    try:
        arr = np.asarray(value)
    except Exception as exc:
        result.error(f"{name}: cannot convert input to a numpy array: {exc}")
        return None
    if arr.ndim == 0:
        result.error(f"{name}: expected a batch-major array, got scalar")
        return None
    return arr


def check_batch(name: str, arr: np.ndarray, batch_size: Optional[int], result: ValidationResult) -> Optional[int]:
    rows = int(arr.shape[0])
    if batch_size is None:
        return rows
    if rows != batch_size:
        result.error(f"{name}: batch size {rows} does not match earlier batch size {batch_size}")
    return batch_size


def is_integer_array(arr: np.ndarray) -> bool:
    if np.issubdtype(arr.dtype, np.integer):
        return True
    if np.issubdtype(arr.dtype, np.floating):
        finite = np.isfinite(arr)
        return bool(finite.all() and np.equal(arr, np.floor(arr)).all())
    return False


def check_id_range(name: str, arr: np.ndarray, vocabulary_size: int, result: ValidationResult) -> None:
    if arr.size == 0:
        result.error(f"{name}: input array is empty")
        return
    if not is_integer_array(arr):
        result.error(f"{name}: sparse ids must be integer-valued, got dtype {arr.dtype}")
        return
    numeric = arr.astype(np.int64, copy=False)
    min_id = int(np.min(numeric))
    max_id = int(np.max(numeric))
    if min_id < 0:
        result.error(f"{name}: found negative id {min_id}; sparse ids must be >= 0")
    if max_id >= vocabulary_size:
        result.error(
            f"{name}: max id {max_id} is outside vocabulary_size {vocabulary_size}; "
            "set vocabulary_size >= max_id + 1 or fix the encoder"
        )


def check_finite_numeric(name: str, arr: np.ndarray, result: ValidationResult) -> None:
    if not np.issubdtype(arr.dtype, np.number):
        result.error(f"{name}: dense values must be numeric, got dtype {arr.dtype}")
        return
    if not np.isfinite(arr.astype(float)).all():
        result.error(f"{name}: dense values contain NaN or infinity")


def validate_sparse(name: str, arr: np.ndarray, vocabulary_size: int, result: ValidationResult) -> None:
    if arr.ndim == 1:
        pass
    elif arr.ndim == 2 and arr.shape[1] == 1:
        pass
    else:
        result.error(f"{name}: SparseFeat input must have shape (n,) or (n, 1), got {tuple(arr.shape)}")
    check_id_range(name, arr, vocabulary_size, result)


def validate_dense(name: str, arr: np.ndarray, dimension: int, result: ValidationResult) -> None:
    if dimension == 1:
        if not (arr.ndim == 1 or (arr.ndim == 2 and arr.shape[1] == 1)):
            result.error(f"{name}: DenseFeat dimension=1 expects shape (n,) or (n, 1), got {tuple(arr.shape)}")
    else:
        if not (arr.ndim == 2 and arr.shape[1] == dimension):
            result.error(
                f"{name}: DenseFeat dimension={dimension} expects shape (n, {dimension}), got {tuple(arr.shape)}"
            )
    check_finite_numeric(name, arr, result)


def validate_varlen(
    name: str,
    arr: np.ndarray,
    vocabulary_size: int,
    maxlen: int,
    length_name: Optional[str],
    length_arr: Optional[np.ndarray],
    padding_value: Any,
    result: ValidationResult,
    batch_size: Optional[int],
) -> Optional[int]:
    if arr.ndim != 2 or arr.shape[1] != maxlen:
        result.error(f"{name}: VarLenSparseFeat maxlen={maxlen} expects shape (n, {maxlen}), got {tuple(arr.shape)}")
    check_id_range(name, arr, vocabulary_size, result)
    batch_size = check_batch(name, arr, batch_size, result)

    if length_name is None:
        if padding_value not in (None, 0, 0.0, "0"):
            result.error(
                f"{name}: padding_value={padding_value!r} is incompatible with no length_name; "
                "DeepCTR-Torch masks only value 0 as padding"
            )
        if arr.size and not np.any(arr == 0):
            result.warn(f"{name}: no zero padding found; this is valid only if every sequence has full maxlen")
    else:
        if length_arr is None:
            result.error(f"{name}: length_name {length_name!r} declared but no length input was provided")
        else:
            if length_arr.ndim == 1:
                pass
            elif length_arr.ndim == 2 and length_arr.shape[1] == 1:
                pass
            else:
                result.error(
                    f"{length_name}: length input must have shape (n,) or (n, 1), got {tuple(length_arr.shape)}"
                )
            check_batch(length_name, length_arr, batch_size, result)
            if not is_integer_array(length_arr):
                result.error(f"{length_name}: lengths must be integer-valued, got dtype {length_arr.dtype}")
            else:
                lengths = length_arr.astype(np.int64, copy=False)
                min_len = int(np.min(lengths)) if lengths.size else 0
                max_len_seen = int(np.max(lengths)) if lengths.size else 0
                if min_len < 0:
                    result.error(f"{length_name}: found negative length {min_len}")
                if max_len_seen > maxlen:
                    result.error(f"{length_name}: max length {max_len_seen} exceeds declared maxlen {maxlen}")
                if min_len == 0:
                    result.warn(
                        f"{length_name}: contains zero-length rows; supported by masking math but often unintended"
                    )
    return batch_size


# ---------------------------------------------------------------------------
# Whole-spec validation
# ---------------------------------------------------------------------------


def validate_spec(spec: Dict[str, Any]) -> Tuple[ValidationResult, Dict[str, Any]]:
    result = ValidationResult()
    metadata: Dict[str, Any] = {"feature_names": [], "columns": [], "batch_size": None}

    features = spec.get("features")
    if not isinstance(features, list) or not features:
        result.error("spec must contain a non-empty 'features' list")
        return result, metadata
    if not all(isinstance(item, dict) for item in features):
        result.error("each item in 'features' must be an object")
        return result, metadata

    columns = []
    for idx, feature in enumerate(features):
        try:
            columns.append(build_column(feature))
        except Exception as exc:
            result.error(f"features[{idx}]: {exc}")

    if result.errors:
        return result, metadata

    metadata["columns"] = columns
    names = [column.name for column in columns]
    name_counts = Counter(names)
    duplicates = sorted([name for name, count in name_counts.items() if count > 1])
    if duplicates:
        collapsed = get_feature_names(columns)
        result.error(
            "duplicate feature names would be collapsed by get_feature_names: "
            f"{duplicates}; collapsed names would be {collapsed}"
        )

    # get_feature_names also exposes length_name requirements.
    try:
        feature_names = get_feature_names(columns)
    except Exception as exc:
        result.error(f"get_feature_names failed: {exc}")
        return result, metadata
    metadata["feature_names"] = feature_names

    model_input = spec.get("model_input", {})
    if model_input is not None and not isinstance(model_input, dict):
        result.error("top-level 'model_input' must be an object when provided")
        model_input = {}

    batch_size: Optional[int] = None
    available_input_names = set()
    length_inputs_seen = set()

    # Shared embedding table consistency.
    embedding_groups: Dict[str, List[Any]] = defaultdict(list)
    for column in columns:
        if isinstance(column, SparseFeat) or isinstance(column, VarLenSparseFeat):
            embedding_groups[column.embedding_name].append(column)
            if column.use_hash:
                result.warn(
                    f"{column.name}: use_hash=True was declared; on-the-fly hashing is not implemented "
                    "in DeepCTR-Torch, so pre-hash/label-encode outside the model"
                )
    for embedding_name, group in embedding_groups.items():
        vocab_dims = {(int(col.vocabulary_size), int(col.embedding_dim)) for col in group}
        if len(vocab_dims) > 1:
            details = ", ".join(
                f"{col.name}(vocab={col.vocabulary_size}, dim={col.embedding_dim})" for col in group
            )
            result.error(
                f"embedding_name {embedding_name!r} is shared by inconsistent columns: {details}"
            )

    for feature, column in zip(features, columns):
        name = column.name
        found, raw_value = get_feature_value(spec, feature, name)
        if not found:
            result.error(f"{name}: missing input array; provide feature.input or model_input[{name!r}]")
            continue
        available_input_names.add(name)
        arr = as_array(raw_value, name, result)
        if arr is None:
            continue

        if isinstance(column, SparseFeat):
            batch_size = check_batch(name, arr, batch_size, result)
            validate_sparse(name, arr, int(column.vocabulary_size), result)
        elif isinstance(column, DenseFeat):
            batch_size = check_batch(name, arr, batch_size, result)
            validate_dense(name, arr, int(column.dimension), result)
        elif isinstance(column, VarLenSparseFeat):
            length_arr = None
            if column.length_name is not None:
                found_len, raw_len = get_length_value(spec, feature, column.length_name)
                if found_len:
                    length_inputs_seen.add(column.length_name)
                    length_arr = as_array(raw_len, column.length_name, result)
                else:
                    result.error(
                        f"{name}: length_name {column.length_name!r} declared but no length input was provided"
                    )
            if str(column.combiner) not in VALID_COMBINERS:
                result.error(f"{name}: combiner {column.combiner!r} is unsupported; use one of {sorted(VALID_COMBINERS)}")
            batch_size = validate_varlen(
                name=name,
                arr=arr,
                vocabulary_size=int(column.vocabulary_size),
                maxlen=int(column.maxlen),
                length_name=column.length_name,
                length_arr=length_arr,
                padding_value=feature.get("padding_value"),
                result=result,
                batch_size=batch_size,
            )

    metadata["batch_size"] = batch_size

    if isinstance(model_input, dict):
        provided = set(model_input.keys())
        required = set(feature_names)
        # Per-feature input/length_input fields count as available for this validator.
        available = available_input_names | length_inputs_seen | provided
        missing = sorted(required - available)
        if missing:
            result.error(f"missing required model_input keys from get_feature_names: {missing}")
        extra = sorted(provided - required)
        if extra:
            result.warn(f"model_input contains extra keys not returned by get_feature_names: {extra}")

    labels = spec.get("labels")
    if labels is not None:
        label_arr = as_array(labels, "labels", result)
        if label_arr is not None and batch_size is not None:
            check_batch("labels", label_arr, batch_size, result)
            if label_arr.ndim > 2:
                result.warn(f"labels: expected 1D or 2D targets for common workflows, got {tuple(label_arr.shape)}")

    if not result.errors:
        result.note("feature input spec is compatible with DeepCTR-Torch feature-column shape/range expectations")
    return result, metadata


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def format_column(column: Any) -> str:
    if isinstance(column, SparseFeat):
        return (
            f"SparseFeat(name={column.name!r}, vocabulary_size={column.vocabulary_size}, "
            f"embedding_dim={column.embedding_dim}, embedding_name={column.embedding_name!r}, "
            f"group_name={column.group_name!r})"
        )
    if isinstance(column, DenseFeat):
        return f"DenseFeat(name={column.name!r}, dimension={column.dimension})"
    if isinstance(column, VarLenSparseFeat):
        return (
            f"VarLenSparseFeat(name={column.name!r}, vocabulary_size={column.vocabulary_size}, "
            f"embedding_dim={column.embedding_dim}, embedding_name={column.embedding_name!r}, "
            f"maxlen={column.maxlen}, combiner={column.combiner!r}, length_name={column.length_name!r})"
        )
    return repr(column)


def emit_report(result: ValidationResult, metadata: Dict[str, Any], strict_warnings: bool) -> int:
    status_ok = not result.errors and not (strict_warnings and result.warnings)
    print("OK" if status_ok else "FAILED")
    if metadata.get("batch_size") is not None:
        print(f"batch_size: {metadata['batch_size']}")
    if metadata.get("feature_names"):
        print("feature_names:")
        for name in metadata["feature_names"]:
            print(f"  - {name}")
    if metadata.get("columns"):
        print("feature_columns:")
        for column in metadata["columns"]:
            print(f"  - {format_column(column)}")
    if result.notes:
        print("notes:")
        for item in result.notes:
            print(f"  - {item}")
    if result.warnings:
        print("warnings:")
        for item in result.warnings:
            print(f"  - {item}")
    if result.errors:
        print("errors:")
        for item in result.errors:
            print(f"  - {item}")
    if strict_warnings and result.warnings and not result.errors:
        print("errors:")
        print("  - --strict-warnings converts warnings to failure")
    return 0 if status_ok else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate DeepCTR-Torch feature-column specs and model_input arrays.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Spec notes:\n"
            "  - features[].type: sparse, dense, or varlen_sparse\n"
            "  - features[].input may hold the array, or top-level model_input[name] may hold it\n"
            "  - varlen_sparse with length_name needs length_input or model_input[length_name]\n"
            "  - default mode runs an inline demo with sparse, dense-vector, shared-embedding,\n"
            "    explicit-length, and zero-padded VarLen features\n"
        ),
    )
    parser.add_argument("--spec", help="Path to a JSON feature-input spec. Omit to run the built-in demo.")
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Return failure if warnings are present, not only hard errors.",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        spec = load_spec(args.spec)
    except Exception as exc:
        print(f"ERROR: failed to load spec: {exc}", file=sys.stderr)
        return 1
    result, metadata = validate_spec(spec)
    return emit_report(result, metadata, args.strict_warnings)


if __name__ == "__main__":
    raise SystemExit(main())
