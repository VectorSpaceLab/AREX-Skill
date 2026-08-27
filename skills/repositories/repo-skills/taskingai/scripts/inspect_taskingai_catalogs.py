#!/usr/bin/env python3
"""Static provider/bundle catalog summary for a TaskingAI checkout.

The helper is safe by default: it reads files under inference/providers and
plugin/bundles, but does not import TaskingAI modules, read credentials, contact
providers, start services, or write to the checkout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

MODEL_TYPE_RE = re.compile(r"^type:\s*['\"]?([a-z_]+)['\"]?\s*$", re.MULTILINE)
MODEL_SCHEMA_ID_RE = re.compile(r"^model_schema_id:\s*['\"]?([^'\"\n]+)['\"]?\s*$", re.MULTILINE)
BUNDLE_ID_RE = re.compile(r"^bundle_id:\s*['\"]?([^'\"\n]+)['\"]?\s*$", re.MULTILINE)
PLUGIN_ID_RE = re.compile(r"^plugin_id:\s*['\"]?([^'\"\n]+)['\"]?\s*$", re.MULTILINE)
CREDENTIAL_REQ_RE = re.compile(r"^\s*-\s*([A-Z0-9_]+)\s*$", re.MULTILINE)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def inspect_inference(repo_root: Path) -> Dict[str, Any]:
    providers_root = repo_root / "inference" / "providers"
    providers: List[Dict[str, Any]] = []
    type_counts: Dict[str, int] = {}
    schema_ids: List[str] = []
    if providers_root.is_dir():
        for provider_dir in sorted(p for p in providers_root.iterdir() if p.is_dir() and not p.name.startswith("template") and not p.name.startswith("__")):
            provider_yml = provider_dir / "resources" / "provider.yml"
            model_files = sorted((provider_dir / "resources" / "models").glob("*.yml")) if (provider_dir / "resources" / "models").is_dir() else []
            provider_text = _read(provider_yml) if provider_yml.is_file() else ""
            required = []
            if "required:" in provider_text:
                required = CREDENTIAL_REQ_RE.findall(provider_text.split("required:", 1)[1].split("additionalProperties", 1)[0])
            model_types: Dict[str, int] = {}
            for model_file in model_files:
                text = _read(model_file)
                model_type = (MODEL_TYPE_RE.search(text) or [None, "unknown"])[1]
                schema_id = (MODEL_SCHEMA_ID_RE.search(text) or [None, ""])[1]
                model_types[model_type] = model_types.get(model_type, 0) + 1
                type_counts[model_type] = type_counts.get(model_type, 0) + 1
                if schema_id:
                    schema_ids.append(schema_id)
            providers.append({"provider_id": provider_dir.name, "model_count": len(model_files), "model_types": model_types, "required_credentials": required})
    return {"provider_count": len(providers), "model_schema_count": len(schema_ids), "model_type_counts": type_counts, "providers": providers}


def inspect_plugins(repo_root: Path) -> Dict[str, Any]:
    bundles_root = repo_root / "plugin" / "bundles"
    bundles: List[Dict[str, Any]] = []
    plugin_count = 0
    no_credential_bundles = 0
    if bundles_root.is_dir():
        for bundle_dir in sorted(p for p in bundles_root.iterdir() if p.is_dir() and not p.name.startswith("__")):
            bundle_schema = bundle_dir / "resources" / "bundle_schema.yml"
            bundle_text = _read(bundle_schema) if bundle_schema.is_file() else ""
            bundle_id = (BUNDLE_ID_RE.search(bundle_text) or [None, bundle_dir.name])[1]
            credential_required = "credentials_schema" in bundle_text and "required:" in bundle_text
            plugins: List[str] = []
            for plugin_schema in sorted((bundle_dir / "plugins").glob("*/plugin_schema.yml")) if (bundle_dir / "plugins").is_dir() else []:
                text = _read(plugin_schema)
                plugin_id = (PLUGIN_ID_RE.search(text) or [None, plugin_schema.parent.name])[1]
                plugins.append(plugin_id)
            plugin_count += len(plugins)
            if not credential_required:
                no_credential_bundles += 1
            bundles.append({"bundle_id": bundle_id, "plugin_count": len(plugins), "plugins": plugins, "credential_required": credential_required})
    return {"bundle_count": len(bundles), "plugin_count": plugin_count, "no_credential_bundle_count": no_credential_bundles, "bundles": bundles}


def inspect(repo_root: Path) -> Dict[str, Any]:
    repo_root = repo_root.resolve()
    return {"inference": inspect_inference(repo_root), "plugin": inspect_plugins(repo_root)}


def print_human(report: Dict[str, Any]) -> None:
    inf = report["inference"]
    plug = report["plugin"]
    print("TaskingAI static catalog summary")
    print("No imports, credentials, network calls, or service startup performed.")
    print(f"Inference providers: {inf['provider_count']}")
    print(f"Inference model schemas: {inf['model_schema_count']}")
    print("Model type counts:")
    for key, value in sorted(inf["model_type_counts"].items()):
        print(f"  - {key}: {value}")
    print(f"Plugin bundles: {plug['bundle_count']}")
    print(f"Plugin implementations: {plug['plugin_count']}")
    print(f"No-credential bundles: {plug['no_credential_bundle_count']}")
    print()
    print("Provider summary:")
    for provider in inf["providers"]:
        types = ", ".join(f"{k}={v}" for k, v in sorted(provider["model_types"].items())) or "none"
        req = ", ".join(provider["required_credentials"]) or "(none/schema only)"
        print(f"  - {provider['provider_id']}: {provider['model_count']} models ({types}); credentials: {req}")
    print()
    print("Bundle summary:")
    for bundle in plug["bundles"]:
        cred = "credentialed" if bundle["credential_required"] else "no-credential or schema-only"
        print(f"  - {bundle['bundle_id']}: {bundle['plugin_count']} plugins; {cred}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Static TaskingAI inference/plugin catalog inspector")
    parser.add_argument("--repo-root", required=True, help="Path to a TaskingAI repository root")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)
    try:
        report = inspect(Path(args.repo_root))
    except Exception as exc:
        print(f"inspect_taskingai_catalogs.py: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
