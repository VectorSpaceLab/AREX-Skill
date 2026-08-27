#!/usr/bin/env python3
"""Check a usable Agent Lightning installation.

This helper is safe by default: it imports the package, verifies a few public
objects, instantiates CPU-only in-memory primitives, and checks CLI help. It does
not start long-running services, call external APIs, download data, or train.

Examples:
    python scripts/check_agentlightning_install.py
    python scripts/check_agentlightning_install.py --include-prometheus
    python scripts/check_agentlightning_install.py --repo-root /path/to/agent-lightning --skip-cli
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def _result(name: str, ok: bool, detail: str) -> Dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}


def _run_command(name: str, command: List[str], timeout: float) -> Dict[str, Any]:
    try:
        completed = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return _result(name, False, f"executable not found: {command[0]}")
    except subprocess.TimeoutExpired:
        return _result(name, False, f"timed out after {timeout} seconds")

    output = (completed.stdout or completed.stderr or "").strip().splitlines()
    first_line = output[0] if output else "<no output>"
    if completed.returncode != 0:
        tail = " | ".join(output[-4:]) if output else "<no output>"
        return _result(name, False, f"exit {completed.returncode}: {tail}")
    return _result(name, True, first_line)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check an Agent Lightning package installation.")
    parser.add_argument("--repo-root", type=Path, help="Optional checkout root to prepend to sys.path before import.")
    parser.add_argument("--skip-cli", action="store_true", help="Skip agl CLI help checks.")
    parser.add_argument(
        "--include-prometheus",
        action="store_true",
        help="Also check `agl prometheus --help`; requires prometheus-client to be installed.",
    )
    parser.add_argument("--timeout", type=float, default=15.0, help="Seconds per CLI help command.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    args = parser.parse_args()

    if args.repo_root:
        sys.path.insert(0, str(args.repo_root))

    checks: List[Dict[str, Any]] = []

    try:
        import agentlightning as agl
    except Exception as exc:  # pragma: no cover - diagnostic path
        checks.append(_result("import agentlightning", False, f"{type(exc).__name__}: {exc}"))
        if args.json:
            print(json.dumps({"ok": False, "checks": checks}, indent=2))
        else:
            print("FAIL import agentlightning:", checks[-1]["detail"])
        return 1

    try:
        version = metadata.version("agentlightning")
    except metadata.PackageNotFoundError:
        version = getattr(agl, "__version__", "unknown")
    checks.append(_result("distribution version", True, str(version)))

    required_attrs = [
        "rollout",
        "llm_rollout",
        "prompt_rollout",
        "LitAgent",
        "LitAgentRunner",
        "InMemoryLightningStore",
        "OtelTracer",
        "Trainer",
        "Baseline",
        "PromptTemplate",
        "LLM",
        "emit_reward",
        "find_final_reward",
    ]
    missing = [name for name in required_attrs if not hasattr(agl, name)]
    checks.append(_result("public object surface", not missing, "missing: " + ", ".join(missing) if missing else "ok"))

    try:
        store = agl.InMemoryLightningStore()
        template = agl.PromptTemplate(template="Hello {name}", engine="f-string")
        formatted = template.format(name="Agent Lightning")
        capabilities = dict(store.capabilities)
        ok = formatted == "Hello Agent Lightning" and "async_safe" in capabilities
        checks.append(_result("in-memory primitives", ok, f"formatted={formatted!r}, capabilities={capabilities}"))
    except Exception as exc:  # pragma: no cover - diagnostic path
        checks.append(_result("in-memory primitives", False, f"{type(exc).__name__}: {exc}"))

    if not args.skip_cli:
        agl_exe = shutil.which("agl")
        if agl_exe is None:
            checks.append(_result("agl executable", False, "not found on PATH"))
        else:
            checks.append(_run_command("agl --help", [agl_exe, "--help"], args.timeout))
            checks.append(_run_command("agl store --help", [agl_exe, "store", "--help"], args.timeout))
            if args.include_prometheus:
                checks.append(_run_command("agl prometheus --help", [agl_exe, "prometheus", "--help"], args.timeout))

    ok = all(check["ok"] for check in checks)
    if args.json:
        print(json.dumps({"ok": ok, "checks": checks}, indent=2))
    else:
        for check in checks:
            status = "PASS" if check["ok"] else "FAIL"
            print(f"{status} {check['name']}: {check['detail']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
