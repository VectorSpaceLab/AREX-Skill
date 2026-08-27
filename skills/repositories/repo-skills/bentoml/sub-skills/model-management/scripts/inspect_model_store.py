#!/usr/bin/env python3
"""Read-only inspection of the active BentoML model store."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


def _model_to_dict(model: Any, include_path: bool = True) -> dict[str, Any]:
    info = getattr(model, "info", None)
    info_dict: dict[str, Any]
    if info is not None and hasattr(info, "to_dict"):
        info_dict = info.to_dict()
    else:
        info_dict = {}

    result: dict[str, Any] = {
        "tag": str(getattr(model, "tag", "")),
        "module": info_dict.get("module", getattr(info, "module", "")),
        "labels": info_dict.get("labels", {}),
        "metadata_keys": sorted((info_dict.get("metadata") or {}).keys()),
        "context": info_dict.get("context", {}),
        "signatures": info_dict.get("signatures", {}),
        "creation_time": str(info_dict.get("creation_time", "")),
    }
    if include_path:
        result["path"] = str(getattr(model, "path", ""))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect BentoML models visible in the active environment without mutating the store."
    )
    parser.add_argument("--tag", help="Optional model tag or name to inspect.")
    parser.add_argument(
        "--no-path",
        action="store_true",
        help="Do not print local model paths in output.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON only.",
    )
    args = parser.parse_args()

    try:
        import bentoml
    except Exception as exc:  # pragma: no cover - diagnostic script
        print(f"ERROR: failed to import bentoml: {exc}", file=sys.stderr)
        return 2

    include_path = not args.no_path
    payload: dict[str, Any] = {
        "bentoml_version": getattr(bentoml, "__version__", "unknown"),
        "environment": {
            key: value
            for key, value in os.environ.items()
            if key.startswith("BENTOML") or key in {"BENTOML_HOME"}
        },
        "query": args.tag,
        "models": [],
        "errors": [],
    }

    try:
        if args.tag:
            try:
                model = bentoml.models.get(args.tag)
            except Exception as exc:  # pragma: no cover - diagnostic script
                payload["errors"].append(
                    {"operation": "get", "tag": args.tag, "error": f"{type(exc).__name__}: {exc}"}
                )
                models = bentoml.models.list(args.tag.split(":", 1)[0])
                payload["models"] = [_model_to_dict(model, include_path) for model in models]
            else:
                payload["models"] = [_model_to_dict(model, include_path)]
        else:
            payload["models"] = [
                _model_to_dict(model, include_path) for model in bentoml.models.list()
            ]
    except Exception as exc:  # pragma: no cover - diagnostic script
        payload["errors"].append(
            {"operation": "list", "error": f"{type(exc).__name__}: {exc}"}
        )

    if args.json:
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(f"BentoML version: {payload['bentoml_version']}")
        if payload["environment"]:
            print("BentoML environment variables:")
            for key, value in sorted(payload["environment"].items()):
                print(f"  {key}={value}")
        if payload["errors"]:
            print("Errors:")
            for error in payload["errors"]:
                print(f"  {error['operation']}: {error['error']}")
        print(f"Models ({len(payload['models'])}):")
        for model in payload["models"]:
            print(f"- {model['tag']} module={model['module'] or '<none>'}")
            if include_path:
                print(f"  path: {model.get('path', '')}")
            if model.get("metadata_keys"):
                print(f"  metadata keys: {', '.join(model['metadata_keys'])}")
            context = model.get("context") or {}
            if context:
                framework = context.get("framework_name") or ""
                versions = context.get("framework_versions") or {}
                print(f"  context: framework={framework or '<none>'} versions={versions}")

    return 1 if payload["errors"] and not payload["models"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
