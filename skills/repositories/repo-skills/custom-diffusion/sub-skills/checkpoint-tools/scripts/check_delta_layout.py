#!/usr/bin/env python3
# Adapted from Adobe Research Custom Diffusion source code.
# Copyright 2022 Adobe Research. All rights reserved.
# To view a copy of the license, visit LICENSE.md.
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import torch

def _load(path: Path) -> dict:
    return torch.load(path, map_location="cpu", weights_only=False)

def _is_tensor_like(value: object) -> bool:
    return isinstance(value, torch.Tensor)

def _is_compressed_entry(value: object) -> bool:
    return isinstance(value, dict) and "u" in value and "v" in value and _is_tensor_like(value["u"]) and _is_tensor_like(value["v"])

def _summarize(path: Path, expect_family: str, expect_compressed: bool | None, require_modifier_token: bool) -> dict[str, object]:
    payload = _load(path)
    summary: dict[str, object] = {"path": str(path)}

    if "state_dict" in payload:
        family = "legacy"
        state = payload["state_dict"]
        compressed = any(_is_compressed_entry(value) for key, value in state.items() if "attn2.to_k" in key or "attn2.to_v" in key)
        summary["family"] = family
        summary["compressed"] = compressed
        summary["attn_keys"] = sum(1 for key in state if "attn2.to_k" in key or "attn2.to_v" in key)
        summary["embed_present"] = "embed" in state
        if expect_family not in {"auto", family}:
            raise ValueError(f"expected {expect_family} delta family, found {family}")
        if expect_compressed is True and not compressed:
            raise ValueError("expected a compressed legacy delta with u/v factors")
        if expect_compressed is False and compressed:
            raise ValueError("expected an uncompressed legacy delta but found u/v factors")
        if summary["attn_keys"] == 0:
            raise ValueError("legacy delta has no attn2.to_k / attn2.to_v keys")
        if require_modifier_token and "embed" not in state:
            raise ValueError("expected embed payload but none was found")
        for key, value in state.items():
            if "to_k" in key or "to_v" in key:
                if compressed:
                    if not _is_compressed_entry(value):
                        raise ValueError(f"compressed legacy entry {key} is missing u/v tensors")
                elif not _is_tensor_like(value):
                    raise ValueError(f"uncompressed legacy entry {key} is not a tensor")
        return summary

    if "unet" in payload:
        family = "diffusers"
        unet = payload["unet"]
        compressed = any(_is_compressed_entry(value) for key, value in unet.items() if "to_k" in key or "to_v" in key)
        summary["family"] = family
        summary["compressed"] = compressed
        summary["attn_keys"] = sum(1 for key in unet if "attn2.to_k" in key or "attn2.to_v" in key)
        summary["modifier_token_present"] = "modifier_token" in payload
        if expect_family not in {"auto", family}:
            raise ValueError(f"expected {expect_family} delta family, found {family}")
        if expect_compressed is True and not compressed:
            raise ValueError("expected a compressed diffusers delta with u/v factors")
        if expect_compressed is False and compressed:
            raise ValueError("expected an uncompressed diffusers delta but found u/v factors")
        if require_modifier_token and "modifier_token" not in payload:
            raise ValueError("expected modifier_token payload but none was found")
        for key, value in unet.items():
            if "to_k" in key or "to_v" in key:
                if compressed:
                    if not _is_compressed_entry(value):
                        raise ValueError(f"compressed entry {key} is missing u/v tensors")
                elif not _is_tensor_like(value):
                    raise ValueError(f"uncompressed entry {key} is not a tensor")
        return summary

    raise ValueError("checkpoint does not look like a legacy or diffusers Custom Diffusion delta")

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Custom Diffusion delta layout.")
    parser.add_argument("path", help="Path to a delta checkpoint.")
    parser.add_argument("--expect-family", choices=["auto", "legacy", "diffusers"], default="auto")
    parser.add_argument("--expect-compressed", choices=["auto", "true", "false"], default="auto")
    parser.add_argument("--require-modifier-token", action="store_true", help="Require a learned-token payload.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    expect_compressed = None if args.expect_compressed == "auto" else args.expect_compressed == "true"
    summary = _summarize(Path(args.path), args.expect_family, expect_compressed, args.require_modifier_token)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
