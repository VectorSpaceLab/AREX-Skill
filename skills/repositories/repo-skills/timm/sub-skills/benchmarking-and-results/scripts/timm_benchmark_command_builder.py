#!/usr/bin/env python3
"""Build bounded timm benchmark commands.

This helper prints commands instead of running them. It is intentionally
conservative around wildcard/all-model benchmark requests because timm can
expand those requests into many expensive model runs.
"""

import argparse
import shlex
import sys
from pathlib import Path


BULK_MODEL_TOKENS = {"all", "all_in1k", "all_res"}
VALID_BENCHES = {
    "infer",
    "inference",
    "train",
    "both",
    "profile",
    "profile_deepspeed",
    "profile_fvcore",
}
BENCH_ALIASES = {"infer": "inference"}
VALID_PRECISIONS = {"float32", "float16", "bfloat16", "amp", "amp_bfloat16"}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def looks_broad_model_selector(model: str) -> bool:
    return model in BULK_MODEL_TOKENS or any(char in model for char in "*?[")


def build_benchmark_args(args: argparse.Namespace) -> list[str]:
    bench = BENCH_ALIASES.get(args.bench, args.bench)
    command = [
        "python",
        "benchmark.py",
        "--model",
        args.model,
        "--bench",
        bench,
        "--device",
        args.device,
        "--batch-size",
        str(args.batch_size),
        "--num-warm-iter",
        str(args.num_warm_iter),
        "--num-bench-iter",
        str(args.num_bench_iter),
    ]

    if args.precision:
        command.extend(["--precision", args.precision])
    if args.amp:
        command.append("--amp")
    if args.amp_dtype:
        command.extend(["--amp-dtype", args.amp_dtype])
    if args.channels_last:
        command.append("--channels-last")
    if args.torchcompile:
        command.extend(["--torchcompile", args.torchcompile])
    if args.torchcompile_mode:
        command.extend(["--torchcompile-mode", args.torchcompile_mode])
    if args.results_file:
        command.extend(["--results-file", args.results_file])
    if args.detail:
        command.append("--detail")
    if args.no_retry:
        command.append("--no-retry")
    return command


def build_bulk_runner_args(args: argparse.Namespace, benchmark_command: list[str]) -> list[str]:
    passthrough = benchmark_command[2:]
    model_index = passthrough.index("--model")
    del passthrough[model_index:model_index + 2]

    command = [
        "python",
        "bulk_runner.py",
        "--model-list",
        args.model,
        "--results-file",
        args.results_file or "benchmark-results.csv",
    ]
    if args.sort_key:
        command.extend(["--sort-key", args.sort_key])
    if args.pretrained:
        command.append("--pretrained")
    if args.delay:
        command.extend(["--delay", str(args.delay)])
    command.append("benchmark.py")
    command.extend(passthrough)
    return command


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print safe timm benchmark.py commands without running them.",
    )
    parser.add_argument("--model", required=True, help="Exact model, wildcard, or all/all_in1k/all_res selector.")
    parser.add_argument("--bench", default="inference", choices=sorted(VALID_BENCHES))
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=positive_int, default=32)
    parser.add_argument("--num-warm-iter", type=non_negative_int, default=2)
    parser.add_argument("--num-bench-iter", type=positive_int, default=5)
    parser.add_argument("--precision", choices=sorted(VALID_PRECISIONS), default="float32")
    parser.add_argument("--amp", action="store_true", help="Add benchmark.py --amp; overrides --precision at runtime.")
    parser.add_argument("--amp-dtype", choices=("float16", "bfloat16"), default=None)
    parser.add_argument("--channels-last", action="store_true")
    parser.add_argument("--torchcompile", nargs="?", const="inductor", default=None)
    parser.add_argument("--torchcompile-mode", default=None)
    parser.add_argument("--results-file", default="")
    parser.add_argument("--detail", action="store_true")
    parser.add_argument("--no-retry", action="store_true")
    parser.add_argument("--allow-bulk", action="store_true", help="Acknowledge broad model selectors or bulk runner output.")
    parser.add_argument("--bulk-runner", action="store_true", help="Print a guarded bulk_runner.py command instead of direct benchmark.py.")
    parser.add_argument("--sort-key", default="", help="bulk_runner.py sort key when --bulk-runner is used.")
    parser.add_argument("--pretrained", action="store_true", help="bulk_runner.py pretrained filter when --bulk-runner is used.")
    parser.add_argument("--delay", type=float, default=0.0, help="bulk_runner.py delay between model invocations.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    broad_selector = looks_broad_model_selector(args.model)

    if broad_selector and not args.allow_bulk:
        print(
            "Refusing to print an unbounded broad benchmark command. "
            "Use an exact --model, a reviewed short model-list workflow, or add --allow-bulk "
            "after setting low iteration counts and an explicit --results-file.",
            file=sys.stderr,
        )
        return 2

    if args.bulk_runner and not args.allow_bulk:
        print(
            "Refusing bulk_runner.py command without --allow-bulk because it may launch many subprocesses.",
            file=sys.stderr,
        )
        return 2

    if args.bulk_runner and not args.results_file:
        print(
            "Refusing bulk_runner.py command without --results-file; choose a run-specific CSV path.",
            file=sys.stderr,
        )
        return 2

    bench = BENCH_ALIASES.get(args.bench, args.bench)

    if bench.startswith("profile") and args.batch_size != 1:
        print(
            "Note: benchmark.py profile mode forces batch size to 1 internally.",
            file=sys.stderr,
        )

    if args.amp and args.precision not in {"amp", "amp_bfloat16", "float32"}:
        print(
            "Note: benchmark.py --amp overrides --precision at runtime.",
            file=sys.stderr,
        )

    command = build_benchmark_args(args)
    if args.bulk_runner:
        command = build_bulk_runner_args(args, command)

    print(shell_join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
