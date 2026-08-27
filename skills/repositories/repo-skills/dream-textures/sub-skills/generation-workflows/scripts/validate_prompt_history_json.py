#!/usr/bin/env python3
"""Validate Dream Textures prompt-history JSON without importing Blender.

The validator checks the distilled DreamPrompt export/import shape used by the
Dream Textures history operators. It performs deterministic schema and enum
checks only; it never loads models, downloads assets, or imports bpy.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROMPT_STRUCTURES = {"custom", "texture", "photography", "concept_art", "file_batch"}
INIT_IMAGE_SOURCES = {"file", "open_editor"}
INIT_IMAGE_ACTIONS = {"modify", "inpaint", "outpaint"}
MODIFY_SOURCE_TYPES = {"color", "depth_generated", "depth_map", "depth"}
INPAINT_MASK_SOURCES = {"alpha", "prompt"}
SEAMLESS_AXES = {"auto", "off", "x", "y", "xy", "Auto-detect", "Off", "X", "Y", "Both", ""}
STEP_PREVIEW_MODES = {"None", "Fast", "Fast (Batch Tiled)", "Accurate", "Accurate (Batch Tiled)"}
SCHEDULERS = {
    "DDIM",
    "DDPM",
    "DEIS Multistep",
    "DPM Solver Multistep",
    "DPM Solver Multistep Karras",
    "DPM Solver Singlestep",
    "DPM Solver Singlestep Karras",
    "Euler Discrete",
    "Euler Discrete Karras",
    "Euler Ancestral Discrete",
    "Heun Discrete",
    "Heun Discrete Karras",
    "KDPM2 Discrete",
    "KDPM2 Ancestral Discrete",
    "LMS Discrete",
    "LMS Discrete Karras",
    "PNDM",
    "UniPC Multistep",
}
PROCESSOR_IDS = {
    "none",
    "depth_leres",
    "depth_leres++",
    "depth_midas",
    "depth_zoe",
    "canny",
    "mlsd",
    "softedge_hed",
    "softedge_hedsafe",
    "softedge_pidinet",
    "softedge_pidsafe",
    "lineart_anime",
    "lineart_coarse",
    "lineart_realistic",
    "normal_bae",
    "openpose",
    "openpose_face",
    "openpose_faceonly",
    "openpose_full",
    "openpose_hand",
    "scribble_hed",
    "scribble_pidinet",
    "shuffle",
}

BASE_KEYS = {
    "backend",
    "model",
    "control_nets",
    "active_control_net",
    "prompt_structure",
    "use_negative_prompt",
    "negative_prompt",
    "use_size",
    "width",
    "height",
    "seamless_axes",
    "show_advanced",
    "random_seed",
    "seed",
    "iterations",
    "steps",
    "cfg_scale",
    "scheduler",
    "step_preview_mode",
    "use_init_img",
    "init_img_src",
    "init_img_action",
    "strength",
    "fit",
    "use_init_img_color",
    "modify_action_source_type",
    "inpaint_mask_src",
    "inpaint_replace",
    "text_mask",
    "text_mask_confidence",
    "outpaint_origin",
    "hash",
}

# Dynamic token fields distilled from prompt_engineering.py.
TOKEN_IDS = {
    "subject",
    "framing",
    "position",
    "film_type",
    "camera_settings",
    "shooting_context",
    "lighting",
    "subject_type",
    "genre",
}
TOKEN_KEYS = {f"prompt_structure_token_{token}" for token in TOKEN_IDS} | {f"prompt_structure_token_{token}_enum" for token in TOKEN_IDS}
KNOWN_KEYS = BASE_KEYS | TOKEN_KEYS
CONTROL_NET_KEYS = {"control_net", "conditioning_scale", "control_image", "processor_id", "enabled"}


@dataclass
class Finding:
    level: str
    path: str
    message: str


def type_name(value: Any) -> str:
    return type(value).__name__


class Validator:
    def __init__(self, *, strict: bool = False) -> None:
        self.strict = strict
        self.findings: list[Finding] = []

    def error(self, path: str, message: str) -> None:
        self.findings.append(Finding("error", path, message))

    def warn(self, path: str, message: str) -> None:
        self.findings.append(Finding("warning", path, message))

    def expect_type(self, obj: dict[str, Any], key: str, expected: tuple[type, ...] | type, label: str) -> None:
        if key not in obj or obj[key] is None:
            return
        if not isinstance(obj[key], expected):
            self.error(key, f"expected {label}, got {type_name(obj[key])}")

    def expect_enum(self, obj: dict[str, Any], key: str, allowed: set[str]) -> None:
        if key not in obj or obj[key] is None:
            return
        value = obj[key]
        if not isinstance(value, str):
            self.error(key, f"expected string enum, got {type_name(value)}")
        elif value not in allowed:
            self.error(key, f"invalid value {value!r}; expected one of {sorted(allowed)!r}")

    def validate_root(self, data: Any) -> None:
        if not isinstance(data, dict):
            self.error("$", f"root must be a JSON object, got {type_name(data)}")
            return

        for key in data:
            if key not in KNOWN_KEYS:
                message = "unknown DreamPrompt/history key"
                if self.strict:
                    self.error(key, message)
                else:
                    self.warn(key, message)

        # Scalar/string fields.
        for key in ("backend", "model", "negative_prompt", "seed", "text_mask", "hash"):
            self.expect_type(data, key, str, "string")

        for key in (
            "use_negative_prompt",
            "use_size",
            "show_advanced",
            "random_seed",
            "use_init_img",
            "fit",
            "use_init_img_color",
        ):
            self.expect_type(data, key, bool, "boolean")

        for key in ("active_control_net", "width", "height", "iterations", "steps"):
            self.expect_type(data, key, int, "integer")

        for key in ("cfg_scale", "strength", "inpaint_replace", "text_mask_confidence"):
            self.expect_type(data, key, (int, float), "number")

        for key in TOKEN_KEYS:
            self.expect_type(data, key, str, "string")

        # Enums.
        self.expect_enum(data, "prompt_structure", PROMPT_STRUCTURES)
        self.expect_enum(data, "seamless_axes", SEAMLESS_AXES)
        self.expect_enum(data, "scheduler", SCHEDULERS)
        self.expect_enum(data, "step_preview_mode", STEP_PREVIEW_MODES)
        self.expect_enum(data, "init_img_src", INIT_IMAGE_SOURCES)
        self.expect_enum(data, "init_img_action", INIT_IMAGE_ACTIONS)
        self.expect_enum(data, "modify_action_source_type", MODIFY_SOURCE_TYPES)
        self.expect_enum(data, "inpaint_mask_src", INPAINT_MASK_SOURCES)

        self.validate_outpaint_origin(data)
        self.validate_control_nets(data)
        self.validate_cross_fields(data)

    def validate_outpaint_origin(self, data: dict[str, Any]) -> None:
        if "outpaint_origin" not in data or data["outpaint_origin"] is None:
            return
        value = data["outpaint_origin"]
        if not isinstance(value, list) or len(value) != 2:
            self.error("outpaint_origin", "expected a two-element JSON array [x, y]")
            return
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in value):
            self.error("outpaint_origin", "origin coordinates must be integers")

    def validate_control_nets(self, data: dict[str, Any]) -> None:
        if "control_nets" not in data or data["control_nets"] is None:
            return
        value = data["control_nets"]
        if not isinstance(value, list):
            self.error("control_nets", f"expected list, got {type_name(value)}")
            return
        for index, item in enumerate(value):
            path = f"control_nets[{index}]"
            if not isinstance(item, dict):
                self.error(path, f"expected object, got {type_name(item)}")
                continue
            for key in item:
                if key not in CONTROL_NET_KEYS:
                    message = "unknown ControlNet key"
                    if self.strict:
                        self.error(f"{path}.{key}", message)
                    else:
                        self.warn(f"{path}.{key}", message)
            if "control_net" in item and item["control_net"] is not None and not isinstance(item["control_net"], str):
                self.error(f"{path}.control_net", f"expected string, got {type_name(item['control_net'])}")
            if "conditioning_scale" in item and item["conditioning_scale"] is not None and not isinstance(item["conditioning_scale"], (int, float)):
                self.error(f"{path}.conditioning_scale", f"expected number, got {type_name(item['conditioning_scale'])}")
            if "processor_id" in item and item["processor_id"] is not None:
                processor_id = item["processor_id"]
                if not isinstance(processor_id, str):
                    self.error(f"{path}.processor_id", f"expected string enum, got {type_name(processor_id)}")
                elif processor_id not in PROCESSOR_IDS:
                    self.error(f"{path}.processor_id", f"invalid processor id {processor_id!r}; expected one of {sorted(PROCESSOR_IDS)!r}")
            if "enabled" in item and item["enabled"] is not None and not isinstance(item["enabled"], bool):
                self.error(f"{path}.enabled", f"expected boolean, got {type_name(item['enabled'])}")

    def validate_cross_fields(self, data: dict[str, Any]) -> None:
        width = data.get("width")
        height = data.get("height")
        if isinstance(width, int):
            if width < 64:
                self.error("width", "DreamPrompt width should be at least 64")
            if width % 64 != 0:
                self.warn("width", "DreamPrompt UI uses 64-pixel increments; non-multiple values may be rounded or rejected by workflows")
        if isinstance(height, int):
            if height < 64:
                self.error("height", "DreamPrompt height should be at least 64")
            if height % 64 != 0:
                self.warn("height", "DreamPrompt UI uses 64-pixel increments; non-multiple values may be rounded or rejected by workflows")

        if isinstance(data.get("iterations"), int) and data["iterations"] < 1:
            self.error("iterations", "must be >= 1")
        if isinstance(data.get("steps"), int) and data["steps"] < 1:
            self.error("steps", "must be >= 1")
        if isinstance(data.get("cfg_scale"), (int, float)) and data["cfg_scale"] < 0:
            self.error("cfg_scale", "must be >= 0")
        if isinstance(data.get("strength"), (int, float)) and not 0 <= data["strength"] <= 1:
            self.error("strength", "must be between 0 and 1")
        if isinstance(data.get("inpaint_replace"), (int, float)) and not 0 <= data["inpaint_replace"] <= 1:
            self.error("inpaint_replace", "must be between 0 and 1")
        if isinstance(data.get("text_mask_confidence"), (int, float)) and data["text_mask_confidence"] < 0:
            self.error("text_mask_confidence", "must be >= 0")

        if data.get("prompt_structure") == "file_batch":
            if data.get("use_negative_prompt"):
                self.warn("use_negative_prompt", "file-batch mode hides the Negative panel and uses blank negative prompt lines")
            if "negative_prompt" in data and data.get("negative_prompt"):
                self.warn("negative_prompt", "negative prompt text is not used by the built-in file-batch path")

        if data.get("use_negative_prompt") is False and data.get("negative_prompt"):
            self.warn("negative_prompt", "negative prompt text is present but use_negative_prompt is false")

        if data.get("use_init_img") is False and data.get("init_img_action") in {"inpaint", "outpaint"}:
            self.warn("init_img_action", "inpaint/outpaint action is ignored unless use_init_img is true")

        if data.get("init_img_action") == "inpaint" and data.get("inpaint_mask_src") == "prompt" and not data.get("text_mask"):
            self.warn("text_mask", "prompt-mask inpainting needs a non-empty mask prompt")

        if data.get("init_img_action") == "outpaint":
            origin = data.get("outpaint_origin")
            if isinstance(origin, list) and len(origin) == 2 and all(isinstance(v, int) and not isinstance(v, bool) for v in origin):
                if isinstance(width, int) and isinstance(height, int):
                    x, y = origin
                    if not -width <= x <= width and width >= 64:
                        self.warn("outpaint_origin", "origin x may be outside valid bounds unless the source image is wider than the generation width")
                    if not -height <= y <= height and height >= 64:
                        self.warn("outpaint_origin", "origin y may be outside valid bounds unless the source image is taller than the generation height")

        if "active_control_net" in data and isinstance(data.get("control_nets"), list) and isinstance(data.get("active_control_net"), int):
            if data["control_nets"] and not 0 <= data["active_control_net"] < len(data["control_nets"]):
                self.warn("active_control_net", "index is outside the control_nets list")

    @property
    def ok(self) -> bool:
        return not any(f.level == "error" for f in self.findings)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Dream Textures prompt-history JSON keys, types, enums, and common cross-field constraints.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("path", type=Path, help="prompt-history JSON file exported from or intended for Dream Textures")
    parser.add_argument("--strict", action="store_true", help="treat unknown keys as errors instead of warnings")
    parser.add_argument("--json", action="store_true", help="print machine-readable validation output")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        data = load_json(args.path)
    except FileNotFoundError:
        print(f"error: file not found: {args.path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: cannot read {args.path}: {exc}", file=sys.stderr)
        return 2

    validator = Validator(strict=args.strict)
    validator.validate_root(data)

    result = {
        "ok": validator.ok,
        "error_count": sum(1 for f in validator.findings if f.level == "error"),
        "warning_count": sum(1 for f in validator.findings if f.level == "warning"),
        "findings": [f.__dict__ for f in validator.findings],
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        if validator.ok:
            print(f"OK: {args.path} is a valid Dream Textures prompt-history JSON shape")
        else:
            print(f"ERROR: {args.path} has {result['error_count']} validation error(s)")
        for finding in validator.findings:
            stream = sys.stderr if finding.level == "error" else sys.stdout
            print(f"{finding.level.upper()}: {finding.path}: {finding.message}", file=stream)

    return 0 if validator.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
