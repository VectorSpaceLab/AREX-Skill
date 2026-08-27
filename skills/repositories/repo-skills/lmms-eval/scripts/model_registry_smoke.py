#!/usr/bin/env python3
"""Inspect the model registry, aliases, and a concrete model resolution."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from lmms_eval.models import (
    AVAILABLE_CHAT_TEMPLATE_MODELS,
    AVAILABLE_SIMPLE_MODELS,
    MODEL_ALIASES,
    MODEL_REGISTRY_V2,
    list_available_models,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect lmms-eval model registry state.")
    parser.add_argument("--model-id", default="qwen2_5_vl", help="Model id or alias to resolve.")
    parser.add_argument("--force-simple", action="store_true", help="Prefer the simple backend when a dual backend exists.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    args = parser.parse_args()

    resolved = MODEL_REGISTRY_V2.resolve(args.model_id, force_simple=args.force_simple)
    manifest = MODEL_REGISTRY_V2.get_manifest(args.model_id)

    report = {
        "counts": {
            "canonical_models": len(list_available_models()),
            "all_model_names": len(list_available_models(include_aliases=True)),
            "simple_backends": len(AVAILABLE_SIMPLE_MODELS),
            "chat_backends": len(AVAILABLE_CHAT_TEMPLATE_MODELS),
            "alias_groups": len(MODEL_ALIASES),
        },
        "sample_model": args.model_id,
        "manifest": {
            "model_id": manifest.model_id,
            "aliases": list(manifest.aliases),
            "simple_class_path": manifest.simple_class_path,
            "chat_class_path": manifest.chat_class_path,
        },
        "resolved": {
            "requested_name": resolved.requested_name,
            "model_id": resolved.model_id,
            "model_type": resolved.model_type,
            "class_path": resolved.class_path,
            "class_name": resolved.class_name,
        },
        "sample_keys": {
            "canonical_models": list(list_available_models())[:10],
            "aliases": sorted({alias for aliases in MODEL_ALIASES.values() for alias in aliases})[:10],
        },
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(f"canonical models: {report['counts']['canonical_models']}")
        print(f"all model names: {report['counts']['all_model_names']}")
        print(f"sample resolve: {resolved.requested_name} -> {resolved.class_path}")
        print(f"aliases for {manifest.model_id}: {', '.join(manifest.aliases) if manifest.aliases else '(none)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
