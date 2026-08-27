#!/usr/bin/env python3
"""Static planner for Neuralangelo mesh extraction.

This helper performs path and metadata checks, estimates lattice/block sizes,
and can print a command template. It intentionally does not import Neuralangelo,
Torch, CUDA, or checkpoint contents.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

Number = float
Bounds = List[List[Number]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan a Neuralangelo extract_mesh.py invocation without running GPU extraction."
    )
    parser.add_argument("--config", required=True, help="Training config YAML used for extraction.")
    parser.add_argument("--checkpoint", required=True, help="Checkpoint .pt path to load.")
    parser.add_argument("--output-file", required=True, help="PLY output path to pass as --output_file.")
    parser.add_argument("--resolution", type=int, default=512, help="Marching-cubes resolution.")
    parser.add_argument("--block-res", type=int, default=64, help="Block-wise marching-cubes resolution.")
    parser.add_argument("--gpus", type=int, default=1, help="Number of processes/GPUs for torchrun command.")
    parser.add_argument("--single-gpu", action="store_true", help="Print a plain python command with --single_gpu.")
    parser.add_argument("--textured", action="store_true", help="Include --textured in the printed command and warnings.")
    parser.add_argument("--keep-lcc", action="store_true", help="Include --keep_lcc in the printed command and warnings.")
    parser.add_argument("--script", default="projects/neuralangelo/scripts/extract_mesh.py", help="Extractor script path for command printing.")
    parser.add_argument("--print-command", action="store_true", help="Print a shell command template.")
    parser.add_argument("--print-json", action="store_true", help="Emit the report as JSON.")
    return parser.parse_args()


def strip_inline_comment(line: str) -> str:
    in_single = False
    in_double = False
    result: List[str] = []
    for ch in line:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            break
        result.append(ch)
    return "".join(result).rstrip()


def clean_scalar(value: str) -> str:
    value = strip_inline_comment(value).strip()
    if not value:
        return value
    if (value[0], value[-1]) in (("'", "'"), ('"', '"')):
        return value[1:-1]
    return value


def parse_data_root(config_path: Path) -> Optional[str]:
    """Parse a common YAML `data.root` scalar using indentation only.

    This is deliberately small and dependency-free. It handles the config style
    used by Neuralangelo, but does not attempt to be a complete YAML parser.
    """
    try:
        lines = config_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = config_path.read_text(errors="replace").splitlines()
    stack: List[Tuple[int, str]] = []
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        line = strip_inline_comment(raw)
        if not line.strip() or ":" not in line:
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, value = line.strip().split(":", 1)
        key = key.strip().strip('"\'')
        while stack and indent <= stack[-1][0]:
            stack.pop()
        path = [item[1] for item in stack] + [key]
        if path == ["data", "root"]:
            return clean_scalar(value)
        if value.strip() == "":
            stack.append((indent, key))
    return None


def as_number(value: Any, name: str) -> Number:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    return float(value)


def parse_vec3(value: Any, name: str) -> List[Number]:
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{name} must be a list of three numbers")
    return [as_number(v, f"{name}[{i}]") for i, v in enumerate(value)]


def parse_aabb(value: Any) -> Optional[Bounds]:
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError("aabb_range must be a 3-by-2 list")
    bounds: Bounds = []
    for axis, pair in enumerate(value):
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError(f"aabb_range[{axis}] must contain [min, max]")
        lo = as_number(pair[0], f"aabb_range[{axis}][0]")
        hi = as_number(pair[1], f"aabb_range[{axis}][1]")
        if hi <= lo:
            raise ValueError(f"aabb_range[{axis}] max must be greater than min")
        bounds.append([lo, hi])
    return bounds


def load_transforms(path: Path) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    warnings: List[str] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return None, ["transforms.json not found"]
    except json.JSONDecodeError as exc:
        return None, [f"transforms.json is not valid JSON: {exc}"]
    if not isinstance(data, dict):
        return None, ["transforms.json root must be an object"]
    return data, warnings


def normalized_bounds(meta: Dict[str, Any]) -> Tuple[Optional[Bounds], List[str], Optional[List[Number]], Optional[Number]]:
    warnings: List[str] = []
    try:
        center = parse_vec3(meta.get("sphere_center"), "sphere_center")
        radius = as_number(meta.get("sphere_radius"), "sphere_radius")
        if radius <= 0:
            raise ValueError("sphere_radius must be positive")
        aabb = parse_aabb(meta.get("aabb_range"))
    except ValueError as exc:
        return None, [str(exc)], None, None
    if aabb is None:
        warnings.append("aabb_range missing; extractor will sample normalized [-1, 1] on all axes")
        return [[-1.0, 1.0], [-1.0, 1.0], [-1.0, 1.0]], warnings, center, radius
    norm: Bounds = []
    for axis in range(3):
        norm.append([(aabb[axis][0] - center[axis]) / radius, (aabb[axis][1] - center[axis]) / radius])
    return norm, warnings, center, radius


def arange_count(lo: Number, hi: Number, step: Number) -> int:
    if hi <= lo or step <= 0:
        return 0
    return int(math.ceil((hi - lo) / step - 1e-12))


def estimate_grid(bounds: Optional[Bounds], resolution: int, block_res: int) -> Dict[str, Any]:
    if bounds is None or resolution <= 0 or block_res <= 0:
        return {}
    interval = 2.0 / float(resolution)
    dims = [arange_count(axis[0], axis[1], interval) for axis in bounds]
    blocks_axis = [int(math.ceil(dim / float(block_res))) if dim > 0 else 0 for dim in dims]
    total_blocks = blocks_axis[0] * blocks_axis[1] * blocks_axis[2]
    per_block_points = (block_res + 1) ** 3
    coord_mb = per_block_points * 3 * 4 / (1024 ** 2)
    sdf_mb = per_block_points * 4 / (1024 ** 2)
    return {
        "interval": interval,
        "grid_dimensions": dims,
        "blocks_per_axis": blocks_axis,
        "total_blocks": total_blocks,
        "per_block_points_max": per_block_points,
        "per_block_coord_tensor_mib": round(coord_mb, 2),
        "per_block_sdf_tensor_mib": round(sdf_mb, 2),
    }


def build_command(args: argparse.Namespace) -> str:
    base: List[str]
    if args.single_gpu:
        base = ["python", args.script, "--single_gpu"]
    else:
        base = ["torchrun", f"--nproc_per_node={args.gpus}", args.script]
    base.extend([
        f"--config={args.config}",
        f"--checkpoint={args.checkpoint}",
        f"--output_file={args.output_file}",
        f"--resolution={args.resolution}",
        f"--block_res={args.block_res}",
    ])
    if args.textured:
        base.append("--textured")
    if args.keep_lcc:
        base.append("--keep_lcc")
    return " ".join(shlex.quote(part) for part in base)


def make_report(args: argparse.Namespace) -> Tuple[Dict[str, Any], int]:
    warnings: List[str] = []
    errors: List[str] = []
    config_path = Path(args.config)
    checkpoint_path = Path(args.checkpoint)
    output_path = Path(args.output_file)

    if not config_path.exists():
        errors.append("config does not exist")
    if not checkpoint_path.exists():
        errors.append("checkpoint does not exist")
    if checkpoint_path.suffix and checkpoint_path.suffix != ".pt":
        warnings.append("checkpoint suffix is not .pt")
    if args.resolution <= 0:
        errors.append("resolution must be positive")
    if args.block_res <= 0:
        errors.append("block_res must be positive")
    if args.resolution > 0 and args.block_res > args.resolution:
        warnings.append("block_res is larger than resolution; this is unusual for production extraction")
    if args.gpus <= 0:
        errors.append("gpus must be positive")
    if args.single_gpu and args.gpus != 1:
        warnings.append("--single-gpu ignores --gpus for command printing")
    if not output_path.parent or str(output_path.parent) in ("", "."):
        warnings.append("output_file has no explicit parent directory; use a path such as mesh_outputs/mesh.ply")
    if output_path.suffix.lower() != ".ply":
        warnings.append("output_file does not end with .ply")
    if args.textured:
        warnings.append("textured extraction evaluates RGB/gradient paths and may need lower block_res")
    if args.keep_lcc:
        warnings.append("keep_lcc is block-local and may remove thin or disconnected structures")

    data_root = None
    transforms_path = None
    transforms_meta = None
    norm_bounds = None
    center = None
    radius = None
    if config_path.exists():
        data_root = parse_data_root(config_path)
        if data_root is None:
            warnings.append("could not parse data.root from config with lightweight parser")
        else:
            root_path = Path(os.path.expandvars(os.path.expanduser(data_root)))
            if not root_path.is_absolute():
                root_path = (config_path.parent / root_path).resolve() if not Path(data_root).exists() else Path(data_root)
            transforms_path = root_path / "transforms.json"
            transforms_meta, t_warnings = load_transforms(transforms_path)
            warnings.extend(t_warnings)
            if transforms_meta is not None:
                norm_bounds, bound_warnings, center, radius = normalized_bounds(transforms_meta)
                warnings.extend(bound_warnings)
                if norm_bounds is None:
                    errors.append("could not derive normalized bounds from transforms.json")

    grid = estimate_grid(norm_bounds, args.resolution, args.block_res)
    if grid:
        if grid["total_blocks"] == 0:
            errors.append("estimated zero lattice blocks; check bounds and resolution")
        if grid["per_block_points_max"] > 2_200_000:
            warnings.append("large per-block sample count; reduce block_res if CUDA memory is tight")
        if max(grid["grid_dimensions"] or [0]) >= 4096:
            warnings.append("very high lattice dimension; expect large runtime and output mesh")

    report: Dict[str, Any] = {
        "config": str(config_path),
        "checkpoint": str(checkpoint_path),
        "output_file": str(output_path),
        "exists": {
            "config": config_path.exists(),
            "checkpoint": checkpoint_path.exists(),
            "output_parent": output_path.parent.exists() if str(output_path.parent) not in ("", ".") else False,
        },
        "data_root": data_root,
        "transforms_json": str(transforms_path) if transforms_path else None,
        "sphere_center": center,
        "sphere_radius": radius,
        "normalized_bounds": norm_bounds,
        "grid_estimate": grid,
        "settings": {
            "resolution": args.resolution,
            "block_res": args.block_res,
            "gpus": 1 if args.single_gpu else args.gpus,
            "single_gpu": bool(args.single_gpu),
            "textured": bool(args.textured),
            "keep_lcc": bool(args.keep_lcc),
        },
        "command": build_command(args),
        "warnings": warnings,
        "errors": errors,
    }
    return report, 2 if errors else 0


def print_text(report: Dict[str, Any], include_command: bool) -> None:
    print("Neuralangelo mesh extraction plan")
    print("- config:", report["config"], "OK" if report["exists"]["config"] else "MISSING")
    print("- checkpoint:", report["checkpoint"], "OK" if report["exists"]["checkpoint"] else "MISSING")
    print("- output_file:", report["output_file"])
    if report.get("data_root"):
        print("- data.root:", report["data_root"])
    if report.get("transforms_json"):
        print("- transforms:", report["transforms_json"])
    if report.get("sphere_center") is not None:
        print("- sphere_center:", report["sphere_center"])
    if report.get("sphere_radius") is not None:
        print("- sphere_radius:", report["sphere_radius"])
    if report.get("normalized_bounds") is not None:
        print("- normalized_bounds:", report["normalized_bounds"])
    grid = report.get("grid_estimate") or {}
    if grid:
        print("- interval:", grid["interval"])
        print("- grid_dimensions:", grid["grid_dimensions"])
        print("- blocks_per_axis:", grid["blocks_per_axis"], "total:", grid["total_blocks"])
        print("- max points/block:", grid["per_block_points_max"])
        print("- approx xyz tensor MiB/block:", grid["per_block_coord_tensor_mib"])
    for warning in report.get("warnings", []):
        print("WARNING:", warning, file=sys.stderr)
    for error in report.get("errors", []):
        print("ERROR:", error, file=sys.stderr)
    if include_command:
        print("\nCommand:")
        print(report["command"])


def main() -> int:
    args = parse_args()
    report, code = make_report(args)
    if args.print_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report, args.print_command)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
