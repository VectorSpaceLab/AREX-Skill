#!/usr/bin/env python3
"""Validate a Kedro catalog YAML file without echoing credential values."""

from __future__ import annotations

import argparse
import copy
import re
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml

_SECRET_KEY_RE = re.compile(
    r"(secret|password|passwd|token|api[_-]?key|access[_-]?key|credential)",
    re.IGNORECASE,
)


def _load_yaml_mapping(path: Path, label: str, *, allow_empty: bool) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as yaml_file:
            loaded = yaml.safe_load(yaml_file)
    except FileNotFoundError:
        raise ValueError(f"{label} file does not exist: {path}") from None
    except yaml.YAMLError as exc:
        raise ValueError(f"{label} YAML is invalid: {exc}") from exc

    if loaded is None and allow_empty:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError(f"{label} YAML must contain a top-level mapping/dictionary.")
    return loaded


def _iter_secret_values(value: Any, parent_key: str = "") -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            yield from _iter_secret_values(nested, key_text)
    elif isinstance(value, list | tuple | set):
        for nested in value:
            yield from _iter_secret_values(nested, parent_key)
    elif isinstance(value, str) and len(value) >= 4 and _SECRET_KEY_RE.search(parent_key):
        yield value


def _redact(message: str, credentials: Mapping[str, Any]) -> str:
    redacted = message
    for secret in sorted(set(_iter_secret_values(credentials)), key=len, reverse=True):
        redacted = redacted.replace(secret, "<redacted>")
    return redacted


def _is_pattern(name: str) -> bool:
    return "{" in name


