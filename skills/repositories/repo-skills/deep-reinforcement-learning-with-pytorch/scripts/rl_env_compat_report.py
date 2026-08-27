#!/usr/bin/env python3
"""Cross-family compatibility probe for the repo's Gym / Torch workflows.

The helper checks torch CUDA availability, the classic-control discrete envs,
modern continuous-control substitutes, and optional Box2D readiness without
training, rendering, or checkpoint loading.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_ENVS = ["CartPole-v0", "MountainCar-v0", "Pendulum-v1", "BipedalWalker-v3"]
LEGACY_MAP = {"Pendulum-v0": "Pendulum-v1", "BipedalWalker-v2": "BipedalWalker-v3"}


def _quiet_import(name: str) -> Dict[str, Any]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            module = importlib.import_module(name)
    except Exception as exc:
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
    return {"ok": True, "version": getattr(module, "__version__", None)}


def _torch_report() -> Dict[str, Any]:
    status = _quiet_import("torch")
    if not status["ok"]:
        return status
    import torch

    report: Dict[str, Any] = {
        "ok": True,
        "version": getattr(torch, "__version__", None),
        "cuda_version": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "selected_device": "cuda" if torch.cuda.is_available() else "cpu",
    }
    if torch.cuda.is_available():
        report["cuda_device_count"] = torch.cuda.device_count()
        report["cuda_device_0"] = torch.cuda.get_device_name(0)
    return report


def _shape_to_list(shape: Any) -> Any:
    if shape is None:
        return None
    if hasattr(shape, "tolist"):
        return shape.tolist()
    if isinstance(shape, tuple):
        return list(shape)
    return shape


def _space_summary(space: Any) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"type": type(space).__name__, "shape": _shape_to_list(getattr(space, "shape", None))}
    if hasattr(space, "n"):
        summary["n"] = getattr(space, "n")
    if hasattr(space, "low"):
        summary["low"] = _shape_to_list(getattr(space, "low"))
    if hasattr(space, "high"):
        summary["high"] = _shape_to_list(getattr(space, "high"))
    return summary


def _step_result(env: Any, action: Any) -> Dict[str, Any]:
    result = env.step(action)
    if len(result) == 5:
        obs, reward, terminated, truncated, info = result
        return {"step_len": 5, "done": bool(terminated or truncated), "obs": _shape_to_list(getattr(obs, "shape", None)), "info_type": type(info).__name__}
    obs, reward, done, info = result
    return {"step_len": 4, "done": bool(done), "obs": _shape_to_list(getattr(obs, "shape", None)), "info_type": type(info).__name__}


def _normalize_action_preview(action_space: Any) -> Optional[Dict[str, Any]]:
    if not (hasattr(action_space, "low") and hasattr(action_space, "high")):
        return None
    try:
        import numpy as np

        low = np.asarray(action_space.low, dtype=float)
        high = np.asarray(action_space.high, dtype=float)
        zero = np.zeros_like(low)
        env_action = low + (zero + 1.0) * 0.5 * (high - low)
        return {"normalized_zero": env_action.tolist(), "low": low.tolist(), "high": high.tolist()}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def _env_report(gym: Any, env_id: str, step: bool) -> Dict[str, Any]:
    report: Dict[str, Any] = {"env_id": env_id, "modern_substitute": LEGACY_MAP.get(env_id)}
    try:
        env = gym.make(env_id)
    except Exception as exc:
        report.update({"ok": False, "error_type": type(exc).__name__, "error": str(exc)})
        if env_id in LEGACY_MAP:
            report["hint"] = f"Use {LEGACY_MAP[env_id]} in the inspected environment."
        return report

    try:
        report.update(
            {
                "ok": True,
                "observation_space": _space_summary(env.observation_space),
                "action_space": _space_summary(env.action_space),
                "normalized_action_preview": _normalize_action_preview(env.action_space),
            }
        )
        if step:
            try:
                try:
                    reset_out = env.reset(seed=1)
                except TypeError:
                    if hasattr(env, "seed"):
                        env.seed(1)
                    reset_out = env.reset()
                report["reset_returns_tuple"] = isinstance(reset_out, tuple)
                action = env.action_space.sample()
                report["step_smoke"] = _step_result(env, action)
            except Exception as exc:
                report["step_smoke"] = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
    finally:
        try:
            env.close()
        except Exception:
            pass
    return report


def build_report(envs: Iterable[str], step: bool) -> Dict[str, Any]:
    status = _quiet_import("gym")
    if not status["ok"]:
        return {"summary": "Gym import failed", "gym": status, "torch": _torch_report(), "box2d": _quiet_import("Box2D"), "pygame": _quiet_import("pygame")}

    import gym

    return {
        "summary": "Cross-family compatibility probe for the repository's RL examples.",
        "torch": _torch_report(),
        "gym": {"ok": True, "version": getattr(gym, "__version__", None), "envs": [_env_report(gym, env_id, step=step) for env_id in envs]},
        "box2d": _quiet_import("Box2D"),
        "pygame": _quiet_import("pygame"),
        "legacy_env_map": LEGACY_MAP,
    }


def _print_text(report: Dict[str, Any]) -> None:
    print(report["summary"])
    print("\nTorch:")
    torch = report["torch"]
    if torch.get("ok"):
        print(f"  version={torch.get('version')} cuda={torch.get('cuda_available')} selected_device={torch.get('selected_device')}")
        if torch.get("cuda_device_count") is not None:
            print(f"  cuda_devices={torch.get('cuda_device_count')} first={torch.get('cuda_device_0')}")
    else:
        print(f"  ERROR {torch.get('error_type')}: {torch.get('error')}")

    print("\nOptional modules:")
    for key in ["box2d", "pygame"]:
        item = report[key]
        if item.get("ok"):
            print(f"  {key}: version={item.get('version')}")
        else:
            print(f"  {key}: ERROR {item.get('error_type')}: {item.get('error')}")

    print("\nGym envs:")
    gym = report["gym"]
    if not gym.get("ok"):
        print(f"  ERROR {gym.get('error_type')}: {gym.get('error')}")
        return
    print(f"  gym version={gym.get('version')}")
    for env in gym.get("envs", []):
        if not env.get("ok"):
            print(f"  {env['env_id']}: ERROR {env.get('error_type')}: {env.get('error')}")
            if env.get("hint"):
                print(f"    hint: {env['hint']}")
            continue
        obs = env.get("observation_space", {})
        action = env.get("action_space", {})
        print(f"  {env['env_id']}: ok obs={obs.get('type')}{obs.get('shape')} action={action.get('type')}{action.get('shape')}")
        if env.get("step_smoke"):
            smoke = env["step_smoke"]
            if smoke.get("step_len") is not None:
                print(f"    step_smoke tuple_len={smoke.get('step_len')} done={smoke.get('done')}")
            else:
                print(f"    step_smoke ERROR {smoke.get('error_type')}: {smoke.get('error')}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", action="append", dest="envs", help="Environment ID to inspect. Repeatable.")
    parser.add_argument("--step", action="store_true", help="Run one random-action step smoke for each environment.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args(argv)

    report = build_report(args.envs or DEFAULT_ENVS, step=args.step)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
