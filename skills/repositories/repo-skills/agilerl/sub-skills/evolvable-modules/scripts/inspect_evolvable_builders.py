#!/usr/bin/env python3
"""Construct tiny AgileRL evolvable config objects and spaces without training."""

from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["mlp", "cnn", "dict"], default="mlp")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report: dict[str, object] = {"mode": args.mode, "checks": []}

    def add(name: str, ok: bool, value: object = None) -> None:
        item = {"name": name, "ok": ok}
        if value is not None:
            item["value"] = value
        report["checks"].append(item)  # type: ignore[index]

    try:
        from gymnasium import spaces
        from agilerl.modules.configs import CnnNetConfig, MlpNetConfig, MultiInputNetConfig

        if args.mode == "mlp":
            obs = spaces.Box(low=-1.0, high=1.0, shape=(4,))
            config = MlpNetConfig(hidden_size=[16, 16])
        elif args.mode == "cnn":
            obs = spaces.Box(low=0, high=255, shape=(3, 32, 32))
            config = CnnNetConfig(channel_size=[8], kernel_size=[3], stride_size=[1])
        else:
            obs = spaces.Dict({"vector": spaces.Box(low=-1.0, high=1.0, shape=(4,)), "flag": spaces.Discrete(2)})
            config = MultiInputNetConfig(latent_dim=16, vector_space_mlp=True, mlp_config={"hidden_size": [16]})
        add("imports", True)
        add("observation_space", True, str(obs))
        add("config", True, config.__class__.__name__)
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        add("builder", False, f"{type(exc).__name__}: {exc}")

    report["ok"] = all(item["ok"] for item in report["checks"])  # type: ignore[index]
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for item in report["checks"]:  # type: ignore[index]
            print(f"{item['name']}: {'ok' if item['ok'] else 'failed'} {item.get('value', '')}")
        print(f"overall: {'ok' if report['ok'] else 'failed'}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
