#!/usr/bin/env python3
"""Validate MemMachine server YAML config shape without starting services."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable


def load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("PyYAML is required: python -m pip install pyyaml") from exc
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def validate(data: Any) -> list[str]:
    issues: list[str] = []
    if not isinstance(data, dict):
        return ["root document is not a mapping"]
    resources = data.get("resources") or {}
    databases = resources.get("databases") if isinstance(resources, dict) else None
    embedders = resources.get("embedders") if isinstance(resources, dict) else None
    language_models = resources.get("language_models") if isinstance(resources, dict) else None
    rerankers = resources.get("rerankers") if isinstance(resources, dict) else None

    if not isinstance(databases, dict) or not databases:
        issues.append("resources.databases missing or empty")

    episode_store = data.get("episode_store") or {}
    if isinstance(episode_store, dict) and episode_store.get("database") and isinstance(databases, dict):
        if episode_store["database"] not in databases:
            issues.append(f"episode_store.database {episode_store['database']!r} not found in resources.databases")

    episodic = data.get("episodic_memory") or {}
    ltm = episodic.get("long_term_memory") if isinstance(episodic, dict) else None
    if not isinstance(ltm, dict):
        issues.append("episodic_memory.long_term_memory missing or not a mapping")
    else:
        backend = ltm.get("backend", "declarative")
        if ltm.get("embedder") and isinstance(embedders, dict) and ltm["embedder"] not in embedders:
            issues.append(f"long_term_memory.embedder {ltm['embedder']!r} not found in resources.embedders")
        if ltm.get("reranker") and isinstance(rerankers, dict) and ltm["reranker"] not in rerankers:
            issues.append(f"long_term_memory.reranker {ltm['reranker']!r} not found in resources.rerankers")
        if backend == "event":
            for key in ("vector_store", "segment_store"):
                if not ltm.get(key):
                    issues.append(f"event long_term_memory missing {key}")
                elif isinstance(databases, dict) and ltm[key] not in databases:
                    issues.append(f"long_term_memory.{key} {ltm[key]!r} not found in resources.databases")
        elif backend == "declarative":
            key = "vector_graph_store"
            if not ltm.get(key):
                issues.append("declarative long_term_memory missing vector_graph_store")
            elif isinstance(databases, dict) and ltm[key] not in databases:
                issues.append(f"long_term_memory.{key} {ltm[key]!r} not found in resources.databases")
        else:
            issues.append(f"unknown long_term_memory backend {backend!r}")

    semantic = data.get("semantic_memory") or {}
    if isinstance(semantic, dict) and semantic.get("enabled", True):
        for key, table in (("database", databases), ("config_database", databases), ("embedding_model", embedders), ("llm_model", language_models)):
            if not semantic.get(key):
                issues.append(f"enabled semantic_memory missing {key}")
            elif isinstance(table, dict) and semantic[key] not in table:
                issues.append(f"semantic_memory.{key} {semantic[key]!r} not found in resources")

    return issues


def docker_info(timeout: float) -> str:
    if not shutil.which("docker"):
        return "docker not found"
    proc = subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=timeout, check=False)
    return "docker available" if proc.returncode == 0 else f"docker unavailable: {proc.stderr.strip()[:120]}"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only MemMachine config validator.")
    parser.add_argument("--config", type=Path, required=True, help="YAML config file to validate.")
    parser.add_argument("--docker", action="store_true", help="Also check Docker daemon availability.")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args(argv)

    data = load_yaml(args.config)
    issues = validate(data)
    if args.docker:
        print(docker_info(args.timeout))
    if issues:
        for issue in issues:
            print(f"ISSUE: {issue}")
        return 1
    print("MemMachine config shape looks consistent for common server sections.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
