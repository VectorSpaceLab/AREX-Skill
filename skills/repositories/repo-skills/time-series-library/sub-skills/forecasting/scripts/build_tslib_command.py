#!/usr/bin/env python3
"""Render safe starter commands for Time-Series-Library forecasting workflows.

The script prints commands only; it does not run TSLib, train models, download
data, or inspect GPUs. Run the printed command from a TSLib source checkout.
"""
from __future__ import annotations

import argparse
import shlex


def q(v: object) -> str:
    return shlex.quote(str(v))


def base_python(args: argparse.Namespace) -> list[str]:
    cmd = [args.python, "-u", "run.py"]
    return cmd


def add_common(cmd: list[str], args: argparse.Namespace, task: str, data: str) -> None:
    cmd += [
        "--task_name", task,
        "--is_training", str(args.is_training),
        "--root_path", args.root_path,
        "--model_id", args.model_id,
        "--model", args.model,
        "--data", data,
        "--features", args.features,
        "--des", args.des,
        "--itr", str(args.itr),
    ]
    if args.cpu_smoke:
        cmd.append("--no_use_gpu")
        cmd += ["--train_epochs", str(args.train_epochs), "--num_workers", "0"]
    elif args.gpu is not None:
        cmd += ["--gpu", str(args.gpu)]


def add_forecast_shape(cmd: list[str], args: argparse.Namespace) -> None:
    cmd += [
        "--seq_len", str(args.seq_len),
        "--label_len", str(args.label_len),
        "--pred_len", str(args.pred_len),
        "--enc_in", str(args.enc_in or args.channels),
        "--dec_in", str(args.dec_in or args.channels),
        "--c_out", str(args.c_out or args.channels),
    ]
    if args.data_path:
        cmd += ["--data_path", args.data_path]
    if args.target:
        cmd += ["--target", args.target]


def add_model_tiny(cmd: list[str], args: argparse.Namespace) -> None:
    if args.tiny_model:
        cmd += ["--e_layers", "1", "--d_layers", "1", "--d_model", "16", "--d_ff", "32", "--top_k", "3", "--batch_size", str(args.batch_size)]
    elif args.batch_size:
        cmd += ["--batch_size", str(args.batch_size)]


def render_long(args: argparse.Namespace) -> list[str]:
    cmd = base_python(args)
    add_common(cmd, args, "long_term_forecast", args.data)
    add_forecast_shape(cmd, args)
    add_model_tiny(cmd, args)
    if args.freq:
        cmd += ["--freq", args.freq]
    return cmd


def render_m4(args: argparse.Namespace) -> list[str]:
    cmd = base_python(args)
    add_common(cmd, args, "short_term_forecast", "m4")
    cmd += [
        "--seasonal_patterns", args.seasonal_patterns,
        "--enc_in", "1", "--dec_in", "1", "--c_out", "1",
        "--loss", args.loss,
    ]
    add_model_tiny(cmd, args)
    return cmd


def render_timexer(args: argparse.Namespace) -> list[str]:
    args.model = "TimeXer"
    cmd = render_long(args)
    cmd += ["--patch_len", str(args.patch_len)]
    return cmd


def render_zero(args: argparse.Namespace) -> list[str]:
    cmd = base_python(args)
    add_common(cmd, args, "zero_shot_forecast", args.data)
    cmd[cmd.index("--is_training") + 1] = "0"
    add_forecast_shape(cmd, args)
    # Do not append train_epochs for zero-shot; it is inference-only.
    if "--train_epochs" in cmd:
        i = cmd.index("--train_epochs")
        del cmd[i:i+2]
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a TSLib forecasting command template.")
    sub = parser.add_subparsers(dest="mode", required=True)

    def add_shared(p: argparse.ArgumentParser) -> None:
        p.add_argument("--python", default="python", help="Python executable to print in the command.")
        p.add_argument("--model", default="DLinear", help="TSLib model name.")
        p.add_argument("--data", default="custom", help="TSLib --data value.")
        p.add_argument("--root-path", default="./dataset/tiny-custom/", help="TSLib --root_path.")
        p.add_argument("--data-path", default="tiny.csv", help="TSLib --data_path for CSV workflows.")
        p.add_argument("--model-id", default="tiny_custom", help="TSLib --model_id.")
        p.add_argument("--features", default="M", choices=["M", "S", "MS"], help="Forecasting feature mode.")
        p.add_argument("--target", default="OT", help="Target column for S/MS/custom data.")
        p.add_argument("--seq-len", type=int, default=8)
        p.add_argument("--label-len", type=int, default=4)
        p.add_argument("--pred-len", type=int, default=4)
        p.add_argument("--channels", type=int, default=3, help="Fallback enc/dec/c_out count.")
        p.add_argument("--enc-in", type=int, default=None)
        p.add_argument("--dec-in", type=int, default=None)
        p.add_argument("--c-out", type=int, default=None)
        p.add_argument("--freq", default="h")
        p.add_argument("--batch-size", type=int, default=4)
        p.add_argument("--train-epochs", type=int, default=1)
        p.add_argument("--is-training", type=int, default=1)
        p.add_argument("--des", default="Smoke")
        p.add_argument("--itr", type=int, default=1)
        p.add_argument("--cpu-smoke", action="store_true", help="Add --no_use_gpu, one epoch, and num_workers=0.")
        p.add_argument("--gpu", type=int, default=None)
        p.add_argument("--tiny-model", action="store_true", default=True, help="Append small model dimensions where useful.")

    add_shared(sub.add_parser("long-term", help="Render a long_term_forecast command."))
    m4 = sub.add_parser("m4", help="Render a short_term_forecast M4 command.")
    add_shared(m4)
    m4.set_defaults(data="m4", model_id="m4_Monthly", root_path="./dataset/m4", data_path="")
    m4.add_argument("--seasonal-patterns", default="Monthly", choices=["Yearly", "Quarterly", "Monthly", "Weekly", "Daily", "Hourly"])
    m4.add_argument("--loss", default="SMAPE", choices=["MSE", "MAPE", "MASE", "SMAPE"])

    tx = sub.add_parser("timexer", help="Render a TimeXer long-term/exogenous command.")
    add_shared(tx)
    tx.set_defaults(model="TimeXer")
    tx.add_argument("--patch-len", type=int, default=16)

    z = sub.add_parser("zero-shot", help="Render a zero_shot_forecast command; verify optional deps separately.")
    add_shared(z)
    z.set_defaults(model="Chronos2", model_id="ETTh1_2048_96", root_path="./dataset/ETT-small/", data_path="ETTh1.csv", data="ETTh1", seq_len=2048, pred_len=96, label_len=48, channels=7, cpu_smoke=False)

    args = parser.parse_args()
    renderers = {"long-term": render_long, "m4": render_m4, "timexer": render_timexer, "zero-shot": render_zero}
    cmd = renderers[args.mode](args)
    print(" ".join(q(part) for part in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
