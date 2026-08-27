#!/usr/bin/env python3
"""Inspect LMDeploy offline pipeline configuration without loading a model.

This helper is safe for documentation, CI smoke checks, and agent diagnosis:
- imports lmdeploy and selected config classes
- prints signatures and dataclass defaults
- optionally runs CLI --help commands
- never calls lmdeploy.pipeline(...), downloads models, or reads private paths
"""

from __future__ import annotations

import argparse
import dataclasses
import inspect
import json
import shutil
import subprocess
import sys
from typing import Any


def _jsonable(value: Any) -> Any:
    if value is dataclasses.MISSING:
        return "<missing>"
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(val) for key, val in value.items()}
    return repr(value)


def _dataclass_defaults(cls: type) -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    for field in dataclasses.fields(cls):
        if field.default is not dataclasses.MISSING:
            defaults[field.name] = _jsonable(field.default)
        elif field.default_factory is not dataclasses.MISSING:  # type: ignore[attr-defined]
            defaults[field.name] = "<default_factory>"
        else:
            defaults[field.name] = "<required>"
    return defaults


def _cli_check(command: list[str], timeout: int) -> dict[str, Any]:
    executable = shutil.which(command[0])
    if executable is None:
        return {
            "command": command,
            "available": False,
            "returncode": None,
            "stdout_first_line": None,
            "stderr_first_line": f"{command[0]!r} not found on PATH",
        }
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "available": True,
            "returncode": "timeout",
            "stdout_first_line": None,
            "stderr_first_line": f"timed out after {timeout}s",
        }
    stdout_lines = completed.stdout.splitlines()
    stderr_lines = completed.stderr.splitlines()
    return {
        "command": command,
        "available": True,
        "returncode": completed.returncode,
        "stdout_first_line": stdout_lines[0] if stdout_lines else None,
        "stderr_first_line": stderr_lines[0] if stderr_lines else None,
    }


def collect(include_cli: bool = False, cli_timeout: int = 15) -> dict[str, Any]:
    import lmdeploy
    from lmdeploy import GenerationConfig, PytorchEngineConfig, TurbomindEngineConfig, pipeline
    from lmdeploy.model import ChatTemplateConfig, MODELS

    try:
        from lmdeploy import VisionConfig
        vision_config_import = True
        vision_config_signature = str(inspect.signature(VisionConfig))
    except Exception as exc:  # pragma: no cover - depends on installed extras/version
        vision_config_import = False
        vision_config_signature = f"import failed: {type(exc).__name__}: {exc}"

    info: dict[str, Any] = {
        "lmdeploy_version": getattr(lmdeploy, "__version__", None),
        "pipeline_signature": str(inspect.signature(pipeline)),
        "generation_config_defaults": _dataclass_defaults(GenerationConfig),
        "pytorch_engine_config_defaults": _dataclass_defaults(PytorchEngineConfig),
        "turbomind_engine_config_defaults": _dataclass_defaults(TurbomindEngineConfig),
        "chat_template_config_signature": str(inspect.signature(ChatTemplateConfig)),
        "registered_chat_templates": sorted(MODELS.module_dict.keys()),
        "vision_config_import": vision_config_import,
        "vision_config_signature": vision_config_signature,
    }

    if include_cli:
        info["cli_checks"] = [
            _cli_check(["lmdeploy", "--help"], cli_timeout),
            _cli_check(["lmdeploy", "chat", "--help"], cli_timeout),
        ]

    return info


def _print_text(info: dict[str, Any]) -> None:
    print(f"LMDeploy version: {info['lmdeploy_version']}")
    print(f"pipeline signature: {info['pipeline_signature']}")
    print(f"ChatTemplateConfig signature: {info['chat_template_config_signature']}")
    print(f"VisionConfig import: {info['vision_config_import']} ({info['vision_config_signature']})")
    print("\nGenerationConfig defaults:")
    for key, value in info["generation_config_defaults"].items():
        print(f"  {key}: {value}")
    print("\nPytorchEngineConfig selected defaults:")
    for key in [
        "dtype",
        "tp",
        "session_len",
        "max_batch_size",
        "cache_max_entry_count",
        "adapters",
        "device_type",
        "model_format",
        "enable_prefix_caching",
    ]:
        print(f"  {key}: {info['pytorch_engine_config_defaults'].get(key)}")
    print("\nTurbomindEngineConfig selected defaults:")
    for key in [
        "dtype",
        "model_format",
        "tp",
        "session_len",
        "max_batch_size",
        "cache_max_entry_count",
        "quant_policy",
        "enable_prefix_caching",
        "async_",
    ]:
        print(f"  {key}: {info['turbomind_engine_config_defaults'].get(key)}")
    print("\nRegistered chat templates:")
    print("  " + ", ".join(info["registered_chat_templates"]))
    if "cli_checks" in info:
        print("\nCLI checks:")
        for check in info["cli_checks"]:
            command = " ".join(check["command"])
            print(f"  {command}: available={check['available']} returncode={check['returncode']}")
            if check["stdout_first_line"]:
                print(f"    stdout: {check['stdout_first_line']}")
            if check["stderr_first_line"]:
                print(f"    stderr: {check['stderr_first_line']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect installed LMDeploy pipeline/config metadata without loading models or downloading weights."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument("--include-cli", action="store_true", help="Also run 'lmdeploy --help' and 'lmdeploy chat --help'.")
    parser.add_argument("--cli-timeout", type=int, default=15, help="Timeout in seconds for each CLI help command.")
    args = parser.parse_args(argv)

    try:
        info = collect(include_cli=args.include_cli, cli_timeout=args.cli_timeout)
    except Exception as exc:
        print(f"failed to inspect lmdeploy: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True))
    else:
        _print_text(info)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
