#!/usr/bin/env python3
"""Build dry-run Lepton workload command examples.

This helper never executes `lep`. It composes shell-quoted example commands for
endpoint, job, and pod basics so an agent can review a command plan with the
user before any live cloud operation.
"""

from __future__ import annotations

import argparse
import json
import shlex
from dataclasses import dataclass, field
from typing import Iterable, List, Optional


CREATE_ACTIONS = {"create"}
MUTATING_ACTIONS = {"create", "update", "stop", "start", "restart", "remove", "ssh"}


@dataclass
class CommandPlan:
    commands: List[List[str]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add(self, *parts: str) -> None:
        self.commands.append([str(p) for p in parts if p is not None])


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(p)) for p in parts)


def require_for_create(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.action in CREATE_ACTIONS:
        missing = []
        if not args.name:
            missing.append("--name")
        if not args.image:
            missing.append("--image")
        if missing:
            parser.error("create examples require " + " and ".join(missing))


def add_common_create_options(plan: CommandPlan, cmd: List[str], args: argparse.Namespace) -> None:
    if args.resource_shape:
        cmd.extend(["--resource-shape", args.resource_shape])
    if args.command:
        flag = "--command" if args.kind == "job" else "--container-command"
        cmd.extend([flag, args.command])
    if args.port:
        flag = "--container-port"
        cmd.extend([flag, args.port])
    if args.public and args.kind == "endpoint":
        cmd.append("--public")
    if args.node_group:
        cmd.extend(["--node-group", args.node_group])
    if args.replica:
        plan.notes.append("Replica is ignored for create actions; use it with log actions.")


def build_endpoint(args: argparse.Namespace) -> CommandPlan:
    plan = CommandPlan()
    name = args.name or "ENDPOINT_NAME"

    if args.action == "create":
        cmd = ["lep", "endpoint", "create", "-n", name, "--container-image", args.image]
        add_common_create_options(plan, cmd, args)
        plan.add(*cmd)
        if not args.port:
            plan.notes.append("Endpoint containers normally need --container-port PORT[:PROTOCOL] that matches the service listener.")
        if not args.public:
            plan.notes.append("Endpoint access control is not included; add --public, --tokens, or route IP/token planning to the integration skill.")
    elif args.action == "list":
        cmd = ["lep", "endpoint", "list"]
        if args.name:
            cmd.extend(["--name", args.name])
        plan.add(*cmd)
    elif args.action in {"get", "status"}:
        plan.add("lep", "endpoint", args.action, "-n", name)
    elif args.action == "update":
        cmd = ["lep", "endpoint", "update", "-n", name]
        if args.image:
            cmd.extend(["--container-image", args.image])
        if args.resource_shape:
            cmd.extend(["--resource-shape", args.resource_shape])
        if len(cmd) == 5:
            plan.warnings.append("No endpoint update fields supplied; add --image, --resource-shape, or edit this generated command.")
        plan.add(*cmd)
    elif args.action in {"stop", "restart", "remove"}:
        plan.add("lep", "endpoint", args.action, "-n", name)
    elif args.action == "log":
        direct = ["lep", "endpoint", "log", "-n", name]
        if args.replica:
            direct.extend(["--replica", args.replica])
        plan.add(*direct)
        hist = [
            "lep",
            "log",
            "get",
            "--endpoint",
            name,
            "--start",
            args.start or "today",
            "--end",
            args.end or "now",
        ]
        if args.replica:
            hist.extend(["--replica", args.replica])
        plan.add(*hist)
        plan.notes.append("First command is a replica live stream; second is historical time-scoped logs.")
    elif args.action == "events":
        plan.add("lep", "endpoint", "events", "-n", name)
    else:
        plan.warnings.append(f"Action {args.action!r} is not supported for endpoints by this helper.")
    return plan


def build_job(args: argparse.Namespace) -> CommandPlan:
    plan = CommandPlan()
    name = args.name or "JOB_NAME"
    job_id = args.id or args.name or "JOB_ID"

    if args.action == "create":
        cmd = ["lep", "job", "create", "-n", name, "--container-image", args.image]
        if args.resource_shape:
            cmd.extend(["--resource-shape", args.resource_shape])
        else:
            cmd.extend(["--resource-shape", "RESOURCE_SHAPE"])
            plan.warnings.append("Job create requires a resource shape; replace RESOURCE_SHAPE with `lep node resource-shape --purpose job` output.")
        if args.command:
            cmd.extend(["--command", args.command])
        else:
            cmd.extend(["--command", "COMMAND"])
            plan.warnings.append("Job create usually needs --command; replace COMMAND with the script to run.")
        if args.workers:
            cmd.extend(["--num-workers", str(args.workers)])
        if args.port:
            cmd.extend(["--container-port", args.port])
        if args.node_group:
            cmd.extend(["--node-group", args.node_group])
        plan.add(*cmd)
    elif args.action == "list":
        cmd = ["lep", "job", "list"]
        if args.name:
            cmd.extend(["--name-or-id", args.name])
        if args.state:
            cmd.extend(["--state", args.state])
        if args.user:
            cmd.extend(["--user", args.user])
        if args.node_group:
            cmd.extend(["--node-group", args.node_group])
        if args.include_archived:
            cmd.append("--include-archived")
        plan.add(*cmd)
    elif args.action in {"get", "status"}:
        if args.id:
            plan.add("lep", "job", "get", "--id", args.id)
        else:
            plan.add("lep", "job", "get", "--name", name)
            plan.notes.append("Job names are not unique; prefer --id after inspecting `lep job list`.")
    elif args.action in {"stop", "start", "remove"}:
        plan.add("lep", "job", args.action, "--id", job_id)
    elif args.action == "log":
        direct = ["lep", "job", "log", "--id", job_id]
        if args.replica:
            direct.extend(["--replica", args.replica])
        plan.add(*direct)
        hist = ["lep", "log", "get", "--job", job_id]
        if args.start or args.end:
            hist.extend(["--start", args.start, "--end", args.end])
        if args.replica:
            hist.extend(["--replica", args.replica])
        plan.add(*hist)
        plan.notes.append("For jobs, historical logs can infer the job time range when start/end are omitted.")
    elif args.action == "events":
        plan.add("lep", "job", "events", "--id", job_id)
    elif args.action == "replicas":
        plan.add("lep", "job", "replicas", "--id", job_id)
    elif args.action == "nodes":
        plan.add("lep", "job", "nodes", "--id", job_id)
    else:
        plan.warnings.append(f"Action {args.action!r} is not supported for jobs by this helper.")
    return plan


def build_pod(args: argparse.Namespace) -> CommandPlan:
    plan = CommandPlan()
    name = args.name or "POD_NAME"

    if args.action == "create":
        cmd = ["lep", "pod", "create", "-n", name, "--container-image", args.image]
        if args.resource_shape:
            cmd.extend(["--resource-shape", args.resource_shape])
        else:
            cmd.extend(["--resource-shape", "RESOURCE_SHAPE"])
            plan.warnings.append("Pod create requires a resource shape; replace RESOURCE_SHAPE with `lep node resource-shape --purpose pod` output.")
        if args.command:
            cmd.extend(["--container-command", args.command])
        if args.port:
            cmd.extend(["--container-port", args.port])
            plan.notes.append("Pod port syntax is PORT:PROTOCOL:STRATEGY[:STRATEGY], for example 22:tcp:hostmap.")
        if args.node_group:
            cmd.extend(["--node-group", args.node_group])
        plan.add(*cmd)
    elif args.action == "list":
        cmd = ["lep", "pod", "list", "--detail"]
        if args.name:
            cmd.extend(["--pattern", args.name])
        plan.add(*cmd)
    elif args.action in {"get", "status"}:
        plan.add("lep", "pod", "get", "-n", name)
        if args.action == "status":
            plan.notes.append("There is no separate `lep pod status`; use `lep pod get` and `lep pod list --detail`.")
    elif args.action in {"stop", "remove"}:
        plan.add("lep", "pod", args.action, "-n", name)
    elif args.action == "ssh":
        plan.add("lep", "pod", "list", "--detail")
        plan.add("lep", "pod", "ssh", "-n", name)
        plan.warnings.append("`lep pod ssh` opens an SSH subprocess; run it only after the user confirms interactive access.")
    elif args.action == "log":
        plan.add("lep", "pod", "get", "-n", name)
        plan.add("lep", "pod", "list", "--detail")
        plan.warnings.append("This CLI has no `lep pod log` live command; inspect pod state/ports or use platform log export if available.")
    else:
        plan.warnings.append(f"Action {args.action!r} is not supported for pods by this helper.")
    return plan


def build_plan(args: argparse.Namespace) -> CommandPlan:
    if args.kind == "endpoint":
        plan = build_endpoint(args)
    elif args.kind == "job":
        plan = build_job(args)
    elif args.kind == "pod":
        plan = build_pod(args)
    else:  # argparse choices should prevent this
        raise ValueError(args.kind)

    if args.action in MUTATING_ACTIONS:
        plan.warnings.append("Dry-run only: review workspace, cost, and side effects before running any mutating command.")
    return plan


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print dry-run Lepton workload command examples; never executes lep."
    )
    parser.add_argument("--kind", choices=["endpoint", "job", "pod"], required=True)
    parser.add_argument(
        "--action",
        choices=[
            "create",
            "list",
            "get",
            "status",
            "update",
            "stop",
            "start",
            "restart",
            "remove",
            "log",
            "events",
            "ssh",
            "replicas",
            "nodes",
        ],
        default="create",
        help="Command family to compose. Defaults to create.",
    )
    parser.add_argument("--name", help="Workload name or name filter.")
    parser.add_argument("--id", help="Job ID for job actions.")
    parser.add_argument("--image", help="Container image for create/update examples.")
    parser.add_argument("--resource-shape", help="Resource shape for create/update examples.")
    parser.add_argument("--command", help="Container/job command string.")
    parser.add_argument("--port", help="Container port expression; syntax depends on workload kind.")
    parser.add_argument("--replica", help="Replica ID for log examples.")
    parser.add_argument("--public", action="store_true", help="Add --public to endpoint create examples.")
    parser.add_argument("--workers", type=int, help="Number of job workers for create examples.")
    parser.add_argument("--node-group", help="Node group for create/list examples.")
    parser.add_argument("--state", help="Job state filter for list examples.")
    parser.add_argument("--user", help="Job user filter for list examples.")
    parser.add_argument("--include-archived", action="store_true", help="Include archived jobs in list/get examples.")
    parser.add_argument("--start", help="Historical log start time. Endpoint examples default to today when omitted.")
    parser.add_argument("--end", help="Historical log end time. Endpoint examples default to now when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")

    args = parser.parse_args(argv)
    require_for_create(parser, args)
    plan = build_plan(args)

    if args.json:
        print(json.dumps({
            "kind": args.kind,
            "action": args.action,
            "commands": [shell_join(c) for c in plan.commands],
            "warnings": plan.warnings,
            "notes": plan.notes,
            "dry_run": True,
        }, indent=2))
    else:
        print("# Dry-run Lepton workload command plan")
        print(f"kind: {args.kind}")
        print(f"action: {args.action}")
        print("\nCommands:")
        if plan.commands:
            for command in plan.commands:
                print("  " + shell_join(command))
        else:
            print("  (no command generated)")
        if plan.warnings:
            print("\nWarnings:")
            for item in plan.warnings:
                print("  - " + item)
        if plan.notes:
            print("\nNotes:")
            for item in plan.notes:
                print("  - " + item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
