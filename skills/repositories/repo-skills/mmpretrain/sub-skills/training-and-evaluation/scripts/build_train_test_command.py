#!/usr/bin/env python3
"""Print reviewed MMPreTrain launch commands without executing them.

The helper is intentionally safe: it only formats commands for training,
testing, distributed launch, Slurm launch, and K-fold planning. It never starts
an actual run.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable

try:
    _shlex_join = shlex.join
except AttributeError:  # pragma: no cover - kept for older Python builds
    def _shlex_join(parts: Iterable[str]) -> str:
        return ' '.join(shlex.quote(str(part)) for part in parts)


def _quote_env(name: str, value: object) -> str:
    return f'{name}={shlex.quote(str(value))}'


def _compose_command(env_items: list[tuple[str, object]], cmd_parts: list[object]) -> str:
    env_prefix = ' '.join(
        _quote_env(name, value)
        for name, value in env_items
        if value is not None and value != ''
    )
    command = _shlex_join([str(part) for part in cmd_parts])
    if env_prefix:
        return f'{env_prefix} {command}'
    return command


def _append_cfg_options(cmd: list[object], cfg_options: list[str] | None) -> None:
    if cfg_options:
        cmd.extend(['--cfg-options', *cfg_options])


def _train_args(
    args: argparse.Namespace,
    include_launcher: bool,
    include_work_dir: bool = True,
) -> list[object]:
    cmd: list[object] = ['mim', 'train', 'mmpretrain', args.config]
    if getattr(args, 'cpu', False):
        cmd.extend(['--gpus', '0'])
    if include_work_dir and args.work_dir is not None:
        cmd.extend(['--work-dir', args.work_dir])
    if args.resume == 'auto':
        cmd.append('--resume')
    elif args.resume is not None:
        cmd.extend(['--resume', args.resume])
    if args.amp:
        cmd.append('--amp')
    if args.no_validate:
        cmd.append('--no-validate')
    if args.auto_scale_lr:
        cmd.append('--auto-scale-lr')
    if args.no_pin_memory:
        cmd.append('--no-pin-memory')
    if args.no_persistent_workers:
        cmd.append('--no-persistent-workers')
    if include_launcher:
        cmd.extend(['--launcher', args.launcher])
    _append_cfg_options(cmd, args.cfg_options)
    return cmd


def _test_args(
    args: argparse.Namespace,
    include_launcher: bool,
    include_work_dir: bool = True,
) -> list[object]:
    cmd: list[object] = ['mim', 'test', 'mmpretrain', args.config, '--checkpoint', args.checkpoint]
    if getattr(args, 'cpu', False):
        cmd.extend(['--gpus', '0'])
    if include_work_dir and args.work_dir is not None:
        cmd.extend(['--work-dir', args.work_dir])
    if args.out is not None:
        cmd.extend(['--out', args.out])
    if args.out_item is not None:
        cmd.extend(['--out-item', args.out_item])
    if args.amp:
        cmd.append('--amp')
    if args.show_dir is not None:
        cmd.extend(['--show-dir', args.show_dir])
    if args.show:
        cmd.append('--show')
    if args.interval is not None:
        cmd.extend(['--interval', str(args.interval)])
    if args.wait_time is not None:
        cmd.extend(['--wait-time', str(args.wait_time)])
    if args.no_pin_memory:
        cmd.append('--no-pin-memory')
    if args.tta:
        cmd.append('--tta')
    if include_launcher:
        cmd.extend(['--launcher', args.launcher])
    _append_cfg_options(cmd, args.cfg_options)
    return cmd


def _kfold_args(args: argparse.Namespace) -> list[object]:
    cmd: list[object] = ['mim', 'run', 'mmpretrain', 'kfold-cross-valid', args.config, '--num-splits', str(args.num_splits)]
    if args.fold is not None:
        cmd.extend(['--fold', str(args.fold)])
    if args.work_dir is not None:
        cmd.extend(['--work-dir', args.work_dir])
    if args.seed is not None:
        cmd.extend(['--seed', str(args.seed)])
    if args.resume:
        cmd.append('--resume')
    if args.amp:
        cmd.append('--amp')
    if args.no_validate:
        cmd.append('--no-validate')
    if args.auto_scale_lr:
        cmd.append('--auto-scale-lr')
    if args.no_pin_memory:
        cmd.append('--no-pin-memory')
    if args.no_persistent_workers:
        cmd.append('--no-persistent-workers')
    cmd.extend(['--launcher', args.launcher])
    _append_cfg_options(cmd, args.cfg_options)
    return cmd


def _print_command(env_items: list[tuple[str, object]], cmd_parts: list[object]) -> int:
    print(_compose_command(env_items, cmd_parts))
    return 0


def _add_cfg_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--cfg-options',
        nargs='+',
        metavar='KEY=VALUE',
        help='Additional config overrides appended to the command.',
    )


def _add_train_flags(parser: argparse.ArgumentParser, *, include_cpu: bool, include_launcher: bool) -> None:
    parser.add_argument('config', help='Config file path')
    parser.add_argument('--work-dir', help='Directory for logs and checkpoints')
    parser.add_argument(
        '--resume',
        nargs='?',
        const='auto',
        type=str,
        help='Resume training, optionally from a specific checkpoint',
    )
    parser.add_argument('--amp', action='store_true', help='Enable automatic mixed precision')
    parser.add_argument('--no-validate', action='store_true', help='Skip validation during training')
    parser.add_argument('--auto-scale-lr', action='store_true', help='Enable automatic LR scaling')
    parser.add_argument('--no-pin-memory', action='store_true', help='Disable dataloader pin memory')
    parser.add_argument(
        '--no-persistent-workers',
        action='store_true',
        help='Disable persistent dataloader workers',
    )
    if include_launcher:
        parser.add_argument(
            '--launcher',
            choices=['none', 'pytorch', 'slurm', 'mpi'],
            default='none',
            help='Launcher mode for direct training commands',
        )
    if include_cpu:
        parser.add_argument(
            '--cpu',
            action='store_true',
            help='Prefix the command with CUDA_VISIBLE_DEVICES=-1',
        )
    _add_cfg_options(parser)


def _add_test_flags(parser: argparse.ArgumentParser, *, include_cpu: bool, include_launcher: bool) -> None:
    parser.add_argument('config', help='Config file path')
    parser.add_argument('checkpoint', help='Checkpoint file path')
    parser.add_argument('--work-dir', help='Directory for evaluation outputs')
    parser.add_argument('--out', help='File to store predictions or metrics')
    parser.add_argument(
        '--out-item',
        choices=['metrics', 'pred'],
        help='What to store in the output file',
    )
    parser.add_argument('--amp', action='store_true', help='Enable fp16 test mode')
    parser.add_argument('--show-dir', help='Directory for rendered visualizations')
    parser.add_argument('--show', action='store_true', help='Display predictions in a window')
    parser.add_argument('--interval', type=int, default=1, help='Visualize every N samples')
    parser.add_argument('--wait-time', type=float, default=2, help='Window display time in seconds')
    parser.add_argument('--no-pin-memory', action='store_true', help='Disable dataloader pin memory')
    parser.add_argument('--tta', action='store_true', help='Enable test-time augmentation')
    if include_launcher:
        parser.add_argument(
            '--launcher',
            choices=['none', 'pytorch', 'slurm', 'mpi'],
            default='none',
            help='Launcher mode for direct testing commands',
        )
    if include_cpu:
        parser.add_argument(
            '--cpu',
            action='store_true',
            help='Prefix the command with CUDA_VISIBLE_DEVICES=-1',
        )
    _add_cfg_options(parser)


def _add_dist_train_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('config', help='Config file path')
    parser.add_argument('gpus', type=int, help='Number of GPUs to use')
    parser.add_argument('--nnodes', type=int, default=1, help='Total number of nodes')
    parser.add_argument('--node-rank', type=int, default=0, help='Rank of the local node')
    parser.add_argument('--port', type=int, default=29500, help='Distributed communication port')
    parser.add_argument('--master-addr', default='127.0.0.1', help='Master node address')
    parser.add_argument('--work-dir', help='Directory for logs and checkpoints')
    parser.add_argument(
        '--resume',
        nargs='?',
        const='auto',
        type=str,
        help='Resume training, optionally from a specific checkpoint',
    )
    parser.add_argument('--amp', action='store_true', help='Enable automatic mixed precision')
    parser.add_argument('--no-validate', action='store_true', help='Skip validation during training')
    parser.add_argument('--auto-scale-lr', action='store_true', help='Enable automatic LR scaling')
    parser.add_argument('--no-pin-memory', action='store_true', help='Disable dataloader pin memory')
    parser.add_argument(
        '--no-persistent-workers',
        action='store_true',
        help='Disable persistent dataloader workers',
    )
    _add_cfg_options(parser)


def _add_dist_test_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('config', help='Config file path')
    parser.add_argument('checkpoint', help='Checkpoint file path')
    parser.add_argument('gpus', type=int, help='Number of GPUs to use')
    parser.add_argument('--nnodes', type=int, default=1, help='Total number of nodes')
    parser.add_argument('--node-rank', type=int, default=0, help='Rank of the local node')
    parser.add_argument('--port', type=int, default=29500, help='Distributed communication port')
    parser.add_argument('--master-addr', default='127.0.0.1', help='Master node address')
    parser.add_argument('--work-dir', help='Directory for evaluation outputs')
    parser.add_argument('--out', help='File to store predictions or metrics')
    parser.add_argument(
        '--out-item',
        choices=['metrics', 'pred'],
        help='What to store in the output file',
    )
    parser.add_argument('--amp', action='store_true', help='Enable fp16 test mode')
    parser.add_argument('--show-dir', help='Directory for rendered visualizations')
    parser.add_argument('--show', action='store_true', help='Display predictions in a window')
    parser.add_argument('--interval', type=int, default=1, help='Visualize every N samples')
    parser.add_argument('--wait-time', type=float, default=2, help='Window display time in seconds')
    parser.add_argument('--no-pin-memory', action='store_true', help='Disable dataloader pin memory')
    parser.add_argument('--tta', action='store_true', help='Enable test-time augmentation')
    _add_cfg_options(parser)


def _add_slurm_train_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('partition', help='Slurm partition name')
    parser.add_argument('job_name', help='Slurm job name')
    parser.add_argument('config', help='Config file path')
    parser.add_argument('work_dir', help='Directory for logs and checkpoints')
    parser.add_argument('--gpus', type=int, default=8, help='Total number of GPUs')
    parser.add_argument('--gpus-per-node', type=int, default=8, help='GPUs to allocate per node')
    parser.add_argument('--cpus-per-task', type=int, default=5, help='CPUs to allocate per task')
    parser.add_argument('--srun-args', default='', help='Extra arguments passed to srun')
    parser.add_argument(
        '--resume',
        nargs='?',
        const='auto',
        type=str,
        help='Resume training, optionally from a specific checkpoint',
    )
    parser.add_argument('--amp', action='store_true', help='Enable automatic mixed precision')
    parser.add_argument('--no-validate', action='store_true', help='Skip validation during training')
    parser.add_argument('--auto-scale-lr', action='store_true', help='Enable automatic LR scaling')
    parser.add_argument('--no-pin-memory', action='store_true', help='Disable dataloader pin memory')
    parser.add_argument(
        '--no-persistent-workers',
        action='store_true',
        help='Disable persistent dataloader workers',
    )
    _add_cfg_options(parser)


def _add_slurm_test_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('partition', help='Slurm partition name')
    parser.add_argument('job_name', help='Slurm job name')
    parser.add_argument('config', help='Config file path')
    parser.add_argument('checkpoint', help='Checkpoint file path')
    parser.add_argument('--work-dir', help='Directory for evaluation outputs')
    parser.add_argument('--gpus', type=int, default=8, help='Total number of GPUs')
    parser.add_argument('--gpus-per-node', type=int, default=8, help='GPUs to allocate per node')
    parser.add_argument('--cpus-per-task', type=int, default=5, help='CPUs to allocate per task')
    parser.add_argument('--srun-args', default='', help='Extra arguments passed to srun')
    parser.add_argument('--out', help='File to store predictions or metrics')
    parser.add_argument(
        '--out-item',
        choices=['metrics', 'pred'],
        help='What to store in the output file',
    )
    parser.add_argument('--amp', action='store_true', help='Enable fp16 test mode')
    parser.add_argument('--show-dir', help='Directory for rendered visualizations')
    parser.add_argument('--show', action='store_true', help='Display predictions in a window')
    parser.add_argument('--interval', type=int, default=1, help='Visualize every N samples')
    parser.add_argument('--wait-time', type=float, default=2, help='Window display time in seconds')
    parser.add_argument('--no-pin-memory', action='store_true', help='Disable dataloader pin memory')
    parser.add_argument('--tta', action='store_true', help='Enable test-time augmentation')
    _add_cfg_options(parser)


def _add_kfold_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('config', help='Config file path')
    parser.add_argument('--num-splits', type=int, required=True, help='Number of folds')
    parser.add_argument('--fold', type=int, help='Run only one fold')
    parser.add_argument('--work-dir', help='Directory for logs and checkpoints')
    parser.add_argument('--seed', type=int, default=None, help='Random seed used for splitting')
    parser.add_argument('--resume', action='store_true', help='Resume the previous K-fold experiment')
    parser.add_argument('--amp', action='store_true', help='Enable automatic mixed precision')
    parser.add_argument('--no-validate', action='store_true', help='Skip validation during training')
    parser.add_argument('--auto-scale-lr', action='store_true', help='Enable automatic LR scaling')
    parser.add_argument('--no-pin-memory', action='store_true', help='Disable dataloader pin memory')
    parser.add_argument(
        '--no-persistent-workers',
        action='store_true',
        help='Disable persistent dataloader workers',
    )
    parser.add_argument(
        '--launcher',
        choices=['none', 'pytorch', 'slurm', 'mpi'],
        default='none',
        help='Launcher mode for the K-fold helper',
    )
    parser.add_argument(
        '--cpu',
        action='store_true',
        help='Prefix the command with CUDA_VISIBLE_DEVICES=-1',
    )
    _add_cfg_options(parser)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Print safe MMPreTrain train/test commands without running them',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='mode', required=True)

    train = subparsers.add_parser('train', help='Print a direct training command')
    _add_train_flags(train, include_cpu=True, include_launcher=True)

    test = subparsers.add_parser('test', help='Print a direct evaluation command')
    _add_test_flags(test, include_cpu=True, include_launcher=True)

    dist_train = subparsers.add_parser('dist-train', help='Print a distributed training command')
    _add_dist_train_flags(dist_train)

    dist_test = subparsers.add_parser('dist-test', help='Print a distributed evaluation command')
    _add_dist_test_flags(dist_test)

    slurm_train = subparsers.add_parser('slurm-train', help='Print a Slurm training command')
    _add_slurm_train_flags(slurm_train)

    slurm_test = subparsers.add_parser('slurm-test', help='Print a Slurm evaluation command')
    _add_slurm_test_flags(slurm_test)

    kfold = subparsers.add_parser('kfold', help='Print a K-fold cross-validation command')
    _add_kfold_flags(kfold)

    return parser


def _validate_test_args(args: argparse.Namespace) -> None:
    if args.out_item is not None and args.out is None:
        raise ValueError('--out-item requires --out')


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.mode == 'train':
            env = [('CUDA_VISIBLE_DEVICES', '-1')] if args.cpu else []
            return _print_command(env, _train_args(args, include_launcher=True))

        if args.mode == 'test':
            _validate_test_args(args)
            env = [('CUDA_VISIBLE_DEVICES', '-1')] if args.cpu else []
            return _print_command(env, _test_args(args, include_launcher=True))

        if args.mode == 'dist-train':
            env = [
                ('NNODES', args.nnodes),
                ('NODE_RANK', args.node_rank),
                ('PORT', args.port),
                ('MASTER_ADDR', args.master_addr),
            ]
            cmd = ['mim', 'train', 'mmpretrain', args.config, '--launcher', 'pytorch', '--gpus', str(args.gpus), '--port', str(args.port)]
            cmd.extend(_train_args(args, include_launcher=False, include_work_dir=True)[4:])
            return _print_command(env, cmd)

        if args.mode == 'dist-test':
            _validate_test_args(args)
            env = [
                ('NNODES', args.nnodes),
                ('NODE_RANK', args.node_rank),
                ('PORT', args.port),
                ('MASTER_ADDR', args.master_addr),
            ]
            cmd = ['mim', 'test', 'mmpretrain', args.config, '--checkpoint', args.checkpoint, '--launcher', 'pytorch', '--gpus', str(args.gpus), '--port', str(args.port)]
            cmd.extend(_test_args(args, include_launcher=False, include_work_dir=True)[6:])
            return _print_command(env, cmd)

        if args.mode == 'slurm-train':
            env = [
                ('GPUS', args.gpus),
                ('GPUS_PER_NODE', args.gpus_per_node),
                ('CPUS_PER_TASK', args.cpus_per_task),
                ('SRUN_ARGS', args.srun_args),
            ]
            cmd = ['mim', 'train', 'mmpretrain', args.config, '--launcher', 'slurm', '--gpus', str(args.gpus), '--gpus-per-node', str(args.gpus_per_node), '--cpus-per-task', str(args.cpus_per_task), '--partition', args.partition, '--work-dir', args.work_dir]
            cmd.extend(_train_args(args, include_launcher=False, include_work_dir=False)[4:])
            return _print_command(env, cmd)

        if args.mode == 'slurm-test':
            _validate_test_args(args)
            env = [
                ('GPUS', args.gpus),
                ('GPUS_PER_NODE', args.gpus_per_node),
                ('CPUS_PER_TASK', args.cpus_per_task),
                ('SRUN_ARGS', args.srun_args),
            ]
            cmd = [
                'mim',
                'test',
                'mmpretrain',
                args.config,
                '--checkpoint',
                args.checkpoint,
                '--launcher',
                'slurm',
                '--gpus',
                str(args.gpus),
                '--gpus-per-node',
                str(args.gpus_per_node),
                '--cpus-per-task',
                str(args.cpus_per_task),
                '--partition',
                args.partition,
            ]
            cmd.extend(_test_args(args, include_launcher=False, include_work_dir=True)[6:])
            return _print_command(env, cmd)

        if args.mode == 'kfold':
            env = [('CUDA_VISIBLE_DEVICES', '-1')] if args.cpu else []
            return _print_command(env, _kfold_args(args))

        raise RuntimeError(f'Unsupported mode: {args.mode}')
    except ValueError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
