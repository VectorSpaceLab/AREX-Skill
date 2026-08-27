#!/usr/bin/env python3
"""Safe TorchRL environment smoke check.

This helper verifies base TorchRL importability and CPU-safe behavior without
running native repo examples, downloading assets, starting services, or requiring
GPU/simulator extras.

Example:
    python check_torchrl_env.py --steps 3 --check-cli --json
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from typing import Any


def _status(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe TorchRL base environment smoke check.")
    parser.add_argument("--steps", type=int, default=3, help="Number of Pendulum rollout steps for the CPU smoke.")
    parser.add_argument("--check-cli", action="store_true", help="Also run rlrender --help if the entry point is available.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable lines.")
    args = parser.parse_args()

    checks: list[dict[str, Any]] = []

    try:
        import torch
        import tensordict
        import torchrl
    except Exception as exc:  # pragma: no cover - diagnostic path
        checks.append(_status("base-imports", False, f"{type(exc).__name__}: {exc}"))
        if args.json:
            print(json.dumps({"ok": False, "checks": checks}, indent=2))
        else:
            print("base-imports: FAIL", checks[-1]["detail"])
        return 1

    checks.append(
        _status(
            "base-imports",
            True,
            f"torch={torch.__version__}; tensordict={tensordict.__version__}; torchrl={torchrl.__version__}",
        )
    )
    checks.append(
        _status(
            "cuda-probe",
            True,
            f"torch.version.cuda={torch.version.cuda}; available={torch.cuda.is_available()}; count={torch.cuda.device_count()}",
        )
    )

    try:
        from tensordict.nn import TensorDictModule
        from torch import nn
        from torchrl.collectors import Collector
        from torchrl.data import LazyTensorStorage, TensorDictReplayBuffer
        from torchrl.envs import PendulumEnv, StepCounter, TransformedEnv, step_mdp
        from torchrl.modules import Actor, ProbabilisticActor, TanhNormal, ValueOperator
        from torchrl.objectives import ClipPPOLoss, DQNLoss, SACLoss

        _ = (Collector, Actor, ProbabilisticActor, TanhNormal, ValueOperator, ClipPPOLoss, DQNLoss, SACLoss)
        env = TransformedEnv(PendulumEnv(), StepCounter(max_steps=max(args.steps, 1)))
        rollout = env.rollout(max_steps=max(args.steps, 1))
        rb = TensorDictReplayBuffer(storage=LazyTensorStorage(16), batch_size=2)
        rb.extend(rollout)
        sample = rb.sample()
        module = TensorDictModule(nn.Linear(3, 1), in_keys=["observation"], out_keys=["action"])
        next_td = step_mdp(rollout[0])
        checks.append(
            _status(
                "core-cpu-smoke",
                True,
                f"rollout_batch={tuple(rollout.batch_size)}; sample_batch={tuple(sample.batch_size)}; module_out={module.out_keys}; next_keys={list(map(str, next_td.keys(True)))[:6]}",
            )
        )
    except Exception as exc:  # pragma: no cover - diagnostic path
        checks.append(_status("core-cpu-smoke", False, f"{type(exc).__name__}: {exc}"))

    optional_modules = {
        "gymnasium": "Gym/Gymnasium wrappers",
        "dm_control": "DM Control wrappers",
        "ray": "Ray collectors/replay/services",
        "vllm": "vLLM LLM serving",
        "sglang": "SGLang LLM serving",
        "lerobot": "VLA/robot datasets",
        "moviepy": "rendering/video",
    }
    for mod, label in optional_modules.items():
        checks.append(_status(f"optional:{mod}", importlib.util.find_spec(mod) is not None, label))

    if args.check_cli:
        exe = shutil.which("rlrender")
        if exe is None:
            from pathlib import Path

            candidate = Path(sys.executable).resolve().parent / "rlrender"
            exe = str(candidate) if candidate.exists() else None
        if exe is None:
            checks.append(_status("rlrender-help", False, "rlrender entry point not found on PATH or next to sys.executable"))
        else:
            proc = subprocess.run([exe, "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
            detail = (proc.stdout or proc.stderr).splitlines()[0] if (proc.stdout or proc.stderr) else "no output"
            checks.append(_status("rlrender-help", proc.returncode == 0, detail))

    ok = all(c["ok"] for c in checks if not c["name"].startswith("optional:"))
    if args.json:
        print(json.dumps({"ok": ok, "checks": checks}, indent=2, sort_keys=True))
    else:
        for c in checks:
            state = "OK" if c["ok"] else "MISSING" if c["name"].startswith("optional:") else "FAIL"
            print(f"{c['name']}: {state} - {c['detail']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
