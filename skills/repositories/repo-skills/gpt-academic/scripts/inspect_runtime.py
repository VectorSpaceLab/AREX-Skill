#!/usr/bin/env python3
"""Print a safe GPT Academic runtime summary from a checkout.

This script does not print API keys and does not call remote services.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", help="GPT Academic checkout root; defaults to current working directory")
    return parser.parse_args()


def setup_repo(repo_root: str | None) -> Path:
    root = Path(repo_root or os.getcwd()).resolve()
    if not (root / "crazy_functional.py").exists():
        raise SystemExit(f"Not a GPT Academic checkout: {root}")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.chdir(root)
    return root


def safe_import(name: str):
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"


def safe_conf(toolbox, *names):
    try:
        values = toolbox.get_conf(*names)
        if len(names) == 1:
            values = (values,)
        return dict(zip(names, values))
    except Exception as exc:  # noqa: BLE001
        return {name: f"<unavailable: {type(exc).__name__}>" for name in names}


def main() -> int:
    args = parse_args()
    root = setup_repo(args.repo_root)
    summary = {
        "repo_root": str(root),
        "python": sys.version.split()[0],
        "version_file": None,
        "imports": {},
        "config_snapshot": {},
        "core_functions": [],
        "plugin_count": None,
        "plugin_groups": {},
        "sample_plugins_by_group": {},
        "model_registry_size": None,
        "sample_model_registry_keys": [],
    }
    version_path = root / "version"
    if version_path.exists():
        try:
            summary["version_file"] = json.loads(version_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            summary["version_file"] = f"unreadable: {exc}"
    modules = {}
    for module_name in ["gradio", "toolbox", "core_functional", "crazy_functional", "check_proxy"]:
        module, error = safe_import(module_name)
        summary["imports"][module_name] = "ok" if error is None else error
        modules[module_name] = module
    toolbox = modules.get("toolbox")
    if toolbox:
        config_names = ["LLM_MODEL", "AVAIL_LLM_MODELS", "DEFAULT_FN_GROUPS", "USE_PROXY", "WEB_PORT", "PATH_LOGGING"]
        summary["config_snapshot"] = safe_conf(toolbox, *config_names)
    core_functional = modules.get("core_functional")
    if core_functional:
        try:
            summary["core_functions"] = list(core_functional.get_core_functions().keys())
        except Exception as exc:  # noqa: BLE001
            summary["core_functions"] = [f"<unavailable: {type(exc).__name__}: {exc}>"]
    crazy_functional = modules.get("crazy_functional")
    if crazy_functional:
        try:
            plugins = crazy_functional.get_crazy_functions()
            summary["plugin_count"] = len(plugins)
            group_counts = Counter()
            samples = defaultdict(list)
            for name, meta in plugins.items():
                for group in str(meta.get("Group", "对话")).split("|"):
                    group_counts[group] += 1
                    if len(samples[group]) < 8:
                        samples[group].append(name)
            summary["plugin_groups"] = dict(group_counts)
            summary["sample_plugins_by_group"] = dict(samples)
        except Exception as exc:  # noqa: BLE001
            summary["plugin_count"] = f"<unavailable: {type(exc).__name__}: {exc}>"
    bridge_all, error = safe_import("request_llms.bridge_all")
    summary["imports"]["request_llms.bridge_all"] = "ok" if error is None else error
    if bridge_all is not None and hasattr(bridge_all, "model_info"):
        keys = list(bridge_all.model_info.keys())
        summary["model_registry_size"] = len(keys)
        summary["sample_model_registry_keys"] = keys[:12]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
