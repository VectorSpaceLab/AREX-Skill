#!/usr/bin/env python3
"""Safe Marqo package/environment probe.

This helper imports Marqo component packages, reports versions and available
FastAPI routes when imports succeed, and checks optional torch/CUDA state. It
never starts services, contacts Vespa/Triton, downloads models, or mutates data.

Examples:
  python scripts/check_marqo_environment.py
  python scripts/check_marqo_environment.py --json
"""
from __future__ import annotations

import argparse
import importlib
import json
from importlib import metadata
from typing import Any

DISTRIBUTIONS = [
    ("marqo-api", "marqo"),
    ("marqo-common", "marqo_common"),
    ("marqo-inference-orchestrator", "inference_orchestrator"),
    ("marqo-model-management", "model_management"),
]


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_status(module_name: str) -> dict[str, Any]:
    try:
        mod = importlib.import_module(module_name)
        return {"ok": True, "module": module_name, "detail": getattr(mod, "__name__", module_name)}
    except Exception as exc:  # diagnostic helper should not crash on import failures
        return {"ok": False, "module": module_name, "error": f"{type(exc).__name__}: {exc}"}


def fastapi_routes(module_name: str, app_attr: str = "app") -> list[dict[str, str]]:
    try:
        mod = importlib.import_module(module_name)
        app = getattr(mod, app_attr)
    except Exception:
        return []
    routes = []
    for route in getattr(app, "routes", []):
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        name = getattr(route, "name", None)
        if not path or path in {"/openapi.json", "/docs", "/redoc", "/docs/oauth2-redirect"}:
            continue
        routes.append({"methods": ",".join(sorted(methods or [])), "path": path, "name": name or ""})
    return sorted(routes, key=lambda item: item["path"])


def model_management_router_routes() -> list[dict[str, str]]:
    try:
        router_mod = importlib.import_module("model_management.api.v1_routes")
        router = router_mod.router
    except Exception:
        return []
    routes = []
    for route in getattr(router, "routes", []):
        routes.append({
            "methods": ",".join(sorted(getattr(route, "methods", []) or [])),
            "path": getattr(route, "path", ""),
            "name": getattr(route, "name", ""),
        })
    return sorted(routes, key=lambda item: item["path"])


def torch_status() -> dict[str, Any]:
    try:
        import torch  # type: ignore
    except Exception as exc:
        return {"installed": False, "error": f"{type(exc).__name__}: {exc}"}
    info: dict[str, Any] = {
        "installed": True,
        "version": getattr(torch, "__version__", None),
        "cuda_runtime": getattr(getattr(torch, "version", None), "cuda", None),
        "cuda_available": False,
        "cuda_device_count": 0,
    }
    try:
        info["cuda_available"] = bool(torch.cuda.is_available())
        info["cuda_device_count"] = int(torch.cuda.device_count()) if info["cuda_available"] else 0
        if info["cuda_available"]:
            tensor = torch.tensor([1.0, 2.0], device="cuda:0")
            info["cuda_smoke_sum"] = float(tensor.sum().cpu())
    except Exception as exc:
        info["cuda_error"] = f"{type(exc).__name__}: {exc}"
    return info


def collect() -> dict[str, Any]:
    packages = []
    for dist, module in DISTRIBUTIONS:
        packages.append({
            "distribution": dist,
            "version": dist_version(dist),
            "import": import_status(module),
        })
    return {
        "packages": packages,
        "routes": {
            "marqo_api": fastapi_routes("marqo.tensor_search.api"),
            "inference_orchestrator": fastapi_routes("inference_orchestrator.main"),
            "model_management": model_management_router_routes(),
        },
        "torch": torch_status(),
        "notes": [
            "This probe is read-only.",
            "It does not start services, contact Vespa/Triton, download models, or mutate indexes/documents.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely inspect Marqo package imports, routes, and optional torch/CUDA state.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()
    report = collect()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Marqo package probe")
        for pkg in report["packages"]:
            status = "ok" if pkg["import"]["ok"] else "FAIL"
            print(f"- {pkg['distribution']} ({pkg['version'] or 'not installed'}), import {pkg['import']['module']}: {status}")
            if not pkg["import"]["ok"]:
                print(f"  {pkg['import']['error']}")
        for service, routes in report["routes"].items():
            print(f"- {service}: {len(routes)} route(s) visible")
        torch = report["torch"]
        if torch.get("installed"):
            print(f"- torch {torch.get('version')}; CUDA available={torch.get('cuda_available')} devices={torch.get('cuda_device_count')}")
        else:
            print(f"- torch: not installed ({torch.get('error')})")
    any_required_failed = any(not pkg["import"]["ok"] for pkg in report["packages"][:2])
    return 1 if any_required_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
