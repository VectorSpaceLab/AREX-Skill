#!/usr/bin/env python3
"""Build a safe, reviewable DGL distributed launch command without running it."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Iterable


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def _workspace_relative(path_value: str, option_name: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        raise argparse.ArgumentTypeError(
            f"{option_name} must be relative to --workspace, not absolute"
        )
    if any(part == ".." for part in path.parts):
        raise argparse.ArgumentTypeError(
            f"{option_name} must not contain '..' path segments"
        )
    return path


def _read_ip_config(path: Path) -> list[tuple[str, int | None]]:
    hosts: list[tuple[str, int | None]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) not in (1, 2):
                raise ValueError(
                    f"{path}: line {line_no} must contain HOST or HOST PORT"
                )
            port = None
            if len(parts) == 2:
                try:
                    port = int(parts[1])
                except ValueError as exc:
                    raise ValueError(
                        f"{path}: line {line_no} port must be an integer"
                    ) from exc
                if not 1 <= port <= 65535:
                    raise ValueError(
                        f"{path}: line {line_no} port must be in 1..65535"
                    )
            hosts.append((parts[0], port))
    if not hosts:
        raise ValueError(f"{path}: no host entries found")
    return hosts


def _read_num_parts(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    num_parts = metadata.get("num_parts")
    if not isinstance(num_parts, int) or num_parts <= 0:
        raise ValueError(f"{path}: num_parts must be a positive integer")
    return num_parts


def _quote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def _launcher_tokens(args: argparse.Namespace) -> list[str]:
    launcher_rel = _workspace_relative(args.launcher_path, "--launcher-path")
    return ["python", str(launcher_rel)]


def build_command(args: argparse.Namespace) -> str:
    part_config = _workspace_relative(args.part_config, "--part-config")
    ip_config = _workspace_relative(args.ip_config, "--ip-config")
    workspace = Path(args.workspace).expanduser()
    part_config_path = workspace / part_config
    ip_config_path = workspace / ip_config

    launcher_path = workspace / _workspace_relative(args.launcher_path, "--launcher-path")

    if args.validate_paths:
        if not workspace.exists() or not workspace.is_dir():
            raise ValueError(f"workspace does not exist or is not a directory: {workspace}")
        if not part_config_path.is_file():
            raise ValueError(f"partition config does not exist: {part_config_path}")
        if not ip_config_path.is_file():
            raise ValueError(f"ip config does not exist: {ip_config_path}")
        if not launcher_path.is_file():
            raise ValueError(
                f"launcher path does not exist under workspace: {launcher_path}"
            )
        host_count = len(_read_ip_config(ip_config_path))
        num_parts = _read_num_parts(part_config_path)
        if host_count != num_parts:
            raise ValueError(
                "host count in ip_config does not match partition config "
                f"num_parts: {host_count} != {num_parts}"
            )

    command = _launcher_tokens(args)
    command.extend(
        [
            "--workspace",
            str(workspace),
            "--num_trainers",
            str(args.num_trainers),
            "--num_samplers",
            str(args.num_samplers),
            "--num_servers",
            str(args.num_servers),
            "--part_config",
            str(part_config),
            "--ip_config",
            str(ip_config),
            "--graph_format",
            args.graph_format,
        ]
    )
    if args.num_omp_threads is not None:
        command.extend(["--num_omp_threads", str(args.num_omp_threads)])
    if args.num_server_threads is not None:
        command.extend(["--num_server_threads", str(args.num_server_threads)])
    if args.ssh_port is not None:
        command.extend(["--ssh_port", str(args.ssh_port)])
    if args.ssh_username:
        command.extend(["--ssh_username", args.ssh_username])
    if args.extra_envs:
        command.append("--extra_envs")
        command.extend(args.extra_envs)
    command.append(args.trainer_command)
    return _quote_command(command)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print a DGL distributed launch command after safe path/count "
            "preflight. This script never SSHes or starts processes."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--workspace",
        required=True,
        help="Shared workspace path that will be passed to DGL launch.py.",
    )
    parser.add_argument(
        "--part-config",
        required=True,
        help="Partition JSON path relative to --workspace.",
    )
    parser.add_argument(
        "--ip-config",
        required=True,
        help="ip_config.txt path relative to --workspace.",
    )
    parser.add_argument(
        "--trainer-command",
        required=True,
        help="Quoted Python trainer command to pass as the launcher's final argument.",
    )
    parser.add_argument(
        "--num-trainers",
        type=_positive_int,
        default=1,
        help="Trainer processes per machine.",
    )
    parser.add_argument(
        "--num-samplers",
        type=_non_negative_int,
        default=0,
        help="Sampler processes per trainer.",
    )
    parser.add_argument(
        "--num-servers",
        type=_positive_int,
        default=1,
        help="DGL graph server processes per machine.",
    )
    parser.add_argument(
        "--num-omp-threads",
        type=_positive_int,
        help="OMP threads per trainer; omit to let DGL estimate.",
    )
    parser.add_argument(
        "--num-server-threads",
        type=_positive_int,
        help="OMP threads per server.",
    )
    parser.add_argument(
        "--graph-format",
        default="csc",
        help="Partition graph format, e.g. csc, csr, coo, or comma-separated.",
    )
    parser.add_argument("--ssh-port", type=_positive_int, help="SSH port.")
    parser.add_argument("--ssh-username", default="", help="Optional SSH username.")
    parser.add_argument(
        "--extra-envs",
        nargs="*",
        default=[],
        metavar="KEY=VALUE",
        help="Extra environment entries for DGL launch.py.",
    )
    parser.add_argument(
        "--launcher-path",
        default="tools/launch.py",
        help=(
            "Workspace-relative DGL launcher path to include in the printed command. "
            "The default mirrors DGL's source-tree launcher syntax."
        ),
    )
    parser.add_argument(
        "--no-validate-paths",
        action="store_false",
        dest="validate_paths",
        help="Skip local existence and num_parts-vs-ip_config preflight.",
    )
    parser.set_defaults(validate_paths=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        print(build_command(args))
    except Exception as exc:  # noqa: BLE001 - CLI should report concise failures.
        print(f"ERROR: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
