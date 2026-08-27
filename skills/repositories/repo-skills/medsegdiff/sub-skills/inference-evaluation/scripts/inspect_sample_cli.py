#!/usr/bin/env python3
"""Inspect MedSegDiff sampling arguments without importing the project.

This tool is deliberately parser-only: it does not inspect a checkpoint, touch
data, initialize torch/CUDA, or create an output directory.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Union



def str2bool(value: Union[str, bool]) -> bool:
    if isinstance(value, bool):
        return value
    lowered = value.lower()
    if lowered in {"yes", "true", "t", "y", "1"}:
        return True
    if lowered in {"no", "false", "f", "n", "0"}:
        return False
    raise argparse.ArgumentTypeError("expected a boolean: true/false")


MODEL_DEFAULTS: Dict[str, Any] = {
    "image_size": 64,
    "num_channels": 128,
    "num_res_blocks": 2,
    "num_heads": 4,
    "in_ch": 5,
    "num_heads_upsample": -1,
    "num_head_channels": -1,
    "attention_resolutions": "16,8",
    "channel_mult": "",
    "dropout": 0.0,
    "class_cond": False,
    "use_checkpoint": False,
    "use_scale_shift_norm": True,
    "resblock_updown": False,
    "use_fp16": False,
    "use_new_attention_order": False,
    "dpm_solver": False,
    "version": "new",
    "learn_sigma": False,
    "diffusion_steps": 1000,
    "noise_schedule": "linear",
    "timestep_respacing": "",
    "use_kl": False,
    "predict_xstart": False,
    "rescale_timesteps": False,
    "rescale_learned_sigmas": False,
}



def add_argument(parser: argparse.ArgumentParser, name: str, default: Any) -> None:
    kind = str2bool if isinstance(default, bool) else type(default)
    parser.add_argument(f"--{name}", default=default, type=kind)



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely parse MedSegDiff sampler flags and print the effective "
            "dataset branch/channel and output plan. No model, CUDA, or data "
            "is loaded."
        )
    )
    sampler_defaults = {
        "data_name": "BRATS",
        "data_dir": "../dataset/brats2020/testing",
        "clip_denoised": True,
        "num_samples": 1,
        "batch_size": 1,
        "use_ddim": False,
        "model_path": "",
        "num_ensemble": 5,
        "gpu_dev": "0",
        "out_dir": "./results/",
        "multi_gpu": None,
        "debug": False,
    }
    for name, default in sampler_defaults.items():
        if default is None:
            parser.add_argument(f"--{name}", default=default, type=str)
        else:
            add_argument(parser, name, default)
    for name, default in MODEL_DEFAULTS.items():
        add_argument(parser, name, default)
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the effective plan as JSON instead of a human-readable report",
    )
    return parser



def effective_plan(args: argparse.Namespace) -> Dict[str, Any]:
    requested = str(args.data_name)
    if requested == "ISIC":
        branch, effective_in_ch, input_channels = "ISIC", 4, "RGB + random noise"
        id_rule = "final underscore token of the input filename"
        data_contract = "ISIC test CSV and image/mask paths"
    elif requested == "BRATS":
        branch, effective_in_ch, input_channels = "BRATS", 5, "four MRI channels + random noise"
        id_rule = "BRATS virtual case token + slice token"
        data_contract = "BRATSDataset3D sequence files and virtual slices"
    else:
        branch, effective_in_ch, input_channels = "custom", 4, "RGB + random noise"
        id_rule = "undefined in the unpatched source custom branch"
        data_contract = "sorted images/*.png and masks/*.png"

    if args.use_ddim:
        sampler = "DDIM-known (source caller passes an unsupported step keyword)"
    elif args.dpm_solver:
        sampler = "DDPM known loop with DPM-Solver++ order-2 multistep"
    else:
        sampler = "DDPM known loop"

    warnings = []
    if args.batch_size != 1:
        warnings.append("source derives one output ID from path[0]; batch_size>1 can collide or mislabel outputs")
    if args.num_ensemble < 1:
        warnings.append("num_ensemble must be positive for aggregation")
    if not args.model_path:
        warnings.append("model_path is empty; this inspection does not load a checkpoint")
    if args.use_ddim:
        warnings.append("unpatched source DDIM-known function does not accept the caller's step argument")
    if branch == "custom":
        warnings.append("source custom branch does not assign slice_ID before writing outputs")

    return {
        "branch": branch,
        "requested_data_name": requested,
        "data_dir": args.data_dir,
        "data_contract": data_contract,
        "effective_in_ch": effective_in_ch,
        "input_channels": input_channels,
        "model_in_ch_flag_before_branch_override": args.in_ch,
        "image_size": args.image_size,
        "version": args.version,
        "sampler": sampler,
        "diffusion_steps": args.diffusion_steps,
        "num_ensemble": args.num_ensemble,
        "batch_size": args.batch_size,
        "output_id_rule": id_rule,
        "ensemble_filename": "<slice_ID>_output_ens.jpg",
        "member_filename": "<slice_ID>_output{i}.jpg",
        "checkpoint_path": args.model_path or None,
        "warnings": warnings,
        "safe_check": "parser/default inspection only; no checkpoint, data, CUDA, or output access",
    }



def main() -> int:
    args = build_parser().parse_args()
    plan = effective_plan(args)
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0
    print("MedSegDiff sampling inspection (no runtime access performed)")
    for key in (
        "branch",
        "data_contract",
        "effective_in_ch",
        "input_channels",
        "image_size",
        "version",
        "sampler",
        "diffusion_steps",
        "num_ensemble",
        "batch_size",
        "output_id_rule",
        "ensemble_filename",
    ):
        print(f"{key}: {plan[key]}")
    if plan["warnings"]:
        print("warnings:")
        for warning in plan["warnings"]:
            print(f"- {warning}")
    else:
        print("warnings: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
