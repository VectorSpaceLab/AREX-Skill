#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def validate_architecture(spec: dict) -> dict:
    mode = spec.get("mode", "full")
    warnings = []
    errors = []
    if not spec.get("use_scale_shift_norm"):
        errors.append("scale-shift adaptive normalization is required for paper-like claims")
    if not spec.get("attention_resolutions"):
        errors.append("attention resolutions are required for ImageNet-style guided diffusion")
    if mode == "full":
        if not spec.get("resblock_updown"):
            errors.append("BigGAN-style residual up/downsampling is required for full claims")
        if not spec.get("learn_sigma"):
            errors.append("learned sigma is required for full paper-like sampling claims")
    else:
        for key in ["resblock_updown", "learn_sigma", "class_cond"]:
            if not spec.get(key):
                warnings.append(f"{key} omitted in declared {mode} run")
    return {"ok": not errors, "mode": mode, "errors": errors, "warnings": warnings, "spec": spec}


def example_spec(name: str) -> dict:
    if name == "paper128":
        return {
            "mode": "full",
            "image_size": 128,
            "num_channels": 256,
            "num_res_blocks": 2,
            "attention_resolutions": [32, 16, 8],
            "use_scale_shift_norm": True,
            "resblock_updown": True,
            "learn_sigma": True,
            "class_cond": True,
        }
    if name == "proxy":
        return {
            "mode": "proxy",
            "image_size": 1,
            "num_channels": 0,
            "num_res_blocks": 0,
            "attention_resolutions": [1],
            "use_scale_shift_norm": True,
            "resblock_updown": False,
            "learn_sigma": False,
            "class_cond": True,
        }
    raise ValueError(f"unknown example: {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--example", choices=["paper128", "proxy"], required=True)
    args = parser.parse_args()
    print(json.dumps(validate_architecture(example_spec(args.example)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
