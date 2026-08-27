#!/usr/bin/env python3
"""Safely inspect a JARVIS checkout and the current Python environment.

This helper performs read-only checks only:
- verifies key source/config files exist
- reports optional package availability
- inspects HuggingGPT config placeholders and mode fields
- runs `python -m pip check` in the current interpreter

Usage:
  python check_jarvis_environment.py --repo-root <jarvis-repo-root>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from importlib import util as importlib_util
from pathlib import Path
from typing import Any, Dict, List


OPTIONAL_MODULES = [
    "openai",
    "langchain",
    "gdown",
    "tiktoken",
    "yaml",
    "click",
    "aiohttp",
    "requests",
    "networkx",
    "matplotlib",
]

ROOT_FILES = [
    "README.md",
    "CITATION.cff",
    "easytool/README.md",
    "easytool/main.py",
    "easytool/requirements.txt",
    "hugginggpt/README.md",
    "hugginggpt/server/awesome_chat.py",
    "hugginggpt/server/models_server.py",
    "hugginggpt/server/get_token_ids.py",
    "hugginggpt/server/configs/config.default.yaml",
    "hugginggpt/server/configs/config.lite.yaml",
    "hugginggpt/server/configs/config.gradio.yaml",
    "hugginggpt/server/configs/config.azure.yaml",
    "hugginggpt/web/package.json",
    "taskbench/README.md",
    "taskbench/inference.py",
    "taskbench/evaluate.py",
    "taskbench/generate_graph.py",
    "taskbench/data_engine.py",
    "taskbench/format_data.py",
    "taskbench/visualize_graph.py",
    "taskbench/requirements.txt",
]


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def has_spec(name: str) -> bool:
    try:
        return importlib_util.find_spec(name) is not None
    except Exception:
        return False


def pip_check() -> Dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout.strip().splitlines()[-5:],
        "stderr_tail": proc.stderr.strip().splitlines()[-5:],
    }


def parse_hugginggpt_config(path: Path) -> Dict[str, Any]:
    text = load_text(path)
    summary: Dict[str, Any] = {
        "path": str(path),
        "present": bool(text),
        "placeholders": {
            "openai_api_key": bool(re.search(r"REPLACE_WITH_YOUR_OPENAI_API_KEY_HERE", text)),
            "huggingface_token": bool(re.search(r"REPLACE_WITH_YOUR_HUGGINGFACE_TOKEN_HERE", text)),
            "azure_api_key": bool(re.search(r"REPLACE_WITH_YOUR_AZURE_API_KEY_HERE", text)),
            "azure_base_url": bool(re.search(r"REPLACE_WITH_YOUR_ENDPOINT_HERE", text)),
            "azure_deployment_name": bool(re.search(r"REPLACE_WITH_YOUR_DEPLOYMENT_NAME_HERE", text)),
        },
        "fields": {},
        "warnings": [],
    }

    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
        if isinstance(data, dict):
            summary["fields"] = {
                "model": data.get("model"),
                "use_completion": data.get("use_completion"),
                "inference_mode": data.get("inference_mode"),
                "local_deployment": data.get("local_deployment"),
                "http_listen": data.get("http_listen"),
                "local_inference_endpoint": data.get("local_inference_endpoint"),
            }
            summary["warnings"].append(
                "Parsed with PyYAML; field values reflect the config file, not runtime credentials."
            )
    except Exception:
        mode_match = re.search(r"^inference_mode:\s*(\S+)", text, re.MULTILINE)
        deployment_match = re.search(r"^local_deployment:\s*(\S+)", text, re.MULTILINE)
        model_match = re.search(r"^model:\s*(\S+)", text, re.MULTILINE)
        summary["fields"] = {
            "model": model_match.group(1) if model_match else None,
            "inference_mode": mode_match.group(1) if mode_match else None,
            "local_deployment": deployment_match.group(1) if deployment_match else None,
        }
        summary["warnings"].append("PyYAML not importable; used regex extraction for top-level mode fields.")

    return summary


def inspect_easytool(repo_root: Path) -> Dict[str, Any]:
    easy = repo_root / "easytool"
    files = [
        easy / "main.py",
        easy / "requirements.txt",
        easy / "easytool" / "util.py",
        easy / "easytool" / "funcQA.py",
        easy / "easytool" / "toolbench.py",
        easy / "easytool" / "toolbench_retrieve.py",
        easy / "easytool" / "restbench.py",
    ]
    return {
        "root": str(easy),
        "present": easy.exists(),
        "files_present": {str(path.relative_to(repo_root)): path.exists() for path in files},
        "relative_import_workaround_needed": True,
    }


def inspect_taskbench(repo_root: Path) -> Dict[str, Any]:
    task = repo_root / "taskbench"
    files = [
        task / "inference.py",
        task / "evaluate.py",
        task / "generate_graph.py",
        task / "graph_sampler.py",
        task / "data_engine.py",
        task / "format_data.py",
        task / "visualize_graph.py",
        task / "requirements.txt",
    ]
    return {
        "root": str(task),
        "present": task.exists(),
        "files_present": {str(path.relative_to(repo_root)): path.exists() for path in files},
    }


def inspect_hugginggpt(repo_root: Path) -> Dict[str, Any]:
    server = repo_root / "hugginggpt" / "server"
    config_dir = server / "configs"
    configs = [
        config_dir / "config.default.yaml",
        config_dir / "config.lite.yaml",
        config_dir / "config.gradio.yaml",
        config_dir / "config.azure.yaml",
    ]
    return {
        "server_root": str(server),
        "present": server.exists(),
        "configs": {str(path.relative_to(repo_root)): parse_hugginggpt_config(path) for path in configs},
        "token_helper": (server / "get_token_ids.py").exists(),
        "web_client": (repo_root / "hugginggpt" / "web" / "package.json").exists(),
    }


def build_summary(repo_root: Path) -> Dict[str, Any]:
    files = {path: (repo_root / path).exists() for path in ROOT_FILES}
    optional = {name: has_spec(name) for name in OPTIONAL_MODULES}
    pip = pip_check()
    return {
        "ok": True,
        "repo_root": str(repo_root),
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
        },
        "files_present": files,
        "optional_modules": optional,
        "pip_check": pip,
        "subprojects": {
            "easytool": inspect_easytool(repo_root),
            "hugginggpt": inspect_hugginggpt(repo_root),
            "taskbench": inspect_taskbench(repo_root),
        },
        "warnings": [
            "This helper is read-only and does not run networked workflows or load heavy model stacks.",
            "EasyTool's inner package directory may still need PYTHONPATH adjustment for direct imports.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely inspect a JARVIS checkout and current Python environment.")
    parser.add_argument("--repo-root", default=".", help="Path to the JARVIS repository root.")
    parser.add_argument("--json", action="store_true", help="Print JSON only (default behavior).")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(json.dumps({"ok": False, "error": f"repo root does not exist: {repo_root}"}, indent=2), file=sys.stderr)
        return 2

    summary = build_summary(repo_root)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
