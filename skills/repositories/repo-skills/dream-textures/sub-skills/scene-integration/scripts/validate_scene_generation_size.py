#!/usr/bin/env python3
"""Validate Dream Textures scene workflow dimensions without importing Blender.

The Cycles Dream Textures render pass rejects the *scaled* render size when it
is not divisible by 64. Texture projection and the Dream Textures render engine
also feed Stable Diffusion/Diffusers generation sizes, which should be planned
as multiples of 64. This helper is safe to run in a normal Python interpreter:
it performs only arithmetic and emits text or JSON.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Iterable

MULTIPLE = 64
WORKFLOWS = ("render-pass", "texture-projection", "render-engine")
RENDER_PASS_INPUTS = ("color", "depth", "color-depth")


@dataclass(frozen=True)
class Size:
    width: int
    height: int

    @property
    def valid_pixels(self) -> bool:
        return self.width > 0 and self.height > 0

    @property
    def multiple_of_64(self) -> bool:
        return self.valid_pixels and self.width % MULTIPLE == 0 and self.height % MULTIPLE == 0

    @property
    def text(self) -> str:
        return f"{self.width}x{self.height}"

    @property
    def aspect(self) -> float | None:
        if not self.valid_pixels:
            return None
        return self.width / self.height


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def positive_percentage(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a number, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("resolution percentage must be positive")
    return parsed


def scale_render_dimension(value: int, percentage: float) -> int:
    """Match the add-on's integer truncation after applying render percentage."""

    return int(value * (percentage / 100.0))


