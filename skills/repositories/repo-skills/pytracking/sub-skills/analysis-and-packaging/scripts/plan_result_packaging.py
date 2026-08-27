#!/usr/bin/env python3
"""Dry-run planner for PyTracking GOT-10k and TrackingNet result packaging.

This script intentionally does not import PyTracking and does not create
archives. It prints the expected input tree, output archive plan, and any
missing files it can determine from the provided paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


DEFAULT_MAX_MISSING = 20


def parse_run_ids(text: str) -> List[int]:
    ids: List[int] = []
    for part in text.split(','):
        part = part.strip()
        if not part:
            continue
        try:
            run_id = int(part)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid run id {part!r}") from exc
        if run_id < 0:
            raise argparse.ArgumentTypeError("run ids must be non-negative")
        ids.append(run_id)
    if not ids:
        raise argparse.ArgumentTypeError("at least one run id is required")
    return ids


def read_sequence_list(path: Path) -> List[str]:
    names: List[str] = []
    for line in path.read_text(encoding='utf-8').splitlines():
        name = line.strip()
        if not name or name.startswith('#'):
            continue
        # Accept either plain names or filenames ending in .txt.
        if name.endswith('.txt'):
            name = name[:-4]
        names.append(name)
    if not names:
        raise SystemExit(f"sequence list is empty: {path}")
    return names


def got10k_sequence_names(count: int) -> List[str]:
    if count <= 0:
        raise SystemExit("--sequence-count must be positive")
    return [f"GOT-10k_Test_{i:06d}" for i in range(1, count + 1)]


def path_str(path: Optional[Path]) -> Optional[str]:
    return None if path is None else str(path)


def sample_missing(paths: Sequence[Path], max_items: int) -> List[str]:
    return [str(p) for p in paths[:max_items]]


def infer_trackingnet_sequences(input_dir: Path) -> List[str]:
    if not input_dir.is_dir():
        return []
    names = []
    for p in sorted(input_dir.glob('*.txt')):
        stem = p.stem
        if stem.endswith('_time') or stem.endswith('_object_presence_scores'):
            continue
        names.append(stem)
    return names


def print_header(title: str) -> None:
    print(f"\n== {title} ==")


def print_plan(plan: dict, max_missing: int) -> None:
    print_header("Packaging plan")
    print(f"Benchmark: {plan['benchmark']}")
    print(f"Tracker:   {plan['tracker_name']}")
    print(f"Parameter: {plan['parameter_name']}")
    if plan.get('run_id') is not None:
        print(f"Run id:    {plan['run_id']:03d}")
    elif plan.get('run_ids'):
        print("Run ids:   " + ', '.join(f"{r:03d}" for r in plan['run_ids']))

    print(f"Results root: {plan.get('results_root') or '(not provided; input files not checked)'}")
    print(f"Packed root:  {plan.get('packed_root')}")
    print(f"Output name:  {plan['output_name']}")
    print(f"Staging dir:  {plan['staging_dir']}")
    print(f"Archive:      {plan['archive_path']}")
    print("Archive creation: not performed by this planner")

    print_header("Expected layout")
    for line in plan['layout_notes']:
        print(f"- {line}")

    print_header("Validation")
    print(f"Expected box files:  {plan['expected_box_files']}")
    if plan.get('expected_time_files') is not None:
        print(f"Expected time files: {plan['expected_time_files']}")
    print(f"Found files:         {plan['found_files']}")
    print(f"Missing files:       {plan['missing_count']}")
    if plan.get('sequence_source'):
        print(f"Sequence source:     {plan['sequence_source']}")
    for warning in plan.get('warnings', []):
        print(f"WARNING: {warning}")
    if plan['missing_count']:
        print(f"\nFirst missing paths (max {max_missing}):")
        for item in plan['missing_sample']:
            print(f"  {item}")
    if plan.get('blocking'):
        print("\nStatus: BLOCKED - required files are missing or the input root is unavailable.")
    elif plan.get('validated'):
        print("\nStatus: OK for the checks this planner can perform.")
    else:
        print("\nStatus: NOT FULLY VALIDATED - provide a results root and, for TrackingNet, a trusted sequence list when possible.")


def build_got10k_plan(args: argparse.Namespace) -> dict:
    output_name = args.output_name or f"{args.tracker_name}_{args.parameter_name}_got10k"
    packed_root = Path(args.packed_root) if args.packed_root else Path('<env_settings().got_packed_results_path>')
    staging_dir = packed_root / output_name
    archive_path = packed_root / f"{output_name}.zip"
    sequences = got10k_sequence_names(args.sequence_count)

    expected_box_files = 0
    expected_time_files = 0
    found_files = 0
    missing: List[Path] = []
    results_root = Path(args.results_root) if args.results_root else None

    if results_root is not None:
        for run_id in args.run_ids:
            run_dir = results_root / args.tracker_name / f"{args.parameter_name}_{run_id:03d}"
            for seq in sequences:
                box_path = run_dir / f"{seq}.txt"
                time_path = run_dir / f"{seq}_time.txt"
                expected_box_files += 1
                expected_time_files += 1
                if box_path.is_file():
                    found_files += 1
                else:
                    missing.append(box_path)
                if time_path.is_file():
                    found_files += 1
                else:
                    missing.append(time_path)
    else:
        expected_box_files = len(sequences) * len(args.run_ids)
        expected_time_files = len(sequences) * len(args.run_ids)

    layout_notes = [
        f"Input: <results-root>/{args.tracker_name}/{args.parameter_name}_000/GOT-10k_Test_000001.txt",
        f"Input time: <results-root>/{args.tracker_name}/{args.parameter_name}_000/GOT-10k_Test_000001_time.txt",
        "Staging: <output-name>/GOT-10k_Test_000001/GOT-10k_Test_000001_1.txt through _3.txt",
        "Staging time: <output-name>/GOT-10k_Test_000001/GOT-10k_Test_000001_time.txt",
        "Final archive: <output-name>.zip",
    ]

    return {
        'benchmark': 'got10k',
        'tracker_name': args.tracker_name,
        'parameter_name': args.parameter_name,
        'run_ids': args.run_ids,
        'results_root': path_str(results_root),
        'packed_root': str(packed_root),
        'output_name': output_name,
        'staging_dir': str(staging_dir),
        'archive_path': str(archive_path),
        'expected_sequences': len(sequences),
        'expected_box_files': expected_box_files,
        'expected_time_files': expected_time_files,
        'found_files': found_files,
        'missing_count': len(missing),
        'missing_sample': sample_missing(missing, args.max_missing),
        'warnings': [],
        'blocking': results_root is not None and bool(missing),
        'validated': results_root is not None and not missing,
        'layout_notes': layout_notes,
    }


def build_trackingnet_plan(args: argparse.Namespace) -> dict:
    run_suffix = None if args.run_id is None else f"_{args.run_id:03d}"
    param_dir_name = args.parameter_name if run_suffix is None else f"{args.parameter_name}{run_suffix}"
    output_name = args.output_name
    if output_name is None:
        output_name = f"{args.tracker_name}_{args.parameter_name}" if args.run_id is None else f"{args.tracker_name}_{args.parameter_name}_{args.run_id:03d}"

    packed_root = Path(args.packed_root) if args.packed_root else Path('<env_settings().tn_packed_results_path>')
    staging_dir = packed_root / output_name
    archive_path = packed_root / f"{output_name}.zip"
    results_root = Path(args.results_root) if args.results_root else None

    warnings: List[str] = []
    sequence_source = None
    sequences: List[str] = []
    input_dir = results_root / args.tracker_name / param_dir_name if results_root is not None else None

    if args.trackingnet_sequence_list:
        seq_path = Path(args.trackingnet_sequence_list)
        sequences = read_sequence_list(seq_path)
        sequence_source = f"explicit list: {seq_path}"
    elif input_dir is not None and input_dir.is_dir():
        sequences = infer_trackingnet_sequences(input_dir)
        sequence_source = f"inferred from existing txt files under {input_dir}"
        warnings.append('No TrackingNet sequence list was provided; inferred files cannot prove official completeness.')
    else:
        sequence_source = 'none'
        warnings.append('No TrackingNet sequence list was provided and no input directory could be inspected.')

    expected_box_files = len(sequences)
    found_files = 0
    missing: List[Path] = []
    if input_dir is not None and sequences:
        for seq in sequences:
            box_path = input_dir / f"{seq}.txt"
            if box_path.is_file():
                found_files += 1
            else:
                missing.append(box_path)
    elif results_root is not None and not sequences:
        # The directory itself is the most actionable missing path.
        missing.append(input_dir if input_dir is not None else results_root)

    layout_notes = [
        f"Input: <results-root>/{args.tracker_name}/{param_dir_name}/<sequence-name>.txt",
        "Staging: <output-name>/<sequence-name>.txt",
        "Final archive: <output-name>.zip",
        "Native PyTracking packer writes result values with comma delimiters and two decimal places.",
    ]

    return {
        'benchmark': 'trackingnet',
        'tracker_name': args.tracker_name,
        'parameter_name': args.parameter_name,
        'run_id': args.run_id,
        'results_root': path_str(results_root),
        'packed_root': str(packed_root),
        'output_name': output_name,
        'staging_dir': str(staging_dir),
        'archive_path': str(archive_path),
        'sequence_source': sequence_source,
        'expected_sequences': len(sequences),
        'expected_box_files': expected_box_files,
        'expected_time_files': None,
        'found_files': found_files,
        'missing_count': len(missing),
        'missing_sample': sample_missing(missing, args.max_missing),
        'warnings': warnings,
        'blocking': results_root is not None and bool(missing),
        'validated': results_root is not None and bool(sequences) and not missing and args.trackingnet_sequence_list is not None,
        'layout_notes': layout_notes,
    }


def add_common(sub: argparse.ArgumentParser) -> None:
    sub.add_argument('--tracker-name', required=True, help='PyTracking tracker name, e.g. dimp')
    sub.add_argument('--parameter-name', required=True, help='Parameter file/name, e.g. dimp50')
    sub.add_argument('--results-root', default=None, help='Root containing tracker result directories. If omitted, only a layout plan is printed.')
    sub.add_argument('--packed-root', default=None, help='Root where the native packer would stage and place the final zip. Defaults to an env_settings placeholder.')
    sub.add_argument('--output-name', default=None, help='Archive/staging basename. Defaults follow PyTracking conventions where possible.')
    sub.add_argument('--max-missing', type=int, default=DEFAULT_MAX_MISSING, help='Maximum missing paths to print. Default: %(default)s')
    sub.add_argument('--json', action='store_true', help='Print machine-readable JSON instead of text.')
    sub.add_argument('--strict', action='store_true', help='Exit with code 2 when required files are missing.')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Dry-run PyTracking GOT-10k/TrackingNet packaging plan. No archives are written.',
    )
    subparsers = parser.add_subparsers(dest='benchmark', required=True)

    got = subparsers.add_parser('got10k', help='Plan GOT-10k test submission packaging.')
    add_common(got)
    got.add_argument('--run-ids', type=parse_run_ids, default=parse_run_ids('0,1,2'),
                     help='Comma-separated zero-based run ids. Default: 0,1,2')
    got.add_argument('--sequence-count', type=int, default=180,
                     help='Expected GOT-10k test sequence count. Default: %(default)s')

    tn = subparsers.add_parser('trackingnet', help='Plan TrackingNet submission packaging.')
    add_common(tn)
    tn.add_argument('--run-id', type=int, default=None,
                    help='Optional run id. If provided, input directory is parameter_###.')
    tn.add_argument('--trackingnet-sequence-list', default=None,
                    help='Text file with one official TrackingNet sequence name per line. Strongly recommended for completeness checks.')
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_missing < 0:
        parser.error('--max-missing must be non-negative')
    if getattr(args, 'run_id', None) is not None and args.run_id < 0:
        parser.error('--run-id must be non-negative')

    if args.benchmark == 'got10k':
        plan = build_got10k_plan(args)
    elif args.benchmark == 'trackingnet':
        plan = build_trackingnet_plan(args)
    else:  # pragma: no cover; argparse enforces choices via subcommands.
        parser.error(f"unsupported benchmark {args.benchmark!r}")

    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print_plan(plan, args.max_missing)

    if args.strict and plan.get('blocking'):
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
