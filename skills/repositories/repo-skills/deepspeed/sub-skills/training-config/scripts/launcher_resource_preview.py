#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# DeepSpeed Team
"""Preview DeepSpeed launcher hostfile include/exclude resources without launching training."""

import argparse
import re
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Dict, List, MutableMapping, Tuple

ResourceMap = MutableMapping[str, List[int]]


def parse_hostfile_text(text: str) -> ResourceMap:
    pattern = re.compile(r"^(\S+)\s+slots=(\d+)")
    resources: ResourceMap = OrderedDict()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = pattern.search(line)
        if not match:
            raise ValueError(f"bad hostfile entry: {line}")
        host = match.group(1)
        slots = int(match.group(2))
        if host in resources:
            raise ValueError(f"hostfile contains multiple entries for {host}")
        if slots <= 0:
            raise ValueError(f"host {host} must have at least one slot")
        resources[host] = list(range(slots))
    if not resources:
        raise ValueError("hostfile is empty or not formatted correctly")
    return resources


def parse_node_config(node_config: str) -> Tuple[str, List[int]]:
    if not node_config:
        raise ValueError("empty node spec")
    if ":" not in node_config:
        return node_config, []
    hostname, slot_text = node_config.split(":", 1)
    if not hostname or not slot_text:
        raise ValueError(f"bad node spec: {node_config}")
    try:
        slots = [int(value) for value in slot_text.split(",")]
    except ValueError as error:
        raise ValueError(f"bad slot list in {node_config}") from error
    if any(slot < 0 for slot in slots):
        raise ValueError(f"negative slot in {node_config}")
    return hostname, slots


def parse_node_config_list(filter_text: str) -> Dict[str, List[int]]:
    node_configs: Dict[str, List[int]] = defaultdict(list)
    for node_config in filter_text.split("@"):
        hostname, slots = parse_node_config(node_config)
        node_configs[hostname].extend(slots)
    return {host: sorted(set(slots)) for host, slots in node_configs.items()}


def apply_filter(host_info: ResourceMap, include: str = "", exclude: str = "") -> ResourceMap:
    if include and exclude:
        raise ValueError("include and exclude are mutually exclusive")
    if not include and not exclude:
        return OrderedDict((host, list(slots)) for host, slots in host_info.items())

    filtered: ResourceMap
    filter_text = include or exclude
    parsed_filter = parse_node_config_list(filter_text)
    if include:
        filtered = OrderedDict()
    else:
        filtered = OrderedDict((host, list(slots)) for host, slots in host_info.items())

    for host, requested_slots in parsed_filter.items():
        if host not in host_info:
            raise ValueError(f"hostname '{host}' not found in hostfile")
        available_slots = host_info[host]
        if requested_slots:
            missing = [slot for slot in requested_slots if slot not in available_slots]
            if missing:
                raise ValueError(f"slots {missing} on host '{host}' not found in hostfile")
            if include:
                filtered[host] = sorted(set(filtered.get(host, []) + requested_slots))
            else:
                remaining = [slot for slot in filtered.get(host, []) if slot not in requested_slots]
                if remaining:
                    filtered[host] = remaining
                elif host in filtered:
                    del filtered[host]
        elif include:
            filtered[host] = list(available_slots)
        elif host in filtered:
            del filtered[host]
    return filtered


def format_resources(resources: ResourceMap) -> str:
    if not resources:
        return "<no resources selected>"
    lines = []
    total = 0
    for host, slots in resources.items():
        total += len(slots)
        slot_text = ",".join(str(slot) for slot in slots)
        lines.append(f"{host}: slots={slot_text} count={len(slots)}")
    lines.append(f"total_slots={total}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hostfile", type=Path, help="Hostfile with lines like 'worker-0 slots=4'")
    parser.add_argument("--host", action="append", default=[], help="Inline host spec HOST:SLOTS, e.g. worker-0:4")
    parser.add_argument("--include", default="", help="DeepSpeed include filter, e.g. worker-0:0,1@worker-1")
    parser.add_argument("--exclude", default="", help="DeepSpeed exclude filter, mutually exclusive with --include")
    args = parser.parse_args()

    try:
        if args.hostfile:
            resources = parse_hostfile_text(args.hostfile.read_text(encoding="utf-8"))
        elif args.host:
            resources = OrderedDict()
            for host_spec in args.host:
                host, slot_count_text = host_spec.rsplit(":", 1)
                slot_count = int(slot_count_text)
                if slot_count <= 0:
                    raise ValueError(f"{host_spec} must have positive slot count")
                if host in resources:
                    raise ValueError(f"duplicate host {host}")
                resources[host] = list(range(slot_count))
        else:
            raise ValueError("provide --hostfile or one or more --host HOST:SLOTS entries")

        selected = apply_filter(resources, include=args.include, exclude=args.exclude)
    except Exception as error:  # noqa: BLE001 - command-line preview should surface concise errors.
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    print(format_resources(selected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
