#!/usr/bin/env python3
"""Validate RL Zoo custom component imports without creating environments or training.

The checker imports requested Gymnasium registration modules and dotted component
paths, parses optional YAML hyperparameter files, checks wrapper/callback mapping
shape, and verifies constructor kwargs against Python signatures when possible.
It does not call gym.make(), instantiate RL algorithms, load model weights, open
network connections, or start training. Custom modules may still execute their
own import-time code, so only validate modules you trust.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only in under-installed envs
    yaml = None  # type: ignore[assignment]


@dataclass
class CheckResult:
    kind: str
    target: str
    source: str
    status: str
    detail: str
    signature: str | None = None
    kwargs: dict[str, Any] | None = None


@dataclass
class ComponentSpec:
    kind: str
    target: str
    source: str
    kwargs: dict[str, Any]


WRAPPER_KEYS = {"env_wrapper": "wrapper", "vec_env_wrapper": "vec_wrapper"}
COMPONENT_KEYS = {"env_wrapper", "vec_env_wrapper", "callback", "policy"}


def _jsonable(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)


def _jsonable_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    return {str(key): _jsonable(value) for key, value in kwargs.items()}


def _result(
    kind: str,
    target: str,
    source: str,
    status: str,
    detail: str,
    signature: str | None = None,
    kwargs: dict[str, Any] | None = None,
) -> CheckResult:
    return CheckResult(
        kind=kind,
        target=target,
        source=source,
        status=status,
        detail=detail,
        signature=signature,
        kwargs=_jsonable_kwargs(kwargs or {}) if kwargs else None,
    )


def import_module(module_name: str, *, kind: str, source: str) -> CheckResult:
    try:
        importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report import-time failure faithfully
        return _result(kind, module_name, source, "error", f"{type(exc).__name__}: {exc}")
    return _result(kind, module_name, source, "ok", "module imported")


def import_dotted(target: str) -> tuple[Any | None, CheckResult | None]:
    if "." not in target:
        return None, _result("component", target, "import", "error", "expected a dotted path like module.Class")
    module_name, attr_name = target.rsplit(".", 1)
    if not module_name or not attr_name:
        return None, _result("component", target, "import", "error", "empty module or attribute in dotted path")
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001
        return None, _result("component", target, "import", "error", f"import {module_name!r} failed: {type(exc).__name__}: {exc}")
    try:
        obj = getattr(module, attr_name)
    except AttributeError as exc:
        return None, _result("component", target, "import", "error", f"attribute {attr_name!r} not found in {module_name!r}: {exc}")
    return obj, None


def signature_text(obj: Any) -> tuple[inspect.Signature | None, str | None, str | None]:
    try:
        signature = inspect.signature(obj)
        return signature, str(signature), None
    except (TypeError, ValueError) as exc:
        try:
            signature = inspect.signature(obj.__init__)
            params = list(signature.parameters.values())
            if params and params[0].name == "self":
                signature = signature.replace(parameters=params[1:])
            return signature, str(signature), None
        except Exception:  # noqa: BLE001
            return None, None, f"signature unavailable: {type(exc).__name__}: {exc}"


def bind_signature(kind: str, target: str, obj: Any, kwargs: dict[str, Any], source: str) -> CheckResult:
    if not callable(obj):
        return _result(kind, target, source, "error", f"imported object is not callable: {type(obj).__name__}", kwargs=kwargs)

    signature, signature_str, signature_warning = signature_text(obj)
    if signature is None:
        return _result(kind, target, source, "warning", signature_warning or "signature unavailable", None, kwargs)

    try:
        if kind in {"wrapper", "vec_wrapper"}:
            # Bind a placeholder for the env/VecEnv first argument without creating one.
            signature.bind(object(), **kwargs)
            detail = "import ok; wrapper constructor accepts placeholder env and supplied kwargs"
        elif kind == "callback":
            signature.bind(**kwargs)
            detail = "import ok; callback constructor accepts supplied kwargs"
        elif kind == "policy":
            detail = "import ok; policy constructor not bound because SB3 supplies spaces and lr_schedule at model creation"
            return _result(kind, target, source, "warning", detail, signature_str, kwargs)
        else:
            detail = "import ok"
    except TypeError as exc:
        return _result(kind, target, source, "error", f"constructor signature mismatch: {exc}", signature_str, kwargs)

    return _result(kind, target, source, "ok", detail, signature_str, kwargs)


def validate_component(spec: ComponentSpec) -> CheckResult:
    obj, error = import_dotted(spec.target)
    if error is not None:
        error.kind = spec.kind
        error.source = spec.source
        error.kwargs = _jsonable_kwargs(spec.kwargs) if spec.kwargs else None
        return error
    return bind_signature(spec.kind, spec.target, obj, spec.kwargs, spec.source)


def normalize_component_items(kind: str, value: Any, source: str) -> Iterable[ComponentSpec | CheckResult]:
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    normalized: list[ComponentSpec | CheckResult] = []
    for index, item in enumerate(items):
        item_source = f"{source}[{index}]" if isinstance(value, list) else source
        if isinstance(item, str):
            normalized.append(ComponentSpec(kind, item, item_source, {}))
            continue
        if isinstance(item, dict):
            if len(item) != 1:
                normalized.append(
                    _result(
                        kind,
                        repr(item),
                        item_source,
                        "error",
                        "component mapping must contain exactly one key; check wrapper/callback YAML indentation",
                    )
                )
                continue
            target, kwargs = next(iter(item.items()))
            if not isinstance(target, str):
                normalized.append(_result(kind, repr(target), item_source, "error", "component key must be a dotted import string"))
                continue
            if kwargs is None:
                kwargs = {}
            if not isinstance(kwargs, dict):
                normalized.append(_result(kind, target, item_source, "error", "component kwargs must be a mapping/dict"))
                continue
            normalized.append(ComponentSpec(kind, target, item_source, kwargs))
            continue
        normalized.append(_result(kind, repr(item), item_source, "error", f"unsupported component entry type: {type(item).__name__}"))
    return normalized


def load_yaml_config(path: Path) -> tuple[dict[str, Any] | None, CheckResult | None]:
    if yaml is None:
        return None, _result("config", str(path), "config", "error", "PyYAML is required to parse --config files")
    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
    except Exception as exc:  # noqa: BLE001
        return None, _result("config", str(path), "config", "error", f"failed to parse YAML: {type(exc).__name__}: {exc}")
    if loaded is None:
        return {}, None
    if not isinstance(loaded, dict):
        return None, _result("config", str(path), "config", "error", "top-level YAML value must be a mapping")
    return loaded, None


def config_sections(config: dict[str, Any], env_id: str | None) -> tuple[list[tuple[str, dict[str, Any]]], list[CheckResult]]:
    errors: list[CheckResult] = []
    if env_id:
        if env_id in config:
            section = config[env_id]
            label = env_id
        elif "default" in config:
            section = config["default"]
            label = "default"
        else:
            return [], [_result("config", env_id, "config", "error", "env key not found and no default section exists")]
        if not isinstance(section, dict):
            return [], [_result("config", label, "config", "error", "selected config section must be a mapping")]
        return [(label, section)], errors

    sections: list[tuple[str, dict[str, Any]]] = []
    for label, section in config.items():
        if isinstance(section, dict):
            sections.append((str(label), section))
    return sections, errors


def collect_config_components(config_path: Path, env_id: str | None) -> tuple[list[ComponentSpec], list[CheckResult]]:
    config, error = load_yaml_config(config_path)
    if error is not None:
        return [], [error]
    assert config is not None
    specs: list[ComponentSpec] = []
    results: list[CheckResult] = []
    sections, section_errors = config_sections(config, env_id)
    results.extend(section_errors)

    for section_label, section in sections:
        for key, value in section.items():
            if key in WRAPPER_KEYS:
                for entry in normalize_component_items(WRAPPER_KEYS[key], value, f"{config_path}:{section_label}:{key}"):
                    if isinstance(entry, ComponentSpec):
                        specs.append(entry)
                    else:
                        results.append(entry)
            elif key == "callback":
                for entry in normalize_component_items("callback", value, f"{config_path}:{section_label}:callback"):
                    if isinstance(entry, ComponentSpec):
                        specs.append(entry)
                    else:
                        results.append(entry)
            elif key == "policy" and isinstance(value, str) and "." in value:
                specs.append(ComponentSpec("policy", value, f"{config_path}:{section_label}:policy", {}))
    return specs, results


def check_env_registry(env_id: str, source: str) -> CheckResult:
    try:
        import rl_zoo3.import_envs  # noqa: F401
        import gymnasium as gym
    except Exception as exc:  # noqa: BLE001
        return _result("env", env_id, source, "error", f"could not import Gymnasium/RL Zoo env registrations: {type(exc).__name__}: {exc}")
    if env_id not in gym.envs.registry:
        return _result("env", env_id, source, "error", "env id is not registered after importing rl_zoo3.import_envs and requested gym packages")
    spec = gym.envs.registry[env_id]
    return _result("env", env_id, source, "ok", f"env id registered; entry_point={spec.entry_point!r}")


def print_text(results: list[CheckResult]) -> None:
    for result in results:
        prefix = {"ok": "OK", "warning": "WARN", "error": "ERROR"}.get(result.status, result.status.upper())
        print(f"[{prefix}] {result.kind}: {result.target} ({result.source})")
        print(f"  {result.detail}")
        if result.signature:
            print(f"  signature: {result.signature}")
        if result.kwargs:
            print(f"  kwargs: {result.kwargs}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate RL Zoo custom component import strings and YAML-declared wrappers/callbacks/policies without creating environments or training."
    )
    parser.add_argument("--config", type=Path, help="Optional RL Zoo YAML hyperparameter config to inspect.")
    parser.add_argument("--env", help="Environment id whose config section should be inspected and/or registry entry checked.")
    parser.add_argument("--gym-package", action="append", default=[], help="Gymnasium registration module to import; may be repeated.")
    parser.add_argument("--wrapper", action="append", default=[], help="Dotted env wrapper import string to validate; may be repeated.")
    parser.add_argument("--vec-wrapper", action="append", default=[], help="Dotted VecEnv wrapper import string to validate; may be repeated.")
    parser.add_argument("--callback", action="append", default=[], help="Dotted callback import string to validate; may be repeated.")
    parser.add_argument("--policy", action="append", default=[], help="Dotted policy import string to validate; may be repeated.")
    parser.add_argument("--skip-registry-check", action="store_true", help="Do not check gym.envs.registry for --env.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results: list[CheckResult] = []
    specs: list[ComponentSpec] = []

    for module_name in args.gym_package:
        results.append(import_module(module_name, kind="gym_package", source="--gym-package"))

    for target in args.wrapper:
        specs.append(ComponentSpec("wrapper", target, "--wrapper", {}))
    for target in args.vec_wrapper:
        specs.append(ComponentSpec("vec_wrapper", target, "--vec-wrapper", {}))
    for target in args.callback:
        specs.append(ComponentSpec("callback", target, "--callback", {}))
    for target in args.policy:
        specs.append(ComponentSpec("policy", target, "--policy", {}))

    if args.config:
        config_specs, config_results = collect_config_components(args.config, args.env)
        specs.extend(config_specs)
        results.extend(config_results)

    for spec in specs:
        results.append(validate_component(spec))

    if args.env and not args.skip_registry_check:
        results.append(check_env_registry(args.env, source="--env"))

    counts = {"ok": 0, "warning": 0, "error": 0}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1

    if args.json:
        print(json.dumps({"summary": counts, "results": [asdict(result) for result in results]}, indent=2, sort_keys=True))
    else:
        print_text(results)
        print(f"Summary: {counts['ok']} ok, {counts['warning']} warning, {counts['error']} error")

    return 1 if counts.get("error", 0) else 0


if __name__ == "__main__":
    sys.exit(main())
