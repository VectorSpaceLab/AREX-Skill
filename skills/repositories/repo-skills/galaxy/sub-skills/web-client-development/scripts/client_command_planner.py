#!/usr/bin/env python3
"""Print safe Galaxy client command plans without running pnpm or make."""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CommandPlan:
    title: str
    cwd: str
    commands: tuple[str, ...]
    prerequisites: tuple[str, ...]
    cautions: tuple[str, ...]
    followups: tuple[str, ...] = ()


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts if part)


def make_env_command(env: dict[str, str], command: str) -> str:
    prefix = " ".join(f"{key}={shlex.quote(value)}" for key, value in env.items() if value)
    return f"{prefix} {command}" if prefix else command


def plan_for(args: argparse.Namespace) -> CommandPlan:
    path = args.path
    env: dict[str, str] = {}
    if args.galaxy_url:
        env["GALAXY_URL"] = args.galaxy_url
    if args.change_origin:
        env["CHANGE_ORIGIN"] = "true"
    if args.vite_port:
        env["VITE_PORT"] = str(args.vite_port)

    if args.task == "dev-build":
        return CommandPlan(
            title="Development client build",
            cwd="Galaxy repository root",
            commands=("make client",),
            prerequisites=("Compatible Node.js and pnpm are available, often through the Galaxy environment.",),
            cautions=("This can install/stage dependencies and build bundles; ask before running in an unprepared checkout.",),
            followups=("Run targeted Vitest or type-check commands for changed UI code if validation is needed.",),
        )

    if args.task == "prod-build":
        command = "make client-production-maps" if args.sourcemaps else "make client-production"
        return CommandPlan(
            title="Production client build",
            cwd="Galaxy repository root",
            commands=(command,),
            prerequisites=("Client dependencies are installed or the make target is allowed to prepare them.",),
            cautions=("Production builds are heavier than targeted tests; confirm the user wants deployment-like validation.",),
        )

    if args.task == "dev-server":
        client_command = make_env_command(env, "pnpm run develop")
        root_env = {key: value for key, value in env.items() if key in {"GALAXY_URL", "CHANGE_ORIGIN"}}
        root_command = make_env_command(root_env, "make client-dev-server")
        return CommandPlan(
            title="Vite dev-server proxy",
            cwd="Galaxy repository root for make, or client/ for pnpm",
            commands=(root_command, f"cd client && {client_command}"),
            prerequisites=("A Galaxy backend is running, or will be started separately with client build skipped.",),
            cautions=(
                "Use GALAXY_URL when the backend is not on the default local port.",
                "Use CHANGE_ORIGIN=true only when intentionally proxying to a remote origin.",
                "Use VITE_PORT when the default Vite port is occupied.",
            ),
            followups=("For a separate backend, run make skip-client or GALAXY_SKIP_CLIENT_BUILD=1 ./run.sh.",),
        )

    if args.task == "test-file":
        pattern = path or "<component-or-test-pattern>"
        return CommandPlan(
            title="Targeted Vitest run",
            cwd="client/",
            commands=(shell_join(("pnpm", "test:watch", pattern)), shell_join(("pnpm", "test", pattern))),
            prerequisites=("Client dependencies are already installed.", "Use a .test.ts/.test.js file or a narrow Vitest pattern."),
            cautions=("Prefer the watch command while developing; run non-watch only for final validation or automation.",),
            followups=("If API calls are involved, add MSW/OpenAPI handlers with useServerMock.",),
        )

    if args.task == "test-all":
        return CommandPlan(
            title="Full client unit tests",
            cwd="client/ or Galaxy repository root",
            commands=("pnpm test", "make client-test"),
            prerequisites=("Client dependencies are installed and the workspace package postinstall/build is complete.",),
            cautions=("This can take longer than targeted Vitest; ask before running all tests.",),
            followups=("Run pnpm run type-check if TypeScript/Vue declarations changed.",),
        )

    if args.task == "lint-format":
        return CommandPlan(
            title="Client lint and format checks",
            cwd="client/ or Galaxy repository root",
            commands=("pnpm run eslint", "pnpm run format-check", "make client-lint", "make client-format"),
            prerequisites=("Client dependencies are installed.",),
            cautions=("Formatting commands may rewrite many files; prefer check commands first unless formatting is requested.",),
        )

    if args.task == "type-check":
        return CommandPlan(
            title="Vue TypeScript check",
            cwd="client/",
            commands=("pnpm run type-check",),
            prerequisites=("The API-client workspace package has built declarations available.",),
            cautions=("If declarations are missing, build @galaxyproject/galaxy-api-client before assuming app code is broken.",),
        )

    if args.task == "api-client-build":
        return CommandPlan(
            title="API-client package build/test",
            cwd="client/",
            commands=(
                "pnpm --filter @galaxyproject/galaxy-api-client run build",
                "pnpm --filter @galaxyproject/galaxy-api-client test",
            ),
            prerequisites=("Workspace dependencies are installed.",),
            cautions=("This validates the package only; backend endpoint semantics and schema generation are separate.",),
            followups=("Use make update-client-api-schema from the Galaxy root if backend OpenAPI changed.",),
        )

    if args.task == "api-schema-update":
        return CommandPlan(
            title="Generated OpenAPI client schema update",
            cwd="Galaxy repository root",
            commands=("make update-client-api-schema",),
            prerequisites=("Python and client build dependencies are available; backend OpenAPI generation can run.",),
            cautions=(
                "This updates generated schema files; review diffs and do not hand-edit generated output.",
                "Route backend endpoint semantics to the API automation skill.",
            ),
            followups=("Run targeted API-client/client tests after schema regeneration.",),
        )

    raise ValueError(f"Unhandled task: {args.task}")


def print_plan(plan: CommandPlan) -> None:
    print(f"# {plan.title}")
    print(f"Working directory: {plan.cwd}")
    print()
    print("Commands:")
    for command in plan.commands:
        print(f"  {command}")
    print()
    print("Prerequisites:")
    for item in plan.prerequisites:
        print(f"  - {item}")
    print()
    print("Cautions:")
    for item in plan.cautions:
        print(f"  - {item}")
    if plan.followups:
        print()
        print("Follow-ups:")
        for item in plan.followups:
            print(f"  - {item}")
    print()
    print("This planner is read-only and did not run any command.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print safe command plans for Galaxy web-client development without executing pnpm or make.",
    )
    parser.add_argument(
        "--task",
        choices=(
            "dev-build",
            "prod-build",
            "dev-server",
            "test-file",
            "test-all",
            "lint-format",
            "type-check",
            "api-client-build",
            "api-schema-update",
        ),
        default="test-file",
        help="Client task to plan. Default: test-file.",
    )
    parser.add_argument("--path", help="Optional test file or Vitest pattern for --task test-file.")
    parser.add_argument("--galaxy-url", help="Backend Galaxy URL for dev-server proxy planning.")
    parser.add_argument("--change-origin", action="store_true", help="Include CHANGE_ORIGIN=true for remote proxy targets.")
    parser.add_argument("--vite-port", type=int, help="Vite dev-server port to include in the plan.")
    parser.add_argument("--sourcemaps", action="store_true", help="Use production build target with sourcemaps.")
    parser.add_argument(
        "--repo-root",
        default=os.getcwd(),
        help="Optional repository root label for caller context; not inspected or modified.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    plan = plan_for(args)
    print_plan(plan)
    return 0


if __name__ == "__main__":
    sys.exit(main())
