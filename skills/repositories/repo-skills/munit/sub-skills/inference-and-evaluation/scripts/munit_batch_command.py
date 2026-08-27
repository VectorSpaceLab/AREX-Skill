#!/usr/bin/env python3
"""Build a safe MUNIT batch inference / metric command without executing it."""
import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import List


def resolve(path_text: str, repo_root: Path) -> Path:
    p = Path(path_text)
    return p if p.is_absolute() else repo_root / p


def quote_cmd(parts: List[str]) -> str:
    return ' '.join(shlex.quote(p) for p in parts)


def main() -> int:
    parser = argparse.ArgumentParser(description='Print and validate a MUNIT test_batch.py command; does not load models or run CUDA.')
    parser.add_argument('--repo-root', default='.', help="User's MUNIT checkout root containing test_batch.py.")
    parser.add_argument('--python', default='python', help='Python executable name/path to place in the printed command.')
    parser.add_argument('--config', required=True, help='Config YAML path passed to --config.')
    parser.add_argument('--input-folder', required=True, help='Input folder path passed to --input_folder.')
    parser.add_argument('--output-folder', required=True, help='Output folder/prefix passed to --output_folder.')
    parser.add_argument('--checkpoint', required=True, help='Generator checkpoint path passed to --checkpoint.')
    parser.add_argument('--a2b', type=int, choices=[0, 1], default=1, help='Direction: 1 for A to B, 0 for B to A.')
    parser.add_argument('--seed', type=int, default=1, help='Random seed.')
    parser.add_argument('--num-style', type=int, default=10, help='Number of random styles per input for MUNIT.')
    parser.add_argument('--synchronized', action='store_true', help='Use the same sampled styles for every input image.')
    parser.add_argument('--output-only', action='store_true', help='Add --output_only to avoid saving input previews.')
    parser.add_argument('--output-path', default='.', help='Value for test_batch.py --output_path.')
    parser.add_argument('--trainer', choices=['MUNIT', 'UNIT'], default='MUNIT', help='Trainer implementation.')
    parser.add_argument('--compute-is', action='store_true', help='Add --compute_IS.')
    parser.add_argument('--compute-cis', action='store_true', help='Add --compute_CIS.')
    parser.add_argument('--inception-a', default='.', help='Inception model path for domain A metrics.')
    parser.add_argument('--inception-b', default='.', help='Inception model path for domain B metrics.')
    parser.add_argument('--json', action='store_true', help='Emit JSON report.')
    parser.add_argument('--allow-missing-assets', action='store_true', help='Warn instead of failing when config/input/checkpoint/metric paths are missing.')
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    errors: List[str] = []
    warnings: List[str] = []
    if not (repo_root / 'test_batch.py').is_file():
        errors.append(f'test_batch.py not found under repo root: {repo_root}')
    for label, value, want_dir in [
        ('config', args.config, False),
        ('input_folder', args.input_folder, True),
        ('checkpoint', args.checkpoint, False),
    ]:
        p = resolve(value, repo_root)
        ok = p.is_dir() if want_dir else p.is_file()
        if not ok:
            msg = f'{label} path is missing or has wrong type: {p}'
            (warnings if args.allow_missing_assets else errors).append(msg)
    if args.num_style <= 0:
        errors.append('--num-style must be positive')
    if args.compute_is or args.compute_cis:
        target_inception = args.inception_b if args.a2b else args.inception_a
        if target_inception == '.':
            warnings.append('metric flags enabled but target-domain Inception path remains default "."')
        else:
            p = resolve(target_inception, repo_root)
            if not p.is_file():
                msg = f'target-domain Inception model path is missing: {p}'
                (warnings if args.allow_missing_assets else errors).append(msg)

    cmd = [
        args.python, 'test_batch.py',
        '--config', args.config,
        '--input_folder', args.input_folder,
        '--output_folder', args.output_folder,
        '--checkpoint', args.checkpoint,
        '--a2b', str(args.a2b),
        '--seed', str(args.seed),
        '--num_style', str(args.num_style),
        '--output_path', args.output_path,
        '--trainer', args.trainer,
        '--inception_a', args.inception_a,
        '--inception_b', args.inception_b,
    ]
    if args.synchronized:
        cmd.append('--synchronized')
    if args.output_only:
        cmd.append('--output_only')
    if args.compute_is:
        cmd.append('--compute_IS')
    if args.compute_cis:
        cmd.append('--compute_CIS')

    output_note = 'MUNIT writes output_folder_00, output_folder_01, ...; UNIT writes output_folder directly.'
    report = {
        'repo_root': str(repo_root),
        'run_from': str(repo_root),
        'command': cmd,
        'shell_command': quote_cmd(cmd),
        'direction': 'A-to-B' if args.a2b else 'B-to-A',
        'metrics_enabled': bool(args.compute_is or args.compute_cis),
        'output_note': output_note,
        'warnings': warnings,
        'errors': errors,
        'notes': [
            'This helper does not execute batch inference, load checkpoints, or compute metrics.',
            'The original MUNIT batch path calls CUDA unconditionally; use a compatible legacy CUDA runtime before running the command.',
            output_note,
        ],
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print('MUNIT batch inference command dry run')
        print(f'run from: {repo_root}')
        print('command:')
        print('  ' + report['shell_command'])
        print('note: ' + output_note)
        for item in warnings:
            print('WARN ' + item)
        for item in errors:
            print('FAIL ' + item)
        if not errors:
            print('OK command is statically ready; execute only after checkpoint, CUDA/runtime, and user approval gates pass')
    return 2 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
