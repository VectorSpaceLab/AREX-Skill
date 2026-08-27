#!/usr/bin/env python3
"""Print a safe TimeMixer command for imputation, anomaly detection, or classification."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple


TASKS = ("imputation", "anomaly_detection", "classification")
GENERIC_DATA = {"ETTh1", "ETTh2", "ETTm1", "ETTm2", "custom", "m4", "PEMS", "Solar"}
ANOMALY_DATA = {"PSM", "MSL", "SMAP", "SMD", "SWAT"}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a shell command for TimeMixer's imputation, anomaly detection, or classification branches. "
            "The command is printed only; no training is launched."
        )
    )
    parser.add_argument("--task", required=True, choices=TASKS, help="TimeMixer task branch to generate.")
    parser.add_argument("--data", required=True, help="run.py data key such as UEA, SMD, or custom.")
    parser.add_argument("--root-path", required=True, help="Dataset root directory passed to run.py.")
    parser.add_argument(
        "--data-path",
        help="Dataset file name or relative path. Required for imputation; ignored by the other two branches.",
    )
    parser.add_argument("--seq-len", type=positive_int, required=True, help="Input/window length.")
    parser.add_argument("--enc-in", type=positive_int, required=True, help="Input channel count.")
    parser.add_argument("--c-out", type=positive_int, required=True, help="Output channel count.")
    parser.add_argument(
        "--down-sampling-layers",
        type=positive_int,
        default=1,
        help="Number of extra PDM scales; source-compatible default is 1 (must be >= 1).",
    )
    parser.add_argument(
        "--down-sampling-window",
        type=positive_int,
        default=2,
        help="Downsampling ratio at each scale; source-compatible default is 2 (must be >= 2).",
    )
    parser.add_argument(
        "--down-sampling-method",
        choices=["avg", "max", "conv"],
        default="avg",
        help="Source downsampling method forwarded to run.py.",
    )
    parser.add_argument(
        "--features", default="M", choices=["M", "S", "MS"], help="Feature mode forwarded to run.py."
    )
    parser.add_argument("--target", default="OT", help="Target column name forwarded to run.py.")
    parser.add_argument("--mask-rate", type=positive_float, default=0.125, help="Imputation mask fraction in (0, 1).")
    parser.add_argument(
        "--anomaly-ratio", type=positive_float, default=0.25, help="Anomaly threshold percentile value, interpreted as a percent."
    )
    parser.add_argument("--train-epochs", type=positive_int, default=100, help="Training epochs to pass through to run.py.")
    parser.add_argument("--model-id", help="Optional run identifier. Defaults to timemixer_<task>_<data>.")
    parser.add_argument("--no-use-gpu", action="store_true", help="Prefix the command with CUDA_VISIBLE_DEVICES=.")
    parser.add_argument("--dry-run-json", action="store_true", help="Print a JSON payload instead of a plain shell command.")
    return parser


def fail(message: str, json_mode: bool, code: int = 2, details: Optional[Dict[str, Any]] = None) -> int:
    if json_mode:
        payload: Dict[str, Any] = {"status": "error", "message": message}
        if details:
            payload.update(details)
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(message, file=sys.stderr)
    return code


def validate_compatibility(args: argparse.Namespace) -> Optional[str]:
    if args.task == "classification":
        if args.data != "UEA":
            return "classification only supports --data UEA"
    elif args.task == "anomaly_detection":
        if args.data not in ANOMALY_DATA:
            return f"anomaly_detection only supports --data one of: {', '.join(sorted(ANOMALY_DATA))}"
    elif args.task == "imputation":
        if args.data not in GENERIC_DATA:
            return f"imputation only supports --data one of: {', '.join(sorted(GENERIC_DATA))}"
        if args.data == "m4":
            return "imputation with --data m4 is unsupported: the source M4 loader requires a positive forecast horizon, so pred_len=0 would fail"
        if not args.data_path:
            return "imputation requires --data-path for this data key"

    if args.down_sampling_layers < 1:
        return "--down-sampling-layers must be >= 1 because TimeMixer PDM indexes a downsampled scale"
    if args.down_sampling_window < 2:
        return "--down-sampling-window must be >= 2; 0/1 does not provide source-compatible multiscale downsampling"
    divisor = args.down_sampling_window ** args.down_sampling_layers
    if args.seq_len < divisor:
        return (
            f"--seq-len must be at least down_sampling_window ** down_sampling_layers ({divisor}); "
            "the smallest PDM scale must have at least one timestep"
        )

    if args.task in {"imputation", "anomaly_detection"} and args.c_out != args.enc_in:
        return "imputation and anomaly detection should keep --c-out equal to --enc-in"
    if args.task == "imputation" and not (0 < args.mask_rate < 1):
        return "--mask-rate must be in (0, 1)"
    if args.task == "anomaly_detection" and not (0 < args.anomaly_ratio < 100):
        return "--anomaly-ratio must be in (0, 100) because the source treats it as a percent"
    return None


def build_command(args: argparse.Namespace) -> Tuple[List[str], List[str], str, int]:
    model_id = args.model_id or f"timemixer_{args.task}_{args.data}"
    label_len = max(1, args.seq_len // 2)
    pred_len = 0
    channel_independence = 0 if args.task == "classification" else 1

    notes: List[str] = []
    if args.task == "classification":
        notes.append("classification uses channel_independence=0 to avoid the multivariate UEA embedding mismatch")
    if args.task == "anomaly_detection":
        notes.append("anomaly_ratio is a percentage value in the source threshold calculation")
    if args.task == "imputation":
        notes.append("mask_rate is a fraction in the source random-mask loop")

    argv: List[str] = [
        "python", "run.py", "--task_name", args.task, "--is_training", "1",
        "--model_id", model_id, "--model", "TimeMixer", "--data", args.data,
        "--root_path", args.root_path, "--seq_len", str(args.seq_len),
        "--label_len", str(label_len), "--pred_len", str(pred_len),
        "--enc_in", str(args.enc_in), "--c_out", str(args.c_out),
        "--down_sampling_layers", str(args.down_sampling_layers),
        "--down_sampling_window", str(args.down_sampling_window),
        "--down_sampling_method", args.down_sampling_method,
        "--channel_independence", str(channel_independence), "--features", args.features,
        "--target", args.target, "--train_epochs", str(args.train_epochs),
    ]
    if args.data_path:
        argv.extend(["--data_path", args.data_path])
    if args.task == "imputation":
        argv.extend(["--mask_rate", str(args.mask_rate)])
    elif args.task == "anomaly_detection":
        argv.extend(["--anomaly_ratio", str(args.anomaly_ratio)])

    command = " ".join(shlex.quote(part) for part in argv)
    if args.no_use_gpu:
        command = f'CUDA_VISIBLE_DEVICES="" {command}'
    return argv, notes, command, channel_independence


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validation_error = validate_compatibility(args)
    if validation_error:
        return fail(validation_error, args.dry_run_json)

    argv_list, notes, command, channel_independence = build_command(args)
    payload: Dict[str, Any] = {
        "task": args.task,
        "data": args.data,
        "root_path": args.root_path,
        "data_path": args.data_path,
        "seq_len": args.seq_len,
        "enc_in": args.enc_in,
        "c_out": args.c_out,
        "down_sampling_layers": args.down_sampling_layers,
        "down_sampling_window": args.down_sampling_window,
        "down_sampling_method": args.down_sampling_method,
        "model_id": args.model_id or f"timemixer_{args.task}_{args.data}",
        "label_len": max(1, args.seq_len // 2),
        "pred_len": 0,
        "channel_independence": channel_independence,
        "command": command,
        "argv": argv_list,
        "notes": notes,
    }
    if args.dry_run_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
