#!/usr/bin/env python3
"""Safe NanoTrack inference preflight and minimal config generator.

This tool never imports NanoTrack, loads a checkpoint, downloads assets, decodes
video, accesses a camera, or opens a GUI. Its default run validates a synthetic
BGR frame declaration and initialization box on CPU.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import sys
from pathlib import Path
from typing import Any


PROFILES: dict[str, dict[str, Any]] = {
    "v1": {
        "backbone": "mobilenetv3_small",
        "head_module": "nanotrack.models.head.ban_v1",
        "channels": 64,
        "stride": 16,
        "output_size": 16,
        "window_influence": 0.462,
        "penalty_k": 0.148,
        "lr": 0.390,
    },
    "v2": {
        "backbone": "mobilenetv3_small",
        "head_module": "nanotrack.models.head.ban_v2",
        "channels": 64,
        "stride": 16,
        "output_size": 16,
        "window_influence": 0.490,
        "penalty_k": 0.150,
        "lr": 0.385,
    },
    "v3": {
        "backbone": "mobilenetv3_small_v3",
        "head_module": "nanotrack.models.head.ban_v3",
        "channels": 96,
        "stride": 16,
        "output_size": 15,
        "window_influence": 0.455,
        "penalty_k": 0.138,
        "lr": 0.348,
    },
}


class ConfigError(ValueError):
    """Raised when an explicit config cannot be parsed safely."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate NanoTrack V1/V2/V3 inference arguments or write a minimal "
            "inference-only YAML. No weights are loaded and no GUI/network I/O occurs."
        )
    )
    parser.add_argument(
        "--variant",
        choices=sorted(PROFILES),
        default="v2",
        help="matched model/config/head variant (default: v2)",
    )
    parser.add_argument(
        "--frame-shape",
        metavar=("HEIGHT", "WIDTH", "CHANNELS"),
        type=int,
        nargs=3,
        default=(240, 320, 3),
        help="declared H W C shape; synthetic default is 240 320 3",
    )
    parser.add_argument(
        "--bbox",
        metavar=("X", "Y", "WIDTH", "HEIGHT"),
        type=float,
        nargs=4,
        default=(40.0, 30.0, 80.0, 60.0),
        help="zero-based initialization box in x y width height order",
    )
    parser.add_argument(
        "--color-order",
        choices=("BGR", "RGB", "GRAY", "BGRA"),
        default="BGR",
        help="declared frame color order; NanoTrack requires BGR",
    )
    parser.add_argument(
        "--dtype",
        default="uint8",
        help="declared frame dtype; safe tracker boundary requires uint8",
    )
    parser.add_argument(
        "--allow-partial-bbox",
        action="store_true",
        help="allow a partially out-of-frame box when it still intersects the frame",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="cpu",
        help="device policy; deterministic default is cpu",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="optional existing YAML to inspect; no implicit config path is used",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        help="optional checkpoint path to existence-check; contents are never loaded",
    )
    parser.add_argument(
        "--require-checkpoint",
        action="store_true",
        help="fail unless --checkpoint names an existing regular file",
    )
    parser.add_argument(
        "--write-config",
        type=Path,
        help="write the selected minimal inference YAML to this explicit path",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="permit --write-config to replace an existing regular file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit one JSON report instead of human-readable lines",
    )
    return parser


def _without_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote == '"':
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if char == "#" and quote is None:
            return line[:index]
    return line


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none", "~"}:
        return None
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value.strip()


