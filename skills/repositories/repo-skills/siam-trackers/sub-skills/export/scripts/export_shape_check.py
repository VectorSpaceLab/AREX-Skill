#!/usr/bin/env python3
"""Validate the NanoTrackV3 split-export contract without writing artifacts.

The default mode checks the canonical tensor/opset arguments. Optional ONNX
inspection requires the caller to install ``onnx``. This script never exports,
downloads, creates directories, or overwrites files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


EXPECTED = {
    "backbone_input": (1, 3, 255, 255),
    "backbone_output": (1, 96, 16, 16),
    "head_template": (1, 96, 8, 8),
    "head_search": (1, 96, 16, 16),
    "head_cls": (1, 2, 15, 15),
    "head_loc": (1, 4, 15, 15),
}
EXPECTED_OPSET = 14


def parse_shape(text: str) -> tuple[int, int, int, int]:
    """Parse an NCHW shape written as 1,3,255,255 or 1x3x255x255."""
    normalized = text.lower().replace("x", ",")
    parts = [part.strip() for part in normalized.split(",") if part.strip()]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(
            f"expected four NCHW integers, got {text!r}"
        )
    try:
        shape = tuple(int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"non-integer shape {text!r}") from exc
    if any(value <= 0 for value in shape):
        raise argparse.ArgumentTypeError(f"shape values must be positive: {text!r}")
    return shape  # type: ignore[return-value]


def shape_text(shape: Iterable[Any]) -> str:
    return "[" + ",".join("?" if value is None else str(value) for value in shape) + "]"


def add_error(errors: list[str], condition: bool, message: str) -> None:
    if condition:
        errors.append(message)


def safe_artifact_path(
    root: Path, relative_name: str, allow_existing: bool, errors: list[str]
) -> Path | None:
    candidate_name = Path(relative_name)
    if candidate_name.is_absolute():
        errors.append(f"artifact name must be relative: {relative_name!r}")
        return None
    if not candidate_name.parts or any(part in {"", ".", ".."} for part in candidate_name.parts):
        errors.append(f"artifact name contains an unsafe path component: {relative_name!r}")
        return None
    if candidate_name.suffix.lower() != ".onnx":
        errors.append(f"artifact name must end in .onnx: {relative_name!r}")
        return None

    resolved_root = root.expanduser().resolve(strict=False)
    resolved_target = (resolved_root / candidate_name).resolve(strict=False)
    try:
        resolved_target.relative_to(resolved_root)
    except ValueError:
        errors.append(f"artifact escapes staging root: {relative_name!r}")
        return None

    if resolved_target.exists() and not allow_existing:
        errors.append(
            f"artifact already exists (checker will not approve overwrite): {resolved_target}"
        )
    return resolved_target


def tensor_shape(value_info: Any) -> tuple[int | None, ...]:
    dims: list[int | None] = []
    for dim in value_info.type.tensor_type.shape.dim:
        if dim.HasField("dim_value") and dim.dim_value > 0:
            dims.append(int(dim.dim_value))
        else:
            dims.append(None)
    return tuple(dims)


def compare_signature(
    *,
    model_path: Path,
    expected_inputs: dict[str, tuple[int, ...]],
    expected_outputs: dict[str, tuple[int, ...]],
    allow_dynamic: bool,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any] | None:
    if not model_path.is_file():
        errors.append(f"ONNX model is not a readable file: {model_path}")
        return None
    try:
        import onnx  # type: ignore[import-not-found]
    except ImportError:
        errors.append(
            "optional dependency 'onnx' is required when --backbone-model or "
            "--head-model is supplied"
        )
        return None

    try:
        model = onnx.load(str(model_path), load_external_data=False)
        onnx.checker.check_model(model)
    except Exception as exc:  # onnx exposes multiple checker/parser exceptions
        errors.append(f"ONNX load/check failed for {model_path}: {type(exc).__name__}: {exc}")
        return None

    initializer_names = {item.name for item in model.graph.initializer}
    actual_inputs = {
        item.name: tensor_shape(item)
        for item in model.graph.input
        if item.name not in initializer_names
    }
    actual_outputs = {item.name: tensor_shape(item) for item in model.graph.output}

    def compare_group(
        label: str,
        actual: dict[str, tuple[int | None, ...]],
        expected: dict[str, tuple[int, ...]],
    ) -> None:
        if set(actual) != set(expected):
            errors.append(
                f"{model_path} {label} names are {sorted(actual)}, expected {sorted(expected)}"
            )
        for name, expected_shape in expected.items():
            if name not in actual:
                continue
            actual_shape = actual[name]
            if len(actual_shape) != len(expected_shape):
                errors.append(
                    f"{model_path} {name} rank {len(actual_shape)}, expected {len(expected_shape)}"
                )
                continue
            for index, (found, wanted) in enumerate(zip(actual_shape, expected_shape)):
                if found is None:
                    if allow_dynamic:
                        warnings.append(
                            f"{model_path} {name} axis {index} is dynamic; canonical sample value is {wanted}"
                        )
                    else:
                        errors.append(
                            f"{model_path} {name} axis {index} is dynamic; expected static {wanted}"
                        )
                elif found != wanted:
                    errors.append(
                        f"{model_path} {name} shape {shape_text(actual_shape)}, "
                        f"expected {shape_text(expected_shape)}"
                    )
                    break

    compare_group("input", actual_inputs, expected_inputs)
    compare_group("output", actual_outputs, expected_outputs)

    default_opsets = [
        int(item.version) for item in model.opset_import if item.domain in {"", "ai.onnx"}
    ]
    if default_opsets != [EXPECTED_OPSET]:
        errors.append(
            f"{model_path} default ONNX opset imports are {default_opsets}, "
            f"expected [{EXPECTED_OPSET}]"
        )

    return {
        "path": str(model_path.resolve()),
        "inputs": {name: list(shape) for name, shape in actual_inputs.items()},
        "outputs": {name: list(shape) for name, shape in actual_outputs.items()},
        "default_opsets": default_opsets,
        "onnx_checker": "passed",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="No-write validation for the canonical NanoTrackV3 split ONNX contract."
    )
    parser.add_argument("--backbone-input", type=parse_shape, default=EXPECTED["backbone_input"])
    parser.add_argument("--backbone-output", type=parse_shape, default=EXPECTED["backbone_output"])
    parser.add_argument("--head-template", type=parse_shape, default=EXPECTED["head_template"])
    parser.add_argument("--head-search", type=parse_shape, default=EXPECTED["head_search"])
    parser.add_argument("--head-cls", type=parse_shape, default=EXPECTED["head_cls"])
    parser.add_argument("--head-loc", type=parse_shape, default=EXPECTED["head_loc"])
    parser.add_argument("--opset", type=int, default=EXPECTED_OPSET)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--backbone-name", help="Relative planned artifact name; no file is written.")
    parser.add_argument("--head-name", help="Relative planned artifact name; no file is written.")
    parser.add_argument(
        "--allow-existing",
        action="store_true",
        help="Acknowledge existing planned paths. This checker still never overwrites them.",
    )
    parser.add_argument("--backbone-model", type=Path, help="Existing ONNX file to inspect.")
    parser.add_argument("--head-model", type=Path, help="Existing ONNX file to inspect.")
    parser.add_argument(
        "--allow-dynamic",
        action="store_true",
        help="Permit symbolic ONNX dimensions while checking known dimensions and names.",
    )
    parser.add_argument("--json-indent", type=int, default=2)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []

    provided_shapes = {
        "backbone_input": args.backbone_input,
        "backbone_output": args.backbone_output,
        "head_template": args.head_template,
        "head_search": args.head_search,
        "head_cls": args.head_cls,
        "head_loc": args.head_loc,
    }
    for name, wanted in EXPECTED.items():
        found = provided_shapes[name]
        add_error(
            errors,
            found != wanted,
            f"{name} is {shape_text(found)}, expected canonical {shape_text(wanted)}",
        )
    add_error(errors, args.opset != EXPECTED_OPSET, f"opset is {args.opset}, expected {EXPECTED_OPSET}")

    planning_values = (args.artifact_root, args.backbone_name, args.head_name)
    if any(value is not None for value in planning_values) and not all(
        value is not None for value in planning_values
    ):
        errors.append(
            "artifact planning requires --artifact-root, --backbone-name, and --head-name together"
        )

    planned: dict[str, str] | None = None
    if all(value is not None for value in planning_values):
        root = args.artifact_root
        assert root is not None and args.backbone_name is not None and args.head_name is not None
        backbone_target = safe_artifact_path(root, args.backbone_name, args.allow_existing, errors)
        head_target = safe_artifact_path(root, args.head_name, args.allow_existing, errors)
        if backbone_target is not None and head_target is not None:
            if backbone_target == head_target:
                errors.append("backbone and head artifact targets must be different")
            planned = {
                "artifact_root": str(root.expanduser().resolve(strict=False)),
                "backbone": str(backbone_target),
                "head": str(head_target),
            }
            if not root.expanduser().exists():
                warnings.append("artifact root does not exist; checker did not create it")

    inspected: dict[str, Any] = {}
    if (args.backbone_model is None) != (args.head_model is None):
        errors.append("ONNX inspection requires --backbone-model and --head-model together")
    elif args.backbone_model is not None and args.head_model is not None:
        inspected["backbone"] = compare_signature(
            model_path=args.backbone_model,
            expected_inputs={"input": EXPECTED["backbone_input"]},
            expected_outputs={"output": EXPECTED["backbone_output"]},
            allow_dynamic=args.allow_dynamic,
            errors=errors,
            warnings=warnings,
        )
        inspected["head"] = compare_signature(
            model_path=args.head_model,
            expected_inputs={
                "input1": EXPECTED["head_template"],
                "input2": EXPECTED["head_search"],
            },
            expected_outputs={
                "output1": EXPECTED["head_cls"],
                "output2": EXPECTED["head_loc"],
            },
            allow_dynamic=args.allow_dynamic,
            errors=errors,
            warnings=warnings,
        )

    result = {
        "status": "error" if errors else "ok",
        "writes_performed": False,
        "contract": {
            "variant": "NanoTrackV3",
            "opset": EXPECTED_OPSET,
            "backbone": {
                "inputs": {"input": list(EXPECTED["backbone_input"])},
                "outputs": {"output": list(EXPECTED["backbone_output"])},
            },
            "head": {
                "inputs": {
                    "input1": list(EXPECTED["head_template"]),
                    "input2": list(EXPECTED["head_search"]),
                },
                "outputs": {
                    "output1": list(EXPECTED["head_cls"]),
                    "output2": list(EXPECTED["head_loc"]),
                },
            },
        },
        "planned_artifacts": planned,
        "inspected_models": inspected or None,
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(result, indent=max(0, args.json_indent), sort_keys=True))
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
