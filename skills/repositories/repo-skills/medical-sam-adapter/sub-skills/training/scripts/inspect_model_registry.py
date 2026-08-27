#!/usr/bin/env python3
"""Inspect documented train.py registries without importing the project.

This helper is read-only and standard-library-only. It does not import torch or
repository modules, instantiate models, read checkpoints, contact a network,
or launch training.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any, Dict, Optional

REGISTRIES: Dict[str, Dict[str, str]] = {
    "sam": {"default": "vit_b", "vit_b": "vit_b", "vit_h": "vit_h", "vit_l": "vit_l"},
    "efficient_sam": {"default": "vit_s", "vit_s": "vit_s", "vit_t": "vit_t"},
    "mobile_sam": {
        "default": "vit_h", "vit_h": "vit_h", "vit_l": "vit_l", "vit_b": "vit_b",
        "tiny_vit": "tiny_vit", "efficientvit_l2": "efficientvit_l2",
        "PromptGuidedDecoder": "PromptGuidedDecoder", "sam_vit_h": "sam_vit_h",
    },
}
MODES = ("sam_adpt", "sam_lora", "sam_adalora")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def parse_json_value(value: str) -> Dict[str, Any]:
    """Read a JSON object literal or a JSON file without executing it."""
    if value.lstrip().startswith("{"):
        raw = value
    else:
        try:
            raw = pathlib.Path(value).read_text(encoding="utf-8")
        except OSError as exc:
            fail(f"--json must be an object literal or readable JSON file: {exc}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"--json is not valid JSON: {exc}")
    if not isinstance(data, dict):
        fail("--json must contain an object with net, encoder, and optional mod")
    return data


def show_catalog(as_json: bool) -> None:
    if as_json:
        print(json.dumps({"registries": REGISTRIES, "modes": list(MODES)}, indent=2))
        return
    print("Documented train.py registries (static; no source imports):")
    for net, encoders in REGISTRIES.items():
        print("  " + net + ": " + ", ".join(f"{key} -> {value}" for key, value in encoders.items()))
    print("Named adaptation modes: " + ", ".join(MODES))


def inspect(net: str, encoder: str, mod: Optional[str]) -> Dict[str, Any]:
    if net not in REGISTRIES:
        fail(f"unknown net '{net}'; expected one of: {', '.join(REGISTRIES)}")
    if encoder not in REGISTRIES[net]:
        fail(f"unknown encoder '{encoder}' for net '{net}'; expected one of: {', '.join(REGISTRIES[net])}")
    if mod is not None and mod not in MODES:
        fail(f"unknown mode '{mod}'; expected one of: {', '.join(MODES)}")

    # These are source-backed construction limitations. They prevent a static
    # check from blessing a known partial or no-LoRA train.py selection.
    if net == "sam" and mod == "sam_adalora":
        fail("sam_adalora is not source-compatible with original SAM: its encoder constructs ordinary Blocks")
    if net == "mobile_sam" and encoder == "PromptGuidedDecoder":
        fail("mobile_sam/PromptGuidedDecoder is not a train.py network; it returns prompt/mask components")
    if net == "mobile_sam" and encoder == "sam_vit_h":
        fail("mobile_sam/sam_vit_h is not a train.py network; it returns an image encoder only")
    if net == "mobile_sam" and encoder in {"default", "vit_h", "vit_l", "vit_b"} and mod in {"sam_lora", "sam_adalora"}:
        fail(f"mobile_sam/{encoder} does not construct LoRA/AdaLoRA blocks for {mod}; use tiny_vit or another verified family")
    if net == "mobile_sam" and encoder == "efficientvit_l2" and mod in MODES:
        fail("mobile_sam/efficientvit_l2 has no source-selected Adapter, LoRA, or AdaLoRA block in its large-backbone constructor")

    warnings = []
    if mod is None:
        warnings.append("mode not supplied; pass --mod to check adaptation compatibility")
    if net == "efficient_sam" and mod == "sam_adalora":
        warnings.append("verify lora_ parameter names and rank-allocator targets in a real CUDA model smoke")
    if net == "mobile_sam" and encoder == "tiny_vit":
        warnings.append("full-model and encoder-only MobileSAM checkpoint wrappers differ; inspect the local artifact")
    return {
        "net": net,
        "encoder": encoder,
        "registry_target": REGISTRIES[net][encoder],
        "mode": mod,
        "status": "compatible-static-selection",
        "checkpoint_note": {
            "sam": "raw model state dict; original builder retains matching names and shapes",
            "efficient_sam": "matching EfficientSAM checkpoint layout for vit_s or vit_t",
            "mobile_sam": "standard SAM-like state dict, or a model-wrapped TinyViT artifact depending on builder",
        }[net],
        "warnings": warnings,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect documented train.py registries without importing CUDA-heavy source modules."
    )
    parser.add_argument("--list", action="store_true", help="list registry names and exit")
    parser.add_argument("--net", help="network family: sam, efficient_sam, or mobile_sam")
    parser.add_argument("--encoder", help="case-sensitive encoder registry name")
    parser.add_argument("--mod", help="named mode: sam_adpt, sam_lora, or sam_adalora")
    parser.add_argument("--json", metavar="OBJECT_OR_FILE", help="JSON object literal or readable JSON file with net, encoder, and optional mod")
    parser.add_argument("--output", choices=("text", "json"), default="text", help="output format (default: text)")
    args = parser.parse_args(argv)

    if args.list:
        show_catalog(args.output == "json")
        return 0
    values: Dict[str, Any] = parse_json_value(args.json) if args.json else {}
    net = args.net if args.net is not None else values.get("net")
    encoder = args.encoder if args.encoder is not None else values.get("encoder")
    mod = args.mod if args.mod is not None else values.get("mod")
    if not isinstance(net, str) or not net:
        fail("provide --net or JSON key 'net'")
    if not isinstance(encoder, str) or not encoder:
        fail("provide --encoder or JSON key 'encoder'")
    if mod is not None and not isinstance(mod, str):
        fail("mode must be a string when supplied")

    result = inspect(net, encoder, mod)
    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"OK: {result['net']}/{result['encoder']} -> {result['registry_target']}")
        if result["mode"]:
            print(f"  mode: {result['mode']}")
        print(f"  checkpoint: {result['checkpoint_note']}")
        for warning in result["warnings"]:
            print(f"  warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
