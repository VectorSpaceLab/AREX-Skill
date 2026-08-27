#!/usr/bin/env python3
"""Safe checker for TRL experimental environment integration contracts.

This script performs import-light checks only. It does not start training,
open network connections, launch OpenEnv/OpenReward servers, or start Harbor
sandboxes. Use it to inspect a local environment class or optional dependency
presence before a full GRPO run.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import os
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from types import ModuleType
from typing import Any


@dataclass
class Finding:
    level: str
    message: str


def _version(package: str) -> str | None:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def _parse_version(value: str) -> tuple[int, ...]:
    parts: list[int] = []
    for piece in value.replace("-", ".").split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        if digits == "":
            break
        parts.append(int(digits))
    return tuple(parts or [0])


def _meets(package: str, minimum: str) -> bool | None:
    value = _version(package)
    if value is None:
        return None
    return _parse_version(value) >= _parse_version(minimum)


def _load_module(module_or_file: str) -> ModuleType:
    if module_or_file.endswith(".py") or os.path.sep in module_or_file:
        path = Path(module_or_file).expanduser().resolve()
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(module_or_file)


def _load_object(target: str) -> Any:
    module_name, sep, object_name = target.partition(":")
    if not sep:
        raise ValueError("--env-class must be MODULE:OBJECT or FILE.py:OBJECT")
    module = _load_module(module_name)
    obj: Any = module
    for part in object_name.split("."):
        obj = getattr(obj, part)
    return obj


def _check_dependency_facts(findings: list[Finding], check_openreward: bool, check_harbor: bool) -> None:
    transformers = _version("transformers")
    if transformers is None:
        findings.append(Finding("warn", "transformers is not installed; GRPO environment_factory requires >=5.2.0."))
    elif _meets("transformers", "5.2.0"):
        findings.append(Finding("ok", f"transformers {transformers} satisfies environment_factory >=5.2.0."))
    else:
        findings.append(Finding("error", f"transformers {transformers} is below environment_factory requirement >=5.2.0."))

    if _version("jmespath") is None:
        findings.append(Finding("error", "jmespath is not installed; GRPO tool parsing requires it."))
    else:
        findings.append(Finding("ok", "jmespath is installed."))

    trl_version = _version("trl")
    if trl_version is None:
        findings.append(Finding("warn", "trl package metadata is not installed; running from source may still work."))
    else:
        findings.append(Finding("ok", f"trl package metadata reports version {trl_version}."))

    if check_openreward:
        if _version("openreward") is None:
            findings.append(Finding("error", "openreward is not installed; install the OpenReward extra before using OpenRewardSpec."))
        else:
            findings.append(Finding("ok", "openreward is installed."))
        if os.environ.get("OPENREWARD_API_KEY"):
            findings.append(Finding("ok", "OPENREWARD_API_KEY is set for catalog environments."))
        else:
            findings.append(Finding("warn", "OPENREWARD_API_KEY is not set; catalog environments may fail authentication."))

    if check_harbor:
        if _version("harbor") is None:
            findings.append(Finding("error", "harbor is not installed; install the Harbor extra before using HarborSpec."))
        else:
            findings.append(Finding("ok", "harbor is installed."))
        vllm = _version("vllm")
        if vllm is None:
            findings.append(Finding("warn", "vllm is not installed; documented Harbor training flows require vLLM."))
        elif _meets("vllm", "0.22.0"):
            findings.append(Finding("ok", f"vllm {vllm} satisfies the documented Harbor requirement >=0.22.0."))
        else:
            findings.append(Finding("error", f"vllm {vllm} is below the documented Harbor requirement >=0.22.0."))
        if os.environ.get("E2B_API_KEY"):
            findings.append(Finding("ok", "E2B_API_KEY is set for E2B sandbox use."))
        else:
            findings.append(Finding("note", "E2B_API_KEY is not set; this is fine unless environment_type='e2b'."))


def _safe_instantiate(factory: Any) -> Any:
    if inspect.isclass(factory):
        signature = inspect.signature(factory)
        required = [
            name
            for name, param in signature.parameters.items()
            if param.default is inspect.Signature.empty
            and param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY)
        ]
        if required:
            raise TypeError(f"class constructor requires arguments: {', '.join(required)}")
    return factory()


def _check_env_class(findings: list[Finding], target: str, instantiate: bool) -> None:
    obj = _load_object(target)
    env = None

    if instantiate:
        env = _safe_instantiate(obj)
        findings.append(Finding("ok", f"instantiated {target} with no arguments."))
    elif inspect.isclass(obj):
        env = obj
        findings.append(Finding("note", f"inspecting class {target} without instantiation."))
    else:
        env = obj
        findings.append(Finding("note", f"inspecting object {target} without calling it."))

    reset = getattr(env, "reset", None)
    if callable(reset):
        findings.append(Finding("ok", "callable reset method found."))
        reset_signature = inspect.signature(reset)
        if any(param.kind == param.VAR_KEYWORD for param in reset_signature.parameters.values()):
            findings.append(Finding("ok", "reset accepts **kwargs from dataset rows."))
        else:
            findings.append(Finding("warn", "reset does not accept **kwargs; dataset columns must exactly match its parameters."))
    else:
        findings.append(Finding("error", "callable reset method is missing."))

    members = inspect.getmembers(env, predicate=inspect.isfunction if inspect.isclass(env) else inspect.ismethod)
    tools = [(name, member) for name, member in members if name != "reset" and not name.startswith("_")]
    if not tools:
        findings.append(Finding("error", "no public tool methods were discovered."))
        return

    findings.append(Finding("ok", f"discovered tool methods: {', '.join(name for name, _ in tools)}."))
    for name, member in tools:
        signature = inspect.signature(member)
        missing_annotations = [
            param_name
            for param_name, param in signature.parameters.items()
            if param_name != "self" and param.annotation is inspect.Signature.empty
        ]
        if missing_annotations:
            findings.append(Finding("warn", f"tool {name} lacks type annotations for: {', '.join(missing_annotations)}."))
        if signature.return_annotation is inspect.Signature.empty:
            findings.append(Finding("warn", f"tool {name} lacks a return annotation."))
        doc = inspect.getdoc(member) or ""
        if "Args:" not in doc:
            findings.append(Finding("warn", f"tool {name} docstring has no Args: section for schema descriptions."))
        else:
            findings.append(Finding("ok", f"tool {name} has an Args: docstring section."))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check TRL experimental environment integration prerequisites without starting services.",
    )
    parser.add_argument("--env-class", help="Environment class/object as MODULE:OBJECT or FILE.py:OBJECT.")
    parser.add_argument(
        "--instantiate",
        action="store_true",
        help="Instantiate --env-class with no arguments to inspect bound methods. Do not use if __init__ starts services.",
    )
    parser.add_argument("--check-openreward", action="store_true", help="Check OpenReward optional package and API key presence.")
    parser.add_argument("--check-harbor", action="store_true", help="Check Harbor/vLLM optional package and sandbox credential hints.")
    args = parser.parse_args()

    findings: list[Finding] = []
    _check_dependency_facts(findings, args.check_openreward, args.check_harbor)

    if args.env_class:
        try:
            _check_env_class(findings, args.env_class, args.instantiate)
        except Exception as exc:  # noqa: BLE001 - report contract checker failure clearly
            findings.append(Finding("error", f"failed to inspect --env-class: {exc}"))

    order = {"error": 0, "warn": 1, "note": 2, "ok": 3}
    for finding in sorted(findings, key=lambda item: order.get(item.level, 9)):
        print(f"[{finding.level}] {finding.message}")

    return 1 if any(f.level == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
