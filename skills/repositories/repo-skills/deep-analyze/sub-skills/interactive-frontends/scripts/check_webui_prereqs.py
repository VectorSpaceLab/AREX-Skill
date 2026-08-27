#!/usr/bin/env python3
"""Read-only WebUI v2 prerequisite checker.

This script reports ports, environment values, Python and Node prerequisites,
Docker image presence, and optional PDF-export tooling. It never starts or
stops services and never kills processes.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any

DEFAULT_FRONTEND_PORT = 4000
DEFAULT_BACKEND_PORT = 8200
DEFAULT_FILE_PORT = 8100
REQUIRED_PYTHON_MODULES = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("openai", "openai"),
    ("httpx", "httpx"),
    ("pandas", "pandas"),
    ("matplotlib", "matplotlib"),
    ("python-multipart", "multipart"),
]
OPTIONAL_PDF_MODULES = [
    ("pypandoc", "pypandoc"),
]
FRONTEND_ENV_DEFAULTS = {
    "NEXT_PUBLIC_BACKEND_URL": "http://localhost:8200",
    "NEXT_PUBLIC_AI_API_URL": "http://localhost:8000",
    "NEXT_PUBLIC_WEBSOCKET_URL": "ws://localhost:8001",
}
BACKEND_ENV_DEFAULTS = {
    "DEEPANALYZE_API_BASE": "http://localhost:8000/v1",
    "DEEPANALYZE_MODEL_PATH": "DeepAnalyze-8B",
    "DEEPANALYZE_WORKSPACE_BASE": "workspace",
    "DEEPANALYZE_FILE_SERVER_HOST": "localhost",
    "DEEPANALYZE_FILE_SERVER_PORT": "8100",
    "DEEPANALYZE_BACKEND_HOST": "0.0.0.0",
    "DEEPANALYZE_BACKEND_PORT": "8200",
    "DEEPANALYZE_EXECUTION_MODE": "local",
    "DEEPANALYZE_EXECUTION_TIMEOUT_SEC": "120",
    "DEEPANALYZE_DOCKER_IMAGE": "deepanalyze-chat-exec:latest",
    "DEEPANALYZE_DOCKER_CONTAINER_NAME": "deepanalyze-chat-exec",
    "DEEPANALYZE_DOCKER_SESSION_IDLE_TTL_SEC": "1800",
    "DEEPANALYZE_DOCKER_WORKSPACE_DIR": "/workspace",
    "DEEPANALYZE_DOCKER_PYTHON_BIN": "python",
    "DEEPANALYZE_DOCKER_STOP_ON_SHUTDOWN": "true",
    "DEEPANALYZE_PDF_CJK_MAINFONT": "",
    "DEEPANALYZE_PDF_AUTO_DOWNLOAD_PANDOC": "true",
    "DEEPANALYZE_PDF_PANDOC_CACHE_DIR": "",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check DeepAnalyze WebUI v2 prerequisites")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Path to the chat_v2 directory or the repository root",
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=None,
        help="Frontend port to check instead of the default or env override",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of a human-readable report",
    )
    return parser.parse_args()


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def merge_envs(*sources: dict[str, str]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for source in sources:
        merged.update({k: v for k, v in source.items() if v is not None})
    return merged


def discover_chat_v2_root(start: Path, explicit: Path | None = None) -> Path:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit.expanduser().resolve())
    candidates.append(start.expanduser().resolve())
    candidates.extend(start.expanduser().resolve().parents)

    for base in candidates:
        if base.name == "chat_v2" and (base / "backend.py").exists():
            return base
        nested = base / "demo" / "chat_v2"
        if (nested / "backend.py").exists() and (nested / "frontend" / "package.json").exists():
            return nested
        if (base / "backend.py").exists() and (base / "frontend" / "package.json").exists():
            return base
    raise FileNotFoundError("Could not locate the chat_v2 demo root")


def port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def command_version(command: str) -> dict[str, str | bool]:
    exe = shutil_which(command)
    if not exe:
        return {"available": False, "path": "", "version": ""}
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        version = (result.stdout or result.stderr or "").strip().splitlines()[0:1]
        return {
            "available": True,
            "path": exe,
            "version": version[0] if version else "",
        }
    except Exception as exc:
        return {"available": True, "path": exe, "version": f"<version check failed: {exc}>"}


def shutil_which(command: str) -> str | None:
    return shutil.which(command)


def check_python_modules() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for label, module_name in REQUIRED_PYTHON_MODULES:
        checks.append(
            {
                "label": label,
                "module": module_name,
                "required": True,
                "present": importlib.util.find_spec(module_name) is not None,
            }
        )
    for label, module_name in OPTIONAL_PDF_MODULES:
        checks.append(
            {
                "label": label,
                "module": module_name,
                "required": False,
                "present": importlib.util.find_spec(module_name) is not None,
            }
        )
    return checks


def env_value(env: dict[str, str], key: str, default: str = "") -> str:
    value = env.get(key, "")
    return value if value != "" else default


def check_docker_image(image_name: str) -> dict[str, Any]:
    docker_exe = shutil_which("docker")
    if not docker_exe:
        return {
            "available": False,
            "path": "",
            "image": image_name,
            "present": False,
            "detail": "docker command not found",
        }
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image_name, "--format", "{{.Id}}"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        present = result.returncode == 0
        detail = (result.stdout or result.stderr or "").strip()
        return {
            "available": True,
            "path": docker_exe,
            "image": image_name,
            "present": present,
            "detail": detail,
        }
    except Exception as exc:
        return {
            "available": True,
            "path": docker_exe,
            "image": image_name,
            "present": False,
            "detail": f"docker inspect failed: {exc}",
        }


def check_pdf_tools() -> dict[str, Any]:
    return {
        "pypandoc": importlib.util.find_spec("pypandoc") is not None,
        "pandoc": shutil_which("pandoc") or "",
        "xelatex": shutil_which("xelatex") or "",
    }


def build_report(root: Path, frontend_port_override: int | None = None) -> dict[str, Any]:
    backend_env_path = root / ".env"
    backend_env = load_env_file(backend_env_path)
    effective_env = merge_envs(backend_env, os.environ)

    frontend_dir = root / "frontend"
    frontend_package = frontend_dir / "package.json"
    frontend_node_modules = frontend_dir / "node_modules"

    frontend_port = frontend_port_override or int(os.getenv("FRONTEND_PORT", "") or DEFAULT_FRONTEND_PORT)
    backend_port = int(env_value(effective_env, "DEEPANALYZE_BACKEND_PORT", str(DEFAULT_BACKEND_PORT)))
    file_port = int(env_value(effective_env, "DEEPANALYZE_FILE_SERVER_PORT", str(DEFAULT_FILE_PORT)))
    execution_mode = env_value(effective_env, "DEEPANALYZE_EXECUTION_MODE", "local").strip().lower() or "local"
    docker_image = env_value(effective_env, "DEEPANALYZE_DOCKER_IMAGE", "deepanalyze-chat-exec:latest")

    ports = {
        "frontend": {"port": frontend_port, "open": port_open(frontend_port)},
        "backend": {"port": backend_port, "open": port_open(backend_port)},
        "file": {"port": file_port, "open": port_open(file_port)},
    }

    python_modules = check_python_modules()
    node_info = command_version("node")
    npm_info = command_version("npm")
    docker_info = check_docker_image(docker_image)
    pdf_tools = check_pdf_tools()

    blockers: list[str] = []
    warnings: list[str] = []

    if not backend_env_path.exists():
        warnings.append("Missing .env file; defaults will apply.")

    if not (root / "backend.py").exists():
        blockers.append("backend.py is missing from the WebUI root.")
    if not frontend_package.exists():
        blockers.append("frontend/package.json is missing.")
    if not (root / "Dockerfile.exec").exists():
        blockers.append("Dockerfile.exec is missing.")

    if not node_info["available"]:
        blockers.append("node is not installed or not on PATH.")
    if not npm_info["available"]:
        blockers.append("npm is not installed or not on PATH.")
    if not frontend_node_modules.exists():
        blockers.append("frontend/node_modules is missing; run npm install first.")

    for module in python_modules:
        if module["required"] and not module["present"]:
            blockers.append(f"Python module missing: {module['module']}")

    if execution_mode == "docker":
        if not docker_info["available"]:
            blockers.append("docker is not installed or not on PATH.")
        if not docker_info["present"]:
            blockers.append(f"Docker image missing: {docker_image}")
    else:
        if not docker_info["available"]:
            warnings.append("docker is not installed; local mode does not require it.")
        if not docker_info["present"]:
            warnings.append(f"Docker image not found: {docker_image} (only needed for docker execution).")

    for name, data in ports.items():
        if data["open"]:
            warnings.append(f"Port {data['port']} is already in use on the {name} surface.")

    if not pdf_tools["pypandoc"]:
        warnings.append("pypandoc is missing; PDF export may fall back to Markdown.")
    if not pdf_tools["pandoc"]:
        warnings.append("pandoc is missing from PATH; PDF export may auto-download it if enabled.")
    if not pdf_tools["xelatex"]:
        warnings.append("xelatex is missing from PATH; PDF export will not complete.")

    report = {
        "root": str(root),
        "backend_env_file": str(backend_env_path),
        "frontend_dir": str(frontend_dir),
        "execution_mode": execution_mode,
        "ports": ports,
        "env": {
            "backend": {key: effective_env.get(key, default) for key, default in BACKEND_ENV_DEFAULTS.items()},
            "frontend": {key: os.getenv(key, FRONTEND_ENV_DEFAULTS[key]) for key in FRONTEND_ENV_DEFAULTS},
        },
        "python_modules": python_modules,
        "node": node_info,
        "npm": npm_info,
        "docker": docker_info,
        "pdf_tools": pdf_tools,
        "blockers": blockers,
        "warnings": warnings,
        "status": "ok" if not blockers else "blocked",
    }
    return report


def print_human_report(report: dict[str, Any]) -> None:
    print("DeepAnalyze WebUI v2 prerequisite report")
    print(f"Root: {report['root']}")
    print(f"Execution mode: {report['execution_mode']}")
    print()

    print("Ports")
    for name, data in report["ports"].items():
        state = "in use" if data["open"] else "free"
        print(f"  - {name:8} {data['port']}: {state}")
    print()

    print("Environment")
    for section_name, section in report["env"].items():
        print(f"  {section_name}:")
        for key, value in section.items():
            shown = value if value else "<unset>"
            print(f"    - {key} = {shown}")
    print()

    print("Python modules")
    for module in report["python_modules"]:
        state = "OK" if module["present"] else "missing"
        note = " (optional)" if not module["required"] else ""
        print(f"  - {module['module']:16} {state}{note}")
    print()

    print("Node / npm")
    for label, info in (("node", report["node"]), ("npm", report["npm"])):
        state = "OK" if info["available"] else "missing"
        detail = f" {info['version']}" if info.get("version") else ""
        path = f" [{info['path']}]" if info.get("path") else ""
        print(f"  - {label:4} {state}{detail}{path}")
    frontend_node_modules = Path(report["root"]) / "frontend" / "node_modules"
    print(f"  - frontend node_modules: {'present' if frontend_node_modules.exists() else 'missing'}")
    print()

    print("Docker")
    docker = report["docker"]
    docker_state = "available" if docker["available"] else "missing"
    image_state = "present" if docker["present"] else "missing"
    print(f"  - docker command: {docker_state}")
    print(f"  - image {docker['image']}: {image_state}")
    if docker.get("detail"):
        print(f"    {docker['detail']}")
    print()

    print("PDF export")
    pdf = report["pdf_tools"]
    print(f"  - pypandoc: {'OK' if pdf['pypandoc'] else 'missing'}")
    print(f"  - pandoc: {pdf['pandoc'] or 'missing'}")
    print(f"  - xelatex: {pdf['xelatex'] or 'missing'}")
    print()

    if report["warnings"]:
        print("Warnings")
        for item in report["warnings"]:
            print(f"  - {item}")
        print()

    if report["blockers"]:
        print("Blocking issues")
        for item in report["blockers"]:
            print(f"  - {item}")
        print()
        print("Status: blocked")
    else:
        print("Status: ok")


def main() -> int:
    args = parse_args()
    try:
        root = discover_chat_v2_root(Path.cwd(), args.root)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 2

    report = build_report(root, args.frontend_port)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_human_report(report)

    return 0 if not report["blockers"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
