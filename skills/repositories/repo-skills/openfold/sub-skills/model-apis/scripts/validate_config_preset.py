#!/usr/bin/env python3
"""Validate an OpenFold config preset and safe high-level overrides.

This helper calls openfold.config.model_config and reports selected config fields.
It does not instantiate AlphaFold, load weights, run model execution, download
assets, compile TensorRT engines, or write files.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path
from typing import Any

VALID_PRECISIONS = {"tf32", "fp32", "fp16", "bf16"}


def add_package_root(package_root: str | None) -> None:
    root = str(Path(package_root).expanduser().resolve()) if package_root else str(Path.cwd())
    if root not in sys.path:
        sys.path.insert(0, root)


def get_path(config: Any, dotted_path: str, default: Any = None) -> Any:
    current = config
    for part in dotted_path.split("."):
        try:
            current = current[part]
        except Exception:
            try:
                current = getattr(current, part)
            except Exception:
                return default
    return current


def validate_args(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    if args.precision not in VALID_PRECISIONS:
        errors.append(f"precision must be one of {', '.join(sorted(VALID_PRECISIONS))}")
    if args.train and args.long_sequence_inference:
        errors.append("long-sequence inference is incompatible with --train")
    if args.trt_mode and not args.trt_engine_dir:
        errors.append("--trt-mode requires --trt-engine-dir")
    if args.trt_num_profiles < 1:
        errors.append("--trt-num-profiles must be at least 1")
    if not 0 <= args.trt_optimization_level <= 5:
        errors.append("--trt-optimization-level should be between 0 and 5")
    if args.trt_max_sequence_len < 1:
        errors.append("--trt-max-sequence-len must be positive")
    if args.use_flash and args.long_sequence_inference:
        errors.append("--use-flash conflicts with long-sequence inference, which disables FlashAttention")
    attention_flags = [
        args.use_flash,
        args.use_deepspeed_evoformer_attention,
        args.use_cuequivariance_attention,
    ]
    if sum(bool(flag) for flag in attention_flags) > 1:
        errors.append(
            "choose at most one attention backend among --use-flash, "
            "--use-deepspeed-evoformer-attention, and --use-cuequivariance-attention"
        )
    return errors


def set_path(config: Any, dotted_path: str, value: Any) -> None:
    parts = dotted_path.split(".")
    current = config
    for part in parts[:-1]:
        try:
            current = current[part]
        except Exception:
            current = getattr(current, part)
    try:
        current[parts[-1]] = value
    except Exception:
        setattr(current, parts[-1], value)


def summarize_config(config: Any) -> dict[str, Any]:
    return {
        "precision": get_path(config, "precision"),
        "globals": {
            "is_multimer": bool(get_path(config, "globals.is_multimer", False)),
            "seqemb_mode_enabled": bool(get_path(config, "globals.seqemb_mode_enabled", False)),
            "use_deepspeed_evo_attention": bool(get_path(config, "globals.use_deepspeed_evo_attention", False)),
            "use_cuequivariance_attention": bool(get_path(config, "globals.use_cuequivariance_attention", False)),
            "use_cuequivariance_multiplicative_update": bool(
                get_path(config, "globals.use_cuequivariance_multiplicative_update", False)
            ),
            "use_flash": bool(get_path(config, "globals.use_flash", False)),
            "use_lma": bool(get_path(config, "globals.use_lma", False)),
            "offload_inference": bool(get_path(config, "globals.offload_inference", False)),
            "chunk_size": get_path(config, "globals.chunk_size"),
            "blocks_per_ckpt": get_path(config, "globals.blocks_per_ckpt"),
        },
        "data": {
            "use_templates": bool(get_path(config, "data.common.use_templates", False)),
            "predict_fixed_size": bool(get_path(config, "data.predict.fixed_size", False)),
            "predict_max_msa_clusters": get_path(config, "data.predict.max_msa_clusters"),
            "predict_max_extra_msa": get_path(config, "data.predict.max_extra_msa"),
            "train_crop_size": get_path(config, "data.train.crop_size"),
        },
        "model": {
            "template_enabled": bool(get_path(config, "model.template.enabled", False)),
            "template_average_templates": bool(get_path(config, "model.template.average_templates", False)),
            "template_offload_templates": bool(get_path(config, "model.template.offload_templates", False)),
            "template_offload_inference": bool(get_path(config, "model.template.offload_inference", False)),
            "template_pair_stack_tune_chunk_size": bool(
                get_path(config, "model.template.template_pair_stack.tune_chunk_size", False)
            ),
            "extra_msa_stack_tune_chunk_size": bool(
                get_path(config, "model.extra_msa.extra_msa_stack.tune_chunk_size", False)
            ),
            "evoformer_stack_tune_chunk_size": bool(
                get_path(config, "model.evoformer_stack.tune_chunk_size", False)
            ),
            "tm_head_enabled": bool(get_path(config, "model.heads.tm.enabled", False)),
        },
        "trt": {
            "mode": get_path(config, "trt.mode"),
            "engine_dir": get_path(config, "trt.engine_dir"),
            "num_profiles": get_path(config, "trt.num_profiles"),
            "optimization_level": get_path(config, "trt.optimization_level"),
            "max_sequence_len": get_path(config, "trt.max_sequence_len"),
        },
    }


def build_config(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    argument_errors = validate_args(args)
    if argument_errors:
        return {"ok": False, "stage": "argument-validation", "errors": argument_errors}, 2

    try:
        from openfold.config import enforce_config_constraints, model_config
    except Exception as exc:
        return {"ok": False, "stage": "import", "errors": [f"{type(exc).__name__}: {exc}"]}, 1

    try:
        config = model_config(
            args.preset,
            train=args.train,
            low_prec=args.low_prec,
            long_sequence_inference=args.long_sequence_inference,
            use_deepspeed_evoformer_attention=args.use_deepspeed_evoformer_attention,
            use_cuequivariance_attention=args.use_cuequivariance_attention,
            use_cuequivariance_multiplicative_update=args.use_cuequivariance_multiplicative_update,
            precision=args.precision,
            trt_mode=args.trt_mode,
            trt_engine_dir=args.trt_engine_dir,
            trt_num_profiles=args.trt_num_profiles,
            trt_optimization_level=args.trt_optimization_level,
            trt_max_sequence_len=args.trt_max_sequence_len,
        )
        if args.use_flash:
            set_path(config, "globals.use_flash", True)
            enforce_config_constraints(config)
    except Exception as exc:
        return {"ok": False, "stage": "model_config", "errors": [f"{type(exc).__name__}: {exc}"]}, 1

    warnings: list[str] = []
    if args.precision == "fp16":
        warnings.append("fp16 is supported by the config API but should be treated as numerically risky")
    if args.long_sequence_inference and get_path(config, "globals.use_deepspeed_evo_attention", False):
        warnings.append("long-sequence inference enabled DeepSpeed Evoformer attention; DeepSpeed4Science must be available")
    if args.trt_mode:
        warnings.append("TensorRT config fields validated, but no engine was compiled or executed")
    if args.preset.startswith("seq"):
        warnings.append("sequence-embedding presets require sequence-embedding features, not ordinary MSA assumptions")
    if "multimer" in args.preset:
        warnings.append("multimer presets require multimer-compatible features and weights")
    if args.low_prec:
        warnings.append("low_prec changes numerical constants and can affect strict checkpoint comparisons")

    return {
        "ok": True,
        "preset": args.preset,
        "train": args.train,
        "low_prec": args.low_prec,
        "long_sequence_inference": args.long_sequence_inference,
        "summary": summarize_config(config),
        "warnings": warnings,
    }, 0


def print_text(report: dict[str, Any]) -> None:
    if not report["ok"]:
        print(f"Config validation failed during {report['stage']}:", file=sys.stderr)
        for error in report["errors"]:
            print(f"  - {error}", file=sys.stderr)
        return

    print(f"Config preset {report['preset']} is valid for construction.")
    summary = report["summary"]
    print(f"  precision: {summary['precision']}")
    print("  globals: " + ", ".join(f"{key}={value!r}" for key, value in summary["globals"].items()))
    print("  data: " + ", ".join(f"{key}={value!r}" for key, value in summary["data"].items()))
    print("  model: " + ", ".join(f"{key}={value!r}" for key, value in summary["model"].items()))
    print("  trt: " + ", ".join(f"{key}={value!r}" for key, value in summary["trt"].items()))
    for warning in report["warnings"]:
        print(f"  warning: {warning}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", required=True, help="OpenFold model_config preset name")
    parser.add_argument("--train", action="store_true", help="request train=True config")
    parser.add_argument("--low-prec", action="store_true", help="request low_prec=True config")
    parser.add_argument("--long-sequence-inference", action="store_true", help="request long_sequence_inference=True")
    parser.add_argument(
        "--use-deepspeed-evoformer-attention",
        action="store_true",
        help="request DeepSpeed Evoformer attention",
    )
    parser.add_argument("--use-cuequivariance-attention", action="store_true", help="request cuEquivariance attention")
    parser.add_argument(
        "--use-cuequivariance-multiplicative-update",
        action="store_true",
        help="request cuEquivariance triangle multiplicative update",
    )
    parser.add_argument(
        "--use-flash",
        action="store_true",
        help="set globals.use_flash after model_config and re-run config constraints",
    )
    parser.add_argument("--precision", default="tf32", help="precision argument for model_config")
    parser.add_argument("--trt-mode", default=None, help="TensorRT mode, such as build or run")
    parser.add_argument("--trt-engine-dir", default=None, help="TensorRT engine directory; not created or modified")
    parser.add_argument("--trt-num-profiles", type=int, default=1, help="TensorRT profile count")
    parser.add_argument("--trt-optimization-level", type=int, default=3, help="TensorRT optimization level")
    parser.add_argument("--trt-max-sequence-len", type=int, default=640, help="TensorRT maximum sequence length")
    parser.add_argument("--package-root", default=None, help="optional OpenFold checkout/package root to prepend to sys.path")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    add_package_root(args.package_root)
    if args.json:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            report, exit_code = build_config(args)
        stream = sys.stdout if report["ok"] else sys.stderr
        print(json.dumps(report, indent=2, sort_keys=True), file=stream)
    else:
        report, exit_code = build_config(args)
        print_text(report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
