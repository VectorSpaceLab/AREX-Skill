#!/usr/bin/env python3
"""Build a safe MMAudio demo command without executing inference.

This helper validates the command shape and prints a shell-quoted `python demo.py ...`
command to stdout. It does not download weights, launch a server, or create files.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Sequence

SUPPORTED_VARIANTS = (
    'small_16k',
    'small_44k',
    'medium_44k',
    'large_44k',
    'large_44k_v2',
)

DEFAULT_VARIANT = 'large_44k_v2'
DEFAULT_DURATION = 8.0
DEFAULT_CFG_STRENGTH = 4.5
DEFAULT_NUM_STEPS = 25
DEFAULT_SEED = 42
DEFAULT_OUTPUT_DIR = './output'
COMMON_MEDIA_SUFFIXES = {'.flac', '.mp4', '.wav', '.mp3', '.ogg', '.m4a', '.aac', '.webm'}


def _validate_non_empty(value: str, field: str) -> str:
    if value is None or not value.strip():
        raise ValueError(f'{field} must be non-empty')
    if '\x00' in value or '\n' in value or '\r' in value:
        raise ValueError(f'{field} must not contain control characters')
    return value


def _validate_directory_like_path(value: str, field: str) -> Path:
    path = Path(value).expanduser()
    if str(path).strip() == '':
        raise ValueError(f'{field} must be a non-empty path')
    if path.exists() and not path.is_dir():
        raise ValueError(f'{field} must point to a directory, not a file: {path}')
    if not path.exists() and path.suffix.lower() in COMMON_MEDIA_SUFFIXES:
        raise ValueError(f'{field} should be a directory path for demo.py, not a media filename: {path}')
    return path


def _validate_file_path(value: str, field: str) -> Path:
    path = Path(value).expanduser()
    if str(path).strip() == '':
        raise ValueError(f'{field} must be a non-empty path')
    if not path.exists():
        raise ValueError(f'{field} does not exist: {path}')
    if not path.is_file():
        raise ValueError(f'{field} must point to a file, not a directory: {path}')
    return path


def _validate_seed(seed: int) -> int:
    if seed < 0:
        raise ValueError('seed must be a non-negative integer for demo.py')
    return seed


def build_demo_command(
    *,
    python_cmd: str,
    variant: str,
    prompt: str,
    duration: float,
    seed: int,
    output_dir: Path,
    negative_prompt: str = '',
    video_path: Path | None = None,
    cfg_strength: float = DEFAULT_CFG_STRENGTH,
    num_steps: int = DEFAULT_NUM_STEPS,
    mask_away_clip: bool = False,
    full_precision: bool = False,
    skip_video_composite: bool | None = None,
) -> str:
    _validate_non_empty(python_cmd, 'python_cmd')
    if variant not in SUPPORTED_VARIANTS:
        raise ValueError(f'unsupported variant: {variant}')
    _validate_non_empty(prompt, 'prompt')
    if duration <= 0:
        raise ValueError('duration must be > 0')
    _validate_seed(seed)
    if cfg_strength <= 0:
        raise ValueError('cfg_strength must be > 0')
    if num_steps <= 0:
        raise ValueError('num_steps must be > 0')

    if skip_video_composite is None:
        skip_video_composite = video_path is None

    python_parts = shlex.split(python_cmd)
    if not python_parts:
        raise ValueError('python_cmd must contain at least one token')

    parts: list[str] = [shlex.quote(part) for part in python_parts]
    parts.extend(['demo.py', '--variant', shlex.quote(variant)])
    if video_path is not None:
        parts.extend(['--video', shlex.quote(str(video_path))])
    parts.extend([
        '--prompt',
        shlex.quote(prompt),
        '--duration',
        shlex.quote(f'{duration:g}'),
        '--cfg_strength',
        shlex.quote(f'{cfg_strength:g}'),
        '--num_steps',
        shlex.quote(str(num_steps)),
        '--seed',
        shlex.quote(str(seed)),
        '--output',
        shlex.quote(str(output_dir)),
    ])

    if negative_prompt:
        _validate_non_empty(negative_prompt, 'negative_prompt')
        parts.extend(['--negative_prompt', shlex.quote(negative_prompt)])
    if mask_away_clip:
        parts.append('--mask_away_clip')
    if full_precision:
        parts.append('--full_precision')
    if skip_video_composite:
        parts.append('--skip_video_composite')

    return ' '.join(parts)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Validate and print a safe MMAudio demo command.')
    parser.add_argument('--python', default='python', help='Interpreter command to print')
    parser.add_argument('--variant', default=DEFAULT_VARIANT, choices=SUPPORTED_VARIANTS)
    parser.add_argument('--prompt', required=True, help='Positive text prompt')
    parser.add_argument('--negative-prompt', default='', help='Optional negative prompt')
    parser.add_argument('--duration', type=float, default=DEFAULT_DURATION)
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED)
    parser.add_argument('--output', default=DEFAULT_OUTPUT_DIR, help='Output directory')
    parser.add_argument('--video', default=None, help='Optional video input path')
    parser.add_argument('--cfg-strength', type=float, default=DEFAULT_CFG_STRENGTH)
    parser.add_argument('--num-steps', type=int, default=DEFAULT_NUM_STEPS)
    parser.add_argument('--mask-away-clip', action='store_true')
    parser.add_argument('--full-precision', action='store_true')
    parser.add_argument(
        '--skip-video-composite',
        action='store_true',
        help='Force --skip_video_composite even when a video is present',
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        prompt = _validate_non_empty(args.prompt, 'prompt')
        negative_prompt = args.negative_prompt.strip()
        if negative_prompt:
            _validate_non_empty(negative_prompt, 'negative_prompt')
        output_dir = _validate_directory_like_path(args.output, 'output')
        video_path = _validate_file_path(args.video, 'video') if args.video else None

        command = build_demo_command(
            python_cmd=args.python,
            variant=args.variant,
            prompt=prompt,
            duration=args.duration,
            seed=args.seed,
            output_dir=output_dir,
            negative_prompt=negative_prompt,
            video_path=video_path,
            cfg_strength=args.cfg_strength,
            num_steps=args.num_steps,
            mask_away_clip=args.mask_away_clip,
            full_precision=args.full_precision,
            skip_video_composite=True if video_path is None else args.skip_video_composite,
        )
    except ValueError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2

    print(command)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
