#!/usr/bin/env python3
"""Read-only MemMachine server prerequisite and config-shape checker.

The doctor does not start or stop services. It checks Python imports, optional
commands, Docker availability, and the shape of a MemMachine YAML config file.
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable

REQUIRED_TOP_LEVEL = {
    "episode_store",
    "episodic_memory",
    "semantic_memory",
    "session_manager",
    "resources",
}


def command_status(cmd: str) -> str:
    exe = shutil.which(cmd)
    return exe or "not-on-PATH"


def docker_status(timeout: float) -> str:
    exe = shutil.which("docker")
    if not exe:
        return "docker-not-on-PATH"
    try:
        proc = subprocess.run(
            [exe, "info"],
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        return f"docker-info-error: {type(exc).__name__}: {exc}"
    if proc.returncode == 0:
        return "docker-daemon-available"
    return f"docker-info-exit-{proc.returncode}: {proc.stderr.strip()[:160]}"


def load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("PyYAML is required to parse config files") from exc
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def validate_config(data: Any) -> list[str]:
    warnings: list[str] = []
    if not isinstance(data, dict):
        return ["config root is not a mapping"]

    missing = sorted(REQUIRED_TOP_LEVEL - set(data))
    if missing:
        warnings.append(f"missing common top-level sections: {', '.join(missing)}")

    resources = data.get("resources") or {}
    if not isinstance(resources, dict):
        warnings.append("resources is not a mapping")
        resources = {}
    databases = resources.get("databases") or {}
    if not isinstance(databases, dict) or not databases:
        warnings.append("resources.databases is missing or empty")

    episodic = data.get("episodic_memory") or {}
    ltm = episodic.get("long_term_memory") if isinstance(episodic, dict) else None
    if isinstance(ltm, dict):
        backend = ltm.get("backend", "declarative")
        if backend == "event":
            for key in ("vector_store", "segment_store"):
                if not ltm.get(key):
                    warnings.append(f"event long_term_memory missing {key}")
        elif backend == "declarative":
            if not ltm.get("vector_graph_store"):
                warnings.append("declarative long_term_memory missing vector_graph_store")
        else:
            warnings.append(f"unknown long_term_memory backend: {backend!r}")
        if not ltm.get("embedder"):
            warnings.append("long_term_memory missing embedder")
    else:
        warnings.append("episodic_memory.long_term_memory is missing or not a mapping")

    semantic = data.get("semantic_memory") or {}
    if isinstance(semantic, dict) and semantic.get("enabled", True):
        for key in ("llm_model", "embedding_model", "database", "config_database"):
            if not semantic.get(key):
                warnings.append(f"enabled semantic_memory missing {key}")

    return warnings


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect MemMachine server prerequisites without starting services.")
    parser.add_argument("--config", type=Path, help="Optional MemMachine YAML config to validate.")
    parser.add_argument("--docker", action="store_true", help="Check whether Docker daemon is reachable.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Timeout for Docker probe.")
    args = parser.parse_args(argv)

    for module in ["memmachine_server", "fastapi", "uvicorn", "pydantic"]:
        print(f"[importable] {module}: {bool(importlib.util.find_spec(module))}")
    for cmd in ["memmachine-server", "memmachine-mcp-http", "memmachine-mcp-stdio", "memmachine-configure", "docker"]:
        print(f"[command] {cmd}: {command_status(cmd)}")

    if args.docker:
        print(f"[docker] {docker_status(args.timeout)}")

    exit_code = 0
    if args.config:
        try:
            data = load_yaml(args.config)
            warnings = validate_config(data)
        except Exception as exc:  # noqa: BLE001
            print(f"[config] failed: {type(exc).__name__}: {exc}")
            return 2
        if warnings:
            exit_code = 1
            for warning in warnings:
                print(f"[config-warning] {warning}")
        else:
            print("[config] shape looks consistent for common MemMachine sections")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
