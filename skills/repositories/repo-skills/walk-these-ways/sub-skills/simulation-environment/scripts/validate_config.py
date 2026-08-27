#!/usr/bin/env python3
"""Validate the static Go1 observation/action configuration contract.

This helper uses only the standard library. It never imports Isaac Gym or the
repository and is safe to run from any working directory.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULTS = {
    "num_obs": 42,
    "num_privileged_obs": 18,
    "history_length": 15,
    "num_actions": 12,
}


def _positive_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be a positive integer" % name)
    if not math.isfinite(float(value)) or int(value) != value or int(value) <= 0:
        raise ValueError("%s must be a positive integer" % name)
    return int(value)


def _load(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise ValueError("config is not a regular file: %s" % path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("config must be a readable JSON object: %s" % exc)
    if not isinstance(value, dict):
        raise ValueError("config root must be a JSON object")
    return value


def _find(mapping: Dict[str, Any], names: tuple) -> Optional[Any]:
    for name in names:
        if name in mapping:
            return mapping[name]
    # Permit a shallow Cfg-style object summary.
    for child in mapping.values():
        if isinstance(child, dict):
            found = _find(child, names)
            if found is not None:
                return found
    return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Go1 observation/history/action dimensions without importing Isaac Gym."
    )
    parser.add_argument("--config", type=Path, help="JSON object containing dimension fields")
    parser.add_argument("--num-obs", type=int)
    parser.add_argument("--num-privileged-obs", type=int)
    parser.add_argument("--history-length", type=int)
    parser.add_argument("--num-obs-history", type=int, help="flattened history width")
    parser.add_argument("--num-actions", type=int)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        config = _load(args.config) if args.config else {}
        supplied = {
            "num_obs": args.num_obs if args.num_obs is not None else _find(config, ("num_obs", "num_observations")),
            "num_privileged_obs": args.num_privileged_obs if args.num_privileged_obs is not None else _find(config, ("num_privileged_obs", "privileged_observations")),
            "history_length": args.history_length if args.history_length is not None else _find(config, ("history_length", "num_observation_history")),
            "num_obs_history": args.num_obs_history if args.num_obs_history is not None else _find(config, ("num_obs_history", "observation_history_width")),
            "num_actions": args.num_actions if args.num_actions is not None else _find(config, ("num_actions", "action_dim")),
        }
        values = dict(DEFAULTS)
        for key, value in supplied.items():
            if value is not None:
                values[key] = _positive_int(key, value)
        values["batch_size"] = _positive_int("batch_size", args.batch_size)
        if "num_obs_history" in supplied and supplied["num_obs_history"] is not None:
            expected = values["history_length"] * values["num_obs"]
            if values["num_obs_history"] != expected:
                raise ValueError("history mismatch: %d * %d != %d" % (values["history_length"], values["num_obs"], values["num_obs_history"]))
        values["num_obs_history"] = values["history_length"] * values["num_obs"]
        result = {
            "ok": True,
            "dimensions": values,
            "contract": {
                "actor_observation": [values["batch_size"], values["num_obs"]],
                "privileged_observation": [values["batch_size"], values["num_privileged_obs"]],
                "history": [values["batch_size"], values["num_obs_history"]],
                "action": [values["batch_size"], values["num_actions"]],
            },
            "runtime_note": "Static validation only; Isaac Gym construction and stepping remain unverified.",
        }
        if args.json:
            print(json.dumps(result, sort_keys=True))
        else:
            print("OK: obs=%d privileged=%d history=%d (%d frames) actions=%d" % (values["num_obs"], values["num_privileged_obs"], values["num_obs_history"], values["history_length"], values["num_actions"]))
            print(result["runtime_note"])
        return 0
    except (OSError, ValueError) as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
