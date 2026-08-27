#!/usr/bin/env python3
"""Build safe PaddleDetection train/eval/infer commands without executing them."""

from __future__ import annotations

import argparse
import shlex


def add_common(parser):
    parser.add_argument("--config", required=True, help="Config path in the target checkout.")
    parser.add_argument("--repo-root", default=".", help="Target PaddleDetection checkout root for shell comments only.")
    parser.add_argument("-o", "--opt", action="append", default=[], help="Override key=value; repeatable.")
    parser.add_argument("--gpu", action="store_true", help="Use use_gpu=true override; default false.")


def quote_cmd(parts):
    return " ".join(shlex.quote(str(p)) for p in parts if p is not None)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print PaddleDetection train/eval/infer command.")
    sub = parser.add_subparsers(dest="mode", required=True)

    train = sub.add_parser("train")
    add_common(train)
    train.add_argument("--eval", action="store_true")
    train.add_argument("--resume")
    train.add_argument("--amp", action="store_true")
    train.add_argument("--fleet", action="store_true")
    train.add_argument("--use-vdl", action="store_true")
    train.add_argument("--vdl-log-dir")
    train.add_argument("--distributed-gpus", help="Comma-separated GPU ids for paddle.distributed.launch.")

    ev = sub.add_parser("eval")
    add_common(ev)
    ev.add_argument("--weights")
    ev.add_argument("--output-eval")
    ev.add_argument("--json-eval", action="store_true")
    ev.add_argument("--classwise", action="store_true")

    infer = sub.add_parser("infer")
    add_common(infer)
    infer.add_argument("--weights")
    src = infer.add_mutually_exclusive_group(required=True)
    src.add_argument("--infer-img")
    src.add_argument("--infer-dir")
    infer.add_argument("--output-dir", default="output")
    infer.add_argument("--draw-threshold", type=float)
    infer.add_argument("--save-results", action="store_true")

    args = parser.parse_args()
    opts = list(args.opt)
    if args.gpu:
        opts.append("use_gpu=true")
    else:
        opts.append("use_gpu=false")
    if getattr(args, "weights", None):
        opts.append(f"weights={args.weights}")

    script = {"train": "tools/train.py", "eval": "tools/eval.py", "infer": "tools/infer.py"}[args.mode]
    base = ["python", script, "-c", args.config]
    if opts:
        base.extend(["-o", *opts])

    if args.mode == "train":
        if args.eval:
            base.append("--eval")
        if args.resume:
            base.extend(["--resume", args.resume])
        if args.amp:
            base.append("--amp")
        if args.fleet:
            base.append("--fleet")
        if args.use_vdl:
            base.extend(["--use_vdl", "true"])
        if args.vdl_log_dir:
            base.extend(["--vdl_log_dir", args.vdl_log_dir])
        if args.distributed_gpus:
            base = ["python", "-m", "paddle.distributed.launch", "--gpus", args.distributed_gpus, *base[1:]]
    elif args.mode == "eval":
        if args.output_eval:
            base.extend(["--output_eval", args.output_eval])
        if args.json_eval:
            base.append("--json_eval")
        if args.classwise:
            base.append("--classwise")
    elif args.mode == "infer":
        if args.infer_img:
            base.extend(["--infer_img", args.infer_img])
        if args.infer_dir:
            base.extend(["--infer_dir", args.infer_dir])
        base.extend(["--output_dir", args.output_dir])
        if args.draw_threshold is not None:
            base.extend(["--draw_threshold", args.draw_threshold])
        if args.save_results:
            base.extend(["--save_results", "true"])

    print("# Run from the target PaddleDetection checkout root:")
    print(quote_cmd(base))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
