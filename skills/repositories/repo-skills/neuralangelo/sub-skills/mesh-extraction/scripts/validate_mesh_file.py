#!/usr/bin/env python3
"""Validate basic PLY structure for Neuralangelo mesh extraction outputs.

The default checks use only the Python standard library and inspect the PLY
header. Optional --use-trimesh performs a best-effort mesh load when trimesh is
installed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


COLOR_NAMES = {"red", "green", "blue", "r", "g", "b", "diffuse_red", "diffuse_green", "diffuse_blue"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a Neuralangelo output PLY file.")
    parser.add_argument("ply", help="Path to a PLY mesh file.")
    parser.add_argument("--min-vertices", type=int, default=0, help="Fail if vertex count is below this threshold.")
    parser.add_argument("--min-faces", type=int, default=0, help="Fail if face count is below this threshold.")
    parser.add_argument("--expect-textured", action="store_true", help="Require vertex color properties in the PLY header.")
    parser.add_argument("--use-trimesh", action="store_true", help="Optionally load with trimesh if installed.")
    parser.add_argument("--print-json", action="store_true", help="Emit JSON report instead of text.")
    return parser.parse_args()


def read_header(path: Path, limit: int = 1024 * 1024) -> Tuple[Optional[List[str]], List[str]]:
    errors: List[str] = []
    try:
        with path.open("rb") as handle:
            data = handle.read(limit)
    except FileNotFoundError:
        return None, ["file does not exist"]
    except OSError as exc:
        return None, [f"could not read file: {exc}"]
    if not data:
        return None, ["file is empty"]
    marker = b"end_header"
    idx = data.find(marker)
    if idx < 0:
        return None, ["PLY header does not contain end_header within read limit"]
    line_end = data.find(b"\n", idx)
    if line_end < 0:
        line_end = idx + len(marker)
    header_bytes = data[:line_end]
    try:
        text = header_bytes.decode("ascii")
    except UnicodeDecodeError:
        text = header_bytes.decode("ascii", errors="replace")
        errors.append("header contains non-ASCII bytes")
    lines = [line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip()]
    return lines, errors


def parse_header(lines: Optional[List[str]]) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "format": None,
        "vertex_count": None,
        "face_count": None,
        "vertex_properties": [],
        "face_properties": [],
        "comments": [],
        "has_color": False,
    }
    if not lines:
        return info
    current_element: Optional[str] = None
    for i, line in enumerate(lines):
        parts = line.split()
        if i == 0 and line != "ply":
            info.setdefault("header_errors", []).append("first header line is not 'ply'")
            continue
        if not parts:
            continue
        if parts[0] == "format" and len(parts) >= 2:
            info["format"] = parts[1]
        elif parts[0] == "comment":
            info["comments"].append(line[len("comment"):].strip())
        elif parts[0] == "element" and len(parts) >= 3:
            current_element = parts[1]
            try:
                count = int(parts[2])
            except ValueError:
                info.setdefault("header_errors", []).append(f"invalid count in line: {line}")
                continue
            if current_element == "vertex":
                info["vertex_count"] = count
            elif current_element == "face":
                info["face_count"] = count
        elif parts[0] == "property" and current_element:
            prop_name = parts[-1]
            if current_element == "vertex":
                info["vertex_properties"].append(prop_name)
            elif current_element == "face":
                info["face_properties"].append(prop_name)
    prop_set = {p.lower() for p in info["vertex_properties"]}
    rgb_long = {"red", "green", "blue"}.issubset(prop_set)
    rgb_short = {"r", "g", "b"}.issubset(prop_set)
    diffuse = {"diffuse_red", "diffuse_green", "diffuse_blue"}.issubset(prop_set)
    info["has_color"] = bool(rgb_long or rgb_short or diffuse or (prop_set & COLOR_NAMES and len(prop_set & COLOR_NAMES) >= 3))
    return info


def run_trimesh_check(path: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {"requested": True, "available": False, "loaded": False}
    try:
        import trimesh  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        result["error"] = f"trimesh unavailable: {exc}"
        return result
    result["available"] = True
    try:
        mesh = trimesh.load(str(path), force="mesh", process=False)
    except Exception as exc:  # pragma: no cover - environment dependent
        result["error"] = f"trimesh load failed: {exc}"
        return result
    result["loaded"] = True
    result["is_empty"] = bool(getattr(mesh, "is_empty", False))
    vertices = getattr(mesh, "vertices", [])
    faces = getattr(mesh, "faces", [])
    result["vertex_count"] = int(len(vertices))
    result["face_count"] = int(len(faces))
    try:
        bounds = getattr(mesh, "bounds", None)
        if bounds is not None:
            result["bounds"] = [[float(x) for x in row] for row in bounds]
    except Exception:
        pass
    return result


def validate(args: argparse.Namespace) -> Tuple[Dict[str, Any], int]:
    path = Path(args.ply)
    errors: List[str] = []
    warnings: List[str] = []
    if args.min_vertices < 0:
        errors.append("min-vertices must be nonnegative")
    if args.min_faces < 0:
        errors.append("min-faces must be nonnegative")

    lines, header_errors = read_header(path)
    errors.extend(header_errors)
    info = parse_header(lines)
    errors.extend(info.pop("header_errors", []))

    if lines is not None:
        if info.get("format") not in {"ascii", "binary_little_endian", "binary_big_endian"}:
            errors.append("PLY format is missing or unsupported")
        if info.get("vertex_count") is None:
            errors.append("PLY header has no vertex element")
        if info.get("face_count") is None:
            warnings.append("PLY header has no face element")
        vertex_count = info.get("vertex_count")
        face_count = info.get("face_count")
        if isinstance(vertex_count, int) and vertex_count < args.min_vertices:
            errors.append(f"vertex count {vertex_count} is below minimum {args.min_vertices}")
        if isinstance(face_count, int) and face_count < args.min_faces:
            errors.append(f"face count {face_count} is below minimum {args.min_faces}")
        if args.expect_textured and not info.get("has_color"):
            errors.append("expected textured PLY but vertex color properties were not found")
        if isinstance(vertex_count, int) and vertex_count == 0:
            warnings.append("PLY declares zero vertices")
        if isinstance(face_count, int) and face_count == 0:
            warnings.append("PLY declares zero faces")

    trimesh_result: Optional[Dict[str, Any]] = None
    if args.use_trimesh and not errors:
        trimesh_result = run_trimesh_check(path)
        if trimesh_result.get("available") and not trimesh_result.get("loaded"):
            errors.append(str(trimesh_result.get("error", "trimesh load failed")))
        elif trimesh_result.get("loaded") and trimesh_result.get("is_empty"):
            warnings.append("trimesh loaded an empty mesh")

    report: Dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "header": info,
        "warnings": warnings,
        "errors": errors,
    }
    if trimesh_result is not None:
        report["trimesh"] = trimesh_result
    return report, 2 if errors else 0


def print_text(report: Dict[str, Any]) -> None:
    print("PLY validation report")
    print("- path:", report["path"])
    print("- exists:", report["exists"])
    print("- size_bytes:", report["size_bytes"])
    header = report.get("header") or {}
    print("- format:", header.get("format"))
    print("- vertices:", header.get("vertex_count"))
    print("- faces:", header.get("face_count"))
    print("- has_color:", header.get("has_color"))
    if report.get("trimesh"):
        print("- trimesh:", report["trimesh"])
    for warning in report.get("warnings", []):
        print("WARNING:", warning, file=sys.stderr)
    for error in report.get("errors", []):
        print("ERROR:", error, file=sys.stderr)


def main() -> int:
    args = parse_args()
    report, code = validate(args)
    if args.print_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
