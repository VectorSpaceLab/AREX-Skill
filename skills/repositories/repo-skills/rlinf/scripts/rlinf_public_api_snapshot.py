#!/usr/bin/env python3
"""Safely snapshot public RLinf package metadata and routing facts.

This helper is read-only. It imports only stable/public modules where possible and
falls back to source metadata when optional runtime dependencies are missing.

Examples:
  python rlinf_public_api_snapshot.py --json
  python rlinf_public_api_snapshot.py --repo-root /path/to/RLinf --json
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import sys
from pathlib import Path


def parse_pyproject_version(repo_root: Path | None) -> str | None:
    if not repo_root:
        return None
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        return None
    for line in pyproject.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("version") and "=" in stripped:
            return stripped.split("=", 1)[1].strip().strip('"')
    return None


def safe_import(name: str):
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # pragma: no cover - diagnostic surface
        return None, f"{type(exc).__name__}: {exc}"


def collect(repo_root: Path | None) -> dict:
    if repo_root:
        sys.path.insert(0, str(repo_root))

    out: dict = {
        "python": sys.version.split()[0],
        "repo_root_used": bool(repo_root),
        "distribution": {},
        "imports": {},
        "rlinf": {},
    }

    try:
        out["distribution"]["rlinf"] = importlib.metadata.version("rlinf")
    except Exception as exc:
        out["distribution"]["rlinf_error"] = f"{type(exc).__name__}: {exc}"
        version = parse_pyproject_version(repo_root)
        if version:
            out["distribution"]["pyproject_version"] = version

    for module_name in ["rlinf", "torch", "ray", "omegaconf", "hydra"]:
        module, err = safe_import(module_name)
        if err:
            out["imports"][module_name] = {"ok": False, "error": err}
        else:
            out["imports"][module_name] = {
                "ok": True,
                "version": getattr(module, "__version__", None),
            }

    config, config_err = safe_import("rlinf.config")
    if config_err:
        out["rlinf"]["config_error"] = config_err
    else:
        out["rlinf"]["task_types"] = list(getattr(config, "SUPPORTED_TASK_TYPE", []))
        out["rlinf"]["training_backends"] = list(
            getattr(config, "SUPPORTED_TRAINING_BACKENDS", [])
        )
        out["rlinf"]["rollout_backends"] = list(
            getattr(config, "SUPPORTED_ROLLOUT_BACKENDS", [])
        )
        model_registry = getattr(getattr(config, "SupportedModel", None), "models", {})
        out["rlinf"]["model_types"] = sorted(model_registry)

    envs, env_err = safe_import("rlinf.envs")
    if env_err:
        out["rlinf"]["env_error"] = env_err
    else:
        env_enum = getattr(envs, "SupportedEnvType", None)
        if env_enum is not None:
            out["rlinf"]["env_types"] = [item.value for item in env_enum]

    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only snapshot of RLinf package metadata and public routing constants."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Optional RLinf repository root to prepend to sys.path for this probe only.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve() if args.repo_root else None
    data = collect(repo_root)

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("RLinf public API snapshot")
        print(f"Python: {data['python']}")
        print(f"Distribution: {data['distribution']}")
        for module, info in data["imports"].items():
            status = "ok" if info.get("ok") else f"missing ({info.get('error')})"
            version = info.get("version")
            print(f"{module}: {status}" + (f" {version}" if version else ""))
        for key in ["task_types", "training_backends", "rollout_backends", "env_types"]:
            if key in data["rlinf"]:
                print(f"{key}: {', '.join(map(str, data['rlinf'][key]))}")
        if "model_types" in data["rlinf"]:
            models = data["rlinf"]["model_types"]
            print(f"model_types ({len(models)}): {', '.join(models[:40])}")
        for key in ["config_error", "env_error"]:
            if key in data["rlinf"]:
                print(f"{key}: {data['rlinf'][key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
