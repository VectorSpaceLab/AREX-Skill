#!/usr/bin/env python3
"""Validate a tiny AgileRL multi-agent setup shape without training."""

from __future__ import annotations

import argparse
import json


def group_id(agent_id: str) -> str:
    return agent_id.rsplit("_", 1)[0] if "_" in agent_id else agent_id


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents", nargs="+", default=["speaker_0", "listener_0"], help="Agent IDs to validate.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report: dict[str, object] = {"agents": args.agents, "checks": []}

    def add(name: str, ok: bool, value: object = None) -> None:
        item = {"name": name, "ok": ok}
        if value is not None:
            item["value"] = value
        report["checks"].append(item)  # type: ignore[index]

    add("unique_agent_ids", len(set(args.agents)) == len(args.agents), args.agents)
    groups = {agent: group_id(agent) for agent in args.agents}
    add("groups", True, groups)

    try:
        from gymnasium import spaces
        import agilerl.vector.pz_async_vec_env  # noqa: F401
        obs_spaces = {agent: str(spaces.Box(low=-1.0, high=1.0, shape=(4,))) for agent in args.agents}
        action_spaces = {agent: str(spaces.Discrete(2)) for agent in args.agents}
        net_config = {group: {"encoder_config": {"hidden_size": [16]}, "head_config": {"hidden_size": [16]}} for group in sorted(set(groups.values()))}
        add("imports", True)
        add("observation_spaces", True, obs_spaces)
        add("action_spaces", True, action_spaces)
        add("group_net_config", True, net_config)
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        add("imports/config", False, f"{type(exc).__name__}: {exc}")

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
