#!/usr/bin/env python3
"""Validate DreamCraft3D preprocessed image sidecars without running models.

The checker is intentionally lightweight: it only inspects paths and basic image
metadata. It does not import torch, call CarveKit/Omnidata/BLIP2, download files,
or modify images.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_metadata(path: Path) -> Dict[str, Any]:
    """Return minimal PNG metadata, or a warning dict for non-PNG files."""
    result: Dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists() or not path.is_file():
        return result
    try:
        with path.open("rb") as f:
            sig = f.read(8)
            if sig != PNG_SIGNATURE:
                result.update({"is_png": False, "warning": "not a PNG file"})
                return result
            length = struct.unpack(">I", f.read(4))[0]
            chunk_type = f.read(4)
            if chunk_type != b"IHDR" or length < 13:
                result.update({"is_png": False, "warning": "invalid PNG IHDR"})
                return result
            ihdr = f.read(13)
            width, height = struct.unpack(">II", ihdr[:8])
            bit_depth = ihdr[8]
            color_type = ihdr[9]
            channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
            result.update(
                {
                    "is_png": True,
                    "width": width,
                    "height": height,
                    "bit_depth": bit_depth,
                    "color_type": color_type,
                    "channels": channels,
                    "has_alpha": color_type in (4, 6),
                }
            )
    except OSError as exc:
        result.update({"is_png": False, "warning": f"could not read PNG metadata: {exc}"})
    return result


def expected_sidecars(image: Path) -> Dict[str, Path]:
    name = image.name
    if name.endswith("_rgba.png"):
        stem = name[: -len("_rgba.png")]
    else:
        stem = image.stem
    return {
        "rgba": image,
        "depth": image.with_name(f"{stem}_depth.png"),
        "normal": image.with_name(f"{stem}_normal.png"),
        "caption": image.with_name(f"{stem}_caption.txt"),
    }


def check(args: argparse.Namespace) -> Tuple[int, Dict[str, Any]]:
    image = Path(args.image)
    sidecars = expected_sidecars(image)
    required = ["rgba"]
    if args.require_depth:
        required.append("depth")
    if args.require_normal:
        required.append("normal")
    if args.require_caption:
        required.append("caption")

    files: Dict[str, Dict[str, Any]] = {}
    problems: List[str] = []
    warnings: List[str] = []

    for key, path in sidecars.items():
        info: Dict[str, Any] = {"path": str(path), "exists": path.exists()}
        if path.exists() and path.is_file() and path.suffix.lower() == ".png":
            info.update(png_metadata(path))
        elif path.exists() and path.is_file() and path.suffix.lower() == ".txt":
            try:
                info["chars"] = len(path.read_text(encoding="utf-8", errors="replace"))
            except OSError as exc:
                info["warning"] = str(exc)
        files[key] = info

        if key in required and not path.exists():
            problems.append(f"required {key} file missing: {path}")
        if key in required and path.exists() and not path.is_file():
            problems.append(f"required {key} path is not a file: {path}")

    rgba = files["rgba"]
    if rgba.get("exists") and rgba.get("is_png") and not rgba.get("has_alpha"):
        warnings.append("RGBA image is a PNG but does not advertise an alpha channel; DreamCraft3D expects an alpha mask.")
    if image.name.endswith("_rgba.png") is False:
        warnings.append("input image name does not end with _rgba.png; DreamCraft3D configs conventionally use the preprocessed RGBA sidecar.")

    status = "ok" if not problems else ("warn" if args.allow_missing else "fail")
    report = {
        "status": status,
        "image": str(image),
        "required": required,
        "files": files,
        "problems": problems,
        "warnings": warnings,
        "notes": [
            "This checker does not run background removal, Omnidata depth/normal prediction, BLIP2 captioning, or any CUDA model.",
            "If required sidecars are missing, run or request full DreamCraft3D preprocessing only in an approved GPU/model environment.",
        ],
    }
    return (0 if status in ("ok", "warn") else 2), report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate DreamCraft3D preprocessed image sidecars.")
    parser.add_argument("--image", required=True, help="Path to the intended *_rgba.png image.")
    parser.add_argument("--require-depth", action="store_true", help="Require <stem>_depth.png.")
    parser.add_argument("--require-normal", action="store_true", help="Require <stem>_normal.png.")
    parser.add_argument("--require-caption", action="store_true", help="Require <stem>_caption.txt.")
    parser.add_argument("--allow-missing", action="store_true", help="Return success with status=warn when required files are missing.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    code, report = check(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        for key, info in report["files"].items():
            suffix = ""
            if info.get("is_png"):
                suffix = f" ({info.get('width')}x{info.get('height')}, channels={info.get('channels')})"
            print(f"{key}: {'present' if info.get('exists') else 'missing'} {info['path']}{suffix}")
        for warning in report["warnings"]:
            print(f"warning: {warning}")
        for problem in report["problems"]:
            print(f"problem: {problem}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
