#!/usr/bin/env python3
"""Inspect the distilled Medical-SAM-Adapter CLI contract without importing the repo."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

OPTIONS: dict[str, dict[str, Any]] = {
    "-seed": {"type": "int", "default": 24},
    "-net": {"type": "str", "default": "sam"},
    "-baseline": {"type": "str", "default": "unet"},
    "-encoder": {"type": "str", "default": "default"},
    "-seg_net": {"type": "str", "default": "transunet"},
    "-mod": {"type": "str", "default": "sam_adpt"},
    "-exp_name": {"type": "str", "default": "msa_test_isic"},
    "-type": {"type": "str", "default": "map"},
    "-vis": {"type": "int", "default": None},
    "-reverse": {"type": "bool", "default": False, "warning": "type=bool parses non-empty strings as true"},
    "-pretrain": {"type": "bool", "default": False, "warning": "type=bool; train.py later treats truthy value as a path"},
    "-val_freq": {"type": "int", "default": 5},
    "-gpu": {"type": "bool", "default": True, "warning": "type=bool; core paths still construct CUDA state"},
    "-gpu_device": {"type": "int", "default": 0},
    "-sim_gpu": {"type": "int", "default": 0},
    "-epoch_ini": {"type": "int", "default": 1},
    "-image_size": {"type": "int", "default": 256},
    "-out_size": {"type": "int", "default": 256},
    "-patch_size": {"type": "int", "default": 2},
    "-dim": {"type": "int", "default": 512},
    "-depth": {"type": "int", "default": 1},
    "-heads": {"type": "int", "default": 16},
    "-mlp_dim": {"type": "int", "default": 1024},
    "-w": {"type": "int", "default": 4},
    "-b": {"type": "int", "default": 2},
    "-s": {"type": "bool", "default": True, "warning": "type=bool parses non-empty strings as true"},
    "-warm": {"type": "int", "default": 1},
    "-lr": {"type": "float", "default": 1e-4},
    "-uinch": {"type": "int", "default": 1},
    "-imp_lr": {"type": "float", "default": 3e-4},
    "-weights": {"type": "str|0", "default": 0},
    "-base_weights": {"type": "str|0", "default": 0},
    "-sim_weights": {"type": "str|0", "default": 0},
    "-distributed": {"type": "str", "default": "none"},
    "-dataset": {"type": "str", "default": "isic"},
    "-sam_ckpt": {"type": "path|None", "default": None},
    "-thd": {"type": "bool", "default": False, "warning": "type=bool; use an effective-value check for 3D mode"},
    "-chunk": {"type": "int|None", "default": None},
    "-num_sample": {"type": "int", "default": 4},
    "-roi_size": {"type": "int", "default": 96},
    "-evl_chunk": {"type": "int|None", "default": None},
    "-mid_dim": {"type": "int|None", "default": None},
    "-multimask_output": {"type": "int", "default": 1},
    "-data_path": {"type": "path", "default": "../data"},
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only catalog of the shared cfg.parse_args contract; never imports or launches training."
    )
    parser.add_argument("--list", action="store_true", help="print all options as JSON")
    parser.add_argument("--flag", help="print one exact flag entry, for example -image_size")
    parser.add_argument("--validate-flag", metavar="FLAG=VALUE", help="check that FLAG is known; use --validate-flag=-thd=False for source-style flags; value is not executed")
    args = parser.parse_args(argv)
    if not args.list and not args.flag and not args.validate_flag:
        parser.error("choose --list, --flag FLAG, or --validate-flag=FLAG=VALUE")
    if args.flag:
        if args.flag not in OPTIONS:
            print(f"unknown flag {args.flag!r}", file=sys.stderr)
            return 2
        print(json.dumps({args.flag: OPTIONS[args.flag]}, indent=2, sort_keys=True))
    if args.validate_flag:
        if "=" not in args.validate_flag:
            parser.error("--validate-flag expects FLAG=VALUE")
        flag, value = args.validate_flag.split("=", 1)
        if flag not in OPTIONS:
            print(f"unknown flag {flag!r}", file=sys.stderr)
            return 2
        print(json.dumps({"flag": flag, "value": value, "known": True, "note": OPTIONS[flag].get("warning")}, indent=2))
    if args.list:
        print(json.dumps(OPTIONS, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
