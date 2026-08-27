#!/usr/bin/env python3
"""Read-only diagnostic for an installed Jina-serve environment."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import shutil
import subprocess
import sys
from importlib import metadata


def safe_version(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-cli", action="store_true", help="Do not invoke the jina console script.")
    args = parser.parse_args()

    result: dict[str, object] = {
        "python": sys.version.split()[0],
        "distributions": {name: safe_version(name) for name in ["jina", "docarray", "grpcio", "protobuf", "pydantic", "jcloud", "jina-hubble-sdk", "setuptools"]},
        "imports": {},
        "api": {},
        "cli": {},
        "warnings": [],
    }

    try:
        import jina
        from jina import Client, Deployment, Executor, Flow, requests
        from jina.clients.mixin import PostMixin

        result["imports"] = {
            "jina": True,
            "Executor": Executor.__name__,
            "Flow": Flow.__name__,
            "Deployment": Deployment.__name__,
            "Client": getattr(Client, "__name__", str(Client)),
            "requests": getattr(requests, "__name__", str(requests)),
        }
        result["api"] = {
            "jina_version": getattr(jina, "__version__", None),
            "client_post_signature": str(inspect.signature(PostMixin.post)),
            "flow_signature": str(inspect.signature(Flow)),
            "deployment_signature": str(inspect.signature(Deployment)),
            "executor_init_signature": str(inspect.signature(Executor.__init__)),
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["imports"] = {"jina": False, "error": repr(exc)}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    if not args.skip_cli:
        jina_cli = shutil.which("jina")
        result["cli"]["path_found"] = bool(jina_cli)
        if jina_cli:
            completed = subprocess.run([jina_cli, "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
            result["cli"]["version_exit_code"] = completed.returncode
            result["cli"]["version_stdout"] = completed.stdout.strip()
            result["cli"]["version_stderr_tail"] = completed.stderr.strip()[-500:]
            if completed.returncode != 0:
                print(json.dumps(result, indent=2, sort_keys=True))
                return completed.returncode

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
