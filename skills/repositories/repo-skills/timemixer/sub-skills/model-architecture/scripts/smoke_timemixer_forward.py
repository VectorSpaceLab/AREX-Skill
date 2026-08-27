#!/usr/bin/env python3
"""Deterministic CPU shape smoke test for the TimeMixer Model API."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple


FORECAST_TASKS = {"long_term_forecast", "short_term_forecast"}
ALL_TASKS = sorted(FORECAST_TASKS | {"imputation", "anomaly_detection", "classification"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Instantiate TimeMixer on CPU, run one deterministic forward pass, "
            "and print JSON input/output shapes."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Source checkout root containing the models/ and layers/ packages (default: current directory).",
    )
    parser.add_argument(
        "--task",
        default="long_term_forecast",
        choices=ALL_TASKS,
        help="TimeMixer task branch to exercise.",
    )
    parser.add_argument(
        "--decomp-method",
        default="moving_avg",
        choices=["moving_avg", "dft_decomp"],
        help="PDM decomposition method.",
    )
    parser.add_argument("--channels", type=int, default=2, help="Number of input/output value channels.")
    parser.add_argument("--seq-len", type=int, default=16, help="Input sequence length.")
    parser.add_argument("--pred-len", type=int, default=4, help="Forecast prediction length.")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size for the synthetic tensor.")
    parser.add_argument(
        "--channel-independence",
        default="auto",
        choices=["auto", "0", "1"],
        help=(
            "Channel independence flag. 'auto' chooses a passing smoke config: "
            "0 for multi-feature classification, otherwise 1."
        ),
    )
    parser.add_argument(
        "--down-sampling-method",
        default="avg",
        choices=["avg", "max", "conv"],
        help="Multiscale downsampling method.",
    )
    parser.add_argument("--down-sampling-layers", type=int, default=1, help="Number of downsampled scales.")
    parser.add_argument("--down-sampling-window", type=int, default=2, help="Downsampling stride/window.")
    parser.add_argument("--moving-avg", type=int, default=3, help="Odd moving-average kernel.")
    parser.add_argument("--top-k", type=int, default=3, help="Top-k DFT coefficients for dft_decomp.")
    parser.add_argument("--d-model", type=int, default=8, help="Embedding width.")
    parser.add_argument("--d-ff", type=int, default=16, help="Feed-forward width.")
    parser.add_argument("--e-layers", type=int, default=1, help="Number of PDM blocks.")
    parser.add_argument("--num-class", type=int, default=3, help="Classification class count.")
    parser.add_argument(
        "--use-future-temporal-feature",
        action="store_true",
        help="Exercise the forecast branch that consumes x_mark_dec future time features.",
    )
    return parser


def emit(payload: Dict[str, Any], exit_code: int = 0) -> int:
    print(json.dumps(payload, indent=2, sort_keys=True))
    return exit_code


def choose_channel_independence(task: str, channels: int, raw: str) -> Tuple[int, List[str]]:
    notes: List[str] = []
    if raw != "auto":
        return int(raw), notes
    if task == "classification" and channels > 1:
        notes.append(
            "auto selected channel_independence=0 because multi-feature classification does not use the forecast reshape"
        )
        return 0, notes
    return 1, notes


def validate_args(args: argparse.Namespace, channel_independence: int) -> Optional[str]:
    positive_fields = {
        "batch_size": args.batch_size,
        "channels": args.channels,
        "seq_len": args.seq_len,
        "down_sampling_window": args.down_sampling_window,
        "d_model": args.d_model,
        "d_ff": args.d_ff,
        "e_layers": args.e_layers,
        "num_class": args.num_class,
        "top_k": args.top_k,
    }
    for name, value in positive_fields.items():
        if value <= 0:
            return f"{name} must be positive"
    if args.pred_len < 0:
        return "pred_len must be non-negative"
    if args.task in FORECAST_TASKS and args.pred_len == 0:
        return "pred_len must be positive for forecast tasks"
    if args.down_sampling_layers < 1:
        return "down_sampling_layers must be at least 1 for the PDM scale mixers"
    if args.seq_len // (args.down_sampling_window ** args.down_sampling_layers) < 1:
        return "seq_len is too short for the requested downsampling depth/window"
    if args.moving_avg <= 0 or args.moving_avg % 2 == 0:
        return "moving_avg must be a positive odd integer to preserve temporal length"
    if args.decomp_method == "dft_decomp" and args.top_k > args.d_model // 2 + 1:
        return "top_k is too large for the DFT smoke configuration; lower top_k or increase d_model"
    if channel_independence not in (0, 1):
        return "channel_independence must be 0 or 1"
    return None


def make_time_features(torch: Any, batch_size: int, length: int) -> Any:
    """Create deterministic hourly timeF-style features shaped (B, T, 4)."""
    t = torch.arange(length, dtype=torch.float32).unsqueeze(0).repeat(batch_size, 1)
    month = ((t % 12.0) / 11.0) - 0.5
    day = ((t % 31.0) / 30.0) - 0.5
    weekday = ((t % 7.0) / 6.0) - 0.5
    hour = ((t % 24.0) / 23.0) - 0.5
    return torch.stack([month, day, weekday, hour], dim=-1)


def make_inputs(torch: Any, args: argparse.Namespace, channel_independence: int) -> Dict[str, Any]:
    total = args.batch_size * args.seq_len * args.channels
    base = torch.arange(total, dtype=torch.float32).reshape(args.batch_size, args.seq_len, args.channels)
    x_enc = torch.sin(base / 7.0) + torch.cos(base / 11.0)

    x_mark_enc: Any
    if args.task == "classification":
        x_mark_enc = torch.ones(args.batch_size, args.seq_len, dtype=torch.float32)
        if args.seq_len > 3:
            x_mark_enc[-1, -2:] = 0.0
    elif args.task in FORECAST_TASKS or args.task == "imputation":
        x_mark_enc = make_time_features(torch, args.batch_size, args.seq_len)
    else:
        x_mark_enc = None

    x_dec = torch.zeros(args.batch_size, max(args.pred_len, 1), args.channels, dtype=torch.float32)
    x_mark_dec = make_time_features(torch, args.batch_size, max(args.pred_len, 1))
    mask = None
    if args.task == "imputation":
        mask = torch.ones_like(x_enc)
        if args.seq_len > 4:
            mask[:, 1::4, :] = 0.0

    return {
        "x_enc": x_enc,
        "x_mark_enc": x_mark_enc,
        "x_dec": x_dec,
        "x_mark_dec": x_mark_dec,
        "mask": mask,
    }


def shape_of(value: Any) -> Optional[List[int]]:
    if value is None:
        return None
    return list(value.shape)


def expected_shape(args: argparse.Namespace) -> List[int]:
    if args.task in FORECAST_TASKS:
        return [args.batch_size, args.pred_len, args.channels]
    if args.task in {"imputation", "anomaly_detection"}:
        return [args.batch_size, args.seq_len, args.channels]
    return [args.batch_size, args.num_class]


def build_config(args: argparse.Namespace, channel_independence: int) -> SimpleNamespace:
    return SimpleNamespace(
        task_name=args.task,
        seq_len=args.seq_len,
        label_len=max(1, args.seq_len // 2),
        pred_len=args.pred_len if args.task in FORECAST_TASKS else 0,
        enc_in=args.channels,
        dec_in=args.channels,
        c_out=args.channels,
        num_class=args.num_class,
        d_model=args.d_model,
        d_ff=args.d_ff,
        e_layers=args.e_layers,
        d_layers=1,
        dropout=0.0,
        embed="timeF",
        freq="h",
        moving_avg=args.moving_avg,
        decomp_method=args.decomp_method,
        top_k=args.top_k,
        channel_independence=channel_independence,
        use_norm=1,
        down_sampling_layers=args.down_sampling_layers,
        down_sampling_window=args.down_sampling_window,
        down_sampling_method=args.down_sampling_method,
        use_future_temporal_feature=1 if args.use_future_temporal_feature else 0,
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    channel_independence, notes = choose_channel_independence(args.task, args.channels, args.channel_independence)
    validation_error = validate_args(args, channel_independence)
    if validation_error:
        return emit({"status": "config_error", "message": validation_error}, exit_code=2)

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not (repo_root / "models" / "TimeMixer.py").exists():
        return emit(
            {
                "status": "import_error",
                "message": "--repo-root must point to a TimeMixer source checkout containing models/TimeMixer.py",
            },
            exit_code=2,
        )
    sys.path.insert(0, str(repo_root))

    try:
        import torch
        from models.TimeMixer import Model
    except Exception as exc:  # pragma: no cover - diagnostic path
        return emit(
            {
                "status": "import_error",
                "message": f"Could not import TimeMixer model from --repo-root: {exc.__class__.__name__}: {exc}",
            },
            exit_code=2,
        )

    torch.manual_seed(0)
    torch.set_num_threads(1)
    config = build_config(args, channel_independence)
    tensors = make_inputs(torch, args, channel_independence)

    try:
        model = Model(config).cpu().eval()
        with torch.no_grad():
            output = model(
                tensors["x_enc"].cpu(),
                None if tensors["x_mark_enc"] is None else tensors["x_mark_enc"].cpu(),
                tensors["x_dec"].cpu(),
                tensors["x_mark_dec"].cpu(),
                None if tensors["mask"] is None else tensors["mask"].cpu(),
            )
    except Exception as exc:  # pragma: no cover - diagnostic path
        hint = None
        if args.task == "classification" and args.channels > 1 and channel_independence == 1:
            hint = "Multi-feature classification usually needs --channel-independence 0."
        return emit(
            {
                "status": "runtime_error",
                "task": args.task,
                "decomp_method": args.decomp_method,
                "channel_independence": channel_independence,
                "input_shapes": {
                    "x_enc": shape_of(tensors["x_enc"]),
                    "x_mark_enc": shape_of(tensors["x_mark_enc"]),
                    "x_dec": shape_of(tensors["x_dec"]),
                    "x_mark_dec": shape_of(tensors["x_mark_dec"]),
                    "mask": shape_of(tensors["mask"]),
                },
                "message": f"{exc.__class__.__name__}: {exc}",
                "hint": hint,
            },
            exit_code=1,
        )

    actual = shape_of(output)
    expected = expected_shape(args)
    return emit(
        {
            "status": "ok" if actual == expected else "shape_mismatch",
            "task": args.task,
            "decomp_method": args.decomp_method,
            "config": {
                "batch_size": args.batch_size,
                "channels": args.channels,
                "seq_len": args.seq_len,
                "pred_len": args.pred_len,
                "c_out": args.channels,
                "channel_independence": channel_independence,
                "down_sampling_method": args.down_sampling_method,
                "down_sampling_layers": args.down_sampling_layers,
                "down_sampling_window": args.down_sampling_window,
                "moving_avg": args.moving_avg,
                "top_k": args.top_k,
                "d_model": args.d_model,
                "use_future_temporal_feature": bool(args.use_future_temporal_feature),
            },
            "input_shapes": {
                "x_enc": shape_of(tensors["x_enc"]),
                "x_mark_enc": shape_of(tensors["x_mark_enc"]),
                "x_dec": shape_of(tensors["x_dec"]),
                "x_mark_dec": shape_of(tensors["x_mark_dec"]),
                "mask": shape_of(tensors["mask"]),
            },
            "output_shape": actual,
            "expected_output_shape": expected,
            "matches_expected": actual == expected,
            "notes": notes,
        },
        exit_code=0 if actual == expected else 1,
    )


if __name__ == "__main__":
    raise SystemExit(main())
