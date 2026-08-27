#!/usr/bin/env python3
"""Build a correctness-gated FLA op benchmark command without running it."""

from __future__ import annotations

import argparse
import shlex


def build_command(args: argparse.Namespace) -> list[str]:
    cmd = [args.python, '-m', 'benchmarks.ops.verify']
    if args.list:
        cmd.append('--list')
        return cmd

    cmd.extend(['--op', args.op])
    if args.base:
        cmd.extend(['--base', args.base])
    if args.gate_k:
        cmd.extend(['--gate-k', args.gate_k])
    if args.modes:
        cmd.append('--modes')
        cmd.extend(args.modes)
    if args.profile:
        cmd.append('--profile')
    return cmd


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            'Print a safe python -m benchmarks.ops.verify command. '
            'This helper never imports FLA, runs pytest, or launches a benchmark.'
        ),
    )
    parser.add_argument(
        '--op',
        help='Registered op name, for example chunk_gla. Required unless --list is used.',
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='Print the benchmark registry list command instead of an op command.',
    )
    parser.add_argument(
        '--base',
        help='Baseline git ref for the gated benchmark comparison, for example main or HEAD~1.',
    )
    parser.add_argument(
        '--gate-k',
        help='pytest -k selection for a fast signal gate. Do not promote from a subset gate.',
    )
    parser.add_argument(
        '--profile',
        action='store_true',
        help='Append --profile to request a torch.profiler trace after the gate and benchmark.',
    )
    parser.add_argument(
        '--modes',
        nargs='+',
        choices=('fwd', 'fwdbwd'),
        help='Benchmark modes to include. If omitted, verify.py uses its default modes.',
    )
    parser.add_argument(
        '--python',
        default='python',
        help='Python executable token to print. Default: python.',
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    if not args.list and not args.op:
        parser.error('--op is required unless --list is used')
    print(shlex.join(build_command(args)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
