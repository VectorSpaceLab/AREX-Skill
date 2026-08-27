#!/usr/bin/env python3
"""Safe, bounded probe for the optional MyoSuite JAX/MJX route.

This script only imports packages, reports devices, and optionally performs a
single in-memory MJX reset/step. It never installs packages, downloads assets,
initializes repositories, renders, writes files, or benchmarks throughput.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.metadata
import io
import json
import os
import platform
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--platform",
        choices=("default", "cpu", "cuda"),
        default="default",
        help="JAX platform selection; applied before importing JAX.",
    )
    parser.add_argument(
        "--env-name",
        default=None,
        help="Optional MJX factory name for an in-memory reset/step probe.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=1,
        help="Bounded number of in-memory steps (0-10; default: 1).",
    )
    parser.add_argument(
        "--seed", type=int, default=0, help="PRNG seed for an environment probe."
    )
    parser.add_argument(
        "--require-mjx",
        action="store_true",
        help="Exit nonzero if the optional JAX/MJX route is unavailable.",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Exit nonzero unless JAX reports a GPU/CUDA device.",
    )
    parser.add_argument(
        "--json", action="store_true", dest="as_json", help="Emit JSON output."
    )
    args = parser.parse_args()
    if not 0 <= args.steps <= 10:
        parser.error("--steps must be between 0 and 10")
    if args.platform == "cuda":
        args.require_cuda = True
    if args.env_name:
        args.require_mjx = True
    return args


def version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def device_record(device: Any) -> dict[str, str | None]:
    return {
        "repr": str(device),
        "platform": str(getattr(device, "platform", "unknown")),
        "device_kind": str(getattr(device, "device_kind", "unknown")),
    }


def is_gpu_device(device: Any) -> bool:
    platform_name = str(getattr(device, "platform", "")).lower()
    kind = str(getattr(device, "device_kind", "")).lower()
    return platform_name in {"gpu", "cuda"} or "cuda" in kind or "nvidia" in kind


def import_optional_modules(report: dict[str, Any]) -> tuple[Any, Any, Any]:
    """Import optional modules independently and record failures."""
    jax = jnp = myo_mjx = None
    try:
        jax = importlib.import_module("jax")
        jnp = importlib.import_module("jax.numpy")
        report["jax"] = {"available": True, "version": version("jax")}
        report["jax"]["devices"] = [device_record(d) for d in jax.devices()]
    except Exception as exc:  # optional backend must be reportable, not fatal
        jax = jnp = None
        report["jax"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    try:
        importlib.import_module("mujoco")
        report["mujoco"] = {
            "available": True,
            "version": version("mujoco"),
        }
    except Exception as exc:
        report["mujoco"] = {
            "available": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    try:
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            myo_mjx = importlib.import_module("myosuite.envs.myo.mjx")
        if captured.getvalue().strip():
            report.setdefault("diagnostics", []).append(captured.getvalue().strip())
        report["myosuite_mjx"] = {"available": True}
    except Exception as exc:
        report["myosuite_mjx"] = {
            "available": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return jax, jnp, myo_mjx


def run_environment_probe(
    report: dict[str, Any], jax: Any, jnp: Any, myo_mjx: Any, args: argparse.Namespace
) -> None:
    if not args.env_name:
        return
    if jax is None or jnp is None or myo_mjx is None:
        report["environment"] = {
            "available": False,
            "error": "JAX/MJX imports are required for --env-name",
        }
        return

    try:
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            env = myo_mjx.make(
                args.env_name,
                config_overrides={"num_envs": 1},
            )
            state = env.reset(jax.random.PRNGKey(args.seed))
            action = jnp.zeros((env.action_size,), dtype=jnp.float32)
            step_records = []
            for _ in range(args.steps):
                state = env.step(state, action)
                step_records.append(
                    {
                        "reward": float(state.reward),
                        "done": float(state.done),
                    }
                )
            observations = {
                str(key): list(value.shape) for key, value in state.obs.items()
            }
            report["environment"] = {
                "available": True,
                "name": args.env_name,
                "action_size": int(env.action_size),
                "observation_shapes": observations,
                "steps": step_records,
                "device": str(getattr(state.data.qpos, "device", "unknown")),
            }
            close = getattr(env, "close", None)
            if callable(close):
                close()
        if captured.getvalue().strip():
            report.setdefault("diagnostics", []).append(captured.getvalue().strip())
    except Exception as exc:
        report["environment"] = {
            "available": False,
            "name": args.env_name,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    args = parse_args()
    if args.platform != "default":
        # Must be set before importing JAX. Do not overwrite an explicit caller
        # selection when the default route is requested.
        os.environ["JAX_PLATFORMS"] = args.platform

    report: dict[str, Any] = {
        "probe": "myosuite-mjx",
        "python": sys.version.split()[0],
        "host": platform.system(),
        "myosuite_version": version("MyoSuite"),
        "requested_platform": args.platform,
        "requested_environment": args.env_name,
    }
    jax, jnp, myo_mjx = import_optional_modules(report)

    if jax is not None:
        devices = jax.devices()
        report["cuda_device_visible"] = any(is_gpu_device(d) for d in devices)
    else:
        report["cuda_device_visible"] = False

    run_environment_probe(report, jax, jnp, myo_mjx, args)

    mjx_available = bool(report.get("myosuite_mjx", {}).get("available"))
    cuda_available = bool(report.get("cuda_device_visible"))
    environment_ok = not args.env_name or bool(
        report.get("environment", {}).get("available")
    )
    required_ok = (not args.require_mjx or mjx_available) and (
        not args.require_cuda or cuda_available
    ) and environment_ok

    if not required_ok:
        report["status"] = "required-backend-unavailable"
    elif not mjx_available:
        report["status"] = "optional-unverified"
    else:
        report["status"] = "ok"
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        print(f"python: {report['python']}")
        print(f"MyoSuite: {report['myosuite_version'] or 'not installed'}")
        for name in ("jax", "mujoco", "myosuite_mjx"):
            item = report.get(name, {})
            state = "available" if item.get("available") else "unavailable"
            detail = item.get("version") or item.get("error", "")
            print(f"{name}: {state}{(' - ' + str(detail)) if detail else ''}")
        print(f"cuda_device_visible: {report['cuda_device_visible']}")
        if "environment" in report:
            item = report["environment"]
            print(
                f"environment {item.get('name')}: "
                f"{'available' if item.get('available') else 'unavailable'}"
            )
            if item.get("error"):
                print(f"environment_error: {item['error']}")

    return 0 if required_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