def round_down_to_multiple(value: int) -> int:
    if value <= 0:
        return MULTIPLE
    return max(MULTIPLE, (value // MULTIPLE) * MULTIPLE)


def round_up_to_multiple(value: int) -> int:
    if value <= 0:
        return MULTIPLE
    return max(MULTIPLE, math.ceil(value / MULTIPLE) * MULTIPLE)


def round_nearest_to_multiple(value: int) -> int:
    down = round_down_to_multiple(value)
    up = round_up_to_multiple(value)
    if abs(value - down) < abs(up - value):
        return down
    return up


def candidate_sizes(size: Size) -> dict[str, Size]:
    return {
        "nearest": Size(round_nearest_to_multiple(size.width), round_nearest_to_multiple(size.height)),
        "down": Size(round_down_to_multiple(size.width), round_down_to_multiple(size.height)),
        "up": Size(round_up_to_multiple(size.width), round_up_to_multiple(size.height)),
    }


def approx_raw_for_effective(size: Size, percentage: float) -> Size:
    """Approximate raw Output Properties dimensions for a desired scaled size."""

    scale = percentage / 100.0
    return Size(math.ceil(size.width / scale), math.ceil(size.height / scale))


def workflow_notes(workflow: str, render_pass_input: str, resolution_applied: bool, percentage: float) -> dict[str, Any]:
    notes: list[str] = [
        "Stable Diffusion/Diffusers image dimensions should be planned as multiples of 64.",
    ]
    flags = {
        "z_pass_required": False,
        "depth_model_required": False,
        "matching_controlnet_required": False,
        "visible_viewport_required": False,
    }
    conditional_requirements: list[str] = []

    if workflow == "render-pass":
        notes.append("Final size is Output Properties width/height after Blender resolution percentage scaling.")
        notes.append("Use Cycles, enable the Dream Textures render pass, and connect Render Layers > Dream Textures to Composite > Image when it should be final output.")
        if render_pass_input == "color":
            notes.append("Pass input Color uses the Cycles Combined pass as image-to-image input; Z pass and a depth model are not required.")
            notes.append("Noise Strength controls how strongly the generated result preserves the Cycles color/composition.")
        elif render_pass_input == "depth":
            flags["z_pass_required"] = True
            flags["depth_model_required"] = True
            notes.append("Pass input Depth uses the Cycles Z pass; enable the view-layer Z pass before rendering.")
            notes.append("Select a depth-capable model such as stabilityai/stable-diffusion-2-depth.")
        else:
            flags["z_pass_required"] = True
            flags["depth_model_required"] = True
            notes.append("Pass input Color and Depth uses Combined color plus Z depth; enable the view-layer Z pass.")
            notes.append("Select a depth-capable model and tune Noise Strength lower to preserve the Cycles color/composition.")
    elif workflow == "texture-projection":
        flags["visible_viewport_required"] = True
        notes.append("Texture projection uses the current 3D Viewport for depth and optional viewport color; Blender render resolution percentage is not applied by the projection operator.")
        notes.append("Before projecting, select mesh objects, enter Edit Mode, and select target faces; Local View limits which objects influence the depth map.")
        notes.append("Depth-to-image projection needs a depth-capable model; the Use ControlNet route needs a matching depth ControlNet model instead.")
        notes.append("Z pass is not used for projection because depth is rendered from the viewport/offscreen context.")
        conditional_requirements.append("Depth-to-image projection route requires a depth-capable model.")
        conditional_requirements.append("Use ControlNet projection route requires a matching depth ControlNet model.")
    else:
        notes.append("Dream Textures render engine node trees normally use node Width/Height values; the default Render Properties node supplies scene resolution X/Y.")
        notes.append("The source render-engine path does not apply Blender resolution percentage to Stable Diffusion node dimensions; leave percentage at 100 unless planning an external scaled target.")
        notes.append("Depth-to-image Stable Diffusion nodes need a depth-capable model; ControlNet nodes need a model matching the selected depth/normal/OpenPose/ADE20K map.")
        notes.append("Render-engine annotation maps usually need a camera, render-visible geometry, and a GPU offscreen context; Viewport Color needs a visible 3D Viewport.")
        conditional_requirements.append("Depth-to-image Stable Diffusion node task requires a depth-capable model.")
        conditional_requirements.append("ControlNet nodes require a model matching the selected depth/normal/OpenPose/ADE20K map.")
        flags["visible_viewport_required"] = True

    if not resolution_applied and percentage != 100:
        notes.append("Resolution percentage was accepted for reporting but is not applied to this workflow's final generation size by Dream Textures source behavior.")

    return {"flags": flags, "conditional_requirements": conditional_requirements, "notes": notes}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    requested = Size(args.width, args.height)
    resolution_applied = args.workflow == "render-pass"
    final = (
        Size(scale_render_dimension(args.width, args.resolution_percentage), scale_render_dimension(args.height, args.resolution_percentage))
        if resolution_applied
        else requested
    )
    candidates = candidate_sizes(final)
    candidate_report: dict[str, Any] = {}
    for label, size in candidates.items():
        item: dict[str, Any] = asdict(size)
        if resolution_applied and args.resolution_percentage != 100:
            item["approx_raw_width"] = approx_raw_for_effective(size, args.resolution_percentage).width
            item["approx_raw_height"] = approx_raw_for_effective(size, args.resolution_percentage).height
        candidate_report[label] = item

    notes = workflow_notes(args.workflow, args.render_pass_input, resolution_applied, args.resolution_percentage)
    status = "ok" if final.multiple_of_64 else "invalid"
    return {
        "status": status,
        "workflow": args.workflow,
        "render_pass_input": args.render_pass_input if args.workflow == "render-pass" else None,
        "requested_size": asdict(requested),
        "resolution_percentage": args.resolution_percentage,
        "resolution_percentage_applied": resolution_applied,
        "final_size": asdict(final),
        "final_aspect": final.aspect,
        "multiple": MULTIPLE,
        "multiple_of_64": final.multiple_of_64,
        "nearest_multiples": candidate_report,
        "requirements": notes["flags"],
        "conditional_requirements": notes["conditional_requirements"],
        "notes": notes["notes"],
    }


def print_text(report: dict[str, Any]) -> None:
    print("Dream Textures scene size validation")
    print(f"status: {report['status']}")
    print(f"workflow: {report['workflow']}")
    if report["render_pass_input"] is not None:
        print(f"render pass input: {report['render_pass_input']}")
    print(f"requested size: {report['requested_size']['width']}x{report['requested_size']['height']}")
    print(f"resolution percentage: {report['resolution_percentage']:g}%")
    print(f"resolution percentage applied: {'yes' if report['resolution_percentage_applied'] else 'no'}")
    print(f"final size checked: {report['final_size']['width']}x{report['final_size']['height']}")
    print(f"multiple-of-{report['multiple']}: {'ok' if report['multiple_of_64'] else 'invalid'}")

    print("nearest multiples:")
    seen: set[tuple[int, int]] = set()
    for label, size in report["nearest_multiples"].items():
        key = (size["width"], size["height"])
        if key in seen:
            continue
        seen.add(key)
        line = f"  {label}: {size['width']}x{size['height']}"
        if "approx_raw_width" in size:
            line += f" (approx raw {size['approx_raw_width']}x{size['approx_raw_height']} at {report['resolution_percentage']:g}%)"
        print(line)

    print("requirements and notes:")
    req = report["requirements"]
    print(f"  z pass required: {'yes' if req['z_pass_required'] else 'no'}")
    print(f"  depth model required: {'yes' if req['depth_model_required'] else 'no/depends on chosen route'}")
    print(f"  matching ControlNet required: {'yes' if req['matching_controlnet_required'] else 'no/only if using ControlNet'}")
    print(f"  visible viewport/GPU offscreen context: {'yes' if req['visible_viewport_required'] else 'not usually'}")
    for note in report.get("conditional_requirements", []):
        print(f"  conditional: {note}")
    for note in report["notes"]:
        print(f"  - {note}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Dream Textures scene workflow render/generation dimensions and summarize depth/Z-pass requirements."
    )
    parser.add_argument("--width", type=positive_int, required=True, help="Raw width in pixels: Output Properties X for render pass, or planned generation Width for projection/render-engine.")
    parser.add_argument("--height", type=positive_int, required=True, help="Raw height in pixels: Output Properties Y for render pass, or planned generation Height for projection/render-engine.")
    parser.add_argument("--resolution-percentage", type=positive_percentage, default=100.0, help="Blender render resolution percentage; applied to render-pass validation, reported but not applied for texture-projection/render-engine. Default: 100.")
    parser.add_argument("--workflow", choices=WORKFLOWS, required=True, help="Scene workflow being planned or diagnosed.")
    parser.add_argument("--render-pass-input", choices=RENDER_PASS_INPUTS, default="color", help="Dream Textures Cycles pass input; relevant when --workflow render-pass. Default: color.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format. Default: text.")
    parser.add_argument("--json", action="store_const", const="json", dest="format", help="Shortcut for --format json.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = build_report(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["multiple_of_64"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
