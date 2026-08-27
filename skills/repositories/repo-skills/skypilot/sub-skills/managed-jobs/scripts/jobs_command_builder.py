#!/usr/bin/env python3
"""Print safe SkyPilot managed-jobs commands without executing them."""

import argparse
import shlex
from typing import Iterable, List, Optional


def _quote(value: object) -> str:
    return shlex.quote(str(value))


def _append_option(command: List[str], flag: str, value: Optional[object]) -> None:
    if value is not None:
        command.extend([flag, str(value)])


def _append_repeated(command: List[str], flag: str, values: Iterable[str]) -> None:
    for value in values:
        command.extend([flag, value])


def _print_command(parts: Iterable[object]) -> None:
    print(' '.join(_quote(part) for part in parts))


def build_launch(args: argparse.Namespace) -> None:
    command: List[object] = ['sky', 'jobs', 'launch']
    _append_option(command, '-n', args.name)
    _append_option(command, '--infra', args.infra)
    _append_option(command, '--gpus', args.gpus)
    _append_option(command, '--cpus', args.cpus)
    _append_option(command, '--memory', args.memory)
    _append_option(command, '--num-nodes', args.num_nodes)
    if args.use_spot:
        command.append('--use-spot')
    _append_option(command, '--job-recovery', args.job_recovery)
    _append_option(command, '--pool', args.pool)
    _append_option(command, '--num-jobs', args.num_jobs)
    _append_repeated(command, '--env', args.env)
    _append_repeated(command, '--secret', args.secret)
    if args.detach:
        command.append('--detach-run')
    if args.yes:
        command.append('-y')
    command.append(args.entrypoint)
    _print_command(command)


def build_queue(args: argparse.Namespace) -> None:
    command: List[object] = ['sky', 'jobs', 'queue']
    if args.refresh:
        command.append('--refresh')
    if args.skip_finished:
        command.append('--skip-finished')
    _append_repeated(command, '--status', args.status)
    _append_option(command, '--since', args.since)
    _append_option(command, '--after', args.after)
    _append_option(command, '--before', args.before)
    if args.all:
        command.append('--all')
    _append_option(command, '--limit', args.limit)
    if args.json:
        command.extend(['--format', 'json'])
    _print_command(command)


def build_logs(args: argparse.Namespace) -> None:
    command: List[object] = ['sky', 'jobs', 'logs']
    _append_option(command, '-n', args.name)
    if args.controller:
        command.append('--controller')
    if args.no_follow:
        command.append('--no-follow')
    if args.refresh:
        command.append('--refresh')
    if args.sync_down:
        command.append('--sync-down')
    _append_option(command, '--tail', args.tail)
    if args.job_id is not None:
        command.append(args.job_id)
    if args.task is not None:
        command.append(args.task)
    _print_command(command)


def build_cancel(args: argparse.Namespace) -> None:
    command: List[object] = ['sky', 'jobs', 'cancel']
    if args.name is not None:
        command.extend(['-n', args.name])
    elif args.pool is not None:
        command.extend(['--pool', args.pool])
    elif args.all:
        command.append('--all')
    elif args.job_ids:
        command.extend(args.job_ids)
    else:
        raise SystemExit('cancel requires job IDs, --name, --pool, or --all')
    if args.graceful:
        command.append('--graceful')
    _append_option(command, '--graceful-timeout', args.graceful_timeout)
    if args.yes:
        command.append('-y')
    _print_command(command)


def build_pool_apply(args: argparse.Namespace) -> None:
    command: List[object] = ['sky', 'jobs', 'pool', 'apply']
    _append_option(command, '-p', args.pool)
    if args.pool_yaml is not None:
        command.append(args.pool_yaml)
    _append_option(command, '--workers', args.workers)
    _append_option(command, '--mode', args.mode)
    _append_option(command, '--infra', args.infra)
    _append_option(command, '--gpus', args.gpus)
    _append_option(command, '--cpus', args.cpus)
    if args.use_spot:
        command.append('--use-spot')
    if args.yes:
        command.append('-y')
    _print_command(command)


