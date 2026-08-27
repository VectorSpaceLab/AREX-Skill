#!/usr/bin/env python3
"""Validate Stable Diffusion WebUI preprocessing plans without image/model imports."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

KNOWN_OPERATIONS = {
    "split_oversized",
    "autosized_crop",
    "focal_crop",
    "create_flipped_copies",
    "caption",
    "upscale",
    "face_restoration",
}

CAPTION_MODELS = {"BLIP", "Deepbooru"}
FLIP_OPTIONS = {"Horizontal", "Vertical", "Both"}
FACE_RESTORERS = {"GFPGAN", "CodeFormer"}
OBJECTIVES = {"Maximize area", "Minimize error"}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def as_operation_name(operation: Any) -> str | None:
    if isinstance(operation, str):
        return operation
    if isinstance(operation, dict):
        name = operation.get("operation", operation.get("name", operation.get("type")))
        return name if isinstance(name, str) else None
    return None


def normalize_operation(operation: Any) -> dict[str, Any]:
    if isinstance(operation, str):
        return {"operation": operation}
    if isinstance(operation, dict):
        data = dict(operation)
        name = as_operation_name(data)
        if name is not None:
            data["operation"] = name
        return data
    return {"operation": None, "_raw": operation}


def require_bool(operation: dict[str, Any], key: str, errors: list[str]) -> None:
    if key in operation and not isinstance(operation[key], bool):
        errors.append(f"{operation['operation']}.{key} must be a boolean")


def require_number_range(
    operation: dict[str, Any],
    key: str,
    errors: list[str],
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    integer: bool = False,
    required: bool = False,
) -> None:
    value = operation.get(key)
    name = operation["operation"]
    if value is None:
        if required:
            errors.append(f"{name}.{key} is required")
        return
    if integer:
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{name}.{key} must be an integer")
            return
    elif not is_number(value):
        errors.append(f"{name}.{key} must be a number")
        return
    if minimum is not None and value < minimum:
        errors.append(f"{name}.{key} must be >= {minimum}")
    if maximum is not None and value > maximum:
        errors.append(f"{name}.{key} must be <= {maximum}")


def require_string(operation: dict[str, Any], key: str, errors: list[str], *, required: bool = False, allow_none_name: bool = False) -> None:
    value = operation.get(key)
    name = operation["operation"]
    if value is None:
        if required:
            errors.append(f"{name}.{key} is required")
        return
    if allow_none_name and value == "None":
        return
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{name}.{key} must be a non-empty string")


def list_image_like_files(path: str) -> list[str]:
    try:
        entries = os.listdir(path)
    except OSError:
        return []
    return [entry for entry in entries if os.path.splitext(entry)[1].lower() in IMAGE_EXTENSIONS]


def validate_top_level(plan: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    source_dir = plan.get("source_dir")
    output_dir = plan.get("output_dir")

    if not isinstance(source_dir, str) or not source_dir.strip():
        errors.append("source_dir is required and must be a non-empty string")
    elif not os.path.isdir(source_dir):
        errors.append("source_dir must exist and be a directory")
    else:
        image_files = list_image_like_files(source_dir)
        if not image_files:
            warnings.append("source_dir contains no obvious image files by extension")

    if not isinstance(output_dir, str) or not output_dir.strip():
        errors.append("output_dir is required and must be a non-empty string")
    elif os.path.exists(output_dir) and not os.path.isdir(output_dir):
        errors.append("output_dir exists but is not a directory")

    if isinstance(source_dir, str) and isinstance(output_dir, str):
        source_abs = os.path.abspath(source_dir)
        output_abs = os.path.abspath(output_dir)
        if source_abs == output_abs:
            if plan.get("allow_in_place") is True:
                warnings.append("output_dir matches source_dir; in-place preprocessing can overwrite captions/images")
            else:
                errors.append("output_dir must differ from source_dir unless allow_in_place is true")

    for key in ("target_width", "target_height"):
        value = plan.get(key)
        if value is not None:
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                errors.append(f"{key} must be a positive integer when provided")
            elif value % 8 != 0:
                warnings.append(f"{key} is not divisible by 8; training sizes usually use multiples of 8")

    operations = plan.get("operations")
    if not isinstance(operations, list) or not operations:
        errors.append("operations must be a non-empty list")

    if "expected_image_count" in plan:
        value = plan["expected_image_count"]
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append("expected_image_count must be a positive integer")
        elif value > 500:
            warnings.append("large expected_image_count can make captioning, upscaling, and face restoration slow")


def operation_enabled(operation: dict[str, Any]) -> bool:
    enabled = operation.get("enable", operation.get("enabled", True))
    return enabled is not False


def validate_operation(
    operation: dict[str, Any],
    index: int,
    plan: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    infos: list[str],
) -> None:
    name = operation.get("operation")
    prefix = f"operations[{index}]"
    if not isinstance(name, str) or not name:
        errors.append(f"{prefix} must specify operation/name/type")
        return
    if name not in KNOWN_OPERATIONS:
        errors.append(f"{prefix}.operation {name!r} is not supported; expected one of {sorted(KNOWN_OPERATIONS)}")
        return

    require_bool(operation, "enable", errors)
    require_bool(operation, "enabled", errors)
    if not operation_enabled(operation):
        infos.append(f"{name} is disabled and will be skipped")
        return

    target_width = plan.get("target_width")
    target_height = plan.get("target_height")

    if name == "split_oversized":
        if not target_width or not target_height:
            errors.append("split_oversized requires top-level target_width and target_height")
        require_number_range(operation, "split_threshold", errors, minimum=0.0, maximum=1.0)
        require_number_range(operation, "overlap_ratio", errors, minimum=0.0, maximum=0.9)
        if operation.get("overlap_ratio", 0) and operation.get("overlap_ratio", 0) > 0.5:
            warnings.append("split_oversized.overlap_ratio above 0.5 can multiply output count substantially")

    elif name == "autosized_crop":
        require_number_range(operation, "mindim", errors, minimum=64, maximum=2048, integer=True)
        require_number_range(operation, "maxdim", errors, minimum=64, maximum=2048, integer=True)
        require_number_range(operation, "minarea", errors, minimum=64 * 64, maximum=2048 * 2048, integer=True)
        require_number_range(operation, "maxarea", errors, minimum=64 * 64, maximum=2048 * 2048, integer=True)
        require_number_range(operation, "threshold", errors, minimum=0.0, maximum=1.0)
        objective = operation.get("objective")
        if objective is not None and objective not in OBJECTIVES:
            errors.append(f"autosized_crop.objective must be one of {sorted(OBJECTIVES)}")
        if operation.get("mindim") and operation.get("maxdim") and operation["mindim"] > operation["maxdim"]:
            errors.append("autosized_crop.mindim must be <= maxdim")
        if operation.get("minarea") and operation.get("maxarea") and operation["minarea"] > operation["maxarea"]:
            errors.append("autosized_crop.minarea must be <= maxarea")

    elif name == "focal_crop":
        if not target_width or not target_height:
            errors.append("focal_crop requires top-level target_width and target_height")
        for key in ("face_weight", "entropy_weight", "edges_weight"):
            require_number_range(operation, key, errors, minimum=0.0, maximum=1.0)
        require_bool(operation, "debug", errors)
        warnings.append("focal_crop may require face detection model availability and can fall back to lower-quality detection")

    elif name == "create_flipped_copies":
        options = operation.get("option", operation.get("options", []))
        if isinstance(options, str):
            options = [options]
        if not isinstance(options, list) or not options:
            errors.append("create_flipped_copies.option/options must include at least one flip option")
        else:
            bad = [value for value in options if value not in FLIP_OPTIONS]
            if bad:
                errors.append(f"create_flipped_copies has invalid options {bad}; expected {sorted(FLIP_OPTIONS)}")
            if "Both" in options or len(options) > 1:
                warnings.append("create_flipped_copies can double or triple the effective dataset size")

    elif name == "caption":
        options = operation.get("option", operation.get("models", []))
        if isinstance(options, str):
            options = [options]
        if not isinstance(options, list) or not options:
            errors.append("caption.option/models must include BLIP, Deepbooru, or both")
        else:
            bad = [value for value in options if value not in CAPTION_MODELS]
            if bad:
                errors.append(f"caption has invalid models {bad}; expected {sorted(CAPTION_MODELS)}")
            warnings.append("captioning requires the selected BLIP/DeepBooru backend models to be available")
        existing = operation.get("existing_caption_action")
        if existing is not None and existing not in {"Prepend", "Append", "Keep", "Overwrite"}:
            errors.append("caption.existing_caption_action must be Prepend, Append, Keep, or Overwrite")

    elif name == "upscale":
        mode = operation.get("resize_mode", operation.get("upscale_mode", 0))
        if mode not in (0, 1):
            errors.append("upscale.resize_mode/upscale_mode must be 0 (scale by) or 1 (scale to)")
        if mode == 0:
            require_number_range(operation, "upscaling_resize", errors, minimum=0.05)
            require_number_range(operation, "max_side_length", errors, minimum=0, integer=True)
            if operation.get("upscaling_resize", 0) > 4:
                warnings.append("upscaling_resize above 4 can be slow and memory intensive")
        if mode == 1:
            require_number_range(operation, "upscaling_resize_w", errors, minimum=1, integer=True, required=True)
            require_number_range(operation, "upscaling_resize_h", errors, minimum=1, integer=True, required=True)
            require_bool(operation, "upscaling_crop", errors)
        require_string(operation, "upscaler_1", errors, allow_none_name=True)
        require_string(operation, "upscaler_2", errors, allow_none_name=True)
        require_number_range(operation, "extras_upscaler_2_visibility", errors, minimum=0.0, maximum=1.0)
        warnings.append("upscale requires requested upscaler names to exist in the running WebUI")

    elif name == "face_restoration":
        restorer = operation.get("restorer")
        if restorer is not None and restorer not in FACE_RESTORERS:
            errors.append(f"face_restoration.restorer must be one of {sorted(FACE_RESTORERS)}")
        require_number_range(operation, "gfpgan_visibility", errors, minimum=0.0, maximum=1.0)
        require_number_range(operation, "codeformer_visibility", errors, minimum=0.0, maximum=1.0)
        require_number_range(operation, "codeformer_weight", errors, minimum=0.0, maximum=1.0)
        if operation.get("gfpgan_visibility", 0) == 0 and operation.get("codeformer_visibility", 0) == 0 and not restorer:
            warnings.append("face_restoration has no visible restorer effect configured")
        warnings.append("face_restoration requires GFPGAN/CodeFormer weights and backend availability")


def validate_plan(plan: Any) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    infos: list[str] = []

    if not isinstance(plan, dict):
        return ["plan root must be a JSON object"], warnings, infos

    validate_top_level(plan, errors, warnings)

    raw_operations = plan.get("operations")
    if isinstance(raw_operations, list):
        normalized = [normalize_operation(operation) for operation in raw_operations]
        for index, operation in enumerate(normalized):
            validate_operation(operation, index, plan, errors, warnings, infos)

        names = [operation.get("operation") for operation in normalized if operation_enabled(operation)]
        if "caption" in names and names.index("caption") < len(names) - 1:
            warnings.append("caption usually belongs near the end so generated captions match final images")
        if "split_oversized" in names and "create_flipped_copies" in names:
            warnings.append("splitting plus flipped copies can expand output count quickly")
        if "upscale" in names and ("autosized_crop" in names or "focal_crop" in names):
            infos.append("upscale/crop order should be intentional because target dimensions affect later splits/crops")

    return errors, warnings, infos


def load_plan(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Stable Diffusion WebUI preprocessing plan JSON file.")
    parser.add_argument("plan", help="Path to a preprocessing plan JSON file")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable validation result")
    args = parser.parse_args(argv)

    try:
        plan = load_plan(args.plan)
    except json.JSONDecodeError as exc:
        result = {"ok": False, "errors": [f"invalid JSON: {exc}"], "warnings": [], "infos": []}
    except OSError as exc:
        result = {"ok": False, "errors": [f"cannot read plan: {exc}"], "warnings": [], "infos": []}
    else:
        errors, warnings, infos = validate_plan(plan)
        result = {"ok": not errors, "errors": errors, "warnings": warnings, "infos": infos}

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = "OK" if result["ok"] else "FAILED"
        print(f"Preprocess plan validation: {status}")
        for label in ("errors", "warnings", "infos"):
            values = result[label]
            if values:
                print(f"\n{label}:")
                for value in values:
                    print(f"- {value}")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
