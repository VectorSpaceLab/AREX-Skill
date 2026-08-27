#!/usr/bin/env python3
"""Create a tiny synthetic AgileRL bandit setup without downloads or training."""

from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=8)
    parser.add_argument("--features", type=int, default=4)
    parser.add_argument("--arms", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report: dict[str, object] = {"checks": []}

    def add(name: str, ok: bool, value: object = None) -> None:
        item = {"name": name, "ok": ok}
        if value is not None:
            item["value"] = value
        report["checks"].append(item)  # type: ignore[index]

    add("positive_rows", args.rows > 0, args.rows)
    add("positive_features", args.features > 0, args.features)
    add("positive_arms", args.arms > 1, args.arms)

    try:
        import numpy as np
        import pandas as pd
        from agilerl.wrappers.learning import BanditEnv

        features = pd.DataFrame(np.arange(args.rows * args.features, dtype=float).reshape(args.rows, args.features))
        targets = pd.DataFrame((np.arange(args.rows) % args.arms).reshape(args.rows, 1))
        env = BanditEnv(features, targets)
        add("bandit_env", True, {"context_dim": env.context_dim, "arms": env.arms})
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        add("bandit_env", False, f"{type(exc).__name__}: {exc}")

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
