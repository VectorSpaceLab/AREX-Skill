#!/usr/bin/env python3
"""Safe MMSegmentation training preflight and optional launcher.

Dry-run is the default. Actual training starts only when --execute is passed.
This wrapper mirrors MMSegmentation's training entry point without importing
MMSegmentation during --help or dry-run paths.
"""

from __future__ import annotations

import argparse
import ast
import json
import logging
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any, Iterable


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _split_cfg_value(value: str) -> Any:
    lowered = value.lower()
    if lowered == 'true':
        return True
    if lowered == 'false':
        return False
    if lowered in {'none', 'null'}:
        return None
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        pass
    if ',' in value and not value.startswith(('"', "'", '[', '(', '{')):
        return [_split_cfg_value(part) for part in value.split(',')]
    return value


def _parse_cfg_options(options: Iterable[str] | None) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for item in options or []:
        if '=' not in item:
            raise ValueError(f'cfg option must use KEY=VALUE form: {item}')
        key, value = item.split('=', 1)
        if not key:
            raise ValueError(f'cfg option has an empty key: {item}')
        parsed[key] = _split_cfg_value(value)
    return parsed


def _quote_command(command: list[str]) -> str:
    return ' '.join(shlex.quote(part) for part in command)


def _script_ref() -> str:
    script_path = Path(__file__)
    try:
        return str(script_path.relative_to(Path.cwd()))
    except ValueError:
        return str(script_path)


def _base_direct_args(args: argparse.Namespace) -> list[str]:
    command = [args.python, _script_ref(), args.config]
    if args.work_dir:
        command += ['--work-dir', args.work_dir]
    if args.resume:
        command.append('--resume')
    if args.amp:
        command.append('--amp')
    cfg_options = list(args.cfg_options or [])
    if args.max_iters is not None:
        cfg_options.append(f'train_cfg.max_iters={args.max_iters}')
    if args.val_interval is not None:
        cfg_options.append(f'train_cfg.val_interval={args.val_interval}')
    if cfg_options:
        command.append('--cfg-options')
        command.extend(cfg_options)
    command += ['--launcher', args.launcher, '--execute', '--direct-run']
    return command


def _distributed_command(args: argparse.Namespace) -> list[str]:
    command = [
        args.python,
        '-m',
        'torch.distributed.launch',
        f'--nnodes={args.nnodes}',
        f'--node_rank={args.node_rank}',
        f'--master_addr={args.master_addr}',
        f'--nproc_per_node={args.gpus}',
        f'--master_port={args.port}',
    ]
    direct = _base_direct_args(args)
    launcher_index = direct.index('--launcher') + 1
    direct[launcher_index] = 'pytorch'
    return command + direct[1:]


def _slurm_command(args: argparse.Namespace) -> list[str]:
    if not args.partition:
        raise ValueError('--partition is required with --slurm')
    if not args.job_name:
        raise ValueError('--job-name is required with --slurm')
    gpus_per_node = args.gpus_per_node or args.gpus
    command = [
        'srun',
        '-p',
        args.partition,
        f'--job-name={args.job_name}',
        f'--gres=gpu:{gpus_per_node}',
        f'--ntasks={args.gpus}',
        f'--ntasks-per-node={gpus_per_node}',
        f'--cpus-per-task={args.cpus_per_task}',
        '--kill-on-bad-exit=1',
    ]
    if args.srun_args:
        command.extend(shlex.split(args.srun_args))
    direct = _base_direct_args(args)
    launcher_index = direct.index('--launcher') + 1
    direct[launcher_index] = 'slurm'
    command += [args.python, '-u'] + direct[1:]
    return command


def _preflight(args: argparse.Namespace, command: list[str]) -> dict[str, Any]:
    config_path = Path(args.config)
    work_dir = Path(args.work_dir) if args.work_dir else None
    checks = {
        'config_exists': config_path.is_file(),
        'work_dir_parent_exists': True if work_dir is None else work_dir.parent.exists(),
        'mode': 'slurm' if args.slurm else 'distributed' if args.distributed else 'single-process',
        'execute': bool(args.execute),
        'command': command,
    }
    if args.check_files and not checks['config_exists']:
        checks['warning'] = 'config file was not found; dry-run still did not import or train'
    return checks


def _print_preflight(args: argparse.Namespace, checks: dict[str, Any]) -> None:
    if args.print_json:
        print(json.dumps(checks, indent=2, sort_keys=True))
        return
    print('MMSegmentation training wrapper')
    print(f"mode: {checks['mode']}")
    print(f"execute: {checks['execute']}")
    print(f"config exists: {checks['config_exists']}")
    print(f"work-dir parent exists: {checks['work_dir_parent_exists']}")
    if checks.get('warning'):
        print(f"warning: {checks['warning']}")
    print('command:')
    print(_quote_command(checks['command']))
    if not args.execute:
        print('dry-run only; add --execute to start training')


