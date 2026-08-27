#!/usr/bin/env python3
"""Diagnose a Stable-Baselines3 installation without running long training.

Examples:
  python scripts/sb3_doctor.py
  python scripts/sb3_doctor.py --check extras --check signatures
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys


def module_version(name: str) -> str | None:
    try:
        module = importlib.import_module(name)
    except Exception:
        return None
    return str(getattr(module, "__version__", "installed"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SB3 imports, optional extras, backend visibility, and key signatures.")
    parser.add_argument("--check", action="append", choices=["extras", "signatures"], default=[], help="Additional checks to run.")
    args = parser.parse_args()

    result: dict[str, object] = {"python": sys.version.split()[0], "imports": {}, "optional": {}, "signatures": {}}

    try:
        import stable_baselines3 as sb3
        import torch
    except Exception as exc:
        print(f"SB3 core import failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    result["stable_baselines3_version"] = sb3.__version__
    result["exports"] = list(getattr(sb3, "__all__", []))
    result["torch"] = {"version": torch.__version__, "cuda_available": bool(torch.cuda.is_available())}

    for module_name in ["gymnasium", "numpy", "cloudpickle"]:
        result["imports"][module_name] = module_version(module_name)

    if "extras" in args.check:
        for module_name in ["tensorboard", "cv2", "pygame", "ale_py", "pandas", "matplotlib", "tqdm", "rich"]:
            result["optional"][module_name] = module_version(module_name)

    if "signatures" in args.check:
        from stable_baselines3 import DQN, PPO, SAC
        from stable_baselines3.common.env_checker import check_env
        from stable_baselines3.common.env_util import make_vec_env
        from stable_baselines3.common.evaluation import evaluate_policy

        result["signatures"] = {
            "PPO.__init__": str(inspect.signature(PPO.__init__)),
            "DQN.__init__": str(inspect.signature(DQN.__init__)),
            "SAC.__init__": str(inspect.signature(SAC.__init__)),
            "check_env": str(inspect.signature(check_env)),
            "make_vec_env": str(inspect.signature(make_vec_env)),
            "evaluate_policy": str(inspect.signature(evaluate_policy)),
        }

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