def _set_nested(root: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    current = root
    for key in path[:-1]:
        child = current.get(key)
        if not isinstance(child, dict):
            child = {}
            current[key] = child
        current = child
    current[path[-1]] = value


def _load_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the plain nested mappings/scalars used by NanoTrack configs.

    This fallback intentionally ignores block-list entries outside the inference
    fields. It is used only when PyYAML is unavailable; profile validation still
    requires every critical inference key.
    """

    result: dict[str, Any] = {}
    parents: list[tuple[int, tuple[str, ...]]] = []
    for number, raw_line in enumerate(text.splitlines(), start=1):
        cleaned = _without_comment(raw_line).rstrip()
        if not cleaned.strip():
            continue
        stripped = cleaned.lstrip(" ")
        if stripped.startswith("-"):
            continue
        if "\t" in cleaned[: len(cleaned) - len(stripped)]:
            raise ConfigError(f"line {number}: tabs are not supported in YAML indentation")
        indent = len(cleaned) - len(stripped)
        if ":" not in stripped:
            raise ConfigError(f"line {number}: expected KEY: VALUE")
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        if not key:
            raise ConfigError(f"line {number}: empty mapping key")
        while parents and indent <= parents[-1][0]:
            parents.pop()
        parent_path = parents[-1][1] if parents else ()
        path = parent_path + (key,)
        raw_value = raw_value.strip()
        if raw_value:
            _set_nested(result, path, _parse_scalar(raw_value))
        else:
            _set_nested(result, path, {})
            parents.append((indent, path))
    return result


def load_config(path: Path) -> tuple[dict[str, Any], str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(str(exc)) from exc
    try:
        import yaml  # type: ignore
    except ImportError:
        return _load_simple_yaml(text), "stdlib-fallback"
    try:
        loaded = yaml.safe_load(text)
    except Exception as exc:  # PyYAML exposes several parser exception types.
        raise ConfigError(str(exc)) from exc
    if not isinstance(loaded, dict):
        raise ConfigError("top-level YAML value must be a mapping")
    return loaded, "yaml.safe_load"


def get_nested(mapping: dict[str, Any], dotted: str) -> Any:
    value: Any = mapping
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            raise KeyError(dotted)
        value = value[part]
    return value


def expected_fields(profile: dict[str, Any]) -> dict[str, Any]:
    channels = profile["channels"]
    return {
        "META_ARC": "nanotrack",
        "BACKBONE.TYPE": profile["backbone"],
        "BACKBONE.KWARGS.used_layers": [4],
        "ADJUST.ADJUST": True,
        "ADJUST.TYPE": "AdjustLayer",
        "ADJUST.KWARGS.in_channels": channels,
        "ADJUST.KWARGS.out_channels": channels,
        "BAN.BAN": True,
        "BAN.TYPE": "DepthwiseBAN",
        "BAN.KWARGS.in_channels": channels,
        "BAN.KWARGS.out_channels": channels,
        "POINT.STRIDE": profile["stride"],
        "TRACK.TYPE": "NanoTracker",
        "TRACK.WINDOW_INFLUENCE": profile["window_influence"],
        "TRACK.PENALTY_K": profile["penalty_k"],
        "TRACK.LR": profile["lr"],
        "TRACK.EXEMPLAR_SIZE": 127,
        "TRACK.INSTANCE_SIZE": 255,
        "TRACK.BASE_SIZE": 7,
        "TRACK.CONTEXT_AMOUNT": 0.5,
        "TRACK.OUTPUT_SIZE": profile["output_size"],
    }


def values_match(actual: Any, expected: Any) -> bool:
    if isinstance(expected, float) and isinstance(actual, (int, float)):
        return math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=1e-12)
    return actual == expected


def validate_config(
    config: dict[str, Any], variant: str, report: dict[str, Any]
) -> None:
    profile = PROFILES[variant]
    checked: dict[str, Any] = {}
    for dotted, expected in expected_fields(profile).items():
        try:
            actual = get_nested(config, dotted)
        except KeyError:
            if dotted == "TRACK.OUTPUT_SIZE" and variant in {"v1", "v2"}:
                report["warnings"].append(
                    "TRACK.OUTPUT_SIZE is omitted; historical V1/V2 YAML relies on "
                    "a fresh-process core default of 16. Prefer setting 16 explicitly."
                )
                checked[dotted] = {"actual": "<core default 16>", "expected": expected}
                continue
            report["errors"].append(f"config missing critical field {dotted}")
            continue
        checked[dotted] = {"actual": actual, "expected": expected}
        if not values_match(actual, expected):
            report["errors"].append(
                f"config field {dotted}={actual!r}; expected {expected!r} for {variant}"
            )
    try:
        config_cuda = get_nested(config, "CUDA")
    except KeyError:
        config_cuda = "<unset>"
    report["config_check"] = {
        "parser": report.get("config_parser"),
        "cuda_declared": config_cuda,
        "fields": checked,
    }


def render_config(variant: str) -> str:
    profile = PROFILES[variant]
    channels = profile["channels"]
    cuda_default = "false"
    return f"""# Minimal NanoTrack {variant.upper()} inference profile.
# Runtime code must override CUDA from its resolved model device.
META_ARC: "nanotrack"
CUDA: {cuda_default}

BACKBONE:
  TYPE: "{profile['backbone']}"
  KWARGS:
    used_layers: [4]

ADJUST:
  ADJUST: true
  TYPE: "AdjustLayer"
  KWARGS:
    in_channels: {channels}
    out_channels: {channels}

BAN:
  BAN: true
  TYPE: "DepthwiseBAN"
  KWARGS:
    in_channels: {channels}
    out_channels: {channels}

POINT:
  STRIDE: {profile['stride']}

TRACK:
  TYPE: "NanoTracker"
  WINDOW_INFLUENCE: {profile['window_influence']:.3f}
  PENALTY_K: {profile['penalty_k']:.3f}
  LR: {profile['lr']:.3f}
  EXEMPLAR_SIZE: 127
  INSTANCE_SIZE: 255
  BASE_SIZE: 7
  CONTEXT_AMOUNT: 0.5
  OUTPUT_SIZE: {profile['output_size']}
"""


def write_config(path: Path, variant: str, overwrite: bool) -> str:
    expanded = path.expanduser()
    if not expanded.parent.is_dir():
        raise ConfigError(f"parent directory does not exist: {expanded.parent}")
    if expanded.exists():
        if not expanded.is_file():
            raise ConfigError(f"output exists and is not a regular file: {expanded}")
        if not overwrite:
            raise ConfigError(f"output exists; pass --overwrite to replace it: {expanded}")
    try:
        expanded.write_text(render_config(variant), encoding="utf-8")
    except OSError as exc:
        raise ConfigError(str(exc)) from exc
    return str(expanded.resolve())


def validate_frame_and_box(args: argparse.Namespace, report: dict[str, Any]) -> None:
    height, width, channels = args.frame_shape
    if height <= 0 or width <= 0:
        report["errors"].append("frame height and width must be positive")
    if channels != 3:
        report["errors"].append("NanoTrack requires an HxWx3 frame")
    if args.color_order != "BGR":
        report["errors"].append(
            f"declared color order {args.color_order}; convert explicitly to BGR"
        )
    if args.dtype.lower() != "uint8":
        report["errors"].append(
            f"declared dtype {args.dtype}; convert explicitly to uint8 with a defined range"
        )

    x, y, box_width, box_height = args.bbox
    if not all(math.isfinite(v) for v in args.bbox):
        report["errors"].append("bbox values must all be finite")
    elif box_width <= 0 or box_height <= 0:
        report["errors"].append("bbox width and height must be positive")
    elif height > 0 and width > 0:
        intersection_width = max(0.0, min(float(width), x + box_width) - max(0.0, x))
        intersection_height = max(0.0, min(float(height), y + box_height) - max(0.0, y))
        fully_inside = (
            x >= 0.0
            and y >= 0.0
            and x + box_width <= float(width)
            and y + box_height <= float(height)
        )
        if intersection_width <= 0.0 or intersection_height <= 0.0:
            report["errors"].append("bbox has no positive-area intersection with the frame")
        elif not fully_inside and not args.allow_partial_bbox:
            report["errors"].append(
                "bbox is partially outside the frame; clip it or pass --allow-partial-bbox"
            )
        elif not fully_inside:
            report["warnings"].append(
                "partial bbox accepted; application must define clipping before tracker.init"
            )

    report["frame"] = {
        "shape_hwc": [height, width, channels],
        "color_order": args.color_order,
        "dtype": args.dtype,
        "synthetic_declaration_only": True,
    }
    report["bbox"] = {
        "xywh": list(args.bbox),
        "zero_based": True,
        "allow_partial": args.allow_partial_bbox,
    }


def resolve_device(requested: str, report: dict[str, Any]) -> str:
    if requested == "cpu":
        return "cpu"
    try:
        import torch  # type: ignore
    except Exception as exc:
        if requested == "cuda":
            report["errors"].append(f"CUDA requested but PyTorch import failed: {exc}")
        else:
            report["warnings"].append(
                "auto device could not import PyTorch; selected CPU for preflight"
            )
        return "cpu"
    cuda_available = bool(torch.cuda.is_available())
    if requested == "cuda" and not cuda_available:
        report["errors"].append(
            "CUDA requested but torch.cuda.is_available() is false"
        )
        return "cuda-unavailable"
    return "cuda" if cuda_available else "cpu"


def emit_human(report: dict[str, Any]) -> None:
    status = "PASS" if report["ok"] else "FAIL"
    print(f"NanoTrack inference preflight: {status}")
    print(f"variant: {report['variant']}")
    print(f"head module: {report['profile']['head_module']}")
    print(f"resolved device: {report['device']['resolved']}")
    print(f"config: {report['config']['path'] or 'built-in profile only'}")
    print(f"checkpoint: {report['checkpoint']['path'] or 'not supplied (validation only)'}")
    if report.get("written_config"):
        print(f"wrote config: {report['written_config']}")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}")
    for error in report["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)
    if report["ok"]:
        print("next: merge config, register matching head, align cfg.CUDA/model device, load weights, init once, then track")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    profile = dict(PROFILES[args.variant])
    report: dict[str, Any] = {
        "ok": False,
        "variant": args.variant,
        "profile": profile,
        "errors": [],
        "warnings": [],
        "written_config": None,
    }

    config_path: Path | None = args.config.expanduser() if args.config else None
    if args.write_config:
        try:
            report["written_config"] = write_config(
                args.write_config, args.variant, args.overwrite
            )
            if config_path is None:
                config_path = Path(report["written_config"])
        except ConfigError as exc:
            report["errors"].append(f"cannot write config: {exc}")

    report["config"] = {"path": str(config_path) if config_path else None}
    if config_path is not None:
        if not config_path.is_file():
            report["errors"].append(f"config is not a regular file: {config_path}")
        else:
            try:
                config, parser_name = load_config(config_path)
                report["config_parser"] = parser_name
                validate_config(config, args.variant, report)
            except ConfigError as exc:
                report["errors"].append(f"cannot parse config: {exc}")

    checkpoint_path = args.checkpoint.expanduser() if args.checkpoint else None
    if checkpoint_path is not None and not checkpoint_path.is_file():
        report["errors"].append(
            f"checkpoint is not a regular file: {checkpoint_path}"
        )
    if args.require_checkpoint and checkpoint_path is None:
        report["errors"].append("--require-checkpoint requires --checkpoint")
    if checkpoint_path is None:
        report["warnings"].append(
            "no checkpoint supplied; this is validation-only and cannot prove tracking"
        )
    report["checkpoint"] = {
        "path": str(checkpoint_path) if checkpoint_path else None,
        "contents_loaded": False,
    }

    validate_frame_and_box(args, report)
    resolved_device = resolve_device(args.device, report)
    report["device"] = {
        "requested": args.device,
        "resolved": resolved_device,
        "cfg_cuda_required": resolved_device == "cuda",
    }

    config_check = report.get("config_check")
    if config_check and isinstance(config_check.get("cuda_declared"), bool):
        declared = config_check["cuda_declared"]
        required = report["device"]["cfg_cuda_required"]
        if declared != required:
            report["warnings"].append(
                f"config CUDA={declared}; runtime must override cfg.CUDA={required} "
                "to match the resolved model device"
            )

    report["lifecycle"] = [
        "fresh process for one variant",
        "merge matching config",
        f"register {profile['head_module']}",
        "set cfg.CUDA to model device",
        "construct ModelBuilder() with no arguments",
        "load matching checkpoint and call model.to(device).eval()",
        "build_tracker(model)",
        "tracker.init(first_bgr_frame, xywh_bbox) once",
        "tracker.track(next_bgr_frame) in temporal order",
    ]
    report["side_effects"] = {
        "network": False,
        "gui": False,
        "camera": False,
        "video_decode": False,
        "checkpoint_load": False,
    }
    report["ok"] = not report["errors"]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        emit_human(report)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
