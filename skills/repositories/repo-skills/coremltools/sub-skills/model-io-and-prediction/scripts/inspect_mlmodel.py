#!/usr/bin/env python3
"""Inspect a Core ML .mlmodel or .mlpackage spec without running prediction."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    return str(value)


def _enum_name(message: Any, field_name: str) -> Any:
    field = getattr(message, "DESCRIPTOR", None)
    if field is None:
        return getattr(message, field_name, None)
    field_desc = field.fields_by_name.get(field_name)
    value = getattr(message, field_name, None)
    if field_desc is not None and field_desc.enum_type is not None:
        enum_value = field_desc.enum_type.values_by_number.get(value)
        if enum_value is not None:
            return enum_value.name
    return value


def _shape(values: Iterable[Any]) -> List[int]:
    return [int(v) for v in values]


def _shape_ranges(size_ranges: Iterable[Any]) -> List[Dict[str, int]]:
    return [
        {
            "lowerBound": int(size_range.lowerBound),
            "upperBound": int(size_range.upperBound),
        }
        for size_range in size_ranges
    ]


def _feature_type_details(feature_type: Any, kind: str) -> Dict[str, Any]:
    details: Dict[str, Any] = {}

    if kind == "multiArrayType":
        value = feature_type.multiArrayType
        if len(value.shape) > 0:
            details["shape"] = _shape(value.shape)
        details["dataType"] = _enum_name(value, "dataType")
        if len(value.shapeRange.sizeRanges) > 0:
            details["shapeRange"] = _shape_ranges(value.shapeRange.sizeRanges)
        if len(value.enumeratedShapes.shapes) > 0:
            details["enumeratedShapes"] = [
                _shape(shape.shape) for shape in value.enumeratedShapes.shapes
            ]
    elif kind == "imageType":
        value = feature_type.imageType
        details["width"] = int(value.width)
        details["height"] = int(value.height)
        details["colorSpace"] = _enum_name(value, "colorSpace")
        width_range = value.imageSizeRange.widthRange
        height_range = value.imageSizeRange.heightRange
        if (
            width_range.lowerBound
            or width_range.upperBound
            or height_range.lowerBound
            or height_range.upperBound
        ):
            details["imageSizeRange"] = {
                "width": {
                    "lowerBound": int(width_range.lowerBound),
                    "upperBound": int(width_range.upperBound),
                },
                "height": {
                    "lowerBound": int(height_range.lowerBound),
                    "upperBound": int(height_range.upperBound),
                },
            }
        if len(value.enumeratedSizes.sizes) > 0:
            details["enumeratedSizes"] = [
                {"width": int(size.width), "height": int(size.height)}
                for size in value.enumeratedSizes.sizes
            ]
    elif kind == "dictionaryType":
        value = feature_type.dictionaryType
        details["keyType"] = value.WhichOneof("KeyType")
    elif kind == "sequenceType":
        value = feature_type.sequenceType
        details["sequenceType"] = value.WhichOneof("Type")
    elif kind in {
        "doubleType",
        "int64Type",
        "stringType",
        "boolType",
    }:
        pass

    return details


def _feature_summary(feature: Any) -> Dict[str, Any]:
    feature_type = feature.type
    kind = feature_type.WhichOneof("Type") or "unspecified"
    result: Dict[str, Any] = {
        "name": feature.name,
        "type": kind,
    }
    if getattr(feature, "shortDescription", ""):
        result["shortDescription"] = feature.shortDescription
    details = _feature_type_details(feature_type, kind)
    if details:
        result["details"] = details
    return result


def _metadata_summary(metadata: Any) -> Dict[str, Any]:
    result = {
        "author": metadata.author,
        "license": metadata.license,
        "shortDescription": metadata.shortDescription,
        "versionString": metadata.versionString,
        "userDefined": dict(metadata.userDefined),
    }
    return {key: value for key, value in result.items() if value not in ("", {}, [])}


def _function_summaries(description: Any) -> List[Dict[str, Any]]:
    functions = []
    for function in getattr(description, "functions", []):
        functions.append(
            {
                "name": function.name,
                "inputs": [_feature_summary(feature) for feature in function.input],
                "outputs": [_feature_summary(feature) for feature in function.output],
                "states": [
                    _feature_summary(feature)
                    for feature in getattr(function, "state", [])
                ],
            }
        )
    return functions


def _summarize_spec(spec: Any, requested_path: Path, loaded_from: Path, notes: List[str]) -> Dict[str, Any]:
    description = spec.description
    summary: Dict[str, Any] = {
        "ok": True,
        "path": str(requested_path),
        "loadedFrom": str(loaded_from),
        "modelType": spec.WhichOneof("Type"),
        "specificationVersion": int(spec.specificationVersion),
        "inputs": [_feature_summary(feature) for feature in description.input],
        "outputs": [_feature_summary(feature) for feature in description.output],
        "metadata": _metadata_summary(description.metadata),
    }

    states = [_feature_summary(feature) for feature in getattr(description, "state", [])]
    if states:
        summary["states"] = states

    functions = _function_summaries(description)
    if functions:
        summary["functions"] = functions

    if description.predictedFeatureName:
        summary["predictedFeatureName"] = description.predictedFeatureName
    if description.predictedProbabilitiesName:
        summary["predictedProbabilitiesName"] = description.predictedProbabilitiesName
    if description.defaultFunctionName:
        summary["defaultFunctionName"] = description.defaultFunctionName
    if notes:
        summary["notes"] = notes
    return summary


def _import_load_spec():
    try:
        from coremltools.models.utils import load_spec
    except Exception as exc:  # pragma: no cover - depends on caller environment
        return None, exc
    return load_spec, None


def _load_spec(path: Path) -> Tuple[Any, Path, List[str]]:
    load_spec, import_error = _import_load_spec()
    if load_spec is None:
        raise RuntimeError(
            "Could not import coremltools.models.utils.load_spec. "
            "Install coremltools or run from an environment where it is importable."
        ) from import_error

    try:
        return load_spec(str(path)), path, []
    except Exception as first_error:
        if path.is_dir():
            package_root_model = path / "Data" / "com.apple.CoreML" / "model.mlmodel"
            if package_root_model.is_file():
                try:
                    return (
                        load_spec(str(package_root_model)),
                        package_root_model,
                        [
                            "load_spec failed on the package directory; loaded the package root model file directly."
                        ],
                    )
                except Exception as fallback_error:
                    raise RuntimeError(
                        "load_spec failed on the package directory and on the package root model file: "
                        f"{first_error}; fallback error: {fallback_error}"
                    ) from fallback_error
        raise


def _feature_line(feature: Dict[str, Any]) -> str:
    pieces = [f"{feature['name']}: {feature['type']}"]
    details = feature.get("details", {})
    for key in (
        "shape",
        "dataType",
        "shapeRange",
        "enumeratedShapes",
        "width",
        "height",
        "colorSpace",
        "imageSizeRange",
        "enumeratedSizes",
        "keyType",
        "sequenceType",
    ):
        if key in details:
            pieces.append(f"{key}={details[key]}")
    if feature.get("shortDescription"):
        pieces.append(f"description={feature['shortDescription']!r}")
    return "; ".join(pieces)


def _print_features(title: str, features: List[Dict[str, Any]]) -> None:
    print(f"{title}:")
    if not features:
        print("  (none)")
        return
    for feature in features:
        print(f"  - {_feature_line(feature)}")


def _print_summary(summary: Dict[str, Any]) -> None:
    print(f"Path: {summary['path']}")
    if summary["loadedFrom"] != summary["path"]:
        print(f"Loaded spec from: {summary['loadedFrom']}")
    print(f"Model type: {summary.get('modelType')}")
    print(f"Specification version: {summary.get('specificationVersion')}")
    if summary.get("defaultFunctionName"):
        print(f"Default function: {summary['defaultFunctionName']}")
    if summary.get("predictedFeatureName"):
        print(f"Predicted feature: {summary['predictedFeatureName']}")
    if summary.get("predictedProbabilitiesName"):
        print(f"Predicted probabilities: {summary['predictedProbabilitiesName']}")

    _print_features("Inputs", summary.get("inputs", []))
    _print_features("Outputs", summary.get("outputs", []))
    if summary.get("states"):
        _print_features("States", summary["states"])

    if summary.get("functions"):
        print("Functions:")
        for function in summary["functions"]:
            print(
                "  - "
                f"{function['name']} "
                f"(inputs={len(function['inputs'])}, "
                f"outputs={len(function['outputs'])}, "
                f"states={len(function.get('states', []))})"
            )

    print("Metadata:")
    metadata = summary.get("metadata", {})
    if not metadata:
        print("  (none)")
    else:
        for key in ("author", "license", "shortDescription", "versionString"):
            if key in metadata:
                print(f"  {key}: {metadata[key]}")
        user_defined = metadata.get("userDefined", {})
        if user_defined:
            print("  userDefined:")
            for key in sorted(user_defined):
                print(f"    {key}: {user_defined[key]}")

    for note in summary.get("notes", []):
        print(f"Note: {note}")


def _error(message: str, json_mode: bool, exc: Optional[Exception] = None) -> int:
    if json_mode:
        payload: Dict[str, Any] = {"ok": False, "error": message}
        if exc is not None:
            payload["details"] = f"{type(exc).__name__}: {exc}"
        print(json.dumps(payload, indent=2, default=_json_default))
    else:
        print(f"ERROR: {message}", file=sys.stderr)
        if exc is not None:
            print(f"DETAILS: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 1


def _build_summary(path: Path) -> Dict[str, Any]:
    spec, loaded_from, notes = _load_spec(path)
    return _summarize_spec(spec, path, loaded_from, notes)


def _write_worker_payload(output_path: Path, payload: Dict[str, Any]) -> None:
    output_path.write_text(json.dumps(payload, default=_json_default), encoding="utf-8")


def _worker_main(path: Path, output_path: Path) -> int:
    try:
        payload = _build_summary(path)
    except Exception as exc:
        payload = {
            "ok": False,
            "error": "failed to load Core ML model spec",
            "details": f"{type(exc).__name__}: {exc}",
        }
        _write_worker_payload(output_path, payload)
        return 1
    _write_worker_payload(output_path, payload)
    return 0


def _run_worker(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
    with tempfile.NamedTemporaryFile(prefix="inspect_mlmodel_", suffix=".json") as output_file:
        output_path = Path(output_file.name)
        command = [
            sys.executable,
            str(Path(__file__)),
            str(path),
            "--_worker-output",
            str(output_path),
        ]
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        payload: Optional[Dict[str, Any]] = None
        if output_path.stat().st_size > 0:
            try:
                payload = json.loads(output_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                payload = {
                    "ok": False,
                    "error": "worker wrote invalid JSON",
                    "details": f"{type(exc).__name__}: {exc}",
                }
        details = completed.stderr.strip() or completed.stdout.strip() or None
        return payload, details, completed.returncode


def _emit_payload(payload: Dict[str, Any], json_mode: bool) -> int:
    if payload.get("ok"):
        if json_mode:
            print(json.dumps(payload, indent=2, default=_json_default))
        else:
            _print_summary(payload)
        return 0

    if json_mode:
        print(json.dumps(payload, indent=2, default=_json_default))
    else:
        print(f"ERROR: {payload.get('error', 'unknown error')}", file=sys.stderr)
        if payload.get("details"):
            print(f"DETAILS: {payload['details']}", file=sys.stderr)
    return 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a Core ML .mlmodel file or .mlpackage directory without "
            "loading the Core ML prediction runtime."
        )
    )
    parser.add_argument("model_path", help="Path to a .mlmodel file or .mlpackage directory.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--_worker-output", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    path = Path(args.model_path).expanduser()
    if not path.exists():
        return _error(f"model path does not exist: {path}", args.json)
    if not (path.is_file() or path.is_dir()):
        return _error(f"model path is neither a file nor a directory: {path}", args.json)

    if args._worker_output:
        return _worker_main(path, Path(args._worker_output))

    payload, details, returncode = _run_worker(path)
    if payload is None:
        payload = {
            "ok": False,
            "error": "coremltools worker process failed before writing a result",
            "details": (
                f"exit code {returncode}; coremltools import or native parsing may have crashed. "
                "Use a compatible coremltools environment and retry."
            ),
        }
    elif returncode != 0 and payload.get("ok"):
        payload = {
            "ok": False,
            "error": "coremltools worker process failed after writing a result",
            "details": f"exit code {returncode}; retry in a compatible coremltools environment.",
        }
    return _emit_payload(payload, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
