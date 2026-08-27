#!/usr/bin/env python3
"""Build LightFM Dataset matrices from tiny local JSONL records.

The helper performs no downloads. It reads interaction and optional feature
records, builds LightFM Dataset mappings, prints a compact summary, and can
write SciPy sparse matrices plus mapping metadata to an output directory.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple, Union

JsonScalar = Union[str, int, float]
Interaction = Tuple[JsonScalar, JsonScalar, float]
FeaturePayload = Union[List[JsonScalar], Dict[JsonScalar, float]]
FeatureRecord = Tuple[JsonScalar, FeaturePayload]


def _location(path: Union[str, Path], line_no: int) -> str:
    return f"{path}:{line_no}"


def _is_valid_id(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    return isinstance(value, (str, int, float))


def _as_id(value: Any, label: str, loc: str) -> JsonScalar:
    if not _is_valid_id(value):
        raise ValueError(f"{loc}: {label} must be a JSON string or number, got {value!r}.")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{loc}: {label} must be finite, got {value!r}.")
    return value


def _as_weight(value: Any, label: str, loc: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{loc}: {label} must be numeric, got boolean {value!r}.")
    try:
        weight = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{loc}: {label} must be numeric, got {value!r}.") from exc
    if not math.isfinite(weight):
        raise ValueError(f"{loc}: {label} must be finite, got {value!r}.")
    return weight


def _load_jsonl(path: Path) -> List[Tuple[Any, int]]:
    if not path.is_file():
        raise ValueError(f"Input file does not exist: {path}")

    records: List[Tuple[Any, int]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append((json.loads(stripped), line_no))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{_location(path, line_no)}: invalid JSON: {exc.msg}") from exc
    return records


def _parse_interaction_record(obj: Any, loc: str) -> Interaction:
    if isinstance(obj, (list, tuple)):
        if len(obj) not in (2, 3):
            raise ValueError(
                f"{loc}: interaction arrays must be [user_id, item_id] or "
                f"[user_id, item_id, weight], got length {len(obj)}."
            )
        user_id = _as_id(obj[0], "user_id", loc)
        item_id = _as_id(obj[1], "item_id", loc)
        weight = _as_weight(obj[2], "weight", loc) if len(obj) == 3 else 1.0
        return user_id, item_id, weight

    if isinstance(obj, Mapping):
        user_value = obj.get("user_id", obj.get("user"))
        item_value = obj.get("item_id", obj.get("item"))
        if user_value is None or item_value is None:
            raise ValueError(
                f"{loc}: interaction objects need user_id/user and item_id/item keys."
            )
        user_id = _as_id(user_value, "user_id", loc)
        item_id = _as_id(item_value, "item_id", loc)
        weight = _as_weight(obj.get("weight", 1.0), "weight", loc)
        return user_id, item_id, weight

    raise ValueError(
        f"{loc}: interaction records must be arrays or objects, got {type(obj).__name__}."
    )


def _parse_feature_payload(value: Any, loc: str) -> FeaturePayload:
    if isinstance(value, str):
        raise ValueError(
            f"{loc}: features must be a list or object. Wrap a single feature as "
            "[\"feature:name\"], not a bare string."
        )

    if isinstance(value, list):
        features: List[JsonScalar] = []
        for idx, feature in enumerate(value):
            features.append(_as_id(feature, f"features[{idx}]", loc))
        return features

    if isinstance(value, Mapping):
        weighted: Dict[JsonScalar, float] = {}
        for feature, weight in value.items():
            feature_id = _as_id(feature, "feature name", loc)
            weighted[feature_id] = _as_weight(weight, f"weight for feature {feature!r}", loc)
        return weighted

    raise ValueError(
        f"{loc}: features must be a list or object, got {type(value).__name__}."
    )


def _parse_feature_record(obj: Any, entity: str, loc: str) -> FeatureRecord:
    id_key = f"{entity}_id"

    if isinstance(obj, (list, tuple)):
        if len(obj) != 2:
            raise ValueError(
                f"{loc}: feature arrays must be [id, features], got length {len(obj)}."
            )
        entity_id = _as_id(obj[0], id_key, loc)
        return entity_id, _parse_feature_payload(obj[1], loc)

    if isinstance(obj, Mapping):
        raw_id = obj.get(id_key, obj.get("id"))
        if raw_id is None:
            raise ValueError(f"{loc}: {entity} feature objects need {id_key} or id.")
        if "features" not in obj:
            raise ValueError(f"{loc}: {entity} feature objects need a features key.")
        entity_id = _as_id(raw_id, id_key, loc)
        return entity_id, _parse_feature_payload(obj["features"], loc)

    raise ValueError(
        f"{loc}: feature records must be arrays or objects, got {type(obj).__name__}."
    )


def _parse_interactions(path: Path) -> List[Interaction]:
    parsed = [
        _parse_interaction_record(obj, _location(path, line_no))
        for obj, line_no in _load_jsonl(path)
    ]
    if not parsed:
        raise ValueError(f"{path}: no interaction records found.")
    return parsed


def _parse_features(path: Optional[Path], entity: str) -> List[FeatureRecord]:
    if path is None:
        return []
    return [
        _parse_feature_record(obj, entity, _location(path, line_no))
        for obj, line_no in _load_jsonl(path)
    ]


def _iter_feature_names(records: Iterable[FeatureRecord]) -> Iterable[JsonScalar]:
    for _, payload in records:
        if isinstance(payload, Mapping):
            yield from payload.keys()
        else:
            yield from payload


def _unique(values: Iterable[JsonScalar]) -> List[JsonScalar]:
    seen = set()
    result: List[JsonScalar] = []
    for value in values:
        key = (type(value).__name__, value)
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _nonzero_feature_payload(payload: FeaturePayload) -> bool:
    if isinstance(payload, Mapping):
        return any(float(weight) != 0.0 for weight in payload.values())
    return len(payload) > 0


def _validate_feature_completeness(
    records: Sequence[FeatureRecord],
    all_ids: Sequence[JsonScalar],
    entity: str,
    identity_enabled: bool,
    normalize: bool,
) -> None:
    if identity_enabled or not normalize or not records:
        return

    ids_with_features = {
        (type(entity_id).__name__, entity_id)
        for entity_id, payload in records
        if _nonzero_feature_payload(payload)
    }
    missing = [
        entity_id
        for entity_id in all_ids
        if (type(entity_id).__name__, entity_id) not in ids_with_features
    ]
    if missing:
        sample = ", ".join(repr(x) for x in missing[:5])
        suffix = "" if len(missing) <= 5 else f" ... and {len(missing) - 5} more"
        raise ValueError(
            f"Cannot build normalized {entity}_features with identity features disabled: "
            f"{len(missing)} fitted {entity} rows have no nonzero feature record "
            f"({sample}{suffix}). Provide features for every row, re-enable identity "
            "features, or disable normalization."
        )


def _demo_records() -> Tuple[List[Interaction], List[FeatureRecord], List[FeatureRecord]]:
    interactions: List[Interaction] = [
        ("alice", "book-1", 1.0),
        ("alice", "book-2", 2.0),
        ("bob", "book-1", 1.0),
        ("carol", "book-3", 1.0),
    ]
    user_features: List[FeatureRecord] = [
        ("alice", {"role:analyst": 2.0, "region:eu": 1.0}),
        ("bob", ["role:analyst", "region:us"]),
        ("carol", ["role:admin", "region:eu"]),
    ]
    item_features: List[FeatureRecord] = [
        ("book-1", ["genre:science-fiction", "author:Le Guin"]),
        ("book-2", ["genre:science-fiction", "author:Butler"]),
        ("book-3", {"genre:fantasy": 1.0, "author:Jemisin": 1.0}),
    ]
    return interactions, user_features, item_features


def _make_fallback_dataset(np: Any, sp: Any):
    """Return a small Dataset-compatible builder for environments without LightFM.

    The fallback mirrors the data-building behavior needed by this helper: mapping
    creation, COO interactions/weights, CSR feature matrices, identity features,
    L1 row normalization, model_dimensions(), and mapping(). It does not train or
    score LightFM models.
    """

    class FallbackDataset:
        def __init__(self, user_identity_features: bool = True, item_identity_features: bool = True):
            self._user_identity_features = user_identity_features
            self._item_identity_features = item_identity_features
            self._user_id_mapping: Dict[Any, int] = {}
            self._item_id_mapping: Dict[Any, int] = {}
            self._user_feature_mapping: Dict[Any, int] = {}
            self._item_feature_mapping: Dict[Any, int] = {}

        def fit(self, users, items, user_features=None, item_features=None):
            self._user_id_mapping = {}
            self._item_id_mapping = {}
            self._user_feature_mapping = {}
            self._item_feature_mapping = {}
            return self.fit_partial(users, items, user_features, item_features)

        def fit_partial(self, users=None, items=None, user_features=None, item_features=None):
            if users is not None:
                for user_id in users:
                    self._user_id_mapping.setdefault(user_id, len(self._user_id_mapping))
                    if self._user_identity_features:
                        self._user_feature_mapping.setdefault(user_id, len(self._user_feature_mapping))
            if items is not None:
                for item_id in items:
                    self._item_id_mapping.setdefault(item_id, len(self._item_id_mapping))
                    if self._item_identity_features:
                        self._item_feature_mapping.setdefault(item_id, len(self._item_feature_mapping))
            if user_features is not None:
                for feature in user_features:
                    self._user_feature_mapping.setdefault(feature, len(self._user_feature_mapping))
            if item_features is not None:
                for feature in item_features:
                    self._item_feature_mapping.setdefault(feature, len(self._item_feature_mapping))

        def interactions_shape(self):
            return len(self._user_id_mapping), len(self._item_id_mapping)

        def _unpack_interaction(self, datum):
            user_id, item_id, weight = datum
            user_idx = self._user_id_mapping.get(user_id)
            item_idx = self._item_id_mapping.get(item_id)
            if user_idx is None:
                raise ValueError(
                    f"User id {user_id} not in user id mapping. Make sure you call the fit method."
                )
            if item_idx is None:
                raise ValueError(
                    f"Item id {item_id} not in item id mapping. Make sure you call the fit method."
                )
            return user_idx, item_idx, weight

        def build_interactions(self, data):
            rows: List[int] = []
            cols: List[int] = []
            interaction_values: List[int] = []
            weight_values: List[float] = []
            for datum in data:
                user_idx, item_idx, weight = self._unpack_interaction(datum)
                rows.append(user_idx)
                cols.append(item_idx)
                interaction_values.append(1)
                weight_values.append(float(weight))
            shape = self.interactions_shape()
            interactions = sp.coo_matrix(
                (np.asarray(interaction_values, dtype=np.int32), (rows, cols)), shape=shape
            )
            weights = sp.coo_matrix(
                (np.asarray(weight_values, dtype=np.float32), (rows, cols)), shape=shape
            )
            return interactions, weights

        @staticmethod
        def _iter_features(features):
            if isinstance(features, Mapping):
                yield from features.items()
            else:
                for feature_name in features:
                    yield feature_name, 1.0

        def _build_features(self, data, id_mapping, feature_mapping, identity_features, normalize, entity_type):
            rows: List[int] = []
            cols: List[int] = []
            values: List[float] = []
            if identity_features:
                for entity_id, row_idx in id_mapping.items():
                    rows.append(row_idx)
                    cols.append(feature_mapping[entity_id])
                    values.append(1.0)
            for datum in data:
                if len(datum) != 2:
                    raise ValueError(f"Expected tuples of ({entity_type}_id, features), got {datum}.")
                entity_id, features = datum
                row_idx = id_mapping.get(entity_id)
                if row_idx is None:
                    raise ValueError(f"{entity_type} id {entity_id} not in {entity_type} id mappings.")
                for feature, weight in self._iter_features(features):
                    if feature not in feature_mapping:
                        raise ValueError(f"Feature {feature} not in feature mapping. Call fit first.")
                    rows.append(row_idx)
                    cols.append(feature_mapping[feature])
                    values.append(float(weight))
            matrix = sp.coo_matrix(
                (np.asarray(values, dtype=np.float32), (rows, cols)),
                shape=(len(id_mapping), len(feature_mapping)),
            ).tocsr()
            if normalize:
                if np.any(matrix.getnnz(1) == 0):
                    raise ValueError(
                        "Cannot normalize feature matrix: some rows have zero norm. "
                        "Ensure that features were provided for all entries."
                    )
                row_norms = np.asarray(abs(matrix).sum(axis=1)).ravel()
                nonzero_rows = row_norms != 0.0
                if np.any(nonzero_rows):
                    inv = np.zeros_like(row_norms, dtype=np.float32)
                    inv[nonzero_rows] = 1.0 / row_norms[nonzero_rows]
                    matrix = sp.diags(inv).dot(matrix).tocsr()
            return matrix

        def user_features_shape(self):
            return len(self._user_id_mapping), len(self._user_feature_mapping)

        def item_features_shape(self):
            return len(self._item_id_mapping), len(self._item_feature_mapping)

        def build_user_features(self, data, normalize=True):
            return self._build_features(
                data,
                self._user_id_mapping,
                self._user_feature_mapping,
                self._user_identity_features,
                normalize,
                "user",
            )

        def build_item_features(self, data, normalize=True):
            return self._build_features(
                data,
                self._item_id_mapping,
                self._item_feature_mapping,
                self._item_identity_features,
                normalize,
                "item",
            )

        def model_dimensions(self):
            return len(self._user_feature_mapping), len(self._item_feature_mapping)

        def mapping(self):
            return (
                self._user_id_mapping,
                self._user_feature_mapping,
                self._item_id_mapping,
                self._item_feature_mapping,
            )

    return FallbackDataset


def _import_runtime():
    try:
        from lightfm.data import Dataset  # type: ignore
        import scipy.sparse as sp  # type: ignore
        return Dataset, sp, None
    except Exception as lightfm_exc:  # pragma: no cover - environment-specific path
        try:
            import numpy as np  # type: ignore
            import scipy.sparse as sp  # type: ignore
        except Exception as scipy_exc:  # pragma: no cover - environment-specific path
            raise RuntimeError(
                "Could not import lightfm.data.Dataset. The bundled fallback also "
                "requires numpy and scipy. Install LightFM, or at minimum numpy and "
                f"scipy, before running this helper. Original LightFM import error: "
                f"{type(lightfm_exc).__name__}: {lightfm_exc}; scipy/numpy error: "
                f"{type(scipy_exc).__name__}: {scipy_exc}"
            ) from scipy_exc
        note = (
            "Using bundled Dataset-compatible matrix builder because importing "
            f"lightfm.data.Dataset failed ({type(lightfm_exc).__name__}: {lightfm_exc}). "
            "Install LightFM before training or scoring models."
        )
        return _make_fallback_dataset(np, sp), sp, note


def _matrix_info(matrix: Any) -> Optional[Dict[str, Any]]:
    if matrix is None:
        return None
    return {
        "shape": [int(matrix.shape[0]), int(matrix.shape[1])],
        "nnz": int(matrix.nnz),
        "dtype": str(matrix.dtype),
        "format": matrix.getformat(),
    }


def _mapping_pairs(mapping: MutableMapping[Any, int]) -> List[Dict[str, Any]]:
    return [{"id": key, "index": int(value)} for key, value in mapping.items()]


def _format_pairs(pairs: Sequence[Dict[str, Any]], limit: int) -> str:
    shown = pairs[:limit]
    body = ", ".join(f"{entry['id']!r}->{entry['index']}" for entry in shown)
    if len(pairs) > limit:
        body += f", ... (+{len(pairs) - limit})"
    return body or "none"


def _build_summary(
    dataset: Any,
    interactions_matrix: Any,
    weights_matrix: Any,
    user_features_matrix: Any,
    item_features_matrix: Any,
    warnings: Sequence[str],
) -> Dict[str, Any]:
    user_id_map, user_feature_map, item_id_map, item_feature_map = dataset.mapping()
    model_user_features, model_item_features = dataset.model_dimensions()
    return {
        "matrices": {
            "interactions": _matrix_info(interactions_matrix),
            "weights": _matrix_info(weights_matrix),
            "user_features": _matrix_info(user_features_matrix),
            "item_features": _matrix_info(item_features_matrix),
        },
        "model_dimensions": {
            "user_features": int(model_user_features),
            "item_features": int(model_item_features),
        },
        "mappings": {
            "user_id_mapping": _mapping_pairs(user_id_map),
            "user_feature_mapping": _mapping_pairs(user_feature_map),
            "item_id_mapping": _mapping_pairs(item_id_map),
            "item_feature_mapping": _mapping_pairs(item_feature_map),
        },
        "warnings": list(warnings),
    }


def _print_summary(summary: Mapping[str, Any], mapping_limit: int) -> None:
    print("LightFM Dataset build summary")
    print("Matrices:")
    for name, info in summary["matrices"].items():
        if info is None:
            print(f"  {name}: skipped")
        else:
            print(
                f"  {name}: shape={tuple(info['shape'])}, nnz={info['nnz']}, "
                f"dtype={info['dtype']}, format={info['format']}"
            )

    dims = summary["model_dimensions"]
    print(
        "Model dimensions: "
        f"user_features={dims['user_features']}, item_features={dims['item_features']}"
    )

    print("Mappings:")
    for name, pairs in summary["mappings"].items():
        print(f"  {name}: {len(pairs)} entries ({_format_pairs(pairs, mapping_limit)})")

    if summary["warnings"]:
        print("Warnings:", file=sys.stderr)
        for warning in summary["warnings"]:
            print(f"  - {warning}", file=sys.stderr)


def _write_outputs(output_dir: Path, sp: Any, summary: Mapping[str, Any], matrices: Mapping[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, matrix in matrices.items():
        if matrix is not None:
            sp.save_npz(output_dir / f"{name}.npz", matrix)
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _build_dataset(args: argparse.Namespace) -> Tuple[Dict[str, Any], Dict[str, Any], Any]:
    if args.demo:
        interactions, user_feature_records, item_feature_records = _demo_records()
    else:
        if args.interactions is None:
            raise ValueError("Provide --interactions PATH or use --demo.")
        interactions = _parse_interactions(args.interactions)
        user_feature_records = _parse_features(args.user_features, "user")
        item_feature_records = _parse_features(args.item_features, "item")

    user_identity = not args.no_user_identity_features
    item_identity = not args.no_item_identity_features
    normalize_user = not args.no_normalize_user_features
    normalize_item = not args.no_normalize_item_features

    users = _unique([user_id for user_id, _, _ in interactions] + [x[0] for x in user_feature_records])
    items = _unique([item_id for _, item_id, _ in interactions] + [x[0] for x in item_feature_records])
    user_feature_names = _unique(_iter_feature_names(user_feature_records))
    item_feature_names = _unique(_iter_feature_names(item_feature_records))

    _validate_feature_completeness(
        user_feature_records, users, "user", user_identity, normalize_user
    )
    _validate_feature_completeness(
        item_feature_records, items, "item", item_identity, normalize_item
    )

    warnings: List[str] = []
    if user_identity:
        user_id_keys = {(type(x).__name__, x) for x in users}
        collisions = [x for x in user_feature_names if (type(x).__name__, x) in user_id_keys]
        if collisions:
            warnings.append(
                "Some user metadata feature names equal raw user ids; Dataset will "
                "reuse those identity feature columns. Namespace metadata labels to avoid this."
            )
    if item_identity:
        item_id_keys = {(type(x).__name__, x) for x in items}
        collisions = [x for x in item_feature_names if (type(x).__name__, x) in item_id_keys]
        if collisions:
            warnings.append(
                "Some item metadata feature names equal raw item ids; Dataset will "
                "reuse those identity feature columns. Namespace metadata labels to avoid this."
            )

    Dataset, sp, runtime_note = _import_runtime()
    if runtime_note is not None:
        warnings.append(runtime_note)
    dataset = Dataset(user_identity_features=user_identity, item_identity_features=item_identity)
    dataset.fit(
        users,
        items,
        user_features=user_feature_names if user_feature_names else None,
        item_features=item_feature_names if item_feature_names else None,
    )

    try:
        interactions_matrix, weights_matrix = dataset.build_interactions(interactions)
        user_features_matrix = None
        if user_feature_records or user_identity:
            user_features_matrix = dataset.build_user_features(
                user_feature_records, normalize=normalize_user
            )
        item_features_matrix = None
        if item_feature_records or item_identity:
            item_features_matrix = dataset.build_item_features(
                item_feature_records, normalize=normalize_item
            )
    except Exception as exc:
        raise RuntimeError(f"LightFM Dataset build failed: {type(exc).__name__}: {exc}") from exc

    if not user_identity and not user_feature_records:
        warnings.append(
            "No user_features matrix was built because user identity features are disabled "
            "and no user feature file was provided. Passing None to LightFM would use "
            "an internal identity matrix for users."
        )
    if not item_identity and not item_feature_records:
        warnings.append(
            "No item_features matrix was built because item identity features are disabled "
            "and no item feature file was provided. Passing None to LightFM would use "
            "an internal identity matrix for items."
        )

    summary = _build_summary(
        dataset,
        interactions_matrix,
        weights_matrix,
        user_features_matrix,
        item_features_matrix,
        warnings,
    )
    matrices = {
        "interactions": interactions_matrix,
        "weights": weights_matrix,
        "user_features": user_features_matrix,
        "item_features": item_features_matrix,
    }
    return summary, matrices, sp


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build LightFM Dataset interactions, weights, optional user/item "
            "feature matrices, and mapping summaries from tiny local JSONL files. "
            "No network access is performed."
        )
    )
    parser.add_argument(
        "--interactions",
        type=Path,
        help=(
            "JSONL interactions. Each line is [user_id, item_id], "
            "[user_id, item_id, weight], or an object with user_id/item_id/weight."
        ),
    )
    parser.add_argument(
        "--user-features",
        type=Path,
        help=(
            "Optional JSONL user features. Each line is [user_id, features] or "
            "an object with user_id/id and features."
        ),
    )
    parser.add_argument(
        "--item-features",
        type=Path,
        help=(
            "Optional JSONL item features. Each line is [item_id, features] or "
            "an object with item_id/id and features."
        ),
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use embedded tiny records instead of input files.",
    )
    parser.add_argument(
        "--no-user-identity-features",
        action="store_true",
        help="Construct Dataset with user_identity_features=False.",
    )
    parser.add_argument(
        "--no-item-identity-features",
        action="store_true",
        help="Construct Dataset with item_identity_features=False.",
    )
    parser.add_argument(
        "--no-normalize-user-features",
        action="store_true",
        help="Call build_user_features(..., normalize=False).",
    )
    parser.add_argument(
        "--no-normalize-item-features",
        action="store_true",
        help="Call build_item_features(..., normalize=False).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help=(
            "Optional directory for interactions.npz, weights.npz, optional "
            "feature .npz files, and summary.json."
        ),
    )
    parser.add_argument(
        "--mapping-preview",
        type=int,
        default=8,
        help="Number of mapping entries to preview per map (default: 8).",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _make_parser()
    args = parser.parse_args(argv)

    if args.mapping_preview < 0:
        parser.error("--mapping-preview must be non-negative")

    try:
        summary, matrices, sp = _build_dataset(args)
        _print_summary(summary, args.mapping_preview)
        if args.output_dir is not None:
            _write_outputs(args.output_dir, sp, summary, matrices)
            print(f"Wrote matrices and summary to {args.output_dir}")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
