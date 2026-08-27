#!/usr/bin/env python3
"""Safely inspect StarVLA framework registry keys without model construction.

This script imports the StarVLA registry when possible, auto-imports public
framework modules to populate registered keys, and optionally reads a YAML config
only to report ``framework.name``. It never calls ``build_framework`` and never
loads or downloads model weights.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import pkgutil
import re
import sys
import warnings
from pathlib import Path
from typing import Any

warnings.filterwarnings("ignore", category=FutureWarning)


def _strip_scalar(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1]
    return text.strip() or None


def _framework_name_from_text(text: str) -> str | None:
    """Tiny fallback parser for common YAML shapes.

    It intentionally supports only the simple block form used by StarVLA configs:

        framework:
          name: QwenGR00T
    """
    lines = text.splitlines()
    framework_indent: int | None = None
    for raw in lines:
        without_comment = raw.split("#", 1)[0].rstrip()
        if not without_comment.strip():
            continue
        indent = len(without_comment) - len(without_comment.lstrip(" "))
        if framework_indent is None:
            if re.match(r"^\s*framework\s*:\s*$", without_comment):
                framework_indent = indent
            continue
        if indent <= framework_indent:
            break
        match = re.match(r"^\s*name\s*:\s*(.+?)\s*$", without_comment)
        if match:
            return _strip_scalar(match.group(1))
    return None


def read_framework_name(config_yaml: str | None) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    if not config_yaml:
        return None, warnings

    path = Path(config_yaml).expanduser()
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:  # pragma: no cover - environment-dependent
        return None, [f"could not read config YAML: {exc}"]

    # Prefer OmegaConf because StarVLA uses OmegaConf dotlists/YAML.
    try:
        from omegaconf import OmegaConf  # type: ignore

        cfg = OmegaConf.load(str(path))
        name = OmegaConf.select(cfg, "framework.name", default=None)
        return _strip_scalar(name), warnings
    except Exception as exc:
        warnings.append(f"OmegaConf YAML parse unavailable/failed: {type(exc).__name__}: {exc}")

    # Fall back to PyYAML if present.
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
        if isinstance(data, dict):
            framework = data.get("framework") or {}
            if isinstance(framework, dict):
                return _strip_scalar(framework.get("name")), warnings
    except Exception as exc:
        warnings.append(f"PyYAML parse unavailable/failed: {type(exc).__name__}: {exc}")

    name = _framework_name_from_text(text)
    if name is None:
        warnings.append("fallback parser did not find a simple framework.name block")
    return name, warnings


def _ensure_starvla_source_on_syspath() -> None:
    """Best-effort support for running from an unpacked StarVLA source tree.

    An installed StarVLA package is preferred. This fallback only adds a parent
    directory that visibly contains ``starVLA/model/framework``; it does not use
    the caller's current directory for any model files or checkpoints.
    """
    candidates = [Path.cwd(), *Path.cwd().parents]
    script_path = Path(__file__).resolve()
    candidates.extend(script_path.parents)
    for parent in candidates:
        if (parent / "starVLA" / "model" / "framework").exists():
            parent_text = str(parent)
            if parent_text not in sys.path:
                sys.path.insert(0, parent_text)
            return


def _candidate_source_roots() -> list[Path]:
    _ensure_starvla_source_on_syspath()
    roots: list[Path] = []
    spec = importlib.util.find_spec("starVLA")
    if spec and spec.submodule_search_locations:
        for loc in spec.submodule_search_locations:
            roots.append(Path(loc))
    return roots


def _parse_registry_decorators_from_source() -> tuple[list[str], list[str]]:
    keys: set[str] = set()
    notes: list[str] = []
    for root in _candidate_source_roots():
        framework_dir = root / "model" / "framework"
        if not framework_dir.exists():
            continue
        for path in framework_dir.rglob("*.py"):
            if any(part.startswith("_") for part in path.relative_to(framework_dir).parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except Exception as exc:  # pragma: no cover - environment-dependent
                notes.append(f"could not read {path.name}: {exc}")
                continue
            for match in re.finditer(r"FRAMEWORK_REGISTRY\.register\(\s*['\"]([^'\"]+)['\"]\s*\)", text):
                keys.add(match.group(1))
    return sorted(keys), notes


def _manual_import_framework_modules() -> list[str]:
    errors: list[str] = []
    try:
        framework_pkg = importlib.import_module("starVLA.model.framework")
    except Exception as exc:  # pragma: no cover - environment-dependent
        return [f"could not import starVLA.model.framework for manual discovery: {type(exc).__name__}: {exc}"]

    skip = {"__init__", "base_framework", "share_tools"}
    for finder, module_name, is_pkg in pkgutil.iter_modules(framework_pkg.__path__):
        if module_name in skip or module_name.startswith("_"):
            continue
        if is_pkg:
            package_name = f"starVLA.model.framework.{module_name}"
            try:
                package = importlib.import_module(package_name)
            except Exception as exc:
                errors.append(f"{package_name}: {type(exc).__name__}: {exc}")
                continue
            for _, sub_name, _ in pkgutil.iter_modules(package.__path__):
                if sub_name.startswith("_"):
                    continue
                full_name = f"{package_name}.{sub_name}"
                try:
                    importlib.import_module(full_name)
                except Exception as exc:
                    errors.append(f"{full_name}: {type(exc).__name__}: {exc}")
        else:
            full_name = f"starVLA.model.framework.{module_name}"
            try:
                importlib.import_module(full_name)
            except Exception as exc:
                errors.append(f"{full_name}: {type(exc).__name__}: {exc}")
    return errors


def load_registry_keys() -> tuple[list[str], str, list[str]]:
    _ensure_starvla_source_on_syspath()
    errors: list[str] = []
    try:
        from starVLA.model.tools import FRAMEWORK_REGISTRY  # type: ignore
    except Exception as exc:
        errors.append(f"could not import starVLA.model.tools.FRAMEWORK_REGISTRY: {type(exc).__name__}: {exc}")
        parsed, parse_notes = _parse_registry_decorators_from_source()
        errors.extend(parse_notes)
        source = "source-parse-fallback" if parsed else "unavailable"
        return parsed, source, errors

    try:
        from starVLA.model.framework.base_framework import _auto_import_framework_modules  # type: ignore

        _auto_import_framework_modules()
    except Exception as exc:
        errors.append(f"auto import failed: {type(exc).__name__}: {exc}")
        errors.extend(_manual_import_framework_modules())

    keys = sorted(getattr(FRAMEWORK_REGISTRY, "_registry", {}).keys())
    if keys:
        return keys, "starVLA.model.tools.FRAMEWORK_REGISTRY", errors

    parsed, parse_notes = _parse_registry_decorators_from_source()
    errors.extend(parse_notes)
    source = "source-parse-fallback" if parsed else "starVLA.model.tools.FRAMEWORK_REGISTRY-empty"
    return parsed, source, errors


def build_report(config_yaml: str | None) -> dict[str, Any]:
    configured_name, yaml_warnings = read_framework_name(config_yaml)
    keys, source, import_errors = load_registry_keys()
    is_registered: bool | None
    if configured_name is None or not keys:
        is_registered = None
    else:
        is_registered = configured_name in keys
    return {
        "configured_framework_name": configured_name,
        "configured_framework_is_registered": is_registered,
        "registered_framework_keys": keys,
        "registry_key_count": len(keys),
        "registry_source": source,
        "config_yaml": config_yaml,
        "warnings": yaml_warnings,
        "import_errors": import_errors,
        "safe_mode": "registry/config inspection only; no build_framework call and no model weight load",
    }


def print_text(report: dict[str, Any]) -> None:
    print("StarVLA framework registry inspection")
    print(f"Safe mode: {report['safe_mode']}")
    print(f"Registry source: {report['registry_source']}")
    print(f"Registered framework keys ({report['registry_key_count']}):")
    for key in report["registered_framework_keys"]:
        print(f"  - {key}")
    if report.get("config_yaml"):
        print(f"Configured framework.name: {report['configured_framework_name'] or '<not found>'}")
        status = report.get("configured_framework_is_registered")
        if status is True:
            print("Configured framework status: registered")
        elif status is False:
            print("Configured framework status: NOT registered")
        else:
            print("Configured framework status: unknown")
    if report["warnings"]:
        print("Warnings:", file=sys.stderr)
        for item in report["warnings"]:
            print(f"  - {item}", file=sys.stderr)
    if report["import_errors"]:
        print("Import notes/errors:", file=sys.stderr)
        for item in report["import_errors"]:
            print(f"  - {item}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "List StarVLA registered framework keys and optionally report "
            "framework.name from a YAML config without instantiating models."
        )
    )
    parser.add_argument("--config-yaml", help="Optional StarVLA YAML config to inspect for framework.name")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text")
    args = parser.parse_args(argv)

    report = build_report(args.config_yaml)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