def _merge_cli_cfg_options(args: argparse.Namespace) -> dict[str, Any]:
    options = list(args.cfg_options or [])
    if args.max_iters is not None:
        options.append(f'train_cfg.max_iters={args.max_iters}')
    if args.val_interval is not None:
        options.append(f'train_cfg.val_interval={args.val_interval}')
    return _parse_cfg_options(options)


def _run_training(args: argparse.Namespace) -> None:
    if 'LOCAL_RANK' not in os.environ:
        os.environ['LOCAL_RANK'] = str(args.local_rank)

    from mmengine.config import Config
    from mmengine.logging import print_log
    from mmengine.runner import Runner

    from mmseg.registry import RUNNERS

    cfg = Config.fromfile(args.config)
    cfg.launcher = args.launcher
    cfg_options = _merge_cli_cfg_options(args)
    if cfg_options:
        cfg.merge_from_dict(cfg_options)

    if args.work_dir is not None:
        cfg.work_dir = args.work_dir
    elif cfg.get('work_dir', None) is None:
        cfg.work_dir = str(Path('./work_dirs') / Path(args.config).stem)

    if args.amp:
        optim_wrapper = cfg.get('optim_wrapper', None)
        wrapper_type = None
        if optim_wrapper is not None:
            wrapper_type = optim_wrapper.get('type', None)
        if wrapper_type == 'AmpOptimWrapper':
            print_log(
                'AMP training is already enabled in your config.',
                logger='current',
                level=logging.WARNING)
        else:
            assert wrapper_type == 'OptimWrapper', (
                '`--amp` is only supported when optim_wrapper.type is '
                f'`OptimWrapper`, but got {wrapper_type}.')
            cfg.optim_wrapper.type = 'AmpOptimWrapper'
            cfg.optim_wrapper.loss_scale = 'dynamic'

    cfg.resume = args.resume

    if 'runner_type' not in cfg:
        runner = Runner.from_cfg(cfg)
    else:
        runner = RUNNERS.build(cfg)
    runner.train()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Dry-run/preflight MMSegmentation training; execute only with --execute.')
    parser.add_argument('config', help='training config file')
    parser.add_argument('--work-dir', help='directory to save logs and models')
    parser.add_argument('--resume', action='store_true', help='resume from latest checkpoint in work_dir')
    parser.add_argument('--amp', action='store_true', help='enable automatic mixed precision when config uses OptimWrapper')
    parser.add_argument('--cfg-options', nargs='+', help='config overrides in KEY=VALUE form')
    parser.add_argument('--launcher', choices=['none', 'pytorch', 'slurm', 'mpi'], default='none')
    parser.add_argument('--local_rank', '--local-rank', type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument('--max-iters', type=int, help='append train_cfg.max_iters override for bounded runs')
    parser.add_argument('--val-interval', type=int, help='append train_cfg.val_interval override')
    parser.add_argument('--distributed', action='store_true', help='construct/launch a torch.distributed command')
    parser.add_argument('--gpus', type=int, default=1, help='processes per node for distributed launch or total Slurm tasks')
    parser.add_argument('--nnodes', type=int, default=_env_int('NNODES', 1))
    parser.add_argument('--node-rank', type=int, default=_env_int('NODE_RANK', 0))
    parser.add_argument('--master-addr', default=os.environ.get('MASTER_ADDR', '127.0.0.1'))
    parser.add_argument('--port', type=int, default=_env_int('PORT', _env_int('MASTER_PORT', 29500)))
    parser.add_argument('--slurm', action='store_true', help='construct/launch an srun command')
    parser.add_argument('--partition', help='Slurm partition, required with --slurm')
    parser.add_argument('--job-name', help='Slurm job name, required with --slurm')
    parser.add_argument('--gpus-per-node', type=int, help='Slurm GPUs per node; defaults to --gpus')
    parser.add_argument('--cpus-per-task', type=int, default=_env_int('CPUS_PER_TASK', 5))
    parser.add_argument('--srun-args', help='extra Slurm arguments, shell-split')
    parser.add_argument('--python', default='python', help='Python executable for generated commands')
    parser.add_argument('--execute', action='store_true', help='actually start training or the launcher command')
    parser.add_argument('--direct-run', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--no-check-files', dest='check_files', action='store_false', help='skip config existence preflight')
    parser.add_argument('--print-json', action='store_true', help='print preflight as JSON')
    parser.set_defaults(check_files=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.distributed and args.slurm:
        raise SystemExit('choose only one of --distributed or --slurm')

    try:
        if args.slurm:
            command = _slurm_command(args)
        elif args.distributed:
            command = _distributed_command(args)
        else:
            command = _base_direct_args(args)
        checks = _preflight(args, command)
        _print_preflight(args, checks)
        if not args.execute:
            return 0
        if args.check_files and not Path(args.config).is_file():
            raise FileNotFoundError(f'config file not found: {args.config}')
        if args.direct_run or (not args.distributed and not args.slurm):
            _run_training(args)
            return 0
        completed = subprocess.run(command, check=False)
        return completed.returncode
    except Exception as exc:  # noqa: BLE001 - CLI should report concise failures.
        print(f'error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
