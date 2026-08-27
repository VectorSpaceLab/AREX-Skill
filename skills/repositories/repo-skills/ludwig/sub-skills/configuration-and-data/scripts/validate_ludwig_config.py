#!/usr/bin/env python3
"""Lightweight Ludwig config validator with optional live Ludwig schema validation."""
import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def load_config(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    if yaml is None:
        raise RuntimeError("PyYAML is required for YAML configs; install pyyaml or pass JSON.")
    return yaml.safe_load(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate basic structure of a Ludwig YAML/JSON config.")
    parser.add_argument("config", help="Path to config YAML/JSON.")
    parser.add_argument("--skip-live-validation", action="store_true", help="Only run lightweight structural checks.")
    args = parser.parse_args()
    config = load_config(Path(args.config))
    errors = []
    if not isinstance(config, dict):
        errors.append("config must be a mapping/object")
    else:
        for key in ["input_features", "output_features"]:
            value = config.get(key)
            if not isinstance(value, list) or not value:
                errors.append(f"{key} must be a non-empty list")
            else:
                for idx, feat in enumerate(value):
                    if not isinstance(feat, dict):
                        errors.append(f"{key}[{idx}] must be a mapping")
                        continue
                    if not feat.get("name") and not feat.get("column"):
                        errors.append(f"{key}[{idx}] needs name or column")
                    if not feat.get("type"):
                        errors.append(f"{key}[{idx}] needs type")
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 2
    if not args.skip_live_validation:
        try:
            from ludwig.schema.model_config import ModelConfig
            ModelConfig.from_dict(config)
            print("live Ludwig ModelConfig validation passed")
        except Exception as exc:
            print(f"WARNING: live Ludwig validation raised {type(exc).__name__}: {exc}", file=sys.stderr)
            print("basic structural validation passed")
            return 1
    else:
        print("basic structural validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