def build_pool_status(args: argparse.Namespace) -> None:
    command: List[object] = ['sky', 'jobs', 'pool', 'status']
    if args.verbose:
        command.append('-v')
    if args.all:
        command.append('--all')
    command.extend(args.pool_names)
    _print_command(command)


def build_pool_logs(args: argparse.Namespace) -> None:
    command: List[object] = ['sky', 'jobs', 'pool', 'logs']
    if args.controller:
        command.append('--controller')
    if args.no_follow:
        command.append('--no-follow')
    if args.sync_down:
        command.append('--sync-down')
    _append_option(command, '--tail', args.tail)
    command.append(args.pool_name)
    command.extend(args.worker_ids)
    _print_command(command)


def build_pool_down(args: argparse.Namespace) -> None:
    command: List[object] = ['sky', 'jobs', 'pool', 'down']
    if args.all:
        command.append('--all')
    else:
        command.extend(args.pool_names)
    if args.purge:
        command.append('--purge')
    if args.yes:
        command.append('-y')
    _print_command(command)


def add_launch_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser('launch', help='Print a sky jobs launch command.')
    parser.add_argument('entrypoint', help='Task YAML path or shell command to submit.')
    parser.add_argument('-n', '--name', help='Managed job name.')
    parser.add_argument('--infra', help='Infrastructure override, for example aws/us-east-1 or kubernetes.')
    parser.add_argument('--gpus', help='GPU accelerator override, for example A100:8.')
    parser.add_argument('--cpus', help='CPU requirement override, for example 4+.')
    parser.add_argument('--memory', help='Memory requirement override, for example 32+.')
    parser.add_argument('--num-nodes', type=int, help='Number of nodes for distributed jobs.')
    parser.add_argument('--use-spot', action='store_true', help='Request spot instances.')
    parser.add_argument('--job-recovery', help='Recovery strategy override, for example FAILOVER or EAGER_NEXT_REGION.')
    parser.add_argument('-p', '--pool', help='Submit to a managed-jobs pool.')
    parser.add_argument('--num-jobs', type=int, help='Number of jobs to submit to a pool.')
    parser.add_argument('--env', action='append', default=[], help='Repeatable KEY=VALUE env override.')
    parser.add_argument('--secret', action='append', default=[], help='Repeatable secret name or KEY=VALUE secret override.')
    parser.add_argument('-d', '--detach', action='store_true', help='Return after submission instead of streaming logs.')
    parser.add_argument('-y', '--yes', action='store_true', help='Add noninteractive confirmation flag.')
    parser.set_defaults(func=build_launch)


def add_queue_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser('queue', help='Print a sky jobs queue command.')
    parser.add_argument('--refresh', action='store_true', help='Refresh statuses.')
    parser.add_argument('--skip-finished', action='store_true', help='Show only active jobs.')
    parser.add_argument('--status', action='append', default=[], help='Repeatable or comma-separated status filter.')
    parser.add_argument('--since', help='Relative submission window, for example 7d or 12h.')
    parser.add_argument('--after', help='Absolute local lower bound, for example 2026-01-01.')
    parser.add_argument('--before', help='Absolute local upper bound, for example 2026-01-31.')
    parser.add_argument('--all', action='store_true', help='Show all jobs.')
    parser.add_argument('--limit', type=int, help='Maximum rows to show.')
    parser.add_argument('--json', action='store_true', help='Request JSON output.')
    parser.set_defaults(func=build_queue)


def add_logs_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser('logs', help='Print a sky jobs logs command.')
    parser.add_argument('job_id', nargs='?', type=int, help='Managed job ID.')
    parser.add_argument('task', nargs='?', help='Task ID or task name for pipelines/job groups.')
    parser.add_argument('-n', '--name', help='Managed job name.')
    parser.add_argument('--controller', action='store_true', help='Show controller logs.')
    parser.add_argument('--no-follow', action='store_true', help='Print logs so far and exit.')
    parser.add_argument('--refresh', action='store_true', help='Refresh logs/status before reading.')
    parser.add_argument('--sync-down', action='store_true', help='Download logs instead of streaming.')
    parser.add_argument('--tail', type=int, help='Number of trailing lines to print.')
    parser.set_defaults(func=build_logs)


