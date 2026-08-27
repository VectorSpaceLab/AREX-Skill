#!/usr/bin/env python3
"""Read-only preflight checks for DGL distributed partition config JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

CANONICAL_ETYPE_RE = re.compile(r"^[^:]+:[^:]+:[^:]+$")


class Finding:
    def __init__(self, level: str, message: str) -> None:
        self.level = level
        self.message = message

    def __str__(self) -> str:
        return f"{self.level}: {self.message}"


class Checker:
    def __init__(self, config_path: Path, workspace: Path | None) -> None:
        self.config_path = config_path
        self.config_dir = config_path.parent
        self.workspace = workspace
        self.findings: list[Finding] = []
        self.metadata: dict[str, Any] = {}

    def error(self, message: str) -> None:
        self.findings.append(Finding("ERROR", message))

    def warn(self, message: str) -> None:
        self.findings.append(Finding("WARN", message))

    def ok(self, message: str) -> None:
        self.findings.append(Finding("OK", message))

    def load(self) -> None:
        try:
            with self.config_path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
        except Exception as exc:  # noqa: BLE001 - CLI should report concise failures.
            self.error(f"cannot read JSON: {exc}")
            return
        if not isinstance(loaded, dict):
            self.error("partition config root must be a JSON object")
            return
        self.metadata = loaded
        self.ok("loaded JSON object")

    def check_required_fields(self) -> None:
        required = ["graph_name", "num_parts", "node_map", "edge_map"]
        for key in required:
            if key not in self.metadata:
                self.error(f"missing required field: {key}")
        graph_name = self.metadata.get("graph_name")
        if isinstance(graph_name, str) and graph_name:
            self.ok(f"graph_name={graph_name}")
        elif "graph_name" in self.metadata:
            self.error("graph_name must be a non-empty string")
        num_parts = self.metadata.get("num_parts")
        if isinstance(num_parts, int) and num_parts > 0:
            self.ok(f"num_parts={num_parts}")
        elif "num_parts" in self.metadata:
            self.error("num_parts must be a positive integer")

    def check_type_maps(self) -> None:
        for key in ("ntypes", "etypes"):
            value = self.metadata.get(key)
            if value is None:
                self.warn(f"missing optional type map: {key}")
                continue
            if not isinstance(value, dict):
                self.error(f"{key} must be an object mapping type string to integer id")
                continue
            bad = [name for name, type_id in value.items() if not isinstance(name, str) or not isinstance(type_id, int)]
            if bad:
                self.error(f"{key} contains non-string keys or non-integer ids: {bad[:5]}")
            else:
                self.ok(f"{key} has {len(value)} entries")
        etypes = self.metadata.get("etypes")
        if isinstance(etypes, dict):
            noncanonical = [key for key in etypes if isinstance(key, str) and not CANONICAL_ETYPE_RE.match(key)]
            if noncanonical:
                self.warn(
                    "etypes contains non-canonical keys; heterograph configs should use "
                    f"src:etype:dst strings: {noncanonical[:5]}"
                )

    def check_ranges(self, key: str) -> None:
        value = self.metadata.get(key)
        num_parts = self.metadata.get("num_parts")
        if not isinstance(value, dict):
            if key in self.metadata:
                self.error(f"{key} must be an object")
            return
        if not isinstance(num_parts, int) or num_parts <= 0:
            self.warn(f"cannot fully validate {key} ranges without valid num_parts")
            return
        for type_name, ranges in value.items():
            if not isinstance(type_name, str):
                self.error(f"{key} contains a non-string type key")
                continue
            if key == "edge_map" and not CANONICAL_ETYPE_RE.match(type_name):
                self.warn(
                    f"edge_map key '{type_name}' is not canonical src:etype:dst; "
                    "migration or regeneration may be required"
                )
            if not isinstance(ranges, list):
                self.error(f"{key}.{type_name} must be a list of [start, end] ranges")
                continue
            if len(ranges) != num_parts:
                self.error(
                    f"{key}.{type_name} has {len(ranges)} ranges, expected num_parts={num_parts}"
                )
                continue
            previous_end: int | None = None
            for part_id, range_pair in enumerate(ranges):
                if (
                    not isinstance(range_pair, list)
                    or len(range_pair) != 2
                    or not all(isinstance(item, int) for item in range_pair)
                ):
                    self.error(f"{key}.{type_name}[{part_id}] must be [int_start, int_end]")
                    continue
                start, end = range_pair
                if start < 0 or end < 0:
                    self.error(f"{key}.{type_name}[{part_id}] contains negative values")
                if start > end:
                    self.error(f"{key}.{type_name}[{part_id}] has start > end")
                if previous_end is not None and start != previous_end:
                    self.warn(
                        f"{key}.{type_name}[{part_id}] starts at {start}, previous end is {previous_end}; "
                        "non-contiguous maps may be intentional but deserve review"
                    )
                previous_end = end
        self.ok(f"checked {key} ranges")

    def check_part_entries(self) -> None:
        num_parts = self.metadata.get("num_parts")
        if not isinstance(num_parts, int) or num_parts <= 0:
            return
        for part_id in range(num_parts):
            key = f"part-{part_id}"
            part_entry = self.metadata.get(key)
            if not isinstance(part_entry, dict):
                self.error(f"missing or invalid {key} object")
                continue
            graph_keys = [
                name
                for name in ("part_graph", "part_graph_graphbolt", "graph")
                if name in part_entry
            ]
            if not graph_keys:
                self.warn(f"{key} has no recognized graph path key")
            for field, value in part_entry.items():
                if not isinstance(value, str):
                    continue
                path = Path(value)
                if path.is_absolute():
                    self.warn(f"{key}.{field} is absolute; shared workspaces usually need relative paths")
                    candidate = path
                else:
                    candidate = self.config_dir / path
                if not candidate.exists():
                    self.warn(f"{key}.{field} path not found from config directory: {value}")
        self.ok("checked part-* entries")

    def check_workspace(self) -> None:
        if self.workspace is None:
            return
        if not self.workspace.exists() or not self.workspace.is_dir():
            self.error(f"workspace does not exist or is not a directory: {self.workspace}")
            return
        try:
            self.config_path.resolve().relative_to(self.workspace.resolve())
            self.ok("part_config is under workspace")
        except ValueError:
            self.warn("part_config is not under workspace; launch.py expects workspace-relative config paths")

    def check_ip_config(self, ip_config: Path | None) -> None:
        if ip_config is None:
            return
        path = ip_config if ip_config.is_absolute() else ((self.workspace or Path.cwd()) / ip_config)
        if not path.is_file():
            self.error(f"ip_config not found: {path}")
            return
        hosts = 0
        with path.open("r", encoding="utf-8") as handle:
            for line_no, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) not in (1, 2):
                    self.error(f"ip_config line {line_no} must contain HOST or HOST PORT")
                    continue
                if len(parts) == 2:
                    try:
                        port = int(parts[1])
                    except ValueError:
                        self.error(f"ip_config line {line_no} port is not an integer")
                        continue
                    if not 1 <= port <= 65535:
                        self.error(f"ip_config line {line_no} port must be in 1..65535")
                hosts += 1
        if hosts == 0:
            self.error("ip_config has no host entries")
            return
        self.ok(f"ip_config host entries={hosts}")
        num_parts = self.metadata.get("num_parts")
        if isinstance(num_parts, int) and hosts != num_parts:
            self.error(f"ip_config host count {hosts} does not match num_parts {num_parts}")

    def run(self, ip_config: Path | None) -> int:
        self.load()
        if self.metadata:
            self.check_required_fields()
            self.check_type_maps()
            self.check_ranges("node_map")
            self.check_ranges("edge_map")
            self.check_part_entries()
            self.check_workspace()
            self.check_ip_config(ip_config)
        for finding in self.findings:
            print(finding)
        errors = [finding for finding in self.findings if finding.level == "ERROR"]
        warnings = [finding for finding in self.findings if finding.level == "WARN"]
        print(f"SUMMARY: errors={len(errors)} warnings={len(warnings)}")
        return 1 if errors else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Perform read-only schema/path preflight for a DGL partition config. "
            "This script does not import DGL, load graph binaries, SSH, launch, or mutate files."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--part-config", required=True, help="Path to graph partition JSON.")
    parser.add_argument("--workspace", help="Optional shared workspace root for launch preflight.")
    parser.add_argument("--ip-config", help="Optional ip_config path; relative paths resolve under --workspace or cwd.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else None
    checker = Checker(Path(args.part_config).expanduser().resolve(), workspace)
    ip_config = Path(args.ip_config).expanduser() if args.ip_config else None
    return checker.run(ip_config)


if __name__ == "__main__":
    raise SystemExit(main())
