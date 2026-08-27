#!/usr/bin/env python3
"""Audit an initialized Langchain-Chatchat data/config root.

This script reads YAML/config files and checks expected directories. It does not
start the server, call model providers, rebuild vectors, or modify user data.

Example:
  python chatchat_config_audit.py --chatchat-root /path/to/chatchat-data --json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

CONFIG_FILES = [
    "basic_settings.yaml",
    "kb_settings.yaml",
    "model_settings.yaml",
    "tool_settings.yaml",
    "prompt_settings.yaml",
]


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        return {"_error": "PyYAML is not installed; cannot parse YAML"}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"_parsed_type": type(data).__name__}
    except Exception as exc:
        return {"_error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a Langchain-Chatchat CHATCHAT_ROOT directory.")
    parser.add_argument("--chatchat-root", required=True, help="Initialized data/config root to inspect.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    root = Path(args.chatchat_root).expanduser().resolve()
    report: dict[str, Any] = {
        "root_exists": root.exists(),
        "root": str(root),
        "config_files": {},
        "directories": {},
        "summary": {},
        "warnings": [],
        "ok": True,
    }

    for rel in CONFIG_FILES:
        path = root / rel
        entry = {"exists": path.is_file()}
        if path.is_file():
            parsed = load_yaml(path)
            entry["parse_ok"] = "_error" not in parsed
            entry["keys"] = sorted([k for k in parsed.keys() if not k.startswith("_")])[:80]
            if "_error" in parsed:
                entry["error"] = parsed["_error"]
            if rel == "basic_settings.yaml":
                report["summary"]["API_SERVER"] = parsed.get("API_SERVER")
                report["summary"]["WEBUI_SERVER"] = parsed.get("WEBUI_SERVER")
                report["summary"]["KB_ROOT_PATH"] = parsed.get("KB_ROOT_PATH")
                report["summary"]["SQLALCHEMY_DATABASE_URI"] = parsed.get("SQLALCHEMY_DATABASE_URI")
            if rel == "kb_settings.yaml":
                report["summary"]["DEFAULT_VS_TYPE"] = parsed.get("DEFAULT_VS_TYPE")
                report["summary"]["DEFAULT_KNOWLEDGE_BASE"] = parsed.get("DEFAULT_KNOWLEDGE_BASE")
            if rel == "model_settings.yaml":
                report["summary"]["DEFAULT_LLM_MODEL"] = parsed.get("DEFAULT_LLM_MODEL")
                report["summary"]["DEFAULT_EMBEDDING_MODEL"] = parsed.get("DEFAULT_EMBEDDING_MODEL")
                platforms = parsed.get("MODEL_PLATFORMS")
                if isinstance(platforms, list):
                    report["summary"]["MODEL_PLATFORMS"] = [
                        {"platform_name": p.get("platform_name"), "platform_type": p.get("platform_type"), "api_base_url": p.get("api_base_url")}
                        for p in platforms if isinstance(p, dict)
                    ]
        else:
            report["ok"] = False
        report["config_files"][rel] = entry

    for rel in ["data", "data/knowledge_base", "data/logs", "data/media", "data/temp"]:
        exists = (root / rel).is_dir()
        report["directories"][rel] = exists
        if not exists:
            report["warnings"].append(f"Missing expected directory: {rel}")

    if not root.exists():
        report["ok"] = False
        report["warnings"].append("CHATCHAT_ROOT does not exist; run `chatchat init` after choosing the intended root.")
    missing_configs = [name for name, entry in report["config_files"].items() if not entry["exists"]]
    if missing_configs:
        report["ok"] = False
        report["warnings"].append("Missing config files: " + ", ".join(missing_configs))

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Chatchat config audit for {root}: {'OK' if report['ok'] else 'CHECK'}")
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")
        for key, value in report["summary"].items():
            print(f"{key}: {value}")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