def add_cancel_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser('cancel', help='Print a sky jobs cancel command.')
    parser.add_argument('job_ids', nargs='*', help='Managed job IDs to cancel.')
    selector = parser.add_mutually_exclusive_group()
    selector.add_argument('-n', '--name', help='Managed job name to cancel.')
    selector.add_argument('-p', '--pool', help='Cancel all jobs in a pool.')
    selector.add_argument('--all', action='store_true', help='Cancel all current-user managed jobs.')
    parser.add_argument('--graceful', action='store_true', help='Request graceful cancellation.')
    parser.add_argument('--graceful-timeout', type=int, help='Graceful cancellation timeout in seconds.')
    parser.add_argument('-y', '--yes', action='store_true', help='Add noninteractive confirmation flag.')
    parser.set_defaults(func=build_cancel)


def add_pool_parsers(subparsers: argparse._SubParsersAction) -> None:
    pool_parser = subparsers.add_parser('pool', help='Print managed-jobs pool commands.')
    pool_subparsers = pool_parser.add_subparsers(dest='pool_command', required=True)

    apply_parser = pool_subparsers.add_parser('apply', help='Print a pool apply command.')
    apply_parser.add_argument('pool_yaml', nargs='?', help='Pool YAML path.')
    apply_parser.add_argument('-p', '--pool', help='Pool name.')
    apply_parser.add_argument('--workers', type=int, help='Worker count override/update.')
    apply_parser.add_argument('--mode', choices=['rolling', 'blue_green'], help='Pool update mode.')
    apply_parser.add_argument('--infra', help='Infrastructure override.')
    apply_parser.add_argument('--gpus', help='GPU override.')
    apply_parser.add_argument('--cpus', help='CPU override.')
    apply_parser.add_argument('--use-spot', action='store_true', help='Request spot workers.')
    apply_parser.add_argument('-y', '--yes', action='store_true', help='Add noninteractive confirmation flag.')
    apply_parser.set_defaults(func=build_pool_apply)

    status_parser = pool_subparsers.add_parser('status', help='Print a pool status command.')
    status_parser.add_argument('pool_names', nargs='*', help='Optional pool names.')
    status_parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed status.')
    status_parser.add_argument('--all', action='store_true', help='Show all workers.')
    status_parser.set_defaults(func=build_pool_status)

    logs_parser = pool_subparsers.add_parser('logs', help='Print a pool logs command.')
    logs_parser.add_argument('pool_name', help='Pool name.')
    logs_parser.add_argument('worker_ids', nargs='*', help='Optional worker IDs.')
    logs_parser.add_argument('--controller', action='store_true', help='Show controller logs.')
    logs_parser.add_argument('--no-follow', action='store_true', help='Print logs so far and exit.')
    logs_parser.add_argument('--sync-down', action='store_true', help='Download logs.')
    logs_parser.add_argument('--tail', type=int, help='Number of trailing lines to print.')
    logs_parser.set_defaults(func=build_pool_logs)

    down_parser = pool_subparsers.add_parser('down', help='Print a pool down command.')
    down_parser.add_argument('pool_names', nargs='*', help='Pool names or glob patterns.')
    down_parser.add_argument('--all', action='store_true', help='Delete all pools.')
    down_parser.add_argument('--purge', action='store_true', help='Tear down failed pools.')
    down_parser.add_argument('-y', '--yes', action='store_true', help='Add noninteractive confirmation flag.')
    down_parser.set_defaults(func=build_pool_down)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Build safe SkyPilot managed-jobs commands without executing cloud actions.',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)
    add_launch_parser(subparsers)
    add_queue_parser(subparsers)
    add_logs_parser(subparsers)
    add_cancel_parser(subparsers)
    add_pool_parsers(subparsers)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
