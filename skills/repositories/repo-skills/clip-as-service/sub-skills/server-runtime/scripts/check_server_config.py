#!/usr/bin/env python3
"""Validate CLIP-as-service server Flow YAML without starting a server.

This static checker catches common runtime-module and shape mistakes before a
Flow triggers model downloads or long-running startup.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RUNTIME_MODULES = {
    "torch": "clip_server.executors.clip_torch",
    "onnx": "clip_server.executors.clip_onnx",
    "tensorrt": "clip_server.executors.clip_tensorrt",
}


def load_yaml(path: Path) -> dict:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - user environment diagnostic
        raise SystemExit("PyYAML is required to validate Flow YAML: pip install pyyaml") from exc
    with path.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping")
    return data


def infer_runtime(modules: list[str]) -> str | None:
    for runtime, module in RUNTIME_MODULES.items():
        if module in modules:
            return runtime
    return None


def validate(data: dict, expected_runtime: str | None = None) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    details: dict = {}

    if data.get("jtype") != "Flow":
        errors.append("top-level jtype should be Flow")
    flow_with = data.get("with") or {}
    if not isinstance(flow_with, dict):
        errors.append("top-level with must be a mapping")
        flow_with = {}
    if "port" not in flow_with:
        warnings.append("top-level with.port is missing; Jina may choose a default")
    protocol = flow_with.get("protocol", "grpc")
    if protocol not in {"grpc", "http", "websocket"}:
        warnings.append(f"unexpected protocol {protocol!r}; expected grpc/http/websocket")

    executors = data.get("executors")
    if not isinstance(executors, list) or not executors:
        errors.append("executors must be a non-empty list")
        executors = []

    runtime_modules: list[str] = []
    for index, executor in enumerate(executors):
        if not isinstance(executor, dict):
            errors.append(f"executor[{index}] must be a mapping")
            continue
        uses = executor.get("uses") or {}
        if not isinstance(uses, dict):
            errors.append(f"executor[{index}].uses must be a mapping")
            continue
        if uses.get("jtype") != "CLIPEncoder":
            warnings.append(f"executor[{index}] jtype is {uses.get('jtype')!r}, not CLIPEncoder")
        metas = uses.get("metas") or {}
        modules = metas.get("py_modules") if isinstance(metas, dict) else None
        if not isinstance(modules, list):
            errors.append(f"executor[{index}].uses.metas.py_modules must list the CLIPEncoder module")
            continue
        runtime_modules.extend(str(item) for item in modules)

    runtime = infer_runtime(runtime_modules)
    details["runtime"] = runtime
    details["runtime_modules"] = runtime_modules
    details["protocol"] = protocol
    details["port"] = flow_with.get("port")

    if runtime is None:
        errors.append("no recognized CLIP-as-service executor module found")
    if expected_runtime and runtime != expected_runtime:
        errors.append(f"expected runtime {expected_runtime!r}, found {runtime!r}")

    return errors, warnings, details


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Statically validate a CLIP-as-service server Flow YAML.")
    parser.add_argument("yaml_path", type=Path)
    parser.add_argument("--expected-runtime", choices=sorted(RUNTIME_MODULES), help="Require a specific runtime module.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        data = load_yaml(args.yaml_path)
        errors, warnings, details = validate(data, args.expected_runtime)
    except Exception as exc:  # noqa: BLE001
        errors, warnings, details = [f"{type(exc).__name__}: {exc}"], [], {}

    report = {"path": str(args.yaml_path), "ok": not errors, "errors": errors, "warnings": warnings, "details": details}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
