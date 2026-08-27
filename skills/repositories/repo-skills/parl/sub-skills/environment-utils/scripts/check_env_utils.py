#!/usr/bin/env python3
"""Safe diagnostics for PARL environment wrappers and utility helpers.

This helper performs non-training, non-network checks only. It verifies that the
installed PARL package can import selected wrapper/utility classes and exercises
small pure-Python/NumPy utilities with tiny data.

Examples:
  python scripts/check_env_utils.py
  python scripts/check_env_utils.py --backend torch --json
  python scripts/check_env_utils.py --optional-wrappers
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import tempfile
from pathlib import Path


def _status(name: str, status: str, detail: str) -> dict:
    return {"name": name, "status": status, "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check safe PARL env/util imports and tiny utility behavior.")
    parser.add_argument("--backend", choices=["auto", "torch", "paddle", "fluid"], default="auto", help="Set PARL_BACKEND before importing parl. Use auto to leave it unset.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--optional-wrappers", action="store_true", help="Also classify optional Atari/MuJoCo/multi-agent wrapper modules without constructing real environments.")
    args = parser.parse_args()

    if args.backend != "auto":
        os.environ["PARL_BACKEND"] = args.backend

    checks = []
    try:
        import numpy as np
        import parl
        from parl.env import ActionMappingWrapper, CompatWrapper, VectorEnv
        from parl.utils import CSVLogger, LinearDecayScheduler, PiecewiseScheduler, ReplayMemory
        checks.append(_status("import", "pass", f"parl {getattr(parl, '__version__', 'unknown')} imported"))
    except Exception as exc:  # pragma: no cover - intentionally diagnostic
        checks.append(_status("import", "fail", f"{type(exc).__name__}: {exc}"))
        if args.json:
            print(json.dumps({"ok": False, "checks": checks}, indent=2))
        else:
            for item in checks:
                print(f"[{item['status']}] {item['name']}: {item['detail']}")
        return 2

    try:
        piecewise = PiecewiseScheduler([(0, 1.0), (3, 0.5)])
        values = [piecewise.step(), piecewise.step(), piecewise.step()]
        linear = LinearDecayScheduler(1.0, 4)
        decay = [linear.step(), linear.step(2), linear.step()]
        assert values == [1.0, 1.0, 0.5]
        assert decay == [0.75, 0.25, 0.0]
        checks.append(_status("schedulers", "pass", f"piecewise={values}; linear={decay}"))
    except Exception as exc:
        checks.append(_status("schedulers", "fail", f"{type(exc).__name__}: {exc}"))

    try:
        rpm = ReplayMemory(max_size=3, obs_dim=2, act_dim=0)
        rpm.append(np.array([0.0, 1.0], dtype="float32"), 1, 1.0, np.array([1.0, 2.0], dtype="float32"), False)
        batch = rpm.sample_batch(1)
        assert len(rpm) == 1
        assert batch[0].shape == (1, 2)
        assert batch[1].shape == (1,)
        checks.append(_status("replay-memory", "pass", "discrete-action tiny append/sample shapes are valid"))
    except Exception as exc:
        checks.append(_status("replay-memory", "fail", f"{type(exc).__name__}: {exc}"))

    try:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "metrics.csv"
            csv_logger = CSVLogger(str(out))
            csv_logger.log_dict({"loss": 1.0, "reward": 2})
            csv_logger.log_dict({"loss": 0.5, "reward": 3})
            csv_logger.flush()
            csv_logger.close()
            text = out.read_text(encoding="utf-8")
            assert "loss,reward" in text and "0.5,3" in text
        checks.append(_status("csv-logger", "pass", "wrote consistent-key metrics to a temporary CSV"))
    except Exception as exc:
        checks.append(_status("csv-logger", "fail", f"{type(exc).__name__}: {exc}"))

    checks.append(_status("core-classes", "pass", f"loaded {CompatWrapper.__name__}, {ActionMappingWrapper.__name__}, {VectorEnv.__name__}"))

    if args.optional_wrappers:
        optional_modules = [
            "parl.env.atari_wrappers",
            "parl.env.mujoco_wrappers",
            "parl.env.multiagent_env",
            "parl.env.multiagent_simple_env",
        ]
        for module_name in optional_modules:
            try:
                importlib.import_module(module_name)
                checks.append(_status(module_name, "pass", "module imported; no environment constructed"))
            except Exception as exc:
                checks.append(_status(module_name, "optional-missing", f"{type(exc).__name__}: {exc}"))

    ok = all(item["status"] in {"pass", "optional-missing"} for item in checks)
    if args.json:
        print(json.dumps({"ok": ok, "checks": checks}, indent=2))
    else:
        for item in checks:
            print(f"[{item['status']}] {item['name']}: {item['detail']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
