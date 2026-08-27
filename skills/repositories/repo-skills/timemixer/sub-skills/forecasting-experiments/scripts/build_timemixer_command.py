#!/usr/bin/env python3
"""Print TimeMixer forecasting run.py commands without executing training."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

M4_DERIVED = {
    "Yearly": {"pred_len": 6, "seq_len": 12, "label_len": 6, "frequency": 1, "d_ff": 32},
    "Quarterly": {"pred_len": 8, "seq_len": 16, "label_len": 8, "frequency": 4, "d_ff": 64},
    "Monthly": {"pred_len": 18, "seq_len": 36, "label_len": 18, "frequency": 12, "d_ff": 32},
    "Weekly": {"pred_len": 13, "seq_len": 26, "label_len": 13, "frequency": 1, "d_ff": 32},
    "Daily": {"pred_len": 14, "seq_len": 28, "label_len": 14, "frequency": 1, "d_ff": 16},
    "Hourly": {"pred_len": 48, "seq_len": 96, "label_len": 48, "frequency": 24, "d_ff": 32},
}

BASE_DEFAULTS: Dict[str, Any] = {
    "is_training": 1,
    "model": "TimeMixer",
    "features": "M",
    "target": "OT",
    "label_len": 0,
    "e_layers": 2,
    "d_layers": 1,
    "factor": 3,
    "des": "Exp",
    "itr": 1,
    "down_sampling_method": "avg",
    "down_sampling_layers": 1,
    "down_sampling_window": 2,
    "comment": None,
    "freq": None,
    "checkpoints": None,
    "num_workers": None,
    "lradj": None,
    "pct_start": None,
    "use_future_temporal_feature": None,
}


def long_preset(
    *,
    data: str,
    data_path: str,
    model_id_prefix: str,
    root_path: str,
    channels: int,
    e_layers: int,
    d_model: int,
    d_ff: int,
    batch_size: int,
    learning_rate: float,
    down_sampling_layers: int,
    down_sampling_window: int,
    pred_len: int = 96,
    train_epochs: Optional[int] = None,
    patience: Optional[int] = None,
    use_norm: Optional[int] = None,
    channel_independence: Optional[int] = None,
) -> Dict[str, Any]:
    cfg = deepcopy(BASE_DEFAULTS)
    cfg.update(
        {
            "task_name": "long_term_forecast",
            "data": data,
            "root_path": root_path,
            "data_path": data_path,
            "model_id_template": f"{model_id_prefix}_{{seq_len}}_{{pred_len}}",
            "seq_len": 96,
            "pred_len": pred_len,
            "enc_in": channels,
            "dec_in": channels,
            "c_out": channels,
            "e_layers": e_layers,
            "d_model": d_model,
            "d_ff": d_ff,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "down_sampling_layers": down_sampling_layers,
            "down_sampling_window": down_sampling_window,
        }
    )
    if train_epochs is not None:
        cfg["train_epochs"] = train_epochs
    if patience is not None:
        cfg["patience"] = patience
    if use_norm is not None:
        cfg["use_norm"] = use_norm
    if channel_independence is not None:
        cfg["channel_independence"] = channel_independence
    return cfg


def m4_preset(season: str) -> Dict[str, Any]:
    derived = M4_DERIVED[season]
    cfg = deepcopy(BASE_DEFAULTS)
    cfg.update(
        {
            "task_name": "short_term_forecast",
            "data": "m4",
            "root_path": "./dataset/m4",
            "data_path": None,
            "model_id_template": "m4_{seasonal_patterns}",
            "seasonal_patterns": season,
            "seq_len": derived["seq_len"],
            "label_len": derived["label_len"],
            "pred_len": derived["pred_len"],
            "enc_in": 1,
            "dec_in": 1,
            "c_out": 1,
            "e_layers": 4,
            "d_layers": 1,
            "factor": 3,
            "d_model": 32,
            "d_ff": derived["d_ff"],
            "batch_size": 128,
            "learning_rate": 0.01,
            "train_epochs": 50,
            "patience": 20,
            "down_sampling_layers": 1,
            "down_sampling_window": 2,
            "loss": "SMAPE",
        }
    )
    return cfg


PRESETS: Dict[str, Dict[str, Any]] = {
    "ettm1": long_preset(
        data="ETTm1",
        data_path="ETTm1.csv",
        model_id_prefix="ETTm1",
        root_path="./dataset/ETT-small/",
        channels=7,
        e_layers=2,
        d_model=16,
        d_ff=32,
        batch_size=16,
        learning_rate=0.01,
        down_sampling_layers=3,
        down_sampling_window=2,
    ),
    "etth1": long_preset(
        data="ETTh1",
        data_path="ETTh1.csv",
        model_id_prefix="ETTh1",
        root_path="./dataset/ETT-small/",
        channels=7,
        e_layers=2,
        d_model=16,
        d_ff=32,
        batch_size=128,
        learning_rate=0.01,
        down_sampling_layers=3,
        down_sampling_window=2,
        train_epochs=10,
        patience=10,
    ),
    "etth2": long_preset(
        data="ETTh2",
        data_path="ETTh2.csv",
        model_id_prefix="ETTh2",
        root_path="./dataset/ETT-small/",
        channels=7,
        e_layers=2,
        d_model=16,
        d_ff=32,
        batch_size=16,
        learning_rate=0.01,
        down_sampling_layers=3,
        down_sampling_window=2,
    ),
    "ettm2": long_preset(
        data="ETTm2",
        data_path="ETTm2.csv",
        model_id_prefix="ETTm2",
        root_path="./dataset/ETT-small/",
        channels=7,
        e_layers=2,
        d_model=32,
        d_ff=32,
        batch_size=128,
        learning_rate=0.01,
        down_sampling_layers=3,
        down_sampling_window=2,
    ),
    "ecl": long_preset(
        data="custom",
        data_path="electricity.csv",
        model_id_prefix="ECL",
        root_path="./dataset/electricity/",
        channels=321,
        e_layers=3,
        d_model=16,
        d_ff=32,
        batch_size=32,
        learning_rate=0.01,
        down_sampling_layers=3,
        down_sampling_window=2,
        train_epochs=20,
        patience=10,
    ),
    "traffic": long_preset(
        data="custom",
        data_path="traffic.csv",
        model_id_prefix="Traffic",
        root_path="./dataset/traffic/",
        channels=862,
        e_layers=3,
        d_model=32,
        d_ff=64,
        batch_size=8,
        learning_rate=0.01,
        down_sampling_layers=3,
        down_sampling_window=2,
    ),
    "weather": long_preset(
        data="custom",
        data_path="weather.csv",
        model_id_prefix="weather",
        root_path="./dataset/weather/",
        channels=21,
        e_layers=3,
        d_model=16,
        d_ff=32,
        batch_size=128,
        learning_rate=0.01,
        down_sampling_layers=3,
        down_sampling_window=2,
        train_epochs=20,
        patience=10,
    ),
    "solar": long_preset(
        data="Solar",
        data_path="solar_AL.txt",
        model_id_prefix="solar",
        root_path="./dataset/solar/",
        channels=137,
        e_layers=3,
        d_model=512,
        d_ff=2048,
        batch_size=32,
        learning_rate=0.001,
        down_sampling_layers=2,
        down_sampling_window=2,
        train_epochs=10,
        patience=3,
        use_norm=0,
        channel_independence=0,
    ),
    "pems03": long_preset(
        data="PEMS",
        data_path="PEMS03.npz",
        model_id_prefix="PEMS03",
        root_path="./dataset/PEMS/",
        channels=358,
        e_layers=5,
        d_model=128,
        d_ff=256,
        batch_size=32,
        learning_rate=0.003,
        down_sampling_layers=1,
        down_sampling_window=2,
        pred_len=12,
        train_epochs=10,
        patience=10,
        use_norm=0,
        channel_independence=0,
    ),
    "pems04": long_preset(
        data="PEMS",
        data_path="PEMS04.npz",
        model_id_prefix="PEMS04",
        root_path="./dataset/PEMS/",
        channels=307,
        e_layers=5,
        d_model=128,
        d_ff=256,
        batch_size=32,
        learning_rate=0.003,
        down_sampling_layers=1,
        down_sampling_window=2,
        pred_len=12,
        train_epochs=10,
        patience=10,
        use_norm=0,
        channel_independence=0,
    ),
    "pems07": long_preset(
        data="PEMS",
        data_path="PEMS07.npz",
        model_id_prefix="PEMS07",
        root_path="./dataset/PEMS/",
        channels=883,
        e_layers=5,
        d_model=128,
        d_ff=256,
        batch_size=32,
        learning_rate=0.003,
        down_sampling_layers=1,
        down_sampling_window=2,
        pred_len=12,
        train_epochs=10,
        patience=10,
        use_norm=0,
        channel_independence=0,
    ),
    "pems08": long_preset(
        data="PEMS",
        data_path="PEMS08.npz",
        model_id_prefix="PEMS08",
        root_path="./dataset/PEMS/",
        channels=170,
        e_layers=5,
        d_model=128,
        d_ff=256,
        batch_size=32,
        learning_rate=0.003,
        down_sampling_layers=1,
        down_sampling_window=2,
        pred_len=12,
        train_epochs=10,
        patience=10,
        use_norm=0,
        channel_independence=0,
    ),
    "m4-yearly": m4_preset("Yearly"),
    "m4-quarterly": m4_preset("Quarterly"),
    "m4-monthly": m4_preset("Monthly"),
    "m4-weekly": m4_preset("Weekly"),
    "m4-daily": m4_preset("Daily"),
    "m4-hourly": m4_preset("Hourly"),
}

OVERRIDES = [
    "task_name",
    "is_training",
    "data",
    "root_path",
    "data_path",
    "model_id",
    "features",
    "target",
    "seq_len",
    "label_len",
    "pred_len",
    "seasonal_patterns",
    "enc_in",
    "dec_in",
    "c_out",
    "e_layers",
    "d_layers",
    "factor",
    "d_model",
    "d_ff",
    "train_epochs",
    "patience",
    "batch_size",
    "learning_rate",
    "down_sampling_layers",
    "down_sampling_method",
    "down_sampling_window",
    "use_norm",
    "channel_independence",
    "loss",
    "freq",
    "checkpoints",
    "num_workers",
    "itr",
    "des",
    "comment",
    "lradj",
    "pct_start",
    "use_future_temporal_feature",
    "gpu",
]

COMMAND_ORDER = [
    "task_name",
    "is_training",
    "root_path",
    "data_path",
    "seasonal_patterns",
    "model_id",
    "model",
    "data",
    "features",
    "target",
    "freq",
    "seq_len",
    "label_len",
    "pred_len",
    "e_layers",
    "d_layers",
    "factor",
    "enc_in",
    "dec_in",
    "c_out",
    "des",
    "itr",
    "d_model",
    "d_ff",
    "batch_size",
    "learning_rate",
    "train_epochs",
    "patience",
    "down_sampling_layers",
    "down_sampling_method",
    "down_sampling_window",
    "use_norm",
    "channel_independence",
    "loss",
    "checkpoints",
    "num_workers",
    "comment",
    "lradj",
    "pct_start",
    "use_future_temporal_feature",
    "gpu",
]

POSITIVE_INT_FIELDS = [
    "seq_len",
    "label_len",
    "pred_len",
    "enc_in",
    "dec_in",
    "c_out",
    "e_layers",
    "d_layers",
    "factor",
    "d_model",
    "d_ff",
    "train_epochs",
    "patience",
    "batch_size",
    "down_sampling_layers",
    "down_sampling_window",
    "num_workers",
    "itr",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print TimeMixer forecasting run.py commands; no training is executed."
    )
    parser.add_argument("--preset", choices=sorted(PRESETS), help="Source-derived forecast preset to adapt.")
    parser.add_argument("--task-name", dest="task_name", choices=["long_term_forecast", "short_term_forecast"])
    parser.add_argument("--is-training", dest="is_training", type=int, choices=[0, 1])
    parser.add_argument("--data")
    parser.add_argument("--root-path", dest="root_path")
    parser.add_argument("--data-path", dest="data_path")
    parser.add_argument("--model-id", dest="model_id")
    parser.add_argument("--features", choices=["M", "S", "MS"])
    parser.add_argument("--target")
    parser.add_argument("--seq-len", dest="seq_len", type=int)
    parser.add_argument("--label-len", dest="label_len", type=int)
    parser.add_argument("--pred-len", dest="pred_len", type=int)
    parser.add_argument("--seasonal-patterns", dest="seasonal_patterns", choices=sorted(M4_DERIVED))
    parser.add_argument("--enc-in", dest="enc_in", type=int)
    parser.add_argument("--dec-in", dest="dec_in", type=int)
    parser.add_argument("--c-out", dest="c_out", type=int)
    parser.add_argument("--e-layers", dest="e_layers", type=int)
    parser.add_argument("--d-layers", dest="d_layers", type=int)
    parser.add_argument("--factor", type=int)
    parser.add_argument("--d-model", dest="d_model", type=int)
    parser.add_argument("--d-ff", dest="d_ff", type=int)
    parser.add_argument("--train-epochs", dest="train_epochs", type=int)
    parser.add_argument("--patience", type=int)
    parser.add_argument("--batch-size", dest="batch_size", type=int)
    parser.add_argument("--learning-rate", dest="learning_rate", type=float)
    parser.add_argument("--down-sampling-layers", dest="down_sampling_layers", type=int)
    parser.add_argument("--down-sampling-method", dest="down_sampling_method", choices=["avg", "max", "conv"])
    parser.add_argument("--down-sampling-window", dest="down_sampling_window", type=int)
    parser.add_argument("--use-norm", dest="use_norm", type=int, choices=[0, 1])
    parser.add_argument("--channel-independence", dest="channel_independence", type=int, choices=[0, 1])
    parser.add_argument("--loss", choices=["MSE", "MAPE", "MASE", "SMAPE"])
    parser.add_argument("--freq")
    parser.add_argument("--checkpoints")
    parser.add_argument("--num-workers", dest="num_workers", type=int)
    parser.add_argument("--itr", type=int)
    parser.add_argument("--des")
    parser.add_argument("--comment")
    parser.add_argument("--lradj")
    parser.add_argument("--pct-start", dest="pct_start", type=float)
    parser.add_argument("--use-future-temporal-feature", dest="use_future_temporal_feature", type=int, choices=[0, 1])
    gpu_group = parser.add_mutually_exclusive_group()
    gpu_group.add_argument("--use-gpu", dest="use_gpu", action="store_true", help="Prefix with CUDA_VISIBLE_DEVICES=<gpu> and include --gpu.")
    gpu_group.add_argument("--no-use-gpu", dest="use_gpu", action="store_false", help="Prefix with CUDA_VISIBLE_DEVICES='' for reliable CPU fallback.")
    parser.set_defaults(use_gpu=None)
    parser.add_argument("--gpu", type=int, default=None, help="Single GPU id to expose when --use-gpu is set; defaults to 0.")
    parser.add_argument("--python", default="python", help="Python executable token for the printed command.")
    parser.add_argument("--run-py", default="run.py", help="Path to the TimeMixer entry-point script in the printed command.")
    parser.add_argument("--dry-run-json", action="store_true", help="Print structured JSON instead of a shell command.")
    return parser


def apply_overrides(cfg: Dict[str, Any], args: argparse.Namespace) -> None:
    for key in OVERRIDES:
        value = getattr(args, key, None)
        if value is not None:
            cfg[key] = value


def fill_model_id(cfg: Dict[str, Any]) -> None:
    if cfg.get("model_id"):
        return
    template = cfg.get("model_id_template")
    if template:
        cfg["model_id"] = template.format(**cfg)


def die(message: str) -> None:
    raise ValueError(message)


def validate(cfg: Dict[str, Any], args: argparse.Namespace) -> List[str]:
    warnings: List[str] = []
    required = ["task_name", "is_training", "model_id", "model", "data", "root_path"]
    if cfg.get("data") != "m4":
        required.append("data_path")
    if cfg.get("task_name") != "short_term_forecast":
        required.extend(["seq_len", "label_len", "pred_len"])
    required.extend(["enc_in", "dec_in", "c_out", "features"])
    missing = [key for key in required if cfg.get(key) in (None, "")]
    if missing:
        die("missing required values: " + ", ".join(missing))

    if cfg["task_name"] not in {"long_term_forecast", "short_term_forecast"}:
        die("forecast command task_name must be long_term_forecast or short_term_forecast")
    if cfg["task_name"] == "short_term_forecast" and cfg["data"] != "m4":
        die("this TimeMixer short_term_forecast workflow is M4-specific; use long_term_forecast for other data")
    if cfg["data"] == "m4" and cfg["task_name"] != "short_term_forecast":
        die("data=m4 must use task_name=short_term_forecast")

    for key in POSITIVE_INT_FIELDS:
        if cfg.get(key) is None:
            continue
        if key == "label_len":
            if cfg[key] < 0:
                die(f"{key} must be >= 0")
        elif key == "down_sampling_layers":
            if cfg[key] < 1:
                die("down_sampling_layers must be >= 1 because TimeMixer PDM requires a downsampled scale")
        elif key == "down_sampling_window":
            if cfg[key] < 2:
                die("down_sampling_window must be >= 2; 0/1 does not provide source-compatible downsampling")
        elif cfg[key] <= 0:
            die(f"{key} must be > 0")

    if cfg.get("learning_rate") is not None and cfg["learning_rate"] <= 0:
        die("learning_rate must be > 0")
    if cfg.get("pct_start") is not None and not (0 < cfg["pct_start"] <= 1):
        die("pct_start must be in (0, 1]")

    features = cfg.get("features")
    if features == "M" and not (cfg["enc_in"] == cfg["dec_in"] == cfg["c_out"]):
        die("features=M normally requires enc_in, dec_in, and c_out to all match the data channel count")
    if features == "S" and not (cfg["enc_in"] == cfg["dec_in"] == cfg["c_out"] == 1):
        die("features=S requires enc_in=dec_in=c_out=1")
    if features == "MS":
        if cfg["enc_in"] != cfg["dec_in"]:
            die("features=MS requires enc_in and dec_in to match input channels")
        if cfg["c_out"] not in {1, cfg["enc_in"]}:
            warnings.append(
                "features=MS is safest with c_out=1 or c_out matching enc_in; verify the forecast loss path before training"
            )
        warnings.append(
            "features=MS has task-path-specific slicing behavior; verify dimensions with a tiny approved run before full training"
        )

    if cfg["data"] == "PEMS":
        if not str(cfg.get("data_path", "")).endswith(".npz"):
            die("data=PEMS expects a .npz data_path")
        if cfg.get("label_len") != 0:
            warnings.append("PEMS presets use label_len=0")
        warnings.append("PEMS uses zero placeholder marks and the experiment passes None time marks")
    if cfg["data"] == "Solar":
        warnings.append("Solar uses numeric rows without calendar marks; freq changes do not add time features")
    if cfg["data"] == "m4":
        season = cfg.get("seasonal_patterns")
        if season not in M4_DERIVED:
            die("data=m4 requires a valid seasonal_patterns value")
        derived = M4_DERIVED[season]
        for field in ["pred_len", "seq_len", "label_len"]:
            provided = getattr(args, field, None)
            if provided is not None and provided != derived[field]:
                die(
                    f"M4 derives {field}={derived[field]} from seasonal_patterns={season}; "
                    f"do not override it with {provided}"
                )
            cfg[field] = derived[field]
        if not (cfg["enc_in"] == cfg["dec_in"] == cfg["c_out"] == 1):
            die("M4 forecasting requires enc_in=dec_in=c_out=1")
        warnings.append("M4 averaged metrics require all six seasonal forecast CSV files")

    if cfg.get("down_sampling_window") and cfg.get("down_sampling_layers"):
        smallest = cfg["seq_len"] // (cfg["down_sampling_window"] ** cfg["down_sampling_layers"])
        if smallest <= 0:
            die("down_sampling_window ** down_sampling_layers must not exceed seq_len")
        if cfg["seq_len"] % (cfg["down_sampling_window"] ** cfg["down_sampling_layers"]) != 0:
            warnings.append(
                "seq_len is not evenly divisible by down_sampling_window ** down_sampling_layers; check multiscale lengths"
            )

    if args.use_gpu is False:
        warnings.append("CPU fallback is implemented by hiding CUDA devices because run.py parses --use_gpu with type=bool")
    elif args.use_gpu is True:
        warnings.append("GPU command assumes the selected CUDA device is available and has enough memory")

    if cfg.get("train_epochs") and cfg["train_epochs"] <= 3:
        warnings.append("very small train_epochs is suitable for debugging only, not benchmark reproduction")
    if cfg.get("batch_size") and cfg["batch_size"] <= 4:
        warnings.append("small batch_size changes benchmark comparability")

    return warnings


def command_argv(cfg: Dict[str, Any], python_token: str, run_py: str) -> List[str]:
    argv = [python_token, "-u", run_py]
    for key in COMMAND_ORDER:
        if key == "data_path" and cfg.get("data") == "m4" and cfg.get(key) is None:
            continue
        value = cfg.get(key)
        if value is None:
            continue
        argv.extend(["--" + key, str(value)])
    return argv


def shell_command(argv: List[str], use_gpu: Optional[bool], gpu: Optional[int]) -> Tuple[str, Dict[str, str]]:
    env: Dict[str, str] = {}
    if use_gpu is False:
        env["CUDA_VISIBLE_DEVICES"] = ""
    elif use_gpu is True:
        env["CUDA_VISIBLE_DEVICES"] = str(0 if gpu is None else gpu)
    parts: List[str] = []
    for key, value in env.items():
        if value == "":
            parts.append(f"{key}=''")
        else:
            parts.append(f"{key}={shlex.quote(value)}")
    parts.extend(shlex.quote(part) for part in argv)
    return " ".join(parts), env


def make_config(args: argparse.Namespace) -> Dict[str, Any]:
    if args.preset:
        cfg = deepcopy(PRESETS[args.preset])
    else:
        cfg = deepcopy(BASE_DEFAULTS)
        cfg.update(
            {
                "model": "TimeMixer",
                "label_len": 0,
                "e_layers": 2,
                "d_layers": 1,
                "factor": 3,
                "d_model": 16,
                "d_ff": 32,
                "down_sampling_layers": 1,
                "down_sampling_window": 2,
                "down_sampling_method": "avg",
                "des": "Exp",
                "itr": 1,
            }
        )
    apply_overrides(cfg, args)
    if cfg.get("data") == "m4" and cfg.get("seasonal_patterns") in M4_DERIVED:
        derived = M4_DERIVED[cfg["seasonal_patterns"]]
        cfg["seq_len"] = derived["seq_len"]
        cfg["label_len"] = derived["label_len"]
        cfg["pred_len"] = derived["pred_len"]
        if args.d_ff is None:
            cfg["d_ff"] = derived["d_ff"]
    fill_model_id(cfg)
    return cfg


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        cfg = make_config(args)
        warnings = validate(cfg, args)
        cmd_argv = command_argv(cfg, args.python, args.run_py)
        command, env = shell_command(cmd_argv, args.use_gpu, cfg.get("gpu"))
    except ValueError as exc:
        parser.error(str(exc))

    if args.dry_run_json:
        payload = {
            "preset": args.preset,
            "command": command,
            "env": env,
            "argv": cmd_argv,
            "config": {key: value for key, value in cfg.items() if key != "model_id_template" and value is not None},
            "warnings": warnings,
            "execution": "not-run; full training is external-data/expensive",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(command)
        if warnings:
            print("\n# Warnings:", file=sys.stderr)
            for item in warnings:
                print(f"# - {item}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
