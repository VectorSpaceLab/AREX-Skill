#!/usr/bin/env python3
"""Safely report installed skrl framework imports and CPU configuration.

This helper is intentionally diagnostic-only: it performs imports, metadata
queries, and explicit CPU device parsing. It never installs packages, starts an
environment, trains, downloads, allocates CUDA tensors, or writes skrl
experiment files. Warp initialization may create its normal kernel cache.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import sys


FRAMEWORKS = ("torch", "jax", "warp")


def _check(framework: str) -> dict[str, object]:
    if framework == "torch":
        import torch
        from skrl import config

        resolved = config.torch.parse_device("cpu")
        return {
            "framework": framework,
            "installed_version": torch.__version__,
            "resolved_device": str(resolved),
            "cuda_available": bool(torch.cuda.is_available()),
            "public_import": importlib.import_module("skrl.agents.torch.ppo").PPO.__name__,
        }
    if framework == "jax":
        import jax
        from skrl import config

        resolved = config.jax.parse_device("cpu")
        return {
            "framework": framework,
            "installed_version": jax.__version__,
            "resolved_device": str(resolved),
            "devices": [str(device) for device in jax.devices()],
            "public_import": importlib.import_module("skrl.agents.jax.ppo").PPO.__name__,
        }

    import warp as wp
    from skrl import config

    wp.init()
    resolved = config.warp.parse_device("cpu")
    return {
        "framework": framework,
        "installed_version": importlib.metadata.version("warp-lang"),
        "resolved_device": str(resolved),
        "cuda_available": bool(wp.is_cuda_available()),
        "public_import": importlib.import_module("skrl.agents.warp.ppo").PPO.__name__,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Report installed skrl framework imports and CPU readiness.")
    parser.add_argument("--framework", choices=FRAMEWORKS, default=None, help="Check one framework; default checks all.")
    args = parser.parse_args()

    results = []
    failures = []
    for framework in (args.framework,) if args.framework else FRAMEWORKS:
        try:
            results.append(_check(framework))
        except (ImportError, ModuleNotFoundError) as exc:
            failures.append({"framework": framework, "error": f"missing optional dependency: {exc}"})
        except Exception as exc:  # keep the diagnostic concise for broken installs
            failures.append({"framework": framework, "error": f"{type(exc).__name__}: {exc}"})

    print(json.dumps({"skrl": importlib.metadata.version("skrl"), "checks": results, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
