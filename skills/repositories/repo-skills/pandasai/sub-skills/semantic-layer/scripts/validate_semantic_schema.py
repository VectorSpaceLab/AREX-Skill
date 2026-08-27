#!/usr/bin/env python3
"""Validate a PandasAI semantic-layer schema YAML file.

Examples:
  python sub-skills/semantic-layer/scripts/validate_semantic_schema.py --schema-yaml schema.yaml
  python sub-skills/semantic-layer/scripts/validate_semantic_schema.py --schema-yaml bad.yaml --expect-valid false
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _parse_bool(value: str) -> bool:
    lowered = value.lower()
    if lowered in {"1", "true", "yes", "y"}:
        return True
    if lowered in {"0", "false", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a PandasAI SemanticLayerSchema YAML file")
    parser.add_argument("--schema-yaml", required=True, help="path to schema.yaml")
    parser.add_argument("--kind", choices=["auto", "table", "view"], default="auto", help="expected schema kind")
    parser.add_argument("--expect-valid", type=_parse_bool, default=True, help="whether validation is expected to pass")
    args = parser.parse_args()

    path = Path(args.schema_yaml)
    report: dict[str, Any] = {"schema_yaml": str(path), "expected_valid": args.expect_valid}

    try:
        import yaml
        from pandasai.data_loader.semantic_layer_schema import SemanticLayerSchema
    except Exception as exc:  # noqa: BLE001
        report.update({"ok": False, "stage": "import", "error": f"{type(exc).__name__}: {exc}"})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        schema = SemanticLayerSchema(**raw)
        actual_kind = "view" if schema.view else "table"
        kind_ok = args.kind == "auto" or args.kind == actual_kind
        report.update(
            {
                "valid": True,
                "kind": actual_kind,
                "kind_ok": kind_ok,
                "name": schema.name,
                "source_type": schema.source.type if schema.source else None,
                "columns": [col.name for col in schema.columns or []],
                "relations": [rel.model_dump(by_alias=True, exclude_none=True) for rel in schema.relations or []],
                "transformations": [t.type for t in schema.transformations or []],
                "group_by": schema.group_by or [],
            }
        )
        ok = args.expect_valid and kind_ok
    except Exception as exc:  # noqa: BLE001
        report.update({"valid": False, "error": f"{type(exc).__name__}: {exc}"})
        ok = not args.expect_valid

    report["ok"] = ok
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
