#!/usr/bin/env python3
"""Print a Raster Vision Docker command without executing Docker.

This helper mirrors Raster Vision's common Docker launch pattern, but only
renders the command line so that agents can inspect or share it safely.
"""

from __future__ import annotations

import argparse
import os
import shlex
from pathlib import Path

DEFAULT_IMAGE = os.environ.get('RV_DOCKER_IMAGE', 'raster-vision-pytorch')
DEFAULT_DATA_DIR = os.environ.get('RASTER_VISION_DATA_DIR', './data')
DEFAULT_NOTEBOOK_DIR = os.environ.get(
    'RASTER_VISION_NOTEBOOK_DIR', './notebooks')
DEFAULT_SOURCE_DIR = os.environ.get('RASTER_VISION_SOURCE_DIR', '.')
DEFAULT_AWS_PROFILE = os.environ.get('AWS_PROFILE', 'default')


def _resolve_path(value: str) -> str:
    return str(Path(value).expanduser().resolve())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            'Render a Docker command for Raster Vision without running Docker.'
        ))
    parser.add_argument('--image', default=DEFAULT_IMAGE)
    parser.add_argument('--source-dir', default=DEFAULT_SOURCE_DIR)
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR)
    parser.add_argument('--notebook-dir', default=DEFAULT_NOTEBOOK_DIR)
    parser.add_argument('--name')
    parser.add_argument('--aws', action='store_true')
    parser.add_argument('--aws-profile', default=DEFAULT_AWS_PROFILE)
    parser.add_argument('--gpu', action='store_true')
    parser.add_argument('--tensorboard', action='store_true')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--arm64', action='store_true')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--command', help='Custom command to run in the container')
    mode.add_argument('--jupyter', action='store_true')
    mode.add_argument('--jupyter-lab', action='store_true')
    mode.add_argument('--docs', action='store_true')
    parser.add_argument(
        '--port', type=int, default=8888,
        help='Port to use for jupyter when --jupyter or --jupyter-lab is set (default: 8888)')
    return parser


def build_docker_command(args: argparse.Namespace) -> list[str]:
    cmd = ['docker', 'run', '--rm', '-it', '--ipc=host']
    if args.name:
        cmd += ['--name', args.name]
    if args.gpu:
        cmd += ['--gpus=all']
    if args.debug:
        cmd += ['-p', '3003:3000']
    if args.tensorboard:
        cmd += ['-p', '6006:6006']
    if args.docs:
        cmd += ['-p', '8000:8000']
    if args.aws:
        cmd += ['-e', f'AWS_PROFILE={args.aws_profile}']
        cmd += ['-v', f'{_resolve_path(Path.home() / ".aws")}:/root/.aws:ro']
    cmd += ['-v', f'{_resolve_path(Path.home() / ".rastervision")}:/root/.rastervision']
    cmd += ['-v', f'{_resolve_path(args.source_dir)}:/opt/src']
    cmd += ['-v', f'{_resolve_path(args.data_dir)}:/opt/data']
    cmd += ['-w', '/opt/src']

    if args.jupyter or args.jupyter_lab:
        cmd += ['-v', f'{_resolve_path(args.notebook_dir)}:/opt/notebooks']
        cmd += ['-p', f'{args.port}:{args.port}']
    if args.jupyter_lab:
        cmd += ['-v', f'{_resolve_path(Path.home() / ".jupyter")}:/root/.jupyter']

    image = args.image + ('-arm64' if args.arm64 else '')
    cmd.append(image)

    if args.jupyter:
        cmd += [
            'jupyter', 'notebook', '--ip', '0.0.0.0', '--port', str(args.port),
            '--no-browser', '--allow-root', '--notebook-dir=/opt/notebooks'
        ]
    elif args.jupyter_lab:
        cmd += [
            '/bin/bash', '-lc',
            'jupyter lab --ip 0.0.0.0 --port {port} --no-browser --allow-root '
            '--notebook-dir=/opt/notebooks & bash'.format(port=args.port)
        ]
    elif args.docs:
        cmd += ['/bin/bash', '-lc', 'cd docs && make livehtml']
    elif args.command:
        cmd += shlex.split(args.command)
    else:
        cmd.append('/bin/bash')

    return cmd


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    print(shlex.join(build_docker_command(args)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
