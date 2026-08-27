#!/usr/bin/env python3
"""Inspect a Cognee custom DataPoint model without running a pipeline.

The script imports a user-specified module/class and prints Pydantic fields,
Cognee metadata, and whether the class subclasses `DataPoint`. It does not call
LLMs, embeddings, databases, or Cognee pipelines.
"""

from __future__ import annotations

import argparse
import importlib
import json
from dataclasses import asdict, dataclass


@dataclass
class ModelSummary:
    class_name: str
    is_datapoint: bool
    fields: list[str]
    metadata: dict | None
    identity_fields: list[str] | None
    index_fields: list[str] | None


def inspect_model(module_name: str, class_name: str) -> ModelSummary:
    from cognee.infrastructure.engine import DataPoint

    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    metadata_field = getattr(cls, "model_fields", {}).get("metadata")
    metadata = getattr(metadata_field, "default", None) if metadata_field is not None else None
    return ModelSummary(
        class_name=class_name,
        is_datapoint=issubclass(cls, DataPoint),
        fields=list(getattr(cls, "model_fields", {}).keys()),
        metadata=metadata,
        identity_fields=(metadata or {}).get("identity_fields") if isinstance(metadata, dict) else None,
        index_fields=(metadata or {}).get("index_fields") if isinstance(metadata, dict) else None,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a Cognee custom DataPoint model.")
    parser.add_argument("--module", required=True, help="Importable module containing the model")
    parser.add_argument("--class-name", required=True, help="Class name to inspect")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    args = parser.parse_args()

    summary = inspect_model(args.module, args.class_name)
    if args.json:
        print(json.dumps(asdict(summary), indent=2, sort_keys=True, default=str))
    else:
        print(f"class={summary.class_name}")
        print(f"is_datapoint={summary.is_datapoint}")
        print(f"fields={', '.join(summary.fields)}")
        print(f"metadata={summary.metadata}")
        print(f"identity_fields={summary.identity_fields}")
        print(f"index_fields={summary.index_fields}")
    return 0 if summary.is_datapoint else 1


if __name__ == "__main__":
    raise SystemExit(main())
