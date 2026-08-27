#!/usr/bin/env python3
"""Print VLA-Adapter ALOHA server/client launch commands without executing them."""

from __future__ import annotations
import argparse
import os
import shlex
import sys
from pathlib import Path
from typing import Sequence

DEFAULT_TASK_LABEL = (
    "Use the right arm to stack the red bowl on the blue one, then use the left arm to place the stack on the shelf."
)

NATIVE_ENTRYPOINTS = {
    "msgpack-server": "experiments/robot/server_deploy/deploy.py",
    "json-server": "vla-scripts/deploy.py",
    "fake-client": "experiments/robot/aloha/run_fake_cobot_client.py",
    "real-client": "experiments/robot/aloha/run_cobot_client.py",
}


def port_number(value: str) -> int:
    """Parse a TCP port accepted by the native server (1 through 65535)."""
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer in the range 1..65535") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("must be in the range 1..65535")
    return port


def resolve_checkpoint(repo_root: str, checkpoint: str) -> str:
    """Resolve a checkpoint relative to the checkout, warning but never requiring it."""
    checkpoint_path = Path(os.path.expanduser(checkpoint))
    if not checkpoint_path.is_absolute():
        checkpoint_path = Path(repo_root) / checkpoint_path
    checkpoint_path = checkpoint_path.resolve(strict=False)
    if not checkpoint_path.exists():
        print(
            f"WARNING: checkpoint path does not exist yet: {checkpoint_path} "
            "(this command builder does not require a real checkpoint).",
            file=sys.stderr,
        )
    return str(checkpoint_path)


def warn_missing_entrypoints(repo_root: str, entrypoint_keys: Sequence[str]) -> None:
    """Report missing native files without turning command rendering into execution."""
    root = Path(repo_root)
    seen = set()
    for key in entrypoint_keys:
        relative_path = NATIVE_ENTRYPOINTS[key]
        if relative_path in seen:
            continue
        seen.add(relative_path)
        entrypoint = root / relative_path
        if not entrypoint.is_file():
            print(
                f"WARNING: native entrypoint is missing: {entrypoint}. "
                "Review the checkout before running the rendered command.",
                file=sys.stderr,
            )



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build ALOHA deployment commands for review.")
    parser.add_argument("mode", nargs="?", choices=["server", "fake-client", "real-client", "all"], default="all")
    parser.add_argument("--repo-root", required=True, help="Absolute VLA-Adapter source checkout root; generated commands run from here.")
    parser.add_argument("--server-kind", choices=["msgpack", "json", "both"], default="both")
    parser.add_argument("--python", default="python")
    parser.add_argument("--checkpoint", default="checkpoint_dir", help="Checkpoint path; relative paths resolve from --repo-root.")
    parser.add_argument("--msgpack-port", type=port_number, default=8888)
    parser.add_argument("--json-port", type=port_number, default=8777)
    parser.add_argument("--device", default="0", help="Forwarded only to the MsgPack server; native semantics apply.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--server-url", default="http://127.0.0.1:8888", help="Client URL; any explicit port must be 1..65535.")
    parser.add_argument("--task-label", default=DEFAULT_TASK_LABEL)
    parser.add_argument("--unnorm-key", default="bowl_stack_and_shelf_aloha_realworld_50")
    parser.add_argument("--model-family", default="openvla")
    return parser.parse_args()


def validate_server_url(url: str) -> None:
    """Reject an explicitly supplied client URL port outside the TCP range."""
    from urllib.parse import urlparse

    parsed = urlparse(url if "://" in url else f"//{url}")
    try:
        port = parsed.port
    except ValueError as exc:
        raise SystemExit(f"--server-url has an invalid port: {exc}") from exc
    if port is not None and not 1 <= port <= 65535:
        raise SystemExit("--server-url port must be in the range 1..65535")


def render(parts: Sequence[str]) -> str:
    return shlex.join([str(part) for part in parts])


def emit(label: str, parts: Sequence[str], repo_root: str) -> None:
    print(f"[{label}] cd {shlex.quote(repo_root)} && {render(parts)}")


def main() -> int:
    args = parse_args()
    validate_server_url(args.server_url)
    if not os.path.isabs(args.repo_root):
        raise SystemExit("--repo-root must be an absolute VLA-Adapter source checkout path")

    checkpoint = resolve_checkpoint(args.repo_root, args.checkpoint)
    entrypoint_keys = []
    print("# NOTE: --device is forwarded only to the MsgPack server; native downstream semantics determine its effect (it does not alter JSON or client commands).")
    if args.mode in {"server", "all"}:
        if args.server_kind in {"msgpack", "both"}:
            entrypoint_keys.append("msgpack-server")
            msgpack_parts = [
                args.python,
                NATIVE_ENTRYPOINTS["msgpack-server"],
                "--pretrained_checkpoint",
                checkpoint,
                "--model_family",
                args.model_family,
                "--port",
                args.msgpack_port,
                "--device",
                args.device,
            ]
            if args.host != "0.0.0.0":
                msgpack_parts.extend(["--host", args.host])
            emit("MsgPack server", msgpack_parts, args.repo_root)

        if args.server_kind in {"json", "both"}:
            entrypoint_keys.append("json-server")
            json_parts = [
                args.python,
                NATIVE_ENTRYPOINTS["json-server"],
                "--pretrained_checkpoint",
                checkpoint,
                "--model_family",
                args.model_family,
                "--unnorm_key",
                args.unnorm_key,
                "--port",
                args.json_port,
            ]
            if args.host != "0.0.0.0":
                json_parts.extend(["--host", args.host])
            emit("JSON server", json_parts, args.repo_root)

    if args.mode in {"fake-client", "all"}:
        entrypoint_keys.append("fake-client")
        fake_parts = [
            args.python,
            NATIVE_ENTRYPOINTS["fake-client"],
            "--use_vla_server",
            "--vla_server_url",
            args.server_url,
            "--model_family",
            args.model_family,
            "--unnorm_key",
            args.unnorm_key,
            "--task_label",
            args.task_label,
        ]
        emit("Fake client", fake_parts, args.repo_root)

    if args.mode in {"real-client", "all"}:
        entrypoint_keys.append("real-client")
        real_parts = [
            args.python,
            NATIVE_ENTRYPOINTS["real-client"],
            "--use_vla_server",
            "--vla_server_url",
            args.server_url,
            "--model_family",
            args.model_family,
            "--unnorm_key",
            args.unnorm_key,
            "--task_label",
            args.task_label,
        ]
        emit("Real client", real_parts, args.repo_root)
        print("# SAFETY: run the real client only in a ROS robot environment with operator supervision.")

    warn_missing_entrypoints(args.repo_root, entrypoint_keys)
    print("# This script prints commands only; it does not start a server or robot client.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
