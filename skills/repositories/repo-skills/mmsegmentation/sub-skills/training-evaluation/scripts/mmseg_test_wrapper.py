#!/usr/bin/env python3
"""Safe MMSegmentation testing preflight and optional launcher.

Dry-run is the default. Actual testing starts only when --execute is passed.
This wrapper mirrors MMSegmentation's test entry point without importing
MMSegmentation during --help or dry-run paths.
"""

from __future__ import annotations

import argparse
import ast
import json
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
    command = [args.python, _script_ref(), args.config, args.checkpoint]
    if args.work_dir:
        command += ['--work-dir', args.work_dir]
    if args.out:
        command += ['--out', args.out]
    if args.show:
        command.append('--show')
    if args.show_dir:
        command += ['--show-dir', args.show_dir]
    if args.wait_time is not None:
        command += ['--wait-time', str(args.wait_time)]
    cfg_options = list(args.cfg_options or [])
    if args.format_only:
        cfg_options.append('test_evaluator.format_only=True')
    if args.keep_results:
        cfg_options.append('test_evaluator.keep_results=True')
    if cfg_options:
        command.append('--cfg-options')
        command.extend(cfg_options)
    command += ['--launcher', args.launcher]
    if args.tta:
        command.append('--tta')
    command += ['--execute', '--direct-run']
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
    checkpoint_path = Path(args.checkpoint)
    work_dir = Path(args.work_dir) if args.work_dir else None
    out_dir = Path(args.out) if args.out else None
    checks = {
        'config_exists': config_path.is_file(),
        'checkpoint_exists': checkpoint_path.is_file(),
        'work_dir_parent_exists': True if work_dir is None else work_dir.parent.exists(),
        'out_dir_parent_exists': True if out_dir is None else out_dir.parent.exists(),
        'mode': 'slurm' if args.slurm else 'distributed' if args.distributed else 'single-process',
        'execute': bool(args.execute),
        'format_only_requested': bool(args.format_only),
        'keep_results_requested': bool(args.keep_results or args.out),
        'command': command,
    }
    warnings = []
    if args.show and args.show_dir:
        warnings.append('--show opens a display while --show-dir saves files; headless servers usually need only --show-dir')
    if args.format_only and not (args.keep_results or args.out):
        warnings.append('format_only skips metrics; set --out or --keep-results with an output_dir override when saved files must persist')
    if args.tta:
        warnings.append('--tta requires cfg.tta_pipeline and cfg.tta_model in the config')
    if warnings:
        checks['warnings'] = warnings
    return checks


def _print_preflight(args: argparse.Namespace, checks: dict[str, Any]) -> None:
    if args.print_json:
        print(json.dumps(checks, indent=2, sort_keys=True))
        return
    print('MMSegmentation testing wrapper')
    print(f"mode: {checks['mode']}")
    print(f"execute: {checks['execute']}")
    print(f"config exists: {checks['config_exists']}")
    print(f"checkpoint exists: {checks['checkpoint_exists']}")
    print(f"work-dir parent exists: {checks['work_dir_parent_exists']}")
    print(f"out-dir parent exists: {checks['out_dir_parent_exists']}")
    for warning in checks.get('warnings', []):
        print(f'warning: {warning}')
    print('command:')
    print(_quote_command(checks['command']))
    if not args.execute:
        print('dry-run only; add --execute to start testing')


def _merge_cli_cfg_options(args: argparse.Namespace) -> dict[str, Any]:
    options = list(args.cfg_options or [])
    if args.format_only:
        options.append('test_evaluator.format_only=True')
    if args.keep_results:
        options.append('test_evaluator.keep_results=True')
    return _parse_cfg_options(options)


def _trigger_visualization_hook(cfg: Any, args: argparse.Namespace) -> Any:
    default_hooks = cfg.default_hooks
    if 'visualization' not in default_hooks:
        raise RuntimeError(
            'VisualizationHook must be included in default_hooks; add a '
            'visualization hook or remove --show/--show-dir.')
    visualization_hook = default_hooks['visualization']
    visualization_hook['draw'] = True
    if args.show:
        visualization_hook['show'] = True
        visualization_hook['wait_time'] = args.wait_time
    if args.show_dir:
        visualizer = cfg.visualizer
        visualizer['save_dir'] = args.show_dir
    return cfg


def _run_testing(args: argparse.Namespace) -> None:
    if 'LOCAL_RANK' not in os.environ:
        os.environ['LOCAL_RANK'] = str(args.local_rank)

    from mmengine.config import Config
    from mmengine.runner import Runner

    cfg = Config.fromfile(args.config)
    cfg.launcher = args.launcher
    cfg_options = _merge_cli_cfg_options(args)
    if cfg_options:
        cfg.merge_from_dict(cfg_options)

    if args.work_dir is not None:
        cfg.work_dir = args.work_dir
    elif cfg.get('work_dir', None) is None:
        cfg.work_dir = str(Path('./work_dirs') / Path(args.config).stem)

    cfg.load_from = args.checkpoint

    if args.show or args.show_dir:
        cfg = _trigger_visualization_hook(cfg, args)

    if args.tta:
        cfg.test_dataloader.dataset.pipeline = cfg.tta_pipeline
        cfg.tta_model.module = cfg.model
        cfg.model = cfg.tta_model

    if args.out is not None:
        cfg.test_evaluator['output_dir'] = args.out
        cfg.test_evaluator['keep_results'] = True

    runner = Runner.from_cfg(cfg)
    runner.test()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Dry-run/preflight MMSegmentation testing; execute only with --execute.')
    parser.add_argument('config', help='test config file')
    parser.add_argument('checkpoint', help='checkpoint file')
    parser.add_argument('--work-dir', help='directory for evaluation metric JSON outputs')
    parser.add_argument('--out', help='directory to save prediction outputs for offline evaluation')
    parser.add_argument('--show', action='store_true', help='show prediction results interactively')
    parser.add_argument('--show-dir', help='directory where visualized predictions will be saved')
    parser.add_argument('--wait-time', type=float, default=2.0, help='show interval in seconds')
    parser.add_argument('--cfg-options', nargs='+', help='config overrides in KEY=VALUE form')
    parser.add_argument('--launcher', choices=['none', 'pytorch', 'slurm', 'mpi'], default='none')
    parser.add_argument('--local_rank', '--local-rank', type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument('--tta', action='store_true', help='enable test-time augmentation config path')
    parser.add_argument('--format-only', action='store_true', help='append test_evaluator.format_only=True override')
    parser.add_argument('--keep-results', action='store_true', help='append test_evaluator.keep_results=True override')
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
    parser.add_argument('--execute', action='store_true', help='actually start testing or the launcher command')
    parser.add_argument('--direct-run', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--no-check-files', dest='check_files', action='store_false', help='skip config/checkpoint existence enforcement before execution')
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
        if args.check_files:
            if not Path(args.config).is_file():
                raise FileNotFoundError(f'config file not found: {args.config}')
            if not Path(args.checkpoint).is_file():
                raise FileNotFoundError(f'checkpoint file not found: {args.checkpoint}')
        if args.direct_run or (not args.distributed and not args.slurm):
            _run_testing(args)
            return 0
        completed = subprocess.run(command, check=False)
        return completed.returncode
    except Exception as exc:  # noqa: BLE001 - CLI should report concise failures.
        print(f'error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
