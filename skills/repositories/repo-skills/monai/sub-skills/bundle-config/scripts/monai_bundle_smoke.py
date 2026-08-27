#!/usr/bin/env python3
"""Safe MONAI Bundle smoke checks using installed package APIs only."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def _require_monai() -> Any:
    try:
        import monai  # noqa: PLC0415
        from monai.bundle import ConfigParser  # noqa: PLC0415
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise SystemExit(f"MONAI bundle imports failed: {exc}") from exc
    return monai, ConfigParser


def _tiny_config() -> dict[str, Any]:
    return {
        "dims": 2,
        "network_def": {
            "_target_": "monai.networks.nets.UNet",
            "spatial_dims": "@dims",
            "in_channels": 1,
            "out_channels": 2,
            "channels": [4, 8],
            "strides": [2],
        },
        "summary": "$@dims + @network_def#out_channels",
    }


def _tiny_metadata(monai_version: str) -> dict[str, Any]:
    return {
        "schema": "https://github.com/Project-MONAI/MONAI-extra-test-data/releases/download/0.8.1/meta_schema_20220324.json",
        "version": "0.1.0",
        "monai_version": monai_version,
        "pytorch_version": "unknown",
        "numpy_version": "unknown",
        "required_packages_version": {},
        "task": "Tiny synthetic Bundle smoke test",
        "description": "A tiny CPU-safe Bundle skeleton for checking MONAI Bundle config parsing.",
        "authors": "Example",
        "copyright": "Example",
        "network_data_format": {
            "inputs": {
                "image": {
                    "type": "image",
                    "format": "magnitude",
                    "modality": "n/a",
                    "num_channels": 1,
                    "spatial_shape": [16, 16],
                    "dtype": "float32",
                    "value_range": [0, 1],
                    "is_patch_data": False,
                    "channel_def": {"0": "image"},
                }
            },
            "outputs": {
                "pred": {
                    "type": "image",
                    "format": "classes",
                    "num_channels": 2,
                    "spatial_shape": [16, 16],
                    "dtype": "float32",
                    "value_range": [],
                    "is_patch_data": False,
                    "channel_def": {"0": "background", "1": "foreground"},
                }
            },
        },
    }


def parse_inline(args: argparse.Namespace) -> int:
    monai, ConfigParser = _require_monai()
    parser = ConfigParser(_tiny_config(), globals={"monai": "monai"})
    parser.update({"network_def#out_channels": args.out_channels})
    raw_network = parser.get_parsed_content("network_def", instantiate=False)
    raw_network_config = getattr(raw_network, "config", raw_network)
    summary = parser.get_parsed_content("summary")
    network = raw_network.instantiate() if args.instantiate_network and hasattr(raw_network, "instantiate") else None
    result = {
        "monai_version": monai.__version__,
        "raw_network_target": raw_network_config.get("_target_"),
        "raw_network_out_channels": raw_network_config.get("out_channels"),
        "summary": summary,
        "instantiated_network_type": type(network).__name__ if network is not None else None,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def build_tiny_bundle(args: argparse.Namespace) -> int:
    monai, ConfigParser = _require_monai()
    output = Path(args.output)
    if output.exists():
        if not args.force:
            raise SystemExit(f"Refusing to overwrite existing path: {output}")
        if output.is_dir():
            shutil.rmtree(output)
        else:
            output.unlink()
    (output / "configs").mkdir(parents=True)
    (output / "models").mkdir()
    (output / "docs").mkdir()
    ConfigParser.export_config_file(_tiny_config(), output / "configs" / "inference.json", indent=2)
    ConfigParser.export_config_file(_tiny_metadata(monai.__version__), output / "configs" / "metadata.json", indent=2)
    (output / "LICENSE").write_text("Select a license for this bundle.\n", encoding="utf-8")
    (output / "docs" / "README.md").write_text(
        "# Tiny MONAI Bundle\n\nThis synthetic bundle is for parser and CLI experiments only.\n",
        encoding="utf-8",
    )
    print(json.dumps({"created": str(output), "config": "configs/inference.json", "metadata": "configs/metadata.json"}, indent=2))
    return 0


def cli_help(args: argparse.Namespace) -> int:
    _require_monai()
    command = [sys.executable, "-m", "monai.bundle"]
    if args.command:
        command.extend([args.command, "--", "--help"])
    else:
        command.append("--help")
    completed = subprocess.run(command, check=False, text=True, capture_output=True)
    print(completed.stdout)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)
    return completed.returncode


def temp_bundle(args: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory(prefix="monai-bundle-smoke-") as directory:
        build_tiny_bundle(argparse.Namespace(output=directory, force=False))
        if args.show_path:
            print(directory)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe MONAI Bundle smoke checks.")
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    parse_parser = subparsers.add_parser("parse-inline", help="Parse a tiny inline Bundle config.")
    parse_parser.add_argument("--out-channels", type=int, default=3, help="Override network_def#out_channels.")
    parse_parser.add_argument(
        "--instantiate-network",
        action="store_true",
        help="Instantiate the tiny UNet after parsing. This is CPU-safe but imports torch network code.",
    )
    parse_parser.set_defaults(func=parse_inline)

    build_parser = subparsers.add_parser("build-tiny-bundle", help="Write a tiny self-contained Bundle skeleton.")
    build_parser.add_argument("--output", required=True, help="Output directory to create.")
    build_parser.add_argument("--force", action="store_true", help="Overwrite the output path if it exists.")
    build_parser.set_defaults(func=build_tiny_bundle)

    help_parser = subparsers.add_parser("cli-help", help="Show MONAI Bundle CLI help through python -m monai.bundle.")
    help_parser.add_argument("--command", help="Optional command name, such as run or verify_metadata.")
    help_parser.set_defaults(func=cli_help)

    temp_parser = subparsers.add_parser("temp-bundle", help="Create and discard a temporary tiny Bundle skeleton.")
    temp_parser.add_argument("--show-path", action="store_true", help="Print the temporary path before it is removed.")
    temp_parser.set_defaults(func=temp_bundle)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
