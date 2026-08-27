#!/usr/bin/env python3
"""Render an RLinf cluster-placement summary from YAML without importing RLinf."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "PyYAML is not available in this Python environment. Install/activate an environment with pyyaml or inspect the YAML manually."
        ) from exc

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _summarize_component_placement(component_placement: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if component_placement is None:
        return rows
    if not isinstance(component_placement, dict):
        rows.append(
            {
                "components": ["<invalid>"],
                "style": "invalid",
                "raw": component_placement,
                "warning": "component_placement should be a mapping",
            }
        )
        return rows

    for key, value in component_placement.items():
        components = [part.strip() for part in str(key).split(",") if part.strip()]
        if isinstance(value, dict):
            rows.append(
                {
                    "components": components,
                    "style": "node-group",
                    "node_group": value.get("node_group", "<default>"),
                    "placement": value.get("placement"),
                    "raw": value,
                }
            )
        else:
            rows.append(
                {
                    "components": components,
                    "style": "short",
                    "node_group": "<default>",
                    "placement": value,
                    "raw": value,
                }
            )
    return rows


def _summarize_node_groups(node_groups: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in _as_list(node_groups):
        if not isinstance(item, dict):
            rows.append({"label": "<invalid>", "raw": item, "warning": "node group entry should be a mapping"})
            continue
        env_configs = []
        for env in _as_list(item.get("env_configs")):
            if isinstance(env, dict):
                env_configs.append(
                    {
                        "node_ranks": env.get("node_ranks"),
                        "python_interpreter_path": env.get("python_interpreter_path"),
                        "env_vars": env.get("env_vars"),
                    }
                )
            else:
                env_configs.append({"raw": env, "warning": "env_config entry should be a mapping"})
        hardware = item.get("hardware")
        rows.append(
            {
                "label": item.get("label"),
                "node_ranks": item.get("node_ranks"),
                "ignore_hardware": item.get("ignore_hardware", False),
                "hardware_type": hardware.get("type") if isinstance(hardware, dict) else None,
                "hardware": hardware,
                "env_configs": env_configs,
            }
        )
    return rows


def build_summary(config: Any, source: str) -> dict[str, Any]:
    if not isinstance(config, dict):
        return {
            "source": source,
            "valid_yaml_mapping": False,
            "warning": "Top-level YAML document is not a mapping.",
        }
    cluster = config.get("cluster") or {}
    if not isinstance(cluster, dict):
        return {
            "source": source,
            "valid_yaml_mapping": True,
            "cluster_present": False,
            "warning": "cluster key is present but is not a mapping.",
        }
    return {
        "source": source,
        "valid_yaml_mapping": True,
        "cluster_present": "cluster" in config,
        "num_nodes": cluster.get("num_nodes"),
        "auto_scheduler": cluster.get("auto_scheduler"),
        "component_placement": _summarize_component_placement(cluster.get("component_placement")),
        "node_groups": _summarize_node_groups(cluster.get("node_groups")),
        "notes": [
            "Short-form placement uses the default cluster-wide resource group.",
            "Node-group placement ranks are local to the selected group or to node ranks for the reserved node group.",
            "This script does not validate hardware availability; compare against ray status and RLinf runtime validation.",
        ],
    }


def print_text(summary: dict[str, Any]) -> None:
    print("RLinf cluster plan")
    print("=" * 18)
    print(f"Source: {summary.get('source')}")
    if not summary.get("valid_yaml_mapping", True):
        print(f"WARNING: {summary.get('warning')}")
        return
    if summary.get("warning"):
        print(f"WARNING: {summary.get('warning')}")
    print(f"cluster present: {summary.get('cluster_present')}")
    print(f"num_nodes: {summary.get('num_nodes')}")
    if summary.get("auto_scheduler") is not None:
        print(f"auto_scheduler: {summary.get('auto_scheduler')}")

    print("\ncomponent_placement:")
    placements = summary.get("component_placement") or []
    if not placements:
        print("  <none>")
    for row in placements:
        comps = ",".join(row.get("components") or [])
        print(
            f"  - components={comps or '<none>'} style={row.get('style')} "
            f"node_group={row.get('node_group')} placement={row.get('placement')}"
        )
        if row.get("warning"):
            print(f"    warning: {row['warning']}")

    print("\nnode_groups:")
    groups = summary.get("node_groups") or []
    if not groups:
        print("  <none> (default cluster group and reserved node group still exist at runtime)")
    for group in groups:
        print(
            f"  - label={group.get('label')} node_ranks={group.get('node_ranks')} "
            f"ignore_hardware={group.get('ignore_hardware')} hardware_type={group.get('hardware_type')}"
        )
        for env in group.get("env_configs") or []:
            print(
                f"    env_config node_ranks={env.get('node_ranks')} "
                f"python={env.get('python_interpreter_path')} env_vars={env.get('env_vars')}"
            )
        if group.get("warning"):
            print(f"    warning: {group['warning']}")

    print("\nnotes:")
    for note in summary.get("notes") or []:
        print(f"  - {note}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize RLinf cluster.num_nodes/component_placement/node_groups from YAML without importing RLinf."
    )
    parser.add_argument("config", help="Path to an RLinf/Hydra YAML config file.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    path = Path(args.config).expanduser()
    if not path.is_file():
        print(f"ERROR: config file does not exist: {path}", file=sys.stderr)
        return 2
    try:
        data = _load_yaml(path)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ERROR: failed to parse YAML: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    summary = build_summary(data, str(path))
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
