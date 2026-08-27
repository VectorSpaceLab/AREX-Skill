#!/usr/bin/env python3
"""Validate tensorflow-yolov3 frozen-PB inference prerequisites.

The checker validates file paths, class/anchor contracts, and frozen-graph
return tensor names. It intentionally does not create a TensorFlow Session and
does not run model inference.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

DEFAULT_EXPECTED_TENSORS: Tuple[str, str, str, str] = (
    "input/input_data:0",
    "pred_sbbox/concat_2:0",
    "pred_mbbox/concat_2:0",
    "pred_lbbox/concat_2:0",
)


class CheckError(RuntimeError):
    """Friendly validation error."""


def _path_text(path: Path) -> str:
    return str(path)


def require_file(raw_path: str, label: str, remedy: str) -> Path:
    path = Path(raw_path).expanduser()
    if not raw_path:
        raise CheckError(f"{label} path is empty. {remedy}")
    if not path.exists():
        raise CheckError(f"Missing {label}: {_path_text(path)}. {remedy}")
    if not path.is_file():
        raise CheckError(f"{label} is not a file: {_path_text(path)}. {remedy}")
    if path.stat().st_size == 0:
        raise CheckError(f"{label} is empty: {_path_text(path)}. {remedy}")
    return path


def check_classes(raw_path: str, num_classes: int, allow_mismatch: bool) -> Dict[str, Any]:
    path = require_file(
        raw_path,
        "class-name file",
        "Pass --classes pointing to the .names file used by the frozen graph.",
    )
    names: List[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            name = line.strip()
            if name:
                names.append(name)

    if not names:
        raise CheckError(f"Class-name file has no non-empty names: {_path_text(path)}.")

    unique_count = len(set(names))
    warnings: List[str] = []
    if unique_count != len(names):
        warnings.append(
            f"class-name file contains {len(names) - unique_count} duplicate non-empty name(s)"
        )

    if len(names) != num_classes:
        message = (
            f"Class count mismatch: {_path_text(path)} contains {len(names)} non-empty "
            f"name(s), but --num-classes is {num_classes}. The prediction reshape uses "
            f"5 + num_classes, so this mismatch can corrupt detections."
        )
        if allow_mismatch:
            warnings.append(message)
        else:
            raise CheckError(message + " Pass --num-classes correctly or use --allow-class-count-mismatch only for exploratory checks.")

    return {
        "path": _path_text(path),
        "count": len(names),
        "first": names[0],
        "last": names[-1],
        "warnings": warnings,
    }


def check_anchors(raw_path: str) -> Dict[str, Any]:
    path = require_file(
        raw_path,
        "anchor file",
        "Pass --anchors pointing to the anchor file used when the graph was built.",
    )
    with path.open("r", encoding="utf-8") as handle:
        line = handle.readline()
    line = line.split("#", 1)[0].strip()
    parts = [part for part in re.split(r"[,\s]+", line) if part]
    if len(parts) != 18:
        raise CheckError(
            f"Anchor file must contain 18 numeric values for shape (3, 3, 2); "
            f"found {len(parts)} value(s) in {_path_text(path)}."
        )

    values: List[float] = []
    for part in parts:
        try:
            value = float(part)
        except ValueError as exc:
            raise CheckError(f"Anchor value is not numeric in {_path_text(path)}: {part!r}.") from exc
        if value <= 0:
            raise CheckError(f"Anchor values must be positive in {_path_text(path)}; found {value}.")
        values.append(value)

    anchors = [
        [[values[(scale * 6) + (anchor * 2)], values[(scale * 6) + (anchor * 2) + 1]] for anchor in range(3)]
        for scale in range(3)
    ]
    return {
        "path": _path_text(path),
        "count": len(values),
        "shape": [3, 3, 2],
        "anchors": anchors,
    }


def check_image(raw_path: str) -> Dict[str, Any]:
    path = require_file(
        raw_path,
        "image file",
        "Pass --image pointing to a readable image, or provide a representative frame for video/camera checks.",
    )
    result: Dict[str, Any] = {"path": _path_text(path), "warnings": []}
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user environment
        result["warnings"].append(
            "Pillow is not importable, so only existence/non-empty image checks were performed: "
            f"{exc.__class__.__name__}: {exc}"
        )
        return result

    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
            mode = image.mode
    except Exception as exc:
        raise CheckError(
            f"Image file exists but Pillow could not read it: {_path_text(path)}. "
            f"Use a valid image file. Original error: {exc.__class__.__name__}: {exc}"
        ) from exc

    if width <= 0 or height <= 0:
        raise CheckError(f"Image has invalid dimensions {width}x{height}: {_path_text(path)}.")

    result.update({"width": width, "height": height, "mode": mode})
    return result


def _load_tensorflow() -> Any:
    try:
        import tensorflow as tf  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user environment
        raise CheckError(
            "TensorFlow is required for PB tensor-name inspection but is not importable. "
            "Install a TensorFlow 1.x-compatible runtime, use TensorFlow 2.x compat.v1 APIs, "
            "or pass --skip-graph-inspection to perform only path/classes/anchors/image checks. "
            f"Original import error: {exc.__class__.__name__}: {exc}"
        ) from exc
    return tf


def _tf_v1(tf: Any) -> Any:
    compat = getattr(tf, "compat", None)
    return getattr(compat, "v1", tf) if compat is not None else tf


def _tf_graph_def_cls(tf: Any) -> Any:
    v1 = _tf_v1(tf)
    graph_def_cls = getattr(v1, "GraphDef", None) or getattr(tf, "GraphDef", None)
    if graph_def_cls is None:
        raise CheckError("TensorFlow does not expose GraphDef; cannot inspect frozen PB tensors.")
    return graph_def_cls


def _tf_gfile(tf: Any) -> Any:
    v1 = _tf_v1(tf)
    gfile_mod = getattr(v1, "gfile", None) or getattr(tf, "gfile", None)
    if gfile_mod is not None:
        gfile_cls = getattr(gfile_mod, "GFile", None) or getattr(gfile_mod, "FastGFile", None)
        if gfile_cls is not None:
            return gfile_cls
    io_mod = getattr(tf, "io", None)
    if io_mod is not None:
        io_gfile_mod = getattr(io_mod, "gfile", None)
        if io_gfile_mod is not None:
            gfile_cls = getattr(io_gfile_mod, "GFile", None)
            if gfile_cls is not None:
                return gfile_cls
    raise CheckError("TensorFlow does not expose a GFile reader; cannot inspect frozen PB tensors.")


def _tf_graph_cls(tf: Any) -> Any:
    v1 = _tf_v1(tf)
    graph_cls = getattr(v1, "Graph", None) or getattr(tf, "Graph", None)
    if graph_cls is None:
        raise CheckError("TensorFlow does not expose Graph; cannot inspect frozen PB tensors.")
    return graph_cls


def _tf_import_graph_def(tf: Any) -> Any:
    v1 = _tf_v1(tf)
    import_graph_def = getattr(v1, "import_graph_def", None) or getattr(tf, "import_graph_def", None)
    if import_graph_def is None:
        raise CheckError("TensorFlow does not expose import_graph_def; cannot inspect frozen PB tensors.")
    return import_graph_def


def _shape_list(tensor: Any) -> List[Any]:
    shape = getattr(tensor, "shape", None)
    if shape is not None:
        try:
            return list(shape.as_list())
        except Exception:
            try:
                return list(shape)
            except Exception:
                pass
    get_shape = getattr(tensor, "get_shape", None)
    if get_shape is not None:
        try:
            return list(get_shape().as_list())
        except Exception:
            pass
    return []


def inspect_pb_tensors(raw_path: str, expected_tensors: Sequence[str], num_classes: int, input_size: int) -> Dict[str, Any]:
    path = require_file(
        raw_path,
        "frozen PB graph",
        "Pass --pb pointing to the frozen graph, usually ./yolov3_coco.pb after conversion/freezing.",
    )
    tf = _load_tensorflow()
    graph_def_cls = _tf_graph_def_cls(tf)
    gfile_cls = _tf_gfile(tf)
    graph_cls = _tf_graph_cls(tf)
    import_graph_def = _tf_import_graph_def(tf)

    graph_def = graph_def_cls()
    try:
        with gfile_cls(str(path), "rb") as handle:
            graph_def.ParseFromString(handle.read())
    except Exception as exc:
        raise CheckError(
            f"Could not parse frozen PB graph {_path_text(path)}. Confirm this is a TensorFlow GraphDef .pb file. "
            f"Original error: {exc.__class__.__name__}: {exc}"
        ) from exc

    node_names = [node.name for node in getattr(graph_def, "node", [])]
    missing_by_node = [tensor for tensor in expected_tensors if tensor.split(":", 1)[0] not in node_names]

    graph = graph_cls()
    try:
        with graph.as_default():
            returned = import_graph_def(graph_def, return_elements=list(expected_tensors), name="")
    except Exception as exc:
        missing_text = f" Missing node(s) by name precheck: {', '.join(missing_by_node)}." if missing_by_node else ""
        raise CheckError(
            f"Frozen graph imported, but one or more expected return tensors were not found in {_path_text(path)}."
            f" Expected: {', '.join(expected_tensors)}.{missing_text} Original error: {exc.__class__.__name__}: {exc}"
        ) from exc

    tensor_infos: List[Dict[str, Any]] = []
    warnings: List[str] = []
    expected_last_dim = 5 + num_classes
    for index, tensor in enumerate(returned):
        name = getattr(tensor, "name", expected_tensors[index])
        shape = _shape_list(tensor)
        tensor_infos.append({"name": name, "shape": shape})
        if index == 0 and shape:
            if len(shape) >= 4 and shape[-1] not in (None, 3):
                warnings.append(f"input tensor last dimension is {shape[-1]}, expected 3 channels")
            if len(shape) >= 3:
                for dim_index, label in ((1, "height"), (2, "width")):
                    dim = shape[dim_index]
                    if dim not in (None, input_size):
                        warnings.append(
                            f"input tensor {label} dimension is {dim}, but --input-size is {input_size}"
                        )
        if index > 0 and shape:
            last_dim = shape[-1]
            if last_dim not in (None, expected_last_dim):
                warnings.append(
                    f"prediction tensor {name} final dimension is {last_dim}, expected 5 + num_classes = {expected_last_dim}"
                )

    return {
        "path": _path_text(path),
        "node_count": len(node_names),
        "expected_tensors": list(expected_tensors),
        "returned_tensors": tensor_infos,
        "warnings": warnings,
    }


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {parsed}")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check tensorflow-yolov3 frozen .pb inference prerequisites without running model inference. "
            "Validates PB/image/classes/anchors paths and expected tensor names."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--pb", default="./yolov3_coco.pb", help="Frozen TensorFlow GraphDef .pb file.")
    parser.add_argument("--image", default="./docs/images/road.jpeg", help="Image file or representative video frame to validate.")
    parser.add_argument("--classes", default="./data/classes/coco.names", help="Class-name file, one class per line.")
    parser.add_argument("--anchors", default="./data/anchors/basline_anchors.txt", help="Anchor file with 18 comma-separated values.")
    parser.add_argument("--input-size", type=positive_int, default=416, help="Inference letterbox size used for the feed tensor.")
    parser.add_argument("--num-classes", type=positive_int, default=80, help="Number of classes used when reshaping prediction tensors.")
    parser.add_argument(
        "--expected-tensors",
        nargs="+",
        default=list(DEFAULT_EXPECTED_TENSORS),
        help="Expected frozen-graph return tensor names, including :0 tensor suffixes.",
    )
    parser.add_argument(
        "--allow-class-count-mismatch",
        action="store_true",
        help="Warn instead of failing when --classes line count differs from --num-classes.",
    )
    parser.add_argument(
        "--skip-graph-inspection",
        action="store_true",
        help="Skip TensorFlow PB parsing/tensor-name checks; path/classes/anchors/image checks still run.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of human-readable text.")
    return parser


def flatten_warnings(checks: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    for check_name, info in checks.items():
        if isinstance(info, dict):
            for warning in info.get("warnings", []) or []:
                warnings.append(f"{check_name}: {warning}")
    return warnings


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result: Dict[str, Any] = {
        "ok": False,
        "checks": {},
        "warnings": [],
        "errors": [],
        "inference_run": False,
    }

    try:
        result["checks"]["classes"] = check_classes(
            args.classes, args.num_classes, args.allow_class_count_mismatch
        )
        result["checks"]["anchors"] = check_anchors(args.anchors)
        result["checks"]["image"] = check_image(args.image)
        if args.skip_graph_inspection:
            require_file(
                args.pb,
                "frozen PB graph",
                "Pass --pb pointing to the frozen graph, usually ./yolov3_coco.pb after conversion/freezing.",
            )
            result["checks"]["graph"] = {
                "path": args.pb,
                "skipped": True,
                "warnings": ["graph tensor-name inspection skipped by --skip-graph-inspection"],
            }
        else:
            result["checks"]["graph"] = inspect_pb_tensors(
                args.pb, args.expected_tensors, args.num_classes, args.input_size
            )
        result["warnings"] = flatten_warnings(result["checks"])
        result["ok"] = True
    except CheckError as exc:
        result["errors"].append(str(exc))
        result["warnings"] = flatten_warnings(result["checks"])
    except KeyboardInterrupt:
        result["errors"].append("Interrupted by user.")

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        if result["ok"]:
            print("OK: tensorflow-yolov3 frozen-PB inference contract checks passed.")
        else:
            print("ERROR: tensorflow-yolov3 frozen-PB inference contract checks failed.", file=sys.stderr)
        for check_name, info in result["checks"].items():
            if not isinstance(info, dict):
                continue
            if check_name == "classes":
                print(
                    f"OK classes: {info['count']} name(s) in {info['path']} "
                    f"(first={info['first']!r}, last={info['last']!r})"
                )
            elif check_name == "anchors":
                print(f"OK anchors: {info['count']} value(s), shape {info['shape']} in {info['path']}")
            elif check_name == "image":
                if "width" in info:
                    print(f"OK image: {info['width']}x{info['height']} {info['mode']} in {info['path']}")
                else:
                    print(f"OK image path: {info['path']}")
            elif check_name == "graph" and info.get("skipped"):
                print(f"OK PB path: {info['path']} (graph tensor inspection skipped)")
            elif check_name == "graph":
                print(f"OK graph: {info['node_count']} node(s) in {info['path']}")
                for tensor in info.get("returned_tensors", []):
                    print(f"  tensor {tensor['name']} shape={tensor['shape']}")
        for warning in result["warnings"]:
            print(f"WARNING: {warning}", file=sys.stderr)
        for error in result["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
        print("No model inference was run.")

    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