def _find_interpolation_paths(value: Any, path: str) -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            paths.extend(_find_interpolation_paths(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(_find_interpolation_paths(nested, f"{path}[{index}]"))
    elif isinstance(value, str) and "${" in value:
        paths.append(path)
    return paths


def _parse_load_versions(entries: list[str] | None) -> dict[str, str]:
    load_versions: dict[str, str] = {}
    for entry in entries or []:
        if "=" not in entry:
            raise ValueError(
                "--load-version values must use DATASET=VERSION syntax."
            )
        dataset_name, version = entry.split("=", 1)
        dataset_name = dataset_name.strip()
        version = version.strip()
        if not dataset_name or not version:
            raise ValueError(
                "--load-version values must include both DATASET and VERSION."
            )
        load_versions[dataset_name] = version
    return load_versions


def _preflight_catalog(raw_catalog: Mapping[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    catalog: dict[str, dict[str, Any]] = {}
    ignored_private_keys: list[str] = []
    errors: list[str] = []

    for raw_name, dataset_config in raw_catalog.items():
        name = str(raw_name)
        if name.startswith("_"):
            ignored_private_keys.append(name)
            continue
        if not isinstance(dataset_config, dict):
            errors.append(
                f"Catalog entry '{name}' must be a mapping. If it is an interpolation helper, prefix the key with '_'."
            )
            continue
        if "type" not in dataset_config:
            errors.append(f"Catalog entry '{name}' is missing required key 'type'.")
            continue
        catalog[name] = dict(dataset_config)

    if errors:
        raise ValueError("\n".join(errors))
    return catalog, ignored_private_keys


def _import_kedro_apis() -> tuple[Any, Any]:
    try:
        from kedro.io import DataCatalog
        from kedro.io.core import parse_dataset_definition
    except Exception as exc:  # pragma: no cover - depends on caller environment
        print(f"ERROR: Unable to import Kedro catalog APIs: {exc}", file=sys.stderr)
        print("Install Kedro in the active Python environment and retry.", file=sys.stderr)
        sys.exit(2)
    return DataCatalog, parse_dataset_definition


def _resolve_declared_type(
    name: str,
    dataset_config: Mapping[str, Any],
    parse_dataset_definition: Any,
) -> str:
    del name
    class_obj, _ = parse_dataset_definition(copy.deepcopy(dict(dataset_config)))
    return f"{class_obj.__module__}.{class_obj.__qualname__}"


def validate(args: argparse.Namespace) -> int:
    DataCatalog, parse_dataset_definition = _import_kedro_apis()
    raw_catalog = _load_yaml_mapping(args.catalog_yaml, "Catalog", allow_empty=True)
    credentials = (
        _load_yaml_mapping(args.credentials_yaml, "Credentials", allow_empty=True)
        if args.credentials_yaml
        else {}
    )
    load_versions = _parse_load_versions(args.load_version)
    catalog_config, ignored_private_keys = _preflight_catalog(raw_catalog)

    warnings = []
    interpolation_paths = _find_interpolation_paths(catalog_config, "catalog")
    if interpolation_paths:
        shown = ", ".join(interpolation_paths[:8])
        suffix = "" if len(interpolation_paths) <= 8 else ", ..."
        warnings.append(
            "unresolved OmegaConf-style interpolation tokens found at "
            f"{shown}{suffix}; standalone YAML validation may be incomplete"
        )

    try:
        catalog = DataCatalog.from_config(
            catalog_config,
            credentials=credentials,
            load_versions=load_versions,
            save_version=args.save_version,
        )
    except Exception as exc:
        print("ERROR: DataCatalog.from_config() failed.", file=sys.stderr)
        print(_redact(str(exc), credentials), file=sys.stderr)
        return 1

    explicit_names = [name for name in catalog_config if not _is_pattern(name)]
    pattern_names = [name for name in catalog_config if _is_pattern(name)]

    type_errors: list[str] = []
    resolved_types: dict[str, str] = {}
    if args.resolve_types:
        for name in explicit_names:
            try:
                resolved_type = catalog.get_type(name)
            except Exception as exc:
                type_errors.append(f"{name}: {_redact(str(exc), credentials)}")
            else:
                resolved_types[name] = resolved_type or "<unresolved>"
        for name in pattern_names:
            try:
                resolved_types[name] = _resolve_declared_type(
                    name, catalog_config[name], parse_dataset_definition
                )
            except Exception as exc:
                type_errors.append(f"{name}: {_redact(str(exc), credentials)}")
    else:
        for name, dataset_config in catalog_config.items():
            resolved_types[name] = str(dataset_config.get("type", "<missing>"))

    if type_errors:
        print("ERROR: Catalog structure loaded, but one or more dataset types failed to resolve.", file=sys.stderr)
        for error in type_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("OK: catalog configuration is valid for DataCatalog.from_config().")
    print(f"Catalog file: {args.catalog_yaml}")
    if args.credentials_yaml:
        print(f"Credentials file: {args.credentials_yaml} (values redacted)")
    else:
        print("Credentials file: <not supplied>")

    if ignored_private_keys:
        print("Ignored private helper keys:")
        for name in sorted(ignored_private_keys):
            print(f"- {name}")

    print(f"Explicit datasets ({len(explicit_names)}):")
    for name in explicit_names:
        print(f"- {name}: {resolved_types.get(name, '<unresolved>')}")

    print(f"Declared factory patterns ({len(pattern_names)}):")
    for name in pattern_names:
        print(f"- {name}: {resolved_types.get(name, '<unresolved>')}")

    resolver_patterns = catalog.config_resolver.list_patterns()
    if resolver_patterns:
        print("Resolver pattern priority, including runtime defaults:")
        for pattern in resolver_patterns:
            print(f"- {pattern}")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely validate a Kedro catalog YAML file and optional credentials YAML "
            "without loading/saving datasets or printing credential values."
        )
    )
    parser.add_argument(
        "--catalog-yaml",
        required=True,
        type=Path,
        help="Path to a catalog.yml-style YAML file.",
    )
    parser.add_argument(
        "--credentials-yaml",
        type=Path,
        help="Optional path to a credentials.yml-style YAML file.",
    )
    parser.add_argument(
        "--load-version",
        action="append",
        metavar="DATASET=VERSION",
        help="Optional load version override; repeat for multiple datasets.",
    )
    parser.add_argument(
        "--save-version",
        help="Optional save version passed to DataCatalog.from_config().",
    )
    parser.add_argument(
        "--no-resolve-types",
        dest="resolve_types",
        action="store_false",
        help="Only validate structure; do not resolve dataset class imports.",
    )
    parser.set_defaults(resolve_types=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return validate(args)
    except ValueError as exc:
        credentials: dict[str, Any] = {}
        print(f"ERROR: {_redact(str(exc), credentials)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
