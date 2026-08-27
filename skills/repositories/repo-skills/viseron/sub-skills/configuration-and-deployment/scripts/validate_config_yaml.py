#!/usr/bin/env python3
"""Safely validate Viseron YAML/secrets references without starting Viseron.

This helper parses a candidate config.yaml and optional secrets.yaml, reports
missing !secret keys, and warns when top-level component entries are null. It
performs only local file reads and does not import or start Viseron.

Examples:
  python validate_config_yaml.py /path/to/config.yaml
  python validate_config_yaml.py /path/to/config.yaml --secrets /path/to/secrets.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SecretRef:
    """A !secret reference found while parsing config.yaml."""

    key: str
    line: int | None = None
    column: int | None = None

    @property
    def location(self) -> str:
        if self.line is None or self.column is None:
            return "unknown location"
        return f"line {self.line}, column {self.column}"


class ValidationError(RuntimeError):
    """Expected validation failure displayed without a Python traceback."""


def _load_yaml_with_pyyaml(path: Path, *, collect_secrets: bool) -> Any:
    import yaml  # type: ignore[import-not-found]

    class Loader(yaml.SafeLoader):
        """SafeLoader subclass so the !secret constructor is local to this script."""

    def secret_constructor(loader: yaml.SafeLoader, node: yaml.Node) -> SecretRef:
        mark = getattr(node, "start_mark", None)
        return SecretRef(
            key=loader.construct_scalar(node),
            line=(mark.line + 1) if mark else None,
            column=(mark.column + 1) if mark else None,
        )

    if collect_secrets:
        Loader.add_constructor("!secret", secret_constructor)
    with path.open("r", encoding="utf-8") as handle:
        return yaml.load(handle, Loader=Loader)


def _load_yaml_with_ruamel(path: Path, *, collect_secrets: bool) -> Any:
    from ruamel.yaml import YAML  # type: ignore[import-not-found]

    yaml = YAML(typ="safe", pure=True)

    def secret_constructor(constructor: Any, node: Any) -> SecretRef:
        mark = getattr(node, "start_mark", None)
        return SecretRef(
            key=constructor.construct_scalar(node),
            line=(mark.line + 1) if mark else None,
            column=(mark.column + 1) if mark else None,
        )

    if collect_secrets:
        yaml.constructor.add_constructor("!secret", secret_constructor)
    with path.open("r", encoding="utf-8") as handle:
        return yaml.load(handle)


def load_yaml(path: Path, *, collect_secrets: bool = False) -> Any:
    """Load YAML using PyYAML when available, falling back to ruamel.yaml."""
    try:
        return _load_yaml_with_pyyaml(path, collect_secrets=collect_secrets)
    except ModuleNotFoundError as pyyaml_error:
        try:
            return _load_yaml_with_ruamel(path, collect_secrets=collect_secrets)
        except ModuleNotFoundError as ruamel_error:
            raise ValidationError(
                "No YAML parser is available. Install PyYAML or ruamel.yaml, or run "
                "this helper inside an environment that has Viseron's YAML dependencies."
            ) from ruamel_error
        except Exception:
            raise
    except Exception:
        raise


def collect_secret_refs(value: Any) -> list[SecretRef]:
    """Return all SecretRef instances nested in a parsed YAML object."""
    refs: list[SecretRef] = []
    if isinstance(value, SecretRef):
        refs.append(value)
    elif isinstance(value, dict):
        for key, nested_value in value.items():
            refs.extend(collect_secret_refs(key))
            refs.extend(collect_secret_refs(nested_value))
    elif isinstance(value, list):
        for item in value:
            refs.extend(collect_secret_refs(item))
    return refs


def validate(config_path: Path, secrets_path: Path | None) -> tuple[int, dict[str, Any]]:
    """Validate config/secrets files and return (exit_code, report)."""
    if not config_path.exists():
        raise ValidationError(f"config file not found: {config_path}")
    if not config_path.is_file():
        raise ValidationError(f"config path is not a file: {config_path}")

    try:
        config_data = load_yaml(config_path, collect_secrets=True)
    except Exception as exc:  # noqa: BLE001 - normalize parser errors for users.
        raise ValidationError(f"failed to parse config YAML: {exc}") from exc

    if config_data is None:
        config_data = {}
    if not isinstance(config_data, dict):
        raise ValidationError("config YAML must be a mapping at the top level")

    refs = collect_secret_refs(config_data)
    secrets_file = secrets_path or (config_path.parent / "secrets.yaml")
    secrets_data: Any = None
    secrets_present = secrets_file.exists()
    secrets_error: str | None = None

    if secrets_present:
        try:
            secrets_data = load_yaml(secrets_file, collect_secrets=False)
        except Exception as exc:  # noqa: BLE001 - normalize parser errors for users.
            secrets_error = f"failed to parse secrets YAML: {exc}"

    secret_keys: set[str] = set()
    if secrets_error is None and secrets_present:
        if secrets_data is None:
            secrets_data = {}
        if not isinstance(secrets_data, dict):
            secrets_error = "secrets YAML must be a mapping at the top level"
        else:
            secret_keys = {str(key) for key in secrets_data}

    missing = []
    if refs:
        if not secrets_present:
            missing = refs
        elif secrets_error is None:
            missing = [ref for ref in refs if ref.key not in secret_keys]

    null_components = [key for key, value in config_data.items() if value is None]

    report: dict[str, Any] = {
        "config": str(config_path),
        "secrets": str(secrets_file) if secrets_present else None,
        "top_level_components": [str(key) for key in config_data.keys()],
        "secret_references": [
            {"key": ref.key, "line": ref.line, "column": ref.column} for ref in refs
        ],
        "missing_secrets": [
            {"key": ref.key, "line": ref.line, "column": ref.column}
            for ref in missing
        ],
        "null_top_level_components": [str(key) for key in null_components],
        "secrets_error": secrets_error,
    }

    exit_code = 0
    if missing or secrets_error:
        exit_code = 2
    return exit_code, report


def print_text_report(report: dict[str, Any]) -> None:
    """Print a human-readable report without secret values."""
    print(f"Config: {report['config']}")
    print(f"Top-level components: {', '.join(report['top_level_components']) or '(none)'}")

    if report["secret_references"]:
        print("Secret references:")
        for ref in report["secret_references"]:
            loc = (
                f"line {ref['line']}, column {ref['column']}"
                if ref["line"] is not None and ref["column"] is not None
                else "unknown location"
            )
            print(f"  - {ref['key']} ({loc})")
    else:
        print("Secret references: none")

    if report["null_top_level_components"]:
        print("Warnings:")
        for component in report["null_top_level_components"]:
            print(
                "  - top-level component "
                f"{component!r} is null; Viseron normalizes this to {{}}, "
                "but explicit {} is clearer."
            )

    if report["secrets_error"]:
        print(f"ERROR: {report['secrets_error']}")

    if report["missing_secrets"]:
        print("ERROR: missing secrets:")
        for ref in report["missing_secrets"]:
            loc = (
                f"line {ref['line']}, column {ref['column']}"
                if ref["line"] is not None and ref["column"] is not None
                else "unknown location"
            )
            print(f"  - {ref['key']} ({loc})")
    elif not report["secrets_error"]:
        print("Missing secrets: none")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Parse a Viseron config.yaml and optional secrets.yaml without starting "
            "Viseron; report missing !secret keys and null top-level components."
        )
    )
    parser.add_argument("config", type=Path, help="Path to config.yaml to validate")
    parser.add_argument(
        "--secrets",
        type=Path,
        default=None,
        help="Path to secrets.yaml; defaults to secrets.yaml next to config.yaml",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON report instead of text",
    )
    args = parser.parse_args(argv)

    try:
        exit_code, report = validate(args.config, args.secrets)
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
