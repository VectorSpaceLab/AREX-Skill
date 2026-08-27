#!/usr/bin/env python3
"""Quickly inspect the installed imagen CLI without training or sampling.

The helper shells out to `imagen --help` and subcommand help, then optionally
runs `imagen config --path <tempfile>` to prove default-config generation. It
never calls `imagen train` or `imagen sample`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

EXPECTED = {
    ("root",): ["Commands:", "config", "sample", "train"],
    ("config",): ["--path TEXT", "Path to the Imagen model config"],
    ("sample",): ["--model TEXT", "--cond_scale INTEGER", "--load_ema BOOLEAN", "TEXT"],
    ("train",): ["--config TEXT", "--unet INTEGER RANGE", "[1<=x<3]", "--epoches INTEGER"],
}


def run_command(command: list[str]) -> dict[str, Any]:
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def check_help(imagen_exe: str) -> tuple[list[dict[str, Any]], list[str]]:
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    commands = {
        ("root",): [imagen_exe, "--help"],
        ("config",): [imagen_exe, "config", "--help"],
        ("sample",): [imagen_exe, "sample", "--help"],
        ("train",): [imagen_exe, "train", "--help"],
    }
    for key, command in commands.items():
        result = run_command(command)
        output = result["stdout"] + result["stderr"]
        missing = [needle for needle in EXPECTED[key] if needle not in output]
        result["missing_expected_fragments"] = missing
        checks.append(result)
        if result["returncode"] != 0:
            errors.append(f"{' '.join(command)} exited {result['returncode']}")
        for needle in missing:
            errors.append(f"{' '.join(command)} help missing expected fragment: {needle!r}")
    return checks, errors


def generate_config(imagen_exe: str, keep_config: Path | None) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="imagen-cli-quickcheck-") as tmp:
        tmp_path = Path(tmp)
        config_path = tmp_path / "imagen_config.json"
        result = run_command([imagen_exe, "config", "--path", str(config_path)])
        if result["returncode"] != 0:
            errors.append(f"imagen config exited {result['returncode']}: {result['stderr'].strip()}")
            return {"command_result": result}, errors
        if not config_path.exists():
            errors.append("imagen config did not create the requested JSON file")
            return {"command_result": result}, errors
        try:
            config_data = json.loads(config_path.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"generated config is invalid JSON: line {exc.lineno} column {exc.colno}: {exc.msg}")
            return {"command_result": result}, errors
        if keep_config is not None:
            keep_config.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(config_path, keep_config)
        summary = {
            "command_result": result,
            "generated_top_level_keys": sorted(config_data.keys()),
            "generated_type": config_data.get("type"),
            "generated_unet_count": len(config_data.get("imagen", {}).get("unets", [])) if isinstance(config_data.get("imagen"), dict) else None,
            "generated_dataset_name": config_data.get("dataset_name"),
            "kept_config": str(keep_config) if keep_config is not None else None,
        }
        required = {"type", "imagen", "trainer", "dataset", "dataset_name", "checkpoint_path"}
        missing = sorted(required - set(config_data))
        if missing:
            errors.append(f"generated config missing expected top-level keys: {missing}")
        return summary, errors


def resolve_executable(exe: str) -> str | None:
    candidates: list[str] = []
    if exe:
        candidates.append(exe)
    env_sibling = Path(sys.executable).with_name(exe)
    candidates.append(str(env_sibling))
    if exe != "imagen":
        candidates.append("imagen")

    for candidate in candidates:
        candidate_path = Path(candidate)
        if candidate_path.is_file():
            return str(candidate_path)
        found = shutil.which(candidate)
        if found:
            return found
    return None


def check_noop_entry(exe: str) -> dict[str, Any]:
    found = resolve_executable(exe if exe else "imagen_pytorch")
    if not found:
        return {"found": False, "note": f"{exe} not found on PATH or next to the current Python executable"}
    result = run_command([found])
    return {
        "found": True,
        "path_basename": Path(found).name,
        "returncode": result["returncode"],
        "stdout_len": len(result["stdout"]),
        "stderr_len": len(result["stderr"]),
        "note": "imagen_pytorch is expected to be a no-op entry point, not the command group",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check installed imagen CLI help and default config generation")
    parser.add_argument("--imagen-exe", default="imagen", help="imagen executable name or path")
    parser.add_argument("--no-generate-config", action="store_true", help="Only check help text; do not run imagen config")
    parser.add_argument("--keep-config", type=Path, default=None, help="Copy the generated temp config to this path")
    parser.add_argument("--check-noop-entry", action="store_true", help="Also inspect the imagen_pytorch no-op entry point")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    imagen_path = resolve_executable(args.imagen_exe)
    errors: list[str] = []
    payload: dict[str, Any] = {"imagen_exe": args.imagen_exe, "resolved_imagen_exe": imagen_path}

    if not imagen_path:
        errors.append(f"imagen executable not found: {args.imagen_exe}")
        payload["errors"] = errors
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"FAILED: {errors[0]}", file=sys.stderr)
        return 1

    help_checks, help_errors = check_help(imagen_path)
    errors.extend(help_errors)
    payload["help_checks"] = [
        {
            "command": item["command"],
            "returncode": item["returncode"],
            "missing_expected_fragments": item["missing_expected_fragments"],
        }
        for item in help_checks
    ]

    if not args.no_generate_config:
        generated, gen_errors = generate_config(imagen_path, args.keep_config)
        errors.extend(gen_errors)
        payload["generated_config"] = generated

    if args.check_noop_entry:
        payload["imagen_pytorch_entry"] = check_noop_entry("imagen_pytorch")

    payload["ok"] = not errors
    payload["errors"] = errors
    payload["notes"] = ["No train or sample command was executed."]

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if errors:
            print("FAILED: imagen CLI quickcheck found issues")
            for msg in errors:
                print(f"  - {msg}")
        else:
            print("OK: imagen CLI help and config generation passed")
            if payload.get("generated_config"):
                gc = payload["generated_config"]
                print(f"  generated type: {gc.get('generated_type')}")
                print(f"  generated unet count: {gc.get('generated_unet_count')}")
                print(f"  generated dataset: {gc.get('generated_dataset_name')}")
        print("Note: no training or sampling was executed.")

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
