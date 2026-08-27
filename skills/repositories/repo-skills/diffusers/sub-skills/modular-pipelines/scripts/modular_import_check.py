#!/usr/bin/env python3
"""Check Diffusers modular pipeline imports and custom_blocks CLI parser registration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


MODULAR_NAMES = [
    "AutoPipelineBlocks",
    "BlockState",
    "ComponentSpec",
    "ComponentsManager",
    "ConditionalPipelineBlocks",
    "ConfigSpec",
    "InputParam",
    "LoopSequentialPipelineBlocks",
    "ModularPipeline",
    "ModularPipelineBlocks",
    "OutputParam",
    "PipelineState",
    "SequentialPipelineBlocks",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify core Diffusers modular imports and custom_blocks CLI parser registration."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    parser.add_argument(
        "--skip-cli",
        action="store_true",
        help="Skip custom_blocks CLI parser import/registration check.",
    )
    return parser


def add_source_checkout_to_path() -> str | None:
    for directory in [Path.cwd(), *Path.cwd().parents]:
        src_dir = directory / "src"
        if (src_dir / "diffusers" / "__init__.py").is_file():
            sys.path.insert(0, str(src_dir))
            return "source checkout src"
    return None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = {"ok": False, "imports": {}, "custom_blocks_cli": None, "errors": []}

    try:
        import diffusers
    except Exception:
        added_path = add_source_checkout_to_path()
        try:
            import diffusers
        except Exception as error:
            result["errors"].append(f"import diffusers failed: {error}")
            return finish(result, args.json, 1)
        if added_path is not None:
            result["path_hint"] = added_path

    result["diffusers_version"] = getattr(diffusers, "__version__", "unknown")

    try:
        import diffusers.modular_pipelines as modular
    except Exception as error:
        result["errors"].append(f"import diffusers.modular_pipelines failed: {error}")
        return finish(result, args.json, 1)

    for name in MODULAR_NAMES:
        try:
            getattr(modular, name)
            result["imports"][name] = True
        except Exception as error:
            result["imports"][name] = False
            result["errors"].append(f"missing modular import {name}: {error}")

    if not args.skip_cli:
        try:
            from diffusers.commands.custom_blocks import CustomBlocksCommand

            parser = argparse.ArgumentParser(prog="diffusers-cli")
            subparsers = parser.add_subparsers(dest="command")
            CustomBlocksCommand.register_subcommand(subparsers)
            parsed = parser.parse_args(["custom_blocks", "--block_module_name", "block.py", "--block_class_name", "ExampleBlock"])
            result["custom_blocks_cli"] = {
                "registered": True,
                "block_module_name": str(parsed.block_module_name),
                "block_class_name": parsed.block_class_name,
                "has_factory": callable(parsed.func),
            }
        except Exception as error:
            result["custom_blocks_cli"] = {"registered": False}
            result["errors"].append(f"custom_blocks CLI check failed: {error}")

    result["ok"] = not result["errors"] and all(result["imports"].values())
    return finish(result, args.json, 0 if result["ok"] else 1)


def finish(result: dict, as_json: bool, status: int) -> int:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"diffusers version: {result.get('diffusers_version', 'unknown')}")
        for name, ok in result.get("imports", {}).items():
            print(f"import {name}: {'ok' if ok else 'FAIL'}")
        cli = result.get("custom_blocks_cli")
        if cli is not None:
            print(f"custom_blocks CLI: {'ok' if cli.get('registered') and cli.get('has_factory') else 'FAIL'}")
        if result.get("errors"):
            print("errors:", file=sys.stderr)
            for error in result["errors"]:
                print(f"- {error}", file=sys.stderr)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
