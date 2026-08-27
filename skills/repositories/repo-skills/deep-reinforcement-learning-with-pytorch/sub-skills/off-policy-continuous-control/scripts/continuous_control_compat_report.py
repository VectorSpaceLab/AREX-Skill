#!/usr/bin/env python3
"""Non-training compatibility probe for the repo's DDPG/SAC/TD3 workflows.

The script checks installed torch/gym support, legacy-vs-modern Gym env IDs,
Box2D/pygame availability, continuous action-space bounds, and optional one-step
random-action smokes. It does not import the original repository scripts, load
checkpoints, render, or train.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import sys
import warnings
from typing import Any, Dict, Iterable, List, Optional

LEGACY_ENV_MAP = {
    "Pendulum-v0": "Pendulum-v1",
    "BipedalWalker-v2": "BipedalWalker-v3",
}
DEFAULT_ENVS = ["Pendulum-v0", "Pendulum-v1", "BipedalWalker-v2", "BipedalWalker-v3"]


def _module_status(module_name: str) -> Dict[str, Any]:
    """Import a module while suppressing noisy import banners.

    Pygame prints a greeting on import and Gym can emit migration warnings;
    suppressing those streams keeps --json output machine-readable.
    """
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - intentionally diagnostic
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
    return {"ok": True, "version": getattr(module, "__version__", None)}


def _torch_report() -> Dict[str, Any]:
    status = _module_status("torch")
    if not status["ok"]:
        return status
    import torch  # type: ignore

    report: Dict[str, Any] = {
        "ok": True,
        "version": getattr(torch, "__version__", None),
        "cuda_version": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "selected_device_by_repo_scripts": "cuda" if torch.cuda.is_available() else "cpu",
    }
    if torch.cuda.is_available():
        try:
            report["cuda_device_count"] = torch.cuda.device_count()
            report["cuda_device_0"] = torch.cuda.get_device_name(0)
        except Exception as exc:  # pragma: no cover - diagnostic only
            report["cuda_detail_error"] = f"{type(exc).__name__}: {exc}"
    return report


def _to_jsonable(value: Any, max_items: int = 8) -> Any:
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, tuple):
        value = list(value)
    if isinstance(value, list):
        clipped = value[:max_items]
        return [_to_jsonable(v, max_items=max_items) for v in clipped]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _space_summary(space: Any) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "type": type(space).__name__,
        "shape": _to_jsonable(getattr(space, "shape", None)),
    }
    if hasattr(space, "low"):
        summary["low"] = _to_jsonable(space.low)
    if hasattr(space, "high"):
        summary["high"] = _to_jsonable(space.high)
    if hasattr(space, "n"):
        summary["n"] = getattr(space, "n")
    return summary


def _normalized_zero_mapping(action_space: Any) -> Optional[Dict[str, Any]]:
    if not (hasattr(action_space, "low") and hasattr(action_space, "high")):
        return None
    try:
        import numpy as np  # type: ignore

        low = np.asarray(action_space.low, dtype=float)
        high = np.asarray(action_space.high, dtype=float)
        zero_norm = np.zeros_like(low)
        env_action = low + (zero_norm + 1.0) * 0.5 * (high - low)
        reversed_action = 2.0 * (env_action - low) / (high - low) - 1.0
        return {
            "normalized_zero_to_env_action": _to_jsonable(env_action),
            "reverse_check": _to_jsonable(reversed_action),
        }
    except Exception as exc:  # pragma: no cover - diagnostic only
        return {"error": f"{type(exc).__name__}: {exc}"}


def _safe_len(value: Any) -> Optional[int]:
    try:
        return len(value)
    except Exception:
        return None


def _env_report(gym: Any, env_id: str, step: bool = False) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "env_id": env_id,
        "modern_substitute": LEGACY_ENV_MAP.get(env_id),
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            env = gym.make(env_id)
        except Exception as exc:
            report.update(
                {
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "warnings": [str(w.message) for w in caught],
                }
            )
            if env_id in LEGACY_ENV_MAP:
                report["hint"] = f"Use {LEGACY_ENV_MAP[env_id]} on modern Gym versions."
            return report

    try:
        report.update(
            {
                "ok": True,
                "warnings": [str(w.message) for w in caught],
                "observation_space": _space_summary(env.observation_space),
                "action_space": _space_summary(env.action_space),
                "continuous_action_space": type(env.action_space).__name__ == "Box",
                "normalized_action_mapping": _normalized_zero_mapping(env.action_space),
            }
        )
        if step:
            try:
                reset_out = env.reset()
                reset_tuple = isinstance(reset_out, tuple)
                sample_action = env.action_space.sample()
                step_out = env.step(sample_action)
                step_len = _safe_len(step_out)
                report["step_smoke"] = {
                    "ok": True,
                    "reset_returns_tuple": reset_tuple,
                    "step_tuple_length": step_len,
                    "api_hint": "5-value step means Gymnasium/new Gym; repo scripts expect 4 values."
                    if step_len == 5
                    else "4-value step matches the repo scripts' old Gym expectation.",
                }
            except Exception as exc:
                report["step_smoke"] = {
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
    finally:
        try:
            env.close()
        except Exception:
            pass
    return report


def _gym_report(env_ids: Iterable[str], step: bool = False) -> Dict[str, Any]:
    status = _module_status("gym")
    if not status["ok"]:
        return status
    import gym  # type: ignore

    return {
        "ok": True,
        "version": getattr(gym, "__version__", None),
        "envs": [_env_report(gym, env_id, step=step) for env_id in env_ids],
    }


def build_report(env_ids: Iterable[str], step: bool = False) -> Dict[str, Any]:
    env_ids = list(env_ids)
    return {
        "summary": "DDPG/SAC/TD3 compatibility probe; no training, rendering, or checkpoint loading performed.",
        "torch": _torch_report(),
        "gym": _gym_report(env_ids, step=step),
        "box2d_module": _module_status("Box2D"),
        "pygame_module": _module_status("pygame"),
        "legacy_env_map": LEGACY_ENV_MAP,
    }


def _print_text(report: Dict[str, Any]) -> None:
    print(report["summary"])
    print("\nTorch:")
    torch = report["torch"]
    if torch.get("ok"):
        print(
            f"  ok: version={torch.get('version')} cuda={torch.get('cuda_available')} "
            f"selected_device={torch.get('selected_device_by_repo_scripts')}"
        )
        if torch.get("cuda_device_count") is not None:
            print(f"  cuda devices: {torch.get('cuda_device_count')} first={torch.get('cuda_device_0')}")
    else:
        print(f"  missing/error: {torch.get('error_type')}: {torch.get('error')}")

    print("\nOptional modules:")
    for key in ["box2d_module", "pygame_module"]:
        item = report[key]
        if item.get("ok"):
            print(f"  {key}: ok version={item.get('version')}")
        else:
            print(f"  {key}: missing/error {item.get('error_type')}: {item.get('error')}")

    print("\nGym environments:")
    gym = report["gym"]
    if not gym.get("ok"):
        print(f"  gym missing/error: {gym.get('error_type')}: {gym.get('error')}")
        return
    print(f"  gym version: {gym.get('version')}")
    for env in gym.get("envs", []):
        env_id = env["env_id"]
        if not env.get("ok"):
            print(f"  {env_id}: ERROR {env.get('error_type')}: {env.get('error')}")
            if env.get("hint"):
                print(f"    hint: {env['hint']}")
            continue
        action = env.get("action_space", {})
        obs = env.get("observation_space", {})
        print(
            f"  {env_id}: ok obs={obs.get('type')}{obs.get('shape')} "
            f"action={action.get('type')}{action.get('shape')}"
        )
        if action.get("low") is not None and action.get("high") is not None:
            print(f"    action low={action.get('low')} high={action.get('high')}")
        mapping = env.get("normalized_action_mapping") or {}
        if mapping and not mapping.get("error"):
            print(f"    normalized zero -> env action {mapping.get('normalized_zero_to_env_action')}")
        if env.get("warnings"):
            print(f"    warnings: {' | '.join(env['warnings'])}")
        if env.get("step_smoke"):
            smoke = env["step_smoke"]
            if smoke.get("ok"):
                print(f"    step smoke: ok, tuple length={smoke.get('step_tuple_length')} ({smoke.get('api_hint')})")
            else:
                print(f"    step smoke: ERROR {smoke.get('error_type')}: {smoke.get('error')}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--env",
        dest="envs",
        action="append",
        help="Gym environment ID to inspect. Can be repeated. Defaults to legacy and modern Pendulum/BipedalWalker IDs.",
    )
    parser.add_argument("--step", action="store_true", help="Also run one random-action env.step smoke for envs that can be created.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args(argv)

    report = build_report(args.envs or DEFAULT_ENVS, step=args.step)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
