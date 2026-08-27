#!/usr/bin/env python3
"""Print a SimpleTuner training command without running it.

The helper is deterministic and side-effect free: it only parses arguments and
prints a shell command. Put downstream SimpleTuner training options after `--`.
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import PurePosixPath
from typing import Iterable

VALID_BACKENDS = {"env", "json", "toml", "cmd"}


def _infer_backend_from_path(path_text: str | None) -> str | None:
    if not path_text:
        return None
    suffix = PurePosixPath(path_text).suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix == ".toml":
        return "toml"
    if suffix == ".env":
        return "env"
    return None


def _infer_env_from_config_path(path_text: str | None) -> str | None:
    if not path_text:
        return None
    path = PurePosixPath(path_text)
    parts = path.parts
    if path.name not in {"config.json", "config.toml", "config.env"}:
        return None
    if len(parts) >= 3 and parts[-3] == "config":
        env_name = parts[-2]
        if env_name and env_name not in {".", ".."}:
            return env_name
    return None


def _strip_remainder_separator(tokens: list[str]) -> list[str]:
    if tokens and tokens[0] == "--":
        return tokens[1:]
    return tokens


def _normalize_wrapper_extra(tokens: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for token in tokens:
        if not token or token == "--":
            continue
        if token.startswith("--"):
            token = token[2:]
        normalized.append(token)
    return normalized


def _normalize_direct_extra(tokens: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for token in tokens:
        if not token or token == "--":
            continue
        if token.startswith("--"):
            normalized.append(token)
        else:
            normalized.append(f"--{token}")
    return normalized


def _shell_join(tokens: Iterable[str]) -> str:
    return shlex.join(list(tokens))


def _assignment(key: str, value: str) -> str:
    return f"{key}={value}"


def _select_launcher(args: argparse.Namespace, backend: str | None, inferred_env: str | None) -> str:
    if args.launcher != "auto":
        return args.launcher
    if args.env or args.example:
        return "wrapper"
    if args.config_path:
        if backend in {"toml", "env"} and inferred_env:
            return "wrapper"
        return "direct"
    return "wrapper"


def build_command(args: argparse.Namespace) -> str:
    extra_tokens = _strip_remainder_separator(list(args.extra_args or []))
    backend = args.config_backend or _infer_backend_from_path(args.config_path)
    if backend and backend not in VALID_BACKENDS:
        raise ValueError(f"Invalid config backend: {backend!r}; expected one of {sorted(VALID_BACKENDS)}")

    inferred_env = args.env or _infer_env_from_config_path(args.config_path)
    if args.config_path and backend in {"toml", "env"} and not inferred_env:
        raise ValueError(
            "TOML/env config backends are environment-layout based in this SimpleTuner snapshot; "
            "provide --env or use a path like config/<env>/config.toml or config/<env>/config.env."
        )

    launcher = _select_launcher(args, backend, inferred_env)
    env_assignments: list[str] = []

    if launcher == "wrapper":
        command = ["simpletuner", "train"]
        if args.example:
            command.extend(["--example", args.example])
        elif inferred_env:
            command.extend(["--env", inferred_env])

        # For the wrapper, use environment variables for explicit backend/path so
        # downstream train.py sees the same values as an actual user shell would.
        if backend:
            env_assignments.append(_assignment("CONFIG_BACKEND", backend))
        if args.config_path and backend == "json":
            env_assignments.append(_assignment("CONFIG_PATH", args.config_path))
        command.extend(_normalize_wrapper_extra(extra_tokens))
        return _shell_join(env_assignments + command)

    command = ["simpletuner-train"]
    if args.example:
        raise ValueError("--example requires the simpletuner train wrapper; use --launcher wrapper or remove --example.")
    if inferred_env:
        env_assignments.append(_assignment("ENV", inferred_env))
    if backend:
        env_assignments.append(_assignment("CONFIG_BACKEND", backend))
    if args.config_path and backend == "json":
        env_assignments.append(_assignment("CONFIG_PATH", args.config_path))
    command.extend(_normalize_direct_extra(extra_tokens))
    return _shell_join(env_assignments + command)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and print a SimpleTuner training command without running training.",
        epilog=(
            "Examples:\n"
            "  build_training_command.py --env flux-lora --config-backend json -- max_train_steps=100 report_to=none\n"
            "  build_training_command.py --config-path config/flux-lora/config.json --config-backend json -- model_family=flux model_type=lora\n"
            "  build_training_command.py --launcher wrapper --example kontext.peft-lora -- max_train_steps=100"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--env", help="SimpleTuner config environment name, e.g. flux-lora.")
    parser.add_argument("--example", help="Packaged SimpleTuner example name; requires the wrapper launcher.")
    parser.add_argument(
        "--config-backend",
        choices=sorted(VALID_BACKENDS),
        help="Config backend to set: env, json, toml, or cmd. If omitted, inferred from --config-path suffix when possible.",
    )
    parser.add_argument(
        "--config-path",
        help="Config file/stem/directory path. Arbitrary paths are supported for JSON; TOML/env need --env or config/<env>/ layout.",
    )
    parser.add_argument(
        "--launcher",
        choices=["auto", "wrapper", "direct"],
        default="auto",
        help="auto chooses simpletuner train for env/example and simpletuner-train for direct JSON paths.",
    )
    parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="Downstream training args after --. Use key=value; --key=value is also accepted and normalized.",
    )
    return parser


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()
    try:
        print(build_command(args))
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
