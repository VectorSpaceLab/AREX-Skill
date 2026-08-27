#!/usr/bin/env python3
"""Inspect SimpleTuner model registry metadata without importing model classes."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from importlib import metadata as importlib_metadata
from importlib import resources as importlib_resources
from pathlib import Path
from typing import Any


METADATA_RELATIVE_PATH = Path("simpletuner/helpers/models/model_metadata.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect installed SimpleTuner model metadata. By default this reads the packaged "
            "model_metadata.json file and does not import the individual model classes."
        )
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format. Default: json.",
    )
    parser.add_argument(
        "--family",
        action="append",
        default=[],
        help="Family id to include. May be repeated or comma-separated.",
    )
    parser.add_argument(
        "--prediction-type",
        default=None,
        help="Only include families with this prediction_type value.",
    )
    parser.add_argument(
        "--metadata-path",
        type=Path,
        default=None,
        help="Optional explicit model_metadata.json path for offline inspection.",
    )
    parser.add_argument(
        "--include-module-path",
        action="store_true",
        help="Include module_path in output tables and JSON family records.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only summary counts, not per-family rows.",
    )
    parser.add_argument(
        "--max-flavours",
        type=int,
        default=8,
        help="Maximum flavour names shown per Markdown row; use a negative value for all. Default: 8.",
    )
    return parser


def _candidate_from_distribution() -> tuple[Path | None, str | None, str | None]:
    try:
        dist = importlib_metadata.distribution("simpletuner")
    except importlib_metadata.PackageNotFoundError:
        return None, None, None
    candidate = Path(dist.locate_file(str(METADATA_RELATIVE_PATH)))
    version = dist.version
    if candidate.is_file():
        return candidate, "installed-distribution", version
    return None, "installed-distribution", version


def _candidate_from_resources() -> Path | None:
    try:
        resource = importlib_resources.files("simpletuner.helpers.models").joinpath("model_metadata.json")
    except (ImportError, ModuleNotFoundError, AttributeError):
        return None
    try:
        candidate = Path(resource)
    except TypeError:
        return None
    return candidate if candidate.is_file() else None


def _candidate_from_working_tree() -> Path | None:
    """Find metadata from a source checkout without importing SimpleTuner.

    This is a fallback for editable/source-tree use. Installed distribution
    metadata remains preferred, and --help never needs this lookup.
    """
    for root in (Path.cwd(), *Path.cwd().parents):
        candidate = root / METADATA_RELATIVE_PATH
        if candidate.is_file():
            return candidate
    return None


def locate_metadata_path(explicit_path: Path | None) -> tuple[Path, str, str | None]:
    if explicit_path is not None:
        path = explicit_path.expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Metadata file not found: {path}")
        return path, "explicit-path", None

    candidate, source, version = _candidate_from_distribution()
    if candidate is not None:
        return candidate, source or "installed-distribution", version

    resource_candidate = _candidate_from_resources()
    if resource_candidate is not None:
        return resource_candidate, "package-resource", version

    working_tree_candidate = _candidate_from_working_tree()
    if working_tree_candidate is not None:
        return working_tree_candidate, "working-tree-metadata", version

    raise FileNotFoundError(
        "Could not locate SimpleTuner model_metadata.json. Install SimpleTuner or pass --metadata-path."
    )


def load_metadata(path: Path) -> dict[str, dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("model_metadata.json must contain a JSON object.")

    normalized: dict[str, dict[str, Any]] = {}
    for family, meta in payload.items():
        if not isinstance(family, str) or not isinstance(meta, dict):
            raise ValueError("model metadata entries must map family strings to objects.")
        normalized[family] = dict(meta)
    return dict(sorted(normalized.items()))


def parse_family_filters(raw_filters: list[str]) -> set[str]:
    selected: set[str] = set()
    for raw in raw_filters:
        for part in str(raw).split(","):
            part = part.strip().lower()
            if part:
                selected.add(part)
    return selected


def filter_metadata(
    metadata: dict[str, dict[str, Any]],
    *,
    families: set[str],
    prediction_type: str | None,
) -> dict[str, dict[str, Any]]:
    if families:
        missing = sorted(family for family in families if family not in metadata)
        if missing:
            available = ", ".join(sorted(metadata))
            raise ValueError(f"Unknown family id(s): {', '.join(missing)}. Available: {available}")
    filtered: dict[str, dict[str, Any]] = {}
    for family, meta in metadata.items():
        if families and family not in families:
            continue
        if prediction_type is not None and meta.get("prediction_type") != prediction_type:
            continue
        filtered[family] = meta
    return filtered


def build_summary(metadata: dict[str, dict[str, Any]], *, source: str, version: str | None) -> dict[str, Any]:
    prediction_counts = Counter(str(meta.get("prediction_type")) for meta in metadata.values())
    return {
        "source": source,
        "simpletuner_version": version,
        "family_count": len(metadata),
        "prediction_type_counts": dict(sorted(prediction_counts.items())),
    }


def family_record(family: str, meta: dict[str, Any], *, include_module_path: bool) -> dict[str, Any]:
    record = {
        "family": family,
        "name": meta.get("name"),
        "class_name": meta.get("class_name"),
        "prediction_type": meta.get("prediction_type"),
        "flavour_choices": meta.get("flavour_choices", []),
    }
    if include_module_path:
        record["module_path"] = meta.get("module_path")
    return record


def emit_json(
    metadata: dict[str, dict[str, Any]],
    *,
    source: str,
    version: str | None,
    include_module_path: bool,
    summary_only: bool,
) -> None:
    summary = build_summary(metadata, source=source, version=version)
    payload: dict[str, Any] = {"summary": summary}
    if not summary_only:
        payload["families"] = [
            family_record(family, meta, include_module_path=include_module_path) for family, meta in metadata.items()
        ]
    print(json.dumps(payload, indent=2, sort_keys=True))


def _escape_markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _flavour_text(flavours: object, *, max_flavours: int) -> str:
    if not isinstance(flavours, list):
        return ""
    values = [str(item) for item in flavours]
    if max_flavours >= 0 and len(values) > max_flavours:
        shown = values[:max_flavours]
        return ", ".join(shown) + f", ... (+{len(values) - len(shown)})"
    return ", ".join(values)


def emit_markdown(
    metadata: dict[str, dict[str, Any]],
    *,
    source: str,
    version: str | None,
    include_module_path: bool,
    summary_only: bool,
    max_flavours: int,
) -> None:
    summary = build_summary(metadata, source=source, version=version)
    print("# SimpleTuner model registry metadata")
    print()
    print(f"- Source: {summary['source']}")
    print(f"- SimpleTuner version: {summary['simpletuner_version'] or 'unknown'}")
    print(f"- Families: {summary['family_count']}")
    print("- Prediction types:")
    for prediction_type, count in summary["prediction_type_counts"].items():
        print(f"  - `{prediction_type}`: {count}")
    if summary_only:
        return
    print()
    columns = ["family", "name", "prediction_type", "flavours"]
    if include_module_path:
        columns.append("module_path")
    print("| " + " | ".join(columns) + " |")
    print("|" + "|".join("---" for _ in columns) + "|")
    for family, meta in metadata.items():
        row = [
            family,
            meta.get("name", ""),
            meta.get("prediction_type", ""),
            _flavour_text(meta.get("flavour_choices", []), max_flavours=max_flavours),
        ]
        if include_module_path:
            row.append(meta.get("module_path", ""))
        print("| " + " | ".join(_escape_markdown_cell(value) for value in row) + " |")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        metadata_path, source, version = locate_metadata_path(args.metadata_path)
        metadata = load_metadata(metadata_path)
        filtered = filter_metadata(
            metadata,
            families=parse_family_filters(args.family),
            prediction_type=args.prediction_type,
        )
        if args.format == "json":
            emit_json(
                filtered,
                source=source,
                version=version,
                include_module_path=args.include_module_path,
                summary_only=args.summary_only,
            )
        else:
            emit_markdown(
                filtered,
                source=source,
                version=version,
                include_module_path=args.include_module_path,
                summary_only=args.summary_only,
                max_flavours=args.max_flavours,
            )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
