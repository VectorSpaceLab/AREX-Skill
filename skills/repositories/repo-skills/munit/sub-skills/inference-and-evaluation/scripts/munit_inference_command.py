#!/usr/bin/env python3
"""Build a safe MUNIT single-image inference command without executing it."""
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
    parser = argparse.ArgumentParser(description='Print and validate a MUNIT test.py command; does not load models or run CUDA.')
    parser.add_argument('--repo-root', default='.', help="User's MUNIT checkout root containing test.py.")
    parser.add_argument('--python', default='python', help='Python executable name/path to place in the printed command.')
    parser.add_argument('--config', required=True, help='Config YAML path passed to --config.')
    parser.add_argument('--input', required=True, help='Input image path passed to --input.')
    parser.add_argument('--output-folder', required=True, help='Output folder passed to --output_folder.')
    parser.add_argument('--checkpoint', required=True, help='Generator checkpoint path passed to --checkpoint.')
    parser.add_argument('--style', default='', help='Optional style image path; forces num_style=1 in original test.py.')
    parser.add_argument('--a2b', type=int, choices=[0, 1], default=1, help='Direction: 1 for A to B, 0 for B to A.')
    parser.add_argument('--seed', type=int, default=10, help='Random seed.')
    parser.add_argument('--num-style', type=int, default=10, help='Number of random styles when --style is absent.')
    parser.add_argument('--synchronized', action='store_true', help='Include parser flag even though single-image test.py does not use it meaningfully.')
    parser.add_argument('--output-only', action='store_true', help='Add --output_only to skip saving the normalized input image.')
    parser.add_argument('--output-path', default='.', help='Value for test.py --output_path.')
    parser.add_argument('--trainer', choices=['MUNIT', 'UNIT'], default='MUNIT', help='Trainer implementation.')
    parser.add_argument('--json', action='store_true', help='Emit JSON report.')
    parser.add_argument('--allow-missing-assets', action='store_true', help='Warn instead of failing when config/input/checkpoint/style paths are missing.')
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    errors: List[str] = []
    warnings: List[str] = []
    if not (repo_root / 'test.py').is_file():
        errors.append(f'test.py not found under repo root: {repo_root}')
    for label, value, want_file in [
        ('config', args.config, True),
        ('input', args.input, True),
        ('checkpoint', args.checkpoint, True),
    ]:
        p = resolve(value, repo_root)
        if want_file and not p.is_file():
            msg = f'{label} path does not exist as a file: {p}'
            (warnings if args.allow_missing_assets else errors).append(msg)
    if args.style:
        style_path = resolve(args.style, repo_root)
        if not style_path.is_file():
            msg = f'style path does not exist as a file: {style_path}'
            (warnings if args.allow_missing_assets else errors).append(msg)
        if args.num_style != 1:
            warnings.append('test.py forces num_style=1 when --style is non-empty')
    if args.num_style <= 0:
        errors.append('--num-style must be positive')

    cmd = [
        args.python, 'test.py',
        '--config', args.config,
        '--input', args.input,
        '--output_folder', args.output_folder,
        '--checkpoint', args.checkpoint,
        '--a2b', str(args.a2b),
        '--seed', str(args.seed),
        '--num_style', str(args.num_style),
        '--output_path', args.output_path,
        '--trainer', args.trainer,
    ]
    if args.style:
        cmd.extend(['--style', args.style])
    if args.synchronized:
        cmd.append('--synchronized')
    if args.output_only:
        cmd.append('--output_only')

    report = {
        'repo_root': str(repo_root),
        'run_from': str(repo_root),
        'command': cmd,
        'shell_command': quote_cmd(cmd),
        'direction': 'A-to-B' if args.a2b else 'B-to-A',
        'style_image': bool(args.style),
        'effective_num_style_note': '1 when style image is supplied, otherwise --num_style',
        'warnings': warnings,
        'errors': errors,
        'notes': [
            'This helper does not execute inference or load checkpoints.',
            'The original MUNIT inference path calls CUDA unconditionally; use a compatible legacy CUDA runtime before running the command.',
        ],
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print('MUNIT single-image inference command dry run')
        print(f'run from: {repo_root}')
        print('command:')
        print('  ' + report['shell_command'])
        for item in warnings:
            print('WARN ' + item)
        for item in errors:
            print('FAIL ' + item)
        if not errors:
            print('OK command is statically ready; execute only after checkpoint, CUDA/runtime, and user approval gates pass')
    return 2 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
