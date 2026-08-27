#!/usr/bin/env python3
"""CPU-safe TorchRL service import and lifecycle smoke test.

Default mode does not start Ray, download models, create environments, render
videos, or spawn Python executor pools. It verifies public signatures and a
minimal direct owner/client lifecycle against the TorchRL Service protocol.

Examples:
    python smoke_services.py
    python smoke_services.py --repo-root /path/to/pytorch-rl
    python smoke_services.py --try-ray
"""
from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import Any


class LocalCounterService:
    """Tiny direct Service-compatible owner used only by this smoke test."""

    def __init__(self, value: int = 0):
        self.value = value
        self._alive = False

    def start(self):
        self._alive = True
        return self

    def shutdown(self, timeout: float | None = None) -> None:
        del timeout
        self._alive = False

    def client(self):
        return self

    @property
    def is_alive(self) -> bool:
        return self._alive

    def increment(self, amount: int = 1) -> int:
        self.value += amount
        return self.value


def _prepend_repo_root(repo_root: str | None) -> None:
    if repo_root:
        root = Path(repo_root).expanduser().resolve()
        sys.path.insert(0, str(root))


def _import_deps() -> dict[str, Any]:
    try:
        from torchrl.envs.llm.transforms import PythonExecutorService, PythonInterpreter
        from torchrl.services import Service, get_services
    except Exception as exc:  # pragma: no cover - user-facing diagnostic path
        print(
            json.dumps(
                {
                    "status": "import_error",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                    "hint": (
                        "Install TorchRL with base dependencies, or pass --repo-root "
                        "for an editable checkout that is importable. Optional Ray is "
                        "not required for the default smoke."
                    ),
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    return {
        "PythonExecutorService": PythonExecutorService,
        "PythonInterpreter": PythonInterpreter,
        "Service": Service,
        "get_services": get_services,
    }


def _try_ray_smoke(get_services, namespace: str) -> dict[str, Any]:
    if importlib.util.find_spec("ray") is None:
        return {
            "status": "skipped",
            "reason": "Ray is not installed; install Ray before testing the service registry.",
        }
    import ray

    services = get_services(backend="ray", namespace=namespace)
    owner = LocalCounterService(10).start()
    try:
        client = services.register("local_counter", owner)
        if client.increment(2) != 12:
            raise AssertionError("registered external service client returned wrong value")
        discovered = services.get_client("local_counter")
        if discovered.value != 12:
            raise AssertionError("registry get_client returned unexpected value")
        services.reset()
        if not owner.is_alive:
            raise AssertionError("registry reset shut down an externally owned service")
        return {"status": "passed", "namespace": namespace}
    finally:
        owner.shutdown()
        try:
            services.shutdown(raise_on_error=False)
        finally:
            if ray.is_initialized():
                ray.shutdown()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        help="Optional TorchRL checkout root to prepend to sys.path before imports.",
    )
    parser.add_argument(
        "--try-ray",
        action="store_true",
        help="Optionally start a local Ray registry smoke. Disabled by default.",
    )
    parser.add_argument(
        "--namespace",
        default="torchrl_skill_smoke",
        help="Ray namespace to use only when --try-ray is set.",
    )
    args = parser.parse_args(argv)

    _prepend_repo_root(args.repo_root)
    deps = _import_deps()
    Service = deps["Service"]
    get_services = deps["get_services"]
    PythonExecutorService = deps["PythonExecutorService"]
    PythonInterpreter = deps["PythonInterpreter"]

    report: dict[str, Any] = {
        "status": "ok",
        "signatures": {
            "get_services": str(inspect.signature(get_services)),
            "PythonExecutorService": str(inspect.signature(PythonExecutorService)),
            "PythonInterpreter": str(inspect.signature(PythonInterpreter)),
        },
        "ray_available": importlib.util.find_spec("ray") is not None,
    }

    owner = LocalCounterService(3).start()
    if not isinstance(owner, Service):
        raise AssertionError("LocalCounterService did not satisfy torchrl.services.Service")
    client = owner.client()
    if client is not owner:
        raise AssertionError("direct service smoke expected identity client")
    if client.increment(4) != 7:
        raise AssertionError("direct service client returned unexpected value")
    owner.shutdown()
    if owner.is_alive:
        raise AssertionError("direct service did not shut down")
    report["direct_lifecycle"] = "passed"

    try:
        get_services(backend="direct")
    except ValueError as exc:
        report["registry_non_ray_backend"] = str(exc)
    except ImportError as exc:
        report["registry_non_ray_backend"] = f"import_error_before_backend_check: {exc}"
    else:
        raise AssertionError("get_services(backend='direct') unexpectedly succeeded")

    report["python_executor_service"] = (
        "signature inspected only; default smoke does not spawn interpreter pools"
    )

    if args.try_ray:
        report["ray_smoke"] = _try_ray_smoke(get_services, args.namespace)
    else:
        report["ray_smoke"] = {
            "status": "skipped",
            "reason": "Pass --try-ray to start a local Ray registry smoke.",
        }

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
