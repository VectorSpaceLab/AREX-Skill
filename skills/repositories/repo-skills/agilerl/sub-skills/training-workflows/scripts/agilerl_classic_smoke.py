#!/usr/bin/env python3
"""Safe AgileRL classical RL pre-flight checks without training."""

from __future__ import annotations

import argparse
import importlib
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algorithm", default="DQN", choices=["PPO", "DQN", "RainbowDQN", "DDPG", "TD3"], help="Algorithm family to validate.")
    parser.add_argument("--env", default="CartPole-v1", help="Gymnasium environment id for space inspection.")
    parser.add_argument("--num-envs", type=int, default=1, help="Vector env count for config validation only.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    args = parser.parse_args()

    report: dict[str, object] = {"algorithm": args.algorithm, "env": args.env, "checks": []}

    def check(name: str, func) -> None:  # type: ignore[no-untyped-def]
        try:
            value = func()
            report["checks"].append({"name": name, "ok": True, "value": value})  # type: ignore[index]
        except Exception as exc:  # noqa: BLE001 - diagnostic helper
            report["checks"].append({"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"})  # type: ignore[index]

    check("import agilerl", lambda: importlib.import_module("agilerl").__name__)
    check("import gymnasium", lambda: importlib.import_module("gymnasium").__version__)
    check("import torch", lambda: importlib.import_module("torch").__version__)

    def inspect_env() -> dict[str, str]:
        gym = importlib.import_module("gymnasium")
        env = gym.make(args.env)
        try:
            return {"observation_space": str(env.observation_space), "action_space": str(env.action_space)}
        finally:
            env.close()

    check("gymnasium spaces", inspect_env)

    discrete_algorithms = {"DQN", "RainbowDQN"}
    continuous_algorithms = {"DDPG", "TD3"}

    def algorithm_family_note() -> str:
        if args.algorithm in discrete_algorithms:
            return "expects a discrete action space"
        if args.algorithm in continuous_algorithms:
            return "expects a continuous Box action space"
        return "PPO can support discrete or continuous actions depending on network/action distribution"

    check("algorithm family", algorithm_family_note)
    check("num_envs positive", lambda: args.num_envs > 0 or (_ for _ in ()).throw(ValueError("num-envs must be positive")))

    ok = all(item["ok"] for item in report["checks"])  # type: ignore[index]
    report["ok"] = ok
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for item in report["checks"]:  # type: ignore[index]
            print(f"{item['name']}: {'ok' if item['ok'] else item['error']}")
        print(f"overall: {'ok' if ok else 'failed'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
