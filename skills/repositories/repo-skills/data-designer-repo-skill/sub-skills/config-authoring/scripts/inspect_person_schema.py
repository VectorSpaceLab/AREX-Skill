#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Inspect installed managed persona parquet schemas for a DataDesigner locale.

The script uses installed ``data_designer`` package constants and optional
``DATA_DESIGNER_MANAGED_ASSETS_PATH`` support. It never reads a source checkout.
Missing packages, pyarrow, or locale parquet files produce clear diagnostics
instead of tracebacks.

Examples:
    python inspect_person_schema.py en_US
    python inspect_person_schema.py en_US --json
    python inspect_person_schema.py --list-locales
    python inspect_person_schema.py --list-installed --managed-assets-path ~/.data-designer/managed-assets
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_config_constants() -> tuple[Path, list[str]]:
    try:
        from data_designer.config.utils.constants import (  # type: ignore
            LOCALES_WITH_MANAGED_DATASETS,
            MANAGED_ASSETS_PATH,
        )
    except Exception as exc:
        print(
            "Could not import DataDesigner config constants. Install data-designer before running this helper. "
            f"Import error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    return Path(MANAGED_ASSETS_PATH), list(LOCALES_WITH_MANAGED_DATASETS)


def _load_field_categories() -> tuple[set[str], set[str], str | None]:
    try:
        from data_designer.engine.sampling_gen.entities.dataset_based_person_fields import (  # type: ignore
            PERSONA_FIELDS,
            PII_FIELDS,
        )
    except Exception as exc:
        return set(), set(), f"Could not import person field categories: {type(exc).__name__}: {exc}"
    return set(PII_FIELDS), set(PERSONA_FIELDS), None


def _installed_locale_files(managed_assets_path: Path) -> list[str]:
    dataset_dir = managed_assets_path.expanduser() / "datasets"
    if not dataset_dir.exists():
        return []
    return sorted(path.stem for path in dataset_dir.glob("*.parquet") if path.is_file())


def _dataset_path(managed_assets_path: Path, locale: str) -> Path:
    return managed_assets_path.expanduser() / "datasets" / f"{locale}.parquet"


def _read_schema(path: Path) -> dict[str, str]:
    try:
        import pyarrow.parquet as pq  # type: ignore
    except Exception as exc:
        print(
            "Could not import pyarrow.parquet, which is required to inspect managed persona parquet schemas. "
            f"Import error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc

    try:
        return {field.name: str(field.type) for field in pq.read_schema(path)}
    except Exception as exc:
        print(f"Could not read parquet schema at {path}: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def _split_fields(schema: dict[str, str], pii_fields: set[str], persona_fields: set[str]) -> dict[str, dict[str, str]]:
    non_null_schema = {name: dtype for name, dtype in schema.items() if dtype != "null"}
    pii = {name: dtype for name, dtype in non_null_schema.items() if name in pii_fields}
    persona = {name: dtype for name, dtype in non_null_schema.items() if name in persona_fields}
    classified = set(pii) | set(persona)
    other = {name: dtype for name, dtype in non_null_schema.items() if name not in classified}
    return {"pii": pii, "persona": persona, "other": other}


def _print_fields(title: str, fields: dict[str, str]) -> None:
    print(f"=== {title} ({len(fields)}) ===")
    if not fields:
        print("  <none>")
        return
    for name, dtype in fields.items():
        print(f"  {name}: {dtype}")


def _print_payload(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    if payload.get("status") != "ok":
        print(payload["message"], file=sys.stderr)
        if installed := payload.get("installed_locales"):
            print("Installed locale files: " + ", ".join(installed), file=sys.stderr)
        if managed := payload.get("managed_locales"):
            print("Managed locales supported by this package: " + ", ".join(managed), file=sys.stderr)
        return

    print(f"Locale: {payload['locale']}")
    print(f"Dataset: {payload['dataset_path']}")
    if payload.get("warning"):
        print(f"Warning: {payload['warning']}")
    print()
    groups = payload["fields"]
    _print_fields("PII fields: included without with_synthetic_personas", groups["pii"])
    print()
    _print_fields("Synthetic persona fields: included when with_synthetic_personas=True", groups["persona"])
    if groups["other"]:
        print()
        _print_fields("Other non-null fields", groups["other"])


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("locale", nargs="?", help="Managed persona locale, e.g. en_US")
    parser.add_argument(
        "--managed-assets-path",
        type=Path,
        default=None,
        help="Override managed assets root; defaults to DataDesigner constants / DATA_DESIGNER_MANAGED_ASSETS_PATH",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument(
        "--list-locales",
        action="store_true",
        help="List managed locales supported by the installed package",
    )
    parser.add_argument("--list-installed", action="store_true", help="List locale parquet files currently installed")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    default_managed_assets_path, managed_locales = _load_config_constants()
    managed_assets_path = args.managed_assets_path or default_managed_assets_path

    if args.list_locales:
        payload = {"managed_locales": managed_locales}
        _print_payload(payload, as_json=args.json) if args.json else print("\n".join(managed_locales))
        return 0

    if args.list_installed:
        installed = _installed_locale_files(managed_assets_path)
        payload = {"managed_assets_path": str(managed_assets_path.expanduser()), "installed_locales": installed}
        if args.json:
            _print_payload(payload, as_json=True)
        else:
            print("\n".join(installed) if installed else "<none>")
        return 0

    if not args.locale:
        print("Usage error: provide a locale or use --list-locales/--list-installed", file=sys.stderr)
        return 2

    locale = args.locale
    path = _dataset_path(managed_assets_path, locale)
    if not path.exists():
        payload = {
            "status": "missing-dataset",
            "locale": locale,
            "dataset_path": str(path),
            "managed_assets_path": str(managed_assets_path.expanduser()),
            "managed_locales": managed_locales,
            "installed_locales": _installed_locale_files(managed_assets_path),
            "message": (
                f"Locale {locale!r} is not available locally; expected managed persona dataset at {path}. "
                "Download/configure managed assets or use PersonFromFakerSamplerParams as a fallback."
            ),
        }
        _print_payload(payload, as_json=args.json)
        return 1

    pii_fields, persona_fields, warning = _load_field_categories()
    schema = _read_schema(path)
    groups = _split_fields(schema, pii_fields, persona_fields)
    if warning and not groups["pii"] and not groups["persona"]:
        # If category constants are unavailable, keep the schema useful by
        # reporting all non-null fields as "other".
        groups["other"] = {name: dtype for name, dtype in schema.items() if dtype != "null"}

    payload = {
        "status": "ok",
        "locale": locale,
        "dataset_path": str(path),
        "managed_assets_path": str(managed_assets_path.expanduser()),
        "is_managed_locale_in_package": locale in managed_locales,
        "warning": warning,
        "fields": groups,
    }
    _print_payload(payload, as_json=args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
