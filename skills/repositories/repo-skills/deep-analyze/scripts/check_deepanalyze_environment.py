#!/usr/bin/env python3
"""Read-only DeepAnalyze environment checker.

The script finds a DeepAnalyze checkout, runs safe import/compile checks, and
prints a concise summary for the router skill. It never starts servers, runs
benchmarks, downloads models, or mutates checkpoints.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional

REQUIRED_MODULES = ["requests", "fastapi", "uvicorn", "openai", "pandas", "rich"]
OPTIONAL_MODULES = ["torch", "transformers", "vllm", "fastmcp", "mcp", "jupyterlab", "notebook"]
CHECK_PATHS = [
    "deepanalyze.py",
    "API/main.py",
    "API/chat_api.py",
    "API/file_api.py",
    "API/models_api.py",
    "demo/chat_v2/backend.py",
    "demo/chat_v2/backend_app/app.py",
    "demo/chat_v2/backend_app/settings.py",
    "demo/cli/api_cli.py",
    "demo/cli/api_cli_ZH.py",
    "demo/jupyter/CLI.py",
    "demo/jupyter/server.py",
    "demo/jupyter/mcp_tools.py",
    "quantize.py",
    "deepanalyze/add_vocab.py",
]


@dataclass
class ModuleStatus:
    name: str
    present: bool
    optional: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only DeepAnalyze environment checker.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Path to a DeepAnalyze checkout.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a human report.")
    return parser.parse_args()


def discover_repo_root(explicit: Optional[Path]) -> Path:
    candidates: List[Path] = []
    if explicit is not None:
        candidates.append(explicit.expanduser().resolve())
    candidates.append(Path.cwd().resolve())
    candidates.extend(Path.cwd().resolve().parents)
    for base in candidates:
        if (base / "deepanalyze.py").exists():
            return base
    raise FileNotFoundError("Could not locate deepanalyze.py from the current working tree")


def module_statuses() -> List[ModuleStatus]:
    status: List[ModuleStatus] = []
    for name in REQUIRED_MODULES:
        status.append(ModuleStatus(name=name, present=importlib.util.find_spec(name) is not None, optional=False))
    for name in OPTIONAL_MODULES:
        status.append(ModuleStatus(name=name, present=importlib.util.find_spec(name) is not None, optional=True))
    return status


def compile_paths(repo_root: Path) -> dict[str, Any]:
    results: List[dict[str, Any]] = []
    for rel in CHECK_PATHS:
        path = repo_root / rel
        if not path.exists():
            results.append({"path": rel, "present": False, "compiled": False, "error": "missing"})
            continue
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
            results.append({"path": rel, "present": True, "compiled": True, "error": ""})
        except Exception as exc:
            results.append({"path": rel, "present": True, "compiled": False, "error": str(exc)})
    return {"results": results, "all_passed": all(item["compiled"] for item in results if item["present"]) }


def deepanalyze_smoke(repo_root: Path) -> dict[str, Any]:
    sys.path.insert(0, str(repo_root))
    try:
        try:
            deepanalyze = importlib.import_module("deepanalyze")
            from deepanalyze import DeepAnalyzeVLLM
        except Exception as exc:
            return {"error": str(exc)}

        runner = DeepAnalyzeVLLM("DeepAnalyze-8B")
        local_exec = runner.execute_code("print(2 + 2)")
        return {
            "module": getattr(deepanalyze, "__file__", ""),
            "local_exec": local_exec.strip(),
            "init_signature": str(importlib.import_module("inspect").signature(DeepAnalyzeVLLM.__init__)),
            "generate_signature": str(importlib.import_module("inspect").signature(DeepAnalyzeVLLM.generate)),
        }
    finally:
        if str(repo_root) in sys.path:
            sys.path.remove(str(repo_root))


def api_smoke(repo_root: Path) -> dict[str, Any]:
    api_dir = repo_root / "API"
    if not api_dir.exists():
        return {"present": False}
    if importlib.util.find_spec("fastapi") is None:
        return {"present": True, "skipped": True, "reason": "fastapi missing from current environment"}
    cwd = Path.cwd()
    try:
        os.chdir(api_dir)
        if str(api_dir) not in sys.path:
            sys.path.insert(0, str(api_dir))
        main = importlib.import_module("main")
        app = main.create_app()
        from fastapi.testclient import TestClient

        client = TestClient(app)
        health = client.get("/health")
        models = client.get("/v1/models")
        files = client.get("/v1/files")
        return {
            "present": True,
            "skipped": False,
            "routes": ["/health", "/v1/models", "/v1/files"],
            "health": health.status_code,
            "models": models.status_code,
            "files": files.status_code,
        }
    except Exception as exc:
        return {"present": True, "skipped": True, "reason": str(exc)}
    finally:
        os.chdir(cwd)
        if str(api_dir) in sys.path:
            sys.path.remove(str(api_dir))


def webui_smoke(repo_root: Path) -> dict[str, Any]:
    chat_v2 = repo_root / "demo" / "chat_v2"
    if not chat_v2.exists():
        return {"present": False}
    if importlib.util.find_spec("fastapi") is None:
        return {"present": True, "skipped": True, "reason": "fastapi missing from current environment"}
    cwd = Path.cwd()
    try:
        os.chdir(chat_v2)
        if str(chat_v2) not in sys.path:
            sys.path.insert(0, str(chat_v2))
        app_mod = importlib.import_module("backend_app.app")
        app = app_mod.create_app()
        from fastapi.testclient import TestClient

        client = TestClient(app)
        files = client.get("/workspace/files")
        tree = client.get("/workspace/tree")
        return {
            "present": True,
            "skipped": False,
            "routes": ["/workspace/files", "/workspace/tree"],
            "files": files.status_code,
            "tree": tree.status_code,
        }
    except Exception as exc:
        return {"present": True, "skipped": True, "reason": str(exc)}
    finally:
        os.chdir(cwd)
        if str(chat_v2) in sys.path:
            sys.path.remove(str(chat_v2))


def main() -> int:
    args = parse_args()
    repo_root = discover_repo_root(args.repo_root)
    modules = module_statuses()
    compile_report = compile_paths(repo_root)
    deepanalyze_report = deepanalyze_smoke(repo_root)
    api_report = api_smoke(repo_root)
    webui_report = webui_smoke(repo_root)

    deepanalyze_ok = "error" not in deepanalyze_report
    api_ok = bool(api_report.get("present")) and not api_report.get("skipped") and api_report.get("health") == 200 and api_report.get("models") == 200 and api_report.get("files") == 200
    webui_ok = bool(webui_report.get("present")) and not webui_report.get("skipped") and webui_report.get("files") == 200 and webui_report.get("tree") == 200
    required_modules_ok = all(item.present for item in modules if not item.optional)
    status_ok = required_modules_ok and compile_report["all_passed"] and deepanalyze_ok and api_ok and webui_ok

    report = {
        "repo_root": str(repo_root),
        "modules": [module.__dict__ for module in modules],
        "compile": compile_report,
        "deepanalyze": deepanalyze_report,
        "api": api_report,
        "webui_v2": webui_report,
        "required_modules_ok": required_modules_ok,
        "optional_modules": {item.name: item.present for item in modules if item.optional},
        "status_ok": status_ok,
    }

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"DeepAnalyze checkout: {repo_root}")
        print("Required modules:")
        for item in modules:
            if item.optional:
                continue
            print(f"  - {item.name}: {'OK' if item.present else 'missing'}")
        print("Optional modules:")
        for item in modules:
            if not item.optional:
                continue
            print(f"  - {item.name}: {'OK' if item.present else 'missing'}")
        print("Compile checks:")
        for item in compile_report["results"]:
            state = "OK" if item["compiled"] else f"missing/error: {item['error']}"
            print(f"  - {item['path']}: {state}")
        print("DeepAnalyzeVLLM:")
        if deepanalyze_ok:
            print(f"  - import: {deepanalyze_report.get('module', '')}")
            print(f"  - execute_code: {deepanalyze_report.get('local_exec', '')}")
        else:
            print(f"  - error: {deepanalyze_report.get('error', '')}")
        print("API smoke:")
        print(f"  - {api_report}")
        print("WebUI v2 smoke:")
        print(f"  - {webui_report}")
        print("Status: ok" if status_ok else "Status: blocked")

    return 0 if status_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
