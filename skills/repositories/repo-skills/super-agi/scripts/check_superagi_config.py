#!/usr/bin/env python3
"""Validate a SuperAGI config.yaml-style file without contacting services.

Example:
  python check_superagi_config.py --config config.yaml
  python check_superagi_config.py --config config_template.yaml --allow-placeholders
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - user-facing dependency message
    print("Missing dependency: PyYAML. Install with `python -m pip install PyYAML`.", file=sys.stderr)
    raise SystemExit(2)

REQUIRED_KEYS = [
    "DB_NAME",
    "DB_HOST",
    "REDIS_URL",
    "STORAGE_TYPE",
    "TOOLS_DIR",
    "MODEL_NAME",
    "MAX_MODEL_TOKEN_LIMIT",
    "MAX_TOOL_TOKEN_LIMIT",
    "JWT_SECRET_KEY",
]

KNOWN_STORAGE_TYPES = {"FILE", "S3"}
KNOWN_VECTOR_STORES = {"REDIS", "PINECONE", "CHROMA", "QDRANT", "WEAVIATE"}
PLACEHOLDER_RE = re.compile(r"^(YOUR_|your_|REPLACE_|INSERT_|<|$)")


def looks_placeholder(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        stripped = value.strip()
        return bool(PLACEHOLDER_RE.match(stripped)) or "YOUR_" in stripped or stripped in {"password", "secret"}
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SuperAGI config keys without network/service calls.")
    parser.add_argument("--config", required=True, help="Path to config.yaml or config_template.yaml")
    parser.add_argument("--allow-placeholders", action="store_true", help="Do not fail placeholder values; report them as warnings only")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    path = Path(args.config)
    result = {"path": str(path), "errors": [], "warnings": [], "present_required": [], "missing_required": []}
    if not path.exists():
        result["errors"].append(f"config file does not exist: {path}")
    else:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if not isinstance(data, dict):
            result["errors"].append("config root must be a YAML mapping")
            data = {}
        for key in REQUIRED_KEYS:
            if key in data and data[key] not in (None, ""):
                result["present_required"].append(key)
            else:
                result["missing_required"].append(key)
                result["errors"].append(f"missing required key: {key}")
        storage = str(data.get("STORAGE_TYPE", "")).upper()
        if storage and storage not in KNOWN_STORAGE_TYPES:
            result["errors"].append(f"STORAGE_TYPE should be one of {sorted(KNOWN_STORAGE_TYPES)}, got {storage!r}")
        vector_store = data.get("RESOURCE_VECTOR_STORE")
        if vector_store and str(vector_store).upper() not in KNOWN_VECTOR_STORES:
            result["warnings"].append(f"RESOURCE_VECTOR_STORE is not one of known values: {sorted(KNOWN_VECTOR_STORES)}")
        if storage == "S3":
            for key in ["BUCKET_NAME", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]:
                if looks_placeholder(data.get(key)):
                    result["errors" if not args.allow_placeholders else "warnings"].append(f"S3 storage requires non-placeholder {key}")
        for key, value in sorted(data.items()):
            if looks_placeholder(value):
                bucket = "warnings" if args.allow_placeholders else "errors"
                if key in {"JWT_SECRET_KEY", "ENCRYPTION_KEY"} or key.endswith("API_KEY") or key.endswith("TOKEN") or key.endswith("SECRET"):
                    result[bucket].append(f"placeholder or weak secret-like value for {key}")
                else:
                    result["warnings"].append(f"placeholder/empty value for optional key {key}")
    result["ok"] = not result["errors"]

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Config: {result['path']}")
        print("OK" if result["ok"] else "NOT OK")
        for section in ["errors", "warnings"]:
            if result[section]:
                print(f"\n{section.upper()}:")
                for item in result[section]:
                    print(f"- {item}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
