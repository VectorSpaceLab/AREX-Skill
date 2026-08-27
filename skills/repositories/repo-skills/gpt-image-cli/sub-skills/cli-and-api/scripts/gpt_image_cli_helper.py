#!/usr/bin/env python3
"""Safe helper for gpt-image-cli preflight and command construction.

Default behavior is deterministic and no-network: it never calls the OpenAI API
unless `build-command --execute` is passed explicitly.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_MODEL = "gpt-image-2"
DEFAULT_SIZE = "1024x1024"
DEFAULT_MODERATION = "low"
DEFAULT_QUALITY = "high"
SIZE_SHORTCUTS = {
    "1k": "1024x1024",
    "2k": "2048x2048",
    "4k": "3840x2160",
    "portrait": "1024x1536",
    "landscape": "1536x1024",
    "square": "1024x1024",
    "wide": "2048x1152",
    "tall": "2160x3840",
}


def _json_dump(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _has_path_separator(command: str) -> bool:
    return os.sep in command or (os.altsep is not None and os.altsep in command)


def _command_available(command: str) -> bool:
    if _has_path_separator(command):
        path = Path(command).expanduser()
        return path.is_file() and os.access(path, os.X_OK)
    return shutil.which(command) is not None


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _env_file_has_openai_key(path: Path) -> bool:
    try:
        if not path.is_file():
            return False
        for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].lstrip()
            if line.startswith("OPENAI_API_KEY") and "=" in line:
                return True
    except OSError:
        return False
    return False


def _key_report() -> dict[str, Any]:
    cwd_env = Path(".env")
    home_env = Path.home() / ".env"
    process_env = bool(os.environ.get("OPENAI_API_KEY"))
    candidates = [
        {
            "path": "./.env",
            "exists": cwd_env.is_file(),
            "contains_openai_api_key": _env_file_has_openai_key(cwd_env),
        },
        {
            "path": "~/.env",
            "exists": home_env.is_file(),
            "contains_openai_api_key": _env_file_has_openai_key(home_env),
        },
    ]
    return {
        "process_env_openai_api_key": process_env,
        "dotenv_candidates": candidates,
        "key_candidate_available_without_value": process_env
        or any(item["contains_openai_api_key"] for item in candidates),
        "secret_values_printed": False,
    }


def _path_status(raw: str) -> dict[str, Any]:
    path = Path(raw).expanduser()
    return {
        "path": raw,
        "exists": path.exists(),
        "is_file": path.is_file(),
    }


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def _compression(value: str) -> int:
    parsed = int(value)
    if not 0 <= parsed <= 100:
        raise argparse.ArgumentTypeError("must be between 0 and 100")
    return parsed


def _resolve_size(value: str) -> str:
    return SIZE_SHORTCUTS.get(value.lower(), value)


def _model_rejects_input_fidelity(model: str) -> bool:
    return model.strip().lower().startswith("gpt-image-2")


def _build_command(args: argparse.Namespace) -> list[str]:
    command = [
        args.cli,
        "-p",
        args.prompt,
        "--model",
        args.model,
        "--size",
        args.size,
        "--quality",
        args.quality,
        "--n",
        str(args.n),
    ]

    if args.file:
        command.extend(["-f", args.file])
    for image_path in args.image or []:
        command.extend(["-i", image_path])
    if args.mask:
        command.extend(["-m", args.mask])
    if args.background:
        command.extend(["--background", args.background])
    edit_intent = bool(args.image or args.mask)
    if not edit_intent and args.moderation:
        command.extend(["--moderation", args.moderation])
    if edit_intent and args.input_fidelity:
        command.extend(["--input-fidelity", args.input_fidelity])
    if args.output_format:
        command.extend(["--format", args.output_format])
    if args.output_compression is not None:
        command.extend(["--compression", str(args.output_compression)])
    if args.user:
        command.extend(["--user", args.user])
    return command


def cmd_preflight(args: argparse.Namespace) -> int:
    cli_available = _command_available(args.cli)
    module_available = _module_available("gpt_image_cli")
    key_report = _key_report()
    payload = {
        "ok": True,
        "checks": {
            "python_version": {
                "current": ".".join(str(part) for part in sys.version_info[:3]),
                "requires_at_least": "3.11",
                "ok": sys.version_info >= (3, 11),
            },
            "cli": {
                "command": args.cli,
                "available": cli_available,
            },
            "python_module": {
                "module": "gpt_image_cli",
                "available": module_available,
            },
            "api_key": key_report,
        },
        "no_api_call_performed": True,
    }

    failures: list[str] = []
    if sys.version_info < (3, 11):
        failures.append("python_version")
    if args.strict and not (cli_available or module_available):
        failures.append("cli_or_module")
    if args.require_key and not key_report["key_candidate_available_without_value"]:
        failures.append("openai_api_key")

    if failures:
        payload["ok"] = False
        payload["failures"] = failures
        _json_dump(payload)
        return 2

    _json_dump(payload)
    return 0


def cmd_build_command(args: argparse.Namespace) -> int:
    endpoint = "edits" if (args.image or args.mask) else "generations"
    errors: list[str] = []
    warnings: list[str] = []

    image_statuses = [_path_status(path) for path in (args.image or [])]
    for status in image_statuses:
        if not status["is_file"]:
            errors.append(f"--image not found or not a file: {status['path']}")

    mask_status = _path_status(args.mask) if args.mask else None
    if args.mask and not args.image:
        errors.append("--mask requires at least one --image")
    if mask_status and not mask_status["is_file"]:
        errors.append(f"--mask not found or not a file: {mask_status['path']}")

    if args.input_fidelity and not (args.image or args.mask):
        warnings.append("--input-fidelity is only meaningful for edits; the CLI does not send it on generation calls")
    if args.input_fidelity and _model_rejects_input_fidelity(args.model):
        warnings.append("gpt-image-2 rejects input_fidelity; the CLI will print a note and drop this parameter")
    if args.output_compression is not None and args.output_format == "png":
        warnings.append("--compression is intended for jpeg/webp and is ignored for png by the API")
    if args.output_compression is not None and args.output_format is None:
        warnings.append("--compression was set without --format; choose jpeg or webp if compression should matter")

    cli_available = _command_available(args.cli)
    command = _build_command(args)
    payload = {
        "ok": not errors,
        "endpoint": endpoint,
        "resolved_size": _resolve_size(args.size),
        "cli": {
            "command": args.cli,
            "available": cli_available,
        },
        "inputs": {
            "images": image_statuses,
            "mask": mask_status,
        },
        "api_key": _key_report(),
        "command": command,
        "shell": shlex.join(command),
        "warnings": warnings,
        "errors": errors,
        "no_api_call_performed": not args.execute,
    }

    if errors:
        _json_dump(payload)
        return 2

    if not args.execute:
        _json_dump(payload)
        return 0

    if not cli_available:
        payload["ok"] = False
        payload["errors"] = warnings + ["cannot execute because the CLI command is not available"]
        _json_dump(payload)
        return 2

    print("About to execute a command that may call the OpenAI Images API and incur cost:", file=sys.stderr)
    print(shlex.join(command), file=sys.stderr)
    completed = subprocess.run(command, check=False)
    return int(completed.returncode)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gpt_image_cli_helper.py",
        description="No-network preflight and command builder for the gpt-image CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser(
        "preflight",
        help="Check Python, CLI/module availability, and key presence without making API calls.",
    )
    preflight.add_argument("--cli", default="gpt-image", help="CLI executable name or path. Default: gpt-image")
    preflight.add_argument("--strict", action="store_true", help="Exit 2 if neither CLI nor Python module is available.")
    preflight.add_argument("--require-key", action="store_true", help="Exit 2 if no OPENAI_API_KEY candidate is detected.")
    preflight.set_defaults(func=cmd_preflight)

    build = subparsers.add_parser(
        "build-command",
        help="Validate local inputs and print a gpt-image command. Does not execute unless --execute is set.",
    )
    build.add_argument("--cli", default="gpt-image", help="CLI executable name or path. Default: gpt-image")
    build.add_argument("-p", "--prompt", required=True, help="Text prompt or edit instruction.")
    build.add_argument("-f", "--file", help="Output file path.")
    build.add_argument("-i", "--image", action="append", default=None, help="Reference image path. Repeat for multi-reference edits.")
    build.add_argument("-m", "--mask", help="Alpha-channel mask path. Requires at least one --image.")
    build.add_argument("--model", default=DEFAULT_MODEL, help=f"Model ID. Default: {DEFAULT_MODEL}")
    build.add_argument("--size", default=DEFAULT_SIZE, help=f"Size shortcut or literal. Default: {DEFAULT_SIZE}")
    build.add_argument("--quality", default=DEFAULT_QUALITY, choices=["auto", "low", "medium", "high"], help=f"Quality/cost knob. Default: {DEFAULT_QUALITY}")
    build.add_argument("-n", "--n", type=_positive_int, default=1, help="Number of images. Default: 1")
    build.add_argument("--background", choices=["auto", "opaque"], help="Background behavior.")
    build.add_argument("--moderation", default=DEFAULT_MODERATION, choices=["auto", "low"], help=f"Generation moderation. Default: {DEFAULT_MODERATION}")
    build.add_argument("--input-fidelity", choices=["low", "high"], help="Edit-only input fidelity; dropped by the CLI for gpt-image-2.")
    build.add_argument("--format", dest="output_format", choices=["png", "jpeg", "webp"], help="Output encoding.")
    build.add_argument("--compression", dest="output_compression", type=_compression, help="JPEG/WebP compression level, 0-100.")
    build.add_argument("--user", help="Optional end-user identifier forwarded by the CLI.")
    build.add_argument("--execute", action="store_true", help="Actually run the built command. This may call OpenAI and incur cost.")
    build.set_defaults(func=cmd_build_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
