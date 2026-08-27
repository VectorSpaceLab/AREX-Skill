#!/usr/bin/env python3
"""Print safe Prefect deployment and worker commands without executing them."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from typing import Iterable


def quote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts if part is not None and str(part) != "")


def add_common_session_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile", help="Prefect profile to pass to the command.")
    parser.add_argument("--no-prompt", action="store_true", help="Add --no-prompt for noninteractive use.")


def append_common_session_flags(parts: list[str], args: argparse.Namespace) -> None:
    if getattr(args, "profile", None):
        parts.extend(["--profile", args.profile])
    if getattr(args, "no_prompt", False):
        parts.append("--no-prompt")


def add_repeated_key_value(parser: argparse.ArgumentParser, flag: str, dest: str, help_text: str) -> None:
    parser.add_argument(flag, dest=dest, action="append", default=[], metavar="KEY=VALUE", help=help_text)


def append_repeated(parts: list[str], flag: str, values: Iterable[str]) -> None:
    for value in values:
        parts.extend([flag, value])


def parse_json_mapping(value: str, option_name: str) -> str:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"{option_name} must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError(f"{option_name} must be a JSON object")
    return json.dumps(parsed, sort_keys=True, separators=(",", ":"))


def build_deploy(args: argparse.Namespace) -> list[str]:
    parts = ["prefect", "deploy"]
    if args.entrypoint:
        parts.append(args.entrypoint)
    if args.name:
        parts.extend(["--name", args.name])
    if args.description:
        parts.extend(["--description", args.description])
    if args.version:
        parts.extend(["--version", args.version])
    if args.version_type:
        parts.extend(["--version-type", args.version_type])
    for tag in args.tag:
        parts.extend(["--tag", tag])
    if args.pool:
        parts.extend(["--pool", args.pool])
    if args.work_queue:
        parts.extend(["--work-queue", args.work_queue])
    if args.concurrency_limit is not None:
        parts.extend(["--concurrency-limit", str(args.concurrency_limit)])
    if args.collision_strategy:
        parts.extend(["--collision-strategy", args.collision_strategy])
    if args.cron:
        parts.extend(["--cron", args.cron])
    if args.interval:
        parts.extend(["--interval", args.interval])
    if args.anchor_date:
        parts.extend(["--anchor-date", args.anchor_date])
    if args.rrule:
        parts.extend(["--rrule", args.rrule])
    if args.timezone:
        parts.extend(["--timezone", args.timezone])
    append_repeated(parts, "--param", args.param)
    if args.params:
        parts.extend(["--params", args.params])
    append_repeated(parts, "--job-variable", args.job_variable)
    append_repeated(parts, "--trigger", args.trigger)
    if args.prefect_file:
        parts.extend(["--prefect-file", args.prefect_file])
    if args.all:
        parts.append("--all")
    if args.enforce_parameter_schema is not None:
        parts.append("--enforce-parameter-schema" if args.enforce_parameter_schema else "--no-enforce-parameter-schema")
    append_common_session_flags(parts, args)
    return parts


def build_serve(args: argparse.Namespace) -> list[str]:
    parts = ["prefect", "flow", "serve", args.entrypoint, "--name", args.name]
    if args.description:
        parts.extend(["--description", args.description])
    if args.version:
        parts.extend(["--version", args.version])
    for tag in args.tag:
        parts.extend(["--tag", tag])
    if args.cron:
        parts.extend(["--cron", args.cron])
    if args.interval:
        parts.extend(["--interval", args.interval])
    if args.anchor_date:
        parts.extend(["--anchor-date", args.anchor_date])
    if args.rrule:
        parts.extend(["--rrule", args.rrule])
    if args.timezone:
        parts.extend(["--timezone", args.timezone])
    if args.limit is not None:
        parts.extend(["--limit", str(args.limit)])
    if args.global_limit is not None:
        parts.extend(["--global-limit", str(args.global_limit)])
    if args.pause_on_shutdown is not None:
        parts.append("--pause-on-shutdown" if args.pause_on_shutdown else "--no-pause-on-shutdown")
    append_common_session_flags(parts, args)
    return parts


def build_run(args: argparse.Namespace) -> list[str]:
    parts = ["prefect", "deployment", "run"]
    if args.id:
        parts.extend(["--id", args.id])
    else:
        parts.append(args.name)
    append_repeated(parts, "--param", args.param)
    if args.params:
        parts.extend(["--params", args.params])
    append_repeated(parts, "--job-variable", args.job_variable)
    for tag in args.tag:
        parts.extend(["--tag", tag])
    if args.flow_run_name:
        parts.extend(["--flow-run-name", args.flow_run_name])
    if args.start_in:
        parts.extend(["--start-in", args.start_in])
    if args.start_at:
        parts.extend(["--start-at", args.start_at])
    if args.watch is not None:
        parts.append("--watch" if args.watch else "--no-watch")
    if args.watch_interval is not None:
        parts.extend(["--watch-interval", str(args.watch_interval)])
    if args.watch_timeout is not None:
        parts.extend(["--watch-timeout", str(args.watch_timeout)])
    append_common_session_flags(parts, args)
    return parts


def build_worker(args: argparse.Namespace) -> list[str]:
    parts = ["prefect", "worker", "start", "--pool", args.pool]
    if args.name:
        parts.extend(["--name", args.name])
    for queue in args.work_queue:
        parts.extend(["--work-queue", queue])
    if args.type:
        parts.extend(["--type", args.type])
    if args.prefetch_seconds is not None:
        parts.extend(["--prefetch-seconds", str(args.prefetch_seconds)])
    if args.run_once:
        parts.append("--run-once")
    if args.limit is not None:
        parts.extend(["--limit", str(args.limit)])
    if args.with_healthcheck is not None:
        parts.append("--with-healthcheck" if args.with_healthcheck else "--no-with-healthcheck")
    if args.install_policy:
        parts.extend(["--install-policy", args.install_policy])
    if args.base_job_template:
        parts.extend(["--base-job-template", args.base_job_template])
    if args.create_pool_if_not_found is not None:
        parts.append("--create-pool-if-not-found" if args.create_pool_if_not_found else "--no-create-pool-if-not-found")
    append_common_session_flags(parts, args)
    return parts


def build_work_pool(args: argparse.Namespace) -> list[str]:
    parts = ["prefect", "work-pool", args.action, args.name]
    if args.action in {"create", "update"}:
        if args.type:
            parts.extend(["--type", args.type])
        if args.base_job_template:
            parts.extend(["--base-job-template", args.base_job_template])
        if args.description:
            parts.extend(["--description", args.description])
        if args.action == "create":
            if args.paused is not None:
                parts.append("--paused" if args.paused else "--no-paused")
            if args.set_as_default:
                parts.append("--set-as-default")
            if args.overwrite:
                parts.append("--overwrite")
            if args.provision_infrastructure is not None:
                parts.append("--provision-infrastructure" if args.provision_infrastructure else "--no-provision-infrastructure")
    elif args.action == "inspect":
        if args.output:
            parts.extend(["--output", args.output])
    elif args.action == "preview":
        if args.hours is not None:
            parts.extend(["--hours", str(args.hours)])
        if args.output:
            parts.extend(["--output", args.output])
    elif args.action == "set-concurrency-limit":
        if args.concurrency_limit is None:
            raise SystemExit("work-pool set-concurrency-limit requires --concurrency-limit")
        parts.append(str(args.concurrency_limit))
    append_common_session_flags(parts, args)
    return parts


def add_deploy_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("deploy", help="Print a prefect deploy command.")
    parser.set_defaults(builder=build_deploy)
    parser.add_argument("--entrypoint", help="Flow entrypoint such as flows.py:daily_etl.")
    parser.add_argument("--name", "-n", help="Deployment name.")
    parser.add_argument("--description", "-d", help="Deployment description.")
    parser.add_argument("--version", help="Deployment version.")
    parser.add_argument("--version-type", help="Deployment version type.")
    parser.add_argument("--tag", "-t", action="append", default=[], help="Deployment tag; repeatable.")
    parser.add_argument("--pool", "-p", help="Work pool name.")
    parser.add_argument("--work-queue", "-q", help="Work queue name.")
    parser.add_argument("--concurrency-limit", type=int, help="Deployment concurrency limit.")
    parser.add_argument("--collision-strategy", help="Concurrency collision strategy.")
    parser.add_argument("--cron", help="Cron schedule string.")
    parser.add_argument("--interval", help="Interval schedule in seconds or accepted duration string.")
    parser.add_argument("--anchor-date", help="Anchor date for interval schedules.")
    parser.add_argument("--rrule", help="RRule schedule string.")
    parser.add_argument("--timezone", help="Schedule timezone, for example UTC.")
    add_repeated_key_value(parser, "--param", "param", "Parameter override; repeatable KEY=VALUE.")
    parser.add_argument("--params", type=lambda value: parse_json_mapping(value, "--params"), help="JSON object of parameters.")
    add_repeated_key_value(parser, "--job-variable", "job_variable", "Job variable override; repeatable KEY=VALUE or JSON object string.")
    parser.add_argument("--trigger", action="append", default=[], help="Trigger JSON string or trigger file path; repeatable.")
    parser.add_argument("--prefect-file", help="Path to prefect.yaml.")
    parser.add_argument("--all", action="store_true", help="Deploy all deployments from the prefect file.")
    schema_group = parser.add_mutually_exclusive_group()
    schema_group.add_argument("--enforce-parameter-schema", dest="enforce_parameter_schema", action="store_true", default=None)
    schema_group.add_argument("--no-enforce-parameter-schema", dest="enforce_parameter_schema", action="store_false")
    add_common_session_flags(parser)


def add_serve_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("serve", help="Print a prefect flow serve command.")
    parser.set_defaults(builder=build_serve)
    parser.add_argument("--entrypoint", required=True, help="Flow entrypoint such as flows.py:hourly_report.")
    parser.add_argument("--name", "-n", required=True, help="Deployment name.")
    parser.add_argument("--description", "-d", help="Deployment description.")
    parser.add_argument("--version", "-v", help="Deployment version.")
    parser.add_argument("--tag", "-t", action="append", default=[], help="Deployment tag; repeatable.")
    parser.add_argument("--cron", help="Cron schedule string.")
    parser.add_argument("--interval", help="Interval schedule in seconds or accepted duration string.")
    parser.add_argument("--anchor-date", help="Anchor date for interval schedules.")
    parser.add_argument("--rrule", help="RRule schedule string.")
    parser.add_argument("--timezone", help="Schedule timezone.")
    parser.add_argument("--limit", type=int, help="Concurrent run limit for this served flow instance.")
    parser.add_argument("--global-limit", type=int, help="Deployment-level global concurrency limit.")
    pause_group = parser.add_mutually_exclusive_group()
    pause_group.add_argument("--pause-on-shutdown", dest="pause_on_shutdown", action="store_true", default=None)
    pause_group.add_argument("--no-pause-on-shutdown", dest="pause_on_shutdown", action="store_false")
    add_common_session_flags(parser)


def add_run_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("run", help="Print a prefect deployment run command.")
    parser.set_defaults(builder=build_run)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--name", help="Deployment target in FLOW_NAME/DEPLOYMENT_NAME form.")
    target.add_argument("--id", help="Deployment UUID.")
    add_repeated_key_value(parser, "--param", "param", "Parameter override; repeatable KEY=VALUE.")
    parser.add_argument("--params", type=lambda value: parse_json_mapping(value, "--params"), help="JSON object of parameters.")
    add_repeated_key_value(parser, "--job-variable", "job_variable", "Job variable override; repeatable KEY=VALUE.")
    parser.add_argument("--tag", "-t", action="append", default=[], help="Flow run tag; repeatable.")
    parser.add_argument("--flow-run-name", help="Name for the created flow run.")
    parser.add_argument("--start-in", help="Delay before starting, for example '2 hours'.")
    parser.add_argument("--start-at", help="Scheduled start timestamp.")
    watch_group = parser.add_mutually_exclusive_group()
    watch_group.add_argument("--watch", dest="watch", action="store_true", default=None)
    watch_group.add_argument("--no-watch", dest="watch", action="store_false")
    parser.add_argument("--watch-interval", type=float, help="Seconds between watch polls.")
    parser.add_argument("--watch-timeout", type=float, help="Maximum seconds to watch.")
    add_common_session_flags(parser)


def add_worker_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("worker", help="Print a prefect worker start command.")
    parser.set_defaults(builder=build_worker)
    parser.add_argument("--pool", "-p", required=True, help="Work pool to poll.")
    parser.add_argument("--name", "-n", help="Worker name.")
    parser.add_argument("--work-queue", "-q", action="append", default=[], help="Work queue to poll; repeatable.")
    parser.add_argument("--type", "-t", help="Worker type.")
    parser.add_argument("--prefetch-seconds", type=int, help="How far ahead to poll for scheduled runs.")
    parser.add_argument("--run-once", action="store_true", help="Add --run-once for bounded polling.")
    parser.add_argument("--limit", "-l", type=int, help="Maximum concurrent runs submitted by this worker.")
    health_group = parser.add_mutually_exclusive_group()
    health_group.add_argument("--with-healthcheck", dest="with_healthcheck", action="store_true", default=None)
    health_group.add_argument("--no-with-healthcheck", dest="with_healthcheck", action="store_false")
    parser.add_argument("--install-policy", choices=("always", "if-not-present", "never", "prompt"), help="Worker package install policy.")
    parser.add_argument("--base-job-template", help="Base job template file path.")
    pool_group = parser.add_mutually_exclusive_group()
    pool_group.add_argument("--create-pool-if-not-found", dest="create_pool_if_not_found", action="store_true", default=None)
    pool_group.add_argument("--no-create-pool-if-not-found", dest="create_pool_if_not_found", action="store_false")
    add_common_session_flags(parser)


def add_work_pool_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("work-pool", help="Print a prefect work-pool command.")
    parser.set_defaults(builder=build_work_pool)
    parser.add_argument(
        "action",
        choices=("create", "update", "inspect", "preview", "pause", "resume", "set-concurrency-limit", "clear-concurrency-limit"),
        help="Work-pool action to build.",
    )
    parser.add_argument("name", help="Work pool name.")
    parser.add_argument("--type", "-t", help="Work pool type for create/update.")
    parser.add_argument("--base-job-template", help="Base job template file path.")
    parser.add_argument("--description", help="Work pool description for create/update.")
    paused_group = parser.add_mutually_exclusive_group()
    paused_group.add_argument("--paused", dest="paused", action="store_true", default=None)
    paused_group.add_argument("--no-paused", dest="paused", action="store_false")
    parser.add_argument("--set-as-default", action="store_true", help="Set created pool as default.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing pool during create.")
    provision_group = parser.add_mutually_exclusive_group()
    provision_group.add_argument("--provision-infrastructure", dest="provision_infrastructure", action="store_true", default=None)
    provision_group.add_argument("--no-provision-infrastructure", dest="provision_infrastructure", action="store_false")
    parser.add_argument("--output", choices=("json", "yaml"), help="Output format for inspect/preview when supported.")
    parser.add_argument("--hours", type=int, help="Preview horizon in hours.")
    parser.add_argument("--concurrency-limit", type=int, help="Limit for set-concurrency-limit.")
    add_common_session_flags(parser)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Prefect deployment, serve, run, worker, and work-pool commands without executing them.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_deploy_parser(subparsers)
    add_serve_parser(subparsers)
    add_run_parser(subparsers)
    add_worker_parser(subparsers)
    add_work_pool_parser(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.builder(args)
    print(quote_command(command))
    return 0


if __name__ == "__main__":
    sys.exit(main())
