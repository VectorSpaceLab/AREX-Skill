#!/usr/bin/env python3
"""Build safe SkyPilot interactive-cluster command suggestions."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence


@dataclass(frozen=True)
class CommandPlan:
    description: str
    argv: List[str]
    category: str = 'read'


def _add_common_options(command: List[str], args: argparse.Namespace) -> None:
    option_pairs = [
        ('infra', '--infra'),
        ('num_nodes', '--num-nodes'),
        ('cpus', '--cpus'),
        ('memory', '--memory'),
        ('disk_size', '--disk-size'),
        ('disk_tier', '--disk-tier'),
        ('network_tier', '--network-tier'),
        ('gpus', '--gpus'),
        ('instance_type', '--instance-type'),
        ('image_id', '--image-id'),
        ('local_disk', '--local-disk'),
        ('workdir', '--workdir'),
        ('name', '--name'),
    ]
    for attribute, flag in option_pairs:
        value = getattr(args, attribute, None)
        if value is not None:
            command.extend([flag, str(value)])
    if getattr(args, 'use_spot', False):
        command.append('--use-spot')
    if getattr(args, 'no_setup', False):
        command.append('--no-setup')
    for port in getattr(args, 'ports', None) or []:
        command.extend(['--ports', str(port)])
    for env_var in getattr(args, 'env', None) or []:
        command.extend(['--env', env_var])
    for secret_name in getattr(args, 'secret_env', None) or []:
        command.extend(['--secret', secret_name])
    for config_value in getattr(args, 'config', None) or []:
        command.extend(['--config', config_value])


def _entrypoint_args(args: argparse.Namespace) -> List[str]:
    task_yaml = getattr(args, 'task_yaml', None)
    entrypoint_command = getattr(args, 'entrypoint_command', None)
    if task_yaml:
        return [task_yaml]
    if entrypoint_command:
        return ['bash', '-lc', entrypoint_command]
    return []


def _exec_entrypoint_args(args: argparse.Namespace) -> List[str]:
    exec_command = getattr(args, 'exec_command', None)
    if exec_command:
        return ['bash', '-lc', exec_command]
    return _entrypoint_args(args)


def _launch_command(args: argparse.Namespace, dryrun: bool) -> List[str]:
    command = ['sky', 'launch']
    if dryrun:
        command.append('--dryrun')
    if args.cluster:
        command.extend(['-c', args.cluster])
    _add_common_options(command, args)
    if getattr(args, 'detach_run', False):
        command.append('--detach-run')
    idle_minutes = getattr(args, 'idle_minutes', None)
    if idle_minutes is not None and not dryrun:
        command.extend(['--idle-minutes-to-autostop', str(idle_minutes)])
        if getattr(args, 'wait_for', None):
            command.extend(['--wait-for', args.wait_for])
    if getattr(args, 'down_after_idle', False) and not dryrun:
        command.append('--down')
    if getattr(args, 'retry_until_up', False):
        command.append('--retry-until-up')
    command.extend(_entrypoint_args(args))
    return command


def _exec_command(args: argparse.Namespace) -> List[str]:
    command = ['sky', 'exec']
    _add_common_options(command, args)
    if getattr(args, 'detach_run', False):
        command.append('--detach-run')
    command.append(args.cluster)
    command.extend(_exec_entrypoint_args(args))
    return command


def _status_command(args: argparse.Namespace, refresh: bool = False) -> List[str]:
    command = ['sky', 'status']
    if refresh:
        command.append('--refresh')
    if getattr(args, 'status_json', True):
        command.extend(['-o', 'json'])
    if args.cluster:
        command.append(args.cluster)
    return command


def _queue_command(args: argparse.Namespace) -> List[str]:
    command = ['sky', 'queue']
    if getattr(args, 'skip_finished', False):
        command.append('--skip-finished')
    if getattr(args, 'queue_json', True):
        command.extend(['-o', 'json'])
    if args.cluster:
        command.append(args.cluster)
    return command


def _logs_command(args: argparse.Namespace, provision: bool = False) -> List[str]:
    command = ['sky', 'logs']
    if provision:
        command.append('--provision')
    if getattr(args, 'no_follow', True):
        command.append('--no-follow')
    tail = getattr(args, 'tail', None)
    if tail is not None:
        command.extend(['--tail', str(tail)])
    if args.cluster:
        command.append(args.cluster)
    job_id = getattr(args, 'job_id', None)
    if job_id is not None and not provision:
        command.append(str(job_id))
    return command


def _autostop_command(args: argparse.Namespace, down: bool = False) -> List[str]:
    command = ['sky', 'autostop', args.cluster, '-i', str(args.idle_minutes)]
    if getattr(args, 'wait_for', None):
        command.extend(['--wait-for', args.wait_for])
    if down:
        command.append('--down')
    return command


def _cancel_autostop_command(args: argparse.Namespace) -> List[str]:
    return ['sky', 'autostop', args.cluster, '--cancel']


def _stop_command(args: argparse.Namespace) -> List[str]:
    command = ['sky', 'stop', args.cluster]
    if getattr(args, 'graceful', False):
        command.append('--graceful')
        timeout = getattr(args, 'graceful_timeout', None)
        if timeout is not None:
            command.extend(['--graceful-timeout', str(timeout)])
    return command


def _start_command(args: argparse.Namespace) -> List[str]:
    command = ['sky', 'start', args.cluster]
    idle_minutes = getattr(args, 'idle_minutes', None)
    if idle_minutes is not None:
        command.extend(['-i', str(idle_minutes)])
        if getattr(args, 'wait_for', None):
            command.extend(['--wait-for', args.wait_for])
    if getattr(args, 'force', False):
        command.append('--force')
    if getattr(args, 'retry_until_up', False):
        command.append('--retry-until-up')
    return command


def _down_command(args: argparse.Namespace) -> List[str]:
    command = ['sky', 'down', args.cluster]
    if getattr(args, 'graceful', False):
        command.append('--graceful')
        timeout = getattr(args, 'graceful_timeout', None)
        if timeout is not None:
            command.extend(['--graceful-timeout', str(timeout)])
    if getattr(args, 'purge', False):
        command.append('--purge')
    return command


def _cost_command(args: argparse.Namespace) -> List[str]:
    command = ['sky', 'cost-report', '--days', str(args.days)]
    if getattr(args, 'cost_json', True):
        command.extend(['-o', 'json'])
    return command


def _debug_cycle(args: argparse.Namespace) -> List[CommandPlan]:
    plans = [
        CommandPlan('Validate the launch plan without provisioning cloud resources.',
                    _launch_command(args, dryrun=True), 'dryrun'),
    ]
    if args.ready_to_launch:
        category = 'launch destructive' if args.down_after_idle else 'launch'
        plans.append(
            CommandPlan('Launch or reuse the named cluster after dry-run review.',
                        _launch_command(args, dryrun=False), category))
    plans.extend([
        CommandPlan('Inspect current cluster state in JSON.',
                    _status_command(args, refresh=True), 'read'),
        CommandPlan('Run the debug command or task on the existing cluster.',
                    _exec_command(args), 'mutation'),
        CommandPlan('Inspect cluster-local job queue in JSON.',
                    _queue_command(args), 'read'),
        CommandPlan('Fetch recent job logs without blocking.',
                    _logs_command(args), 'read'),
        CommandPlan('Ensure restartable cleanup after the debug session.',
                    _autostop_command(args), 'mutation'),
    ])
    if args.cleanup == 'stop':
        plans.append(CommandPlan('Stop compute while preserving restartable disk state.',
                                 _stop_command(args), 'mutation'))
    elif args.cleanup == 'down':
        plans.append(CommandPlan('Destroy the cluster after confirming disk state is no longer needed.',
                                 _down_command(args), 'destructive'))
    return plans


def _launch_plan(args: argparse.Namespace) -> List[CommandPlan]:
    plans = [
        CommandPlan('Validate the launch plan without provisioning cloud resources.',
                    _launch_command(args, dryrun=True), 'dryrun')
    ]
    if args.ready_to_launch:
        category = 'launch destructive' if args.down_after_idle else 'launch'
        plans.append(
            CommandPlan('Launch or reuse the named cluster after dry-run review.',
                        _launch_command(args, dryrun=False), category))
    return plans


def _inspect_plan(args: argparse.Namespace) -> List[CommandPlan]:
    plans = [
        CommandPlan('Inspect cluster state in JSON.',
                    _status_command(args, refresh=args.refresh), 'read'),
        CommandPlan('Inspect cluster-local job queue in JSON.',
                    _queue_command(args), 'read'),
        CommandPlan('Fetch recent job logs without blocking.',
                    _logs_command(args), 'read'),
    ]
    if args.provision_logs:
        plans.append(CommandPlan('Fetch recent provisioning logs.',
                                 _logs_command(args, provision=True), 'read'))
    if args.include_cost:
        plans.append(CommandPlan('Estimate recent cluster costs from local history.',
                                 _cost_command(args), 'read'))
    return plans


def _lifecycle_plan(args: argparse.Namespace) -> List[CommandPlan]:
    if args.action == 'autostop':
        return [CommandPlan('Schedule restartable autostop.',
                            _autostop_command(args), 'mutation')]
    if args.action == 'autodown':
        return [CommandPlan('Schedule destructive autodown after idle time.',
                            _autostop_command(args, down=True), 'destructive')]
    if args.action == 'cancel-autostop':
        return [CommandPlan('Cancel active auto-stop/down settings.',
                            _cancel_autostop_command(args), 'mutation')]
    if args.action == 'stop':
        return [CommandPlan('Stop compute while preserving restartable disk state.',
                            _stop_command(args), 'mutation')]
    if args.action == 'start':
        return [CommandPlan('Restart a stopped or INIT cluster.',
                            _start_command(args), 'mutation')]
    if args.action == 'down':
        return [CommandPlan('Destroy the cluster after confirming disk state is no longer needed.',
                            _down_command(args), 'destructive')]
    raise ValueError(f'Unsupported lifecycle action: {args.action}')


def _render(plans: Iterable[CommandPlan]) -> str:
    sections = []
    for plan in plans:
        sections.append(f'# {plan.description}\n{shlex.join(plan.argv)}')
    return '\n\n'.join(sections)


def _execution_error(plan: CommandPlan, args: argparse.Namespace) -> Optional[str]:
    categories = set(plan.category.split())
    if 'launch' in categories and not args.allow_launch:
        return 'refusing to execute non-dryrun launch without --allow-launch'
    if 'mutation' in categories and not args.allow_mutation:
        return 'refusing to execute mutating command without --allow-mutation'
    if 'destructive' in categories and not args.allow_destructive:
        return 'refusing to execute destructive command without --allow-destructive'
    return None


def _execute(plans: Sequence[CommandPlan], args: argparse.Namespace) -> int:
    for plan in plans:
        error = _execution_error(plan, args)
        if error is not None:
            print(f'ERROR: {error}: {shlex.join(plan.argv)}', file=sys.stderr)
            return 2
    for plan in plans:
        print(f'## {plan.description}', file=sys.stderr)
        print(shlex.join(plan.argv), file=sys.stderr)
        completed = subprocess.run(plan.argv, check=False)
        if completed.returncode != 0:
            return completed.returncode
    return 0


def _add_execution_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--execute', action='store_true',
                        help='Run generated commands. Default is print-only.')
    parser.add_argument('--allow-launch', action='store_true',
                        help='Allow executing non-dryrun sky launch commands.')
    parser.add_argument('--allow-mutation', action='store_true',
                        help='Allow executing exec, autostop, start, stop, or cancel commands.')
    parser.add_argument('--allow-destructive', action='store_true',
                        help='Allow executing down/autodown commands.')


def _add_resource_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--infra', help='Optional infrastructure pin, e.g. aws/us-east-1 or k8s/context.')
    parser.add_argument('--num-nodes', type=int, help='Number of nodes for the task or cluster.')
    parser.add_argument('--cpus', help='CPU requirement, e.g. 8 or 8+.')
    parser.add_argument('--memory', help='Memory requirement in GB, e.g. 32 or 32+.')
    parser.add_argument('--disk-size', type=int, help='OS disk size in GB.')
    parser.add_argument('--disk-tier', choices=['low', 'medium', 'high', 'ultra', 'best', 'none'], help='OS disk tier.')
    parser.add_argument('--network-tier', choices=['standard', 'best'], help='Network tier.')
    parser.add_argument('--gpus', help='Accelerator requirement, e.g. A100:1.')
    parser.add_argument('--instance-type', help='Exact instance type. Prefer resource constraints unless needed.')
    parser.add_argument('--image-id', help='Custom image id, or none to reset a YAML value.')
    parser.add_argument('--local-disk', help='Local disk requirement, e.g. nvme:1000+.')
    parser.add_argument('--ports', action='append', help='Port, range, or comma-separated ports. Repeatable.')
    parser.add_argument('--use-spot', action='store_true', help='Request spot instances.')
    parser.add_argument('--env', action='append', help='Environment variable assignment or inherited variable. Repeatable.')
    parser.add_argument('--secret-env', action='append', help='Secret environment variable name to inherit. Repeatable.')
    parser.add_argument('--config', action='append', help='SkyPilot config file or key=value override. Repeatable.')
    parser.add_argument('--workdir', help='Local workdir to sync before run commands.')
    parser.add_argument('--name', help='Task name override.')


def _add_entrypoint_options(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--task-yaml', help='Task YAML entrypoint.')
    group.add_argument('--entrypoint-command', help='Shell command entrypoint, wrapped as bash -lc.')


def _add_lifecycle_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--idle-minutes', type=int, default=30,
                        help='Idle minutes for launch/start/autostop suggestions.')
    parser.add_argument('--wait-for', choices=['jobs_and_ssh', 'jobs', 'none'],
                        help='Condition that resets idleness timer.')
    parser.add_argument('--down-after-idle', action='store_true',
                        help='Use autodown instead of autostop on launch suggestions.')
    parser.add_argument('--graceful', action='store_true',
                        help='Wait for MOUNT_CACHED uploads before stop/down.')
    parser.add_argument('--graceful-timeout', type=int,
                        help='Timeout seconds for graceful stop/down.')
    parser.add_argument('--retry-until-up', action='store_true',
                        help='Retry provisioning until resources become available.')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Build safe SkyPilot interactive-cluster command suggestions. Prints only by default.')
    subparsers = parser.add_subparsers(dest='subcommand', required=True)

    debug_parser = subparsers.add_parser(
        'debug-cycle', help='Plan launch, exec, status, logs, autostop, and optional cleanup commands.')
    debug_parser.add_argument('--cluster', required=True, help='Cluster name to create, reuse, inspect, or clean up.')
    _add_entrypoint_options(debug_parser)
    debug_parser.add_argument('--exec-command',
                              help='Shell command for the exec step; useful when launch uses a YAML but debugging runs a direct command.')
    _add_resource_options(debug_parser)
    _add_lifecycle_options(debug_parser)
    debug_parser.add_argument('--ready-to-launch', action='store_true',
                              help='Also print a real launch command after the dry-run command.')
    debug_parser.add_argument('--no-setup', action='store_true', help='Skip setup on launch suggestions.')
    debug_parser.add_argument('--detach-run', action='store_true', help='Detach run and inspect with queue/logs later.')
    debug_parser.add_argument('--job-id', type=int, help='Job id for logs; omitted means latest job.')
    debug_parser.add_argument('--tail', type=int, default=200, help='Log tail line count.')
    debug_parser.add_argument('--skip-finished', action='store_true', help='Show only pending/running jobs in queue.')
    debug_parser.add_argument('--cleanup', choices=['none', 'stop', 'down'], default='none',
                              help='Optional final cleanup command to include after autostop.')
    _add_execution_options(debug_parser)
    debug_parser.set_defaults(plan_builder=_debug_cycle)

    launch_parser = subparsers.add_parser('launch', help='Plan a dry-run launch and optional real launch.')
    launch_parser.add_argument('--cluster', required=True, help='Cluster name to create or reuse.')
    _add_entrypoint_options(launch_parser)
    _add_resource_options(launch_parser)
    _add_lifecycle_options(launch_parser)
    launch_parser.add_argument('--ready-to-launch', action='store_true',
                               help='Also print a real launch command after the dry-run command.')
    launch_parser.add_argument('--no-setup', action='store_true', help='Skip setup on launch suggestions.')
    launch_parser.add_argument('--detach-run', action='store_true', help='Detach run and inspect with queue/logs later.')
    _add_execution_options(launch_parser)
    launch_parser.set_defaults(plan_builder=_launch_plan)

    inspect_parser = subparsers.add_parser('inspect', help='Plan read-only status, queue, logs, and cost checks.')
    inspect_parser.add_argument('--cluster', required=True, help='Cluster name to inspect.')
    inspect_parser.add_argument('--refresh', action='store_true', help='Refresh status from cloud providers.')
    inspect_parser.add_argument('--job-id', type=int, help='Job id for logs; omitted means latest job.')
    inspect_parser.add_argument('--tail', type=int, default=200, help='Log tail line count.')
    inspect_parser.add_argument('--skip-finished', action='store_true', help='Show only pending/running jobs in queue.')
    inspect_parser.add_argument('--provision-logs', action='store_true', help='Include provisioning log command.')
    inspect_parser.add_argument('--include-cost', action='store_true', help='Include cost-report command.')
    inspect_parser.add_argument('--days', type=int, default=7, help='Days for cost-report if included.')
    _add_execution_options(inspect_parser)
    inspect_parser.set_defaults(plan_builder=_inspect_plan)

    lifecycle_parser = subparsers.add_parser('lifecycle', help='Plan one lifecycle command.')
    lifecycle_parser.add_argument('--cluster', required=True, help='Cluster name to operate on.')
    lifecycle_parser.add_argument('action', choices=['autostop', 'autodown', 'cancel-autostop', 'stop', 'start', 'down'],
                                  help='Lifecycle action to plan.')
    _add_lifecycle_options(lifecycle_parser)
    lifecycle_parser.add_argument('--force', action='store_true', help='Force start even if the cluster is already UP.')
    lifecycle_parser.add_argument('--purge', action='store_true', help='Advanced: purge local cluster table state on down.')
    _add_execution_options(lifecycle_parser)
    lifecycle_parser.set_defaults(plan_builder=_lifecycle_plan)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    plans = args.plan_builder(args)
    print(_render(plans))
    if args.execute:
        return _execute(plans, args)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
