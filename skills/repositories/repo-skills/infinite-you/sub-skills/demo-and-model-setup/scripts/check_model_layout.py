#!/usr/bin/env python3
"""Validate the local InfiniteYou model layout without downloading anything."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_MODEL_DIR = "./models/InfiniteYou"
DEFAULT_BASE_MODEL_PATH = "./models/FLUX.1-dev"
GATED_BASE_MODEL_ID = "black-forest-labs/FLUX.1-dev"

REQUIRED_LAYOUT = (
    ("infu_flux_v1.0/aes_stage2/InfuseNetModel", "dir"),
    ("infu_flux_v1.0/aes_stage2/image_proj_model.bin", "file"),
    ("infu_flux_v1.0/sim_stage1/InfuseNetModel", "dir"),
    ("infu_flux_v1.0/sim_stage1/image_proj_model.bin", "file"),
    ("supports/insightface", "dir"),
)

OPTIONAL_LORA_LAYOUT = (
    ("supports/optional_loras/flux_realism_lora.safetensors", "file"),
    ("supports/optional_loras/flux_anti_blur_lora.safetensors", "file"),
)


def path_exists(path: Path, kind: str) -> bool:
    if kind == "dir":
        return path.is_dir()
    if kind == "file":
        return path.is_file()
    raise ValueError(f"Unsupported path kind: {kind}")


def inspect_base_model(base_model_path: str | None) -> dict[str, Any]:
    report: dict[str, Any] = {
        "value": base_model_path,
        "mode": "unset",
        "exists": None,
        "warnings": [],
    }

    if not base_model_path:
        return report

    if base_model_path == GATED_BASE_MODEL_ID:
        report["mode"] = "gated_hf_repo"
        report["warnings"].append(
            "base_model_path points to black-forest-labs/FLUX.1-dev; gated Hugging Face access may be required before download succeeds."
        )
        return report

    candidate = Path(base_model_path).expanduser()
    if candidate.exists():
        report["mode"] = "local_dir" if candidate.is_dir() else "local_file"
        report["exists"] = True
        if candidate.is_dir():
            for subfolder in ("transformer", "text_encoder_2"):
                subpath = candidate / subfolder
                if not subpath.exists():
                    report["warnings"].append(
                        f"local base model is missing expected subpath: {subpath}"
                    )
        else:
            report["warnings"].append(
                "base_model_path resolves to a file, but the demo expects a directory-style FLUX base model layout."
            )
        return report

    report["mode"] = "missing_local"
    report["exists"] = False
    report["warnings"].append(
        "base_model_path does not exist locally; if this is meant to be a local directory, correct the path. If it is a remote repo id, ensure access and authentication."
    )
    return report


def build_report(model_dir: Path, base_model_path: str | None, require_optional_loras: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "model_dir": str(model_dir),
        "base_model_path": base_model_path,
        "require_optional_loras": require_optional_loras,
        "required": [],
        "optional_loras": [],
        "missing_required": [],
        "missing_optional": [],
        "warnings": [],
        "base_model": None,
    }

    if not model_dir.exists():
        report["warnings"].append(f"model_dir does not exist locally: {model_dir}")
    elif not model_dir.is_dir():
        report["warnings"].append(f"model_dir is not a directory: {model_dir}")

    for rel_path, kind in REQUIRED_LAYOUT:
        path = model_dir / rel_path
        exists = path_exists(path, kind)
        item = {
            "relative_path": rel_path,
            "path": str(path),
            "kind": kind,
            "exists": exists,
            "required": True,
        }
        report["required"].append(item)
        if not exists:
            report["missing_required"].append(str(path))

    for rel_path, kind in OPTIONAL_LORA_LAYOUT:
        path = model_dir / rel_path
        exists = path_exists(path, kind)
        item = {
            "relative_path": rel_path,
            "path": str(path),
            "kind": kind,
            "exists": exists,
            "required": require_optional_loras,
        }
        report["optional_loras"].append(item)
        if not exists:
            if require_optional_loras:
                report["missing_required"].append(str(path))
            else:
                report["missing_optional"].append(str(path))

    base_model_report = inspect_base_model(base_model_path)
    report["base_model"] = base_model_report
    report["warnings"].extend(base_model_report["warnings"])

    report["ok"] = len(report["missing_required"]) == 0
    return report


def render_text(report: dict[str, Any], quiet: bool) -> None:
    if not quiet:
        status = "OK" if report["ok"] else "NOT OK"
        print(f"Model layout: {status}")
        print(f"Model dir: {report['model_dir']}")
        if report.get("base_model_path"):
            print(f"Base model path: {report['base_model_path']}")
        print("")

    if report["missing_required"]:
        print("Missing required paths:", file=sys.stderr)
        for item in report["missing_required"]:
            print(f"  - {item}", file=sys.stderr)

    if report["missing_optional"] and not quiet:
        print("Missing optional LoRA paths:")
        for item in report["missing_optional"]:
            print(f"  - {item}")

    warnings = report["warnings"]
    if warnings:
        stream = sys.stderr if report["missing_required"] else sys.stdout
        heading = "Warnings:" if not quiet else "warning"
        print(heading, file=stream)
        for item in warnings:
            print(f"  - {item}", file=stream)

    if not quiet and not report["missing_required"]:
        print("All required InfiniteYou paths are present.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the local InfiniteYou model directory layout without downloading models.",
        epilog=(
            "Examples:\n"
            "  python scripts/check_model_layout.py\n"
            "  python scripts/check_model_layout.py --model-dir ./models/InfiniteYou --base-model-path ./models/FLUX.1-dev\n"
            "  python scripts/check_model_layout.py --require-optional-loras --json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--model-dir",
        default=DEFAULT_MODEL_DIR,
        help="Root directory for the InfiniteYou model tree (default: ./models/InfiniteYou)",
    )
    parser.add_argument(
        "--base-model-path",
        default=DEFAULT_BASE_MODEL_PATH,
        help="Optional FLUX base-model path or repo id (default: ./models/FLUX.1-dev)",
    )
    parser.add_argument(
        "--require-optional-loras",
        action="store_true",
        help="Treat the optional LoRA files as required paths.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of text.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce text output to warnings and missing-path details.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    model_dir = Path(args.model_dir).expanduser()
    report = build_report(model_dir, args.base_model_path, args.require_optional_loras)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        render_text(report, quiet=args.quiet)

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
