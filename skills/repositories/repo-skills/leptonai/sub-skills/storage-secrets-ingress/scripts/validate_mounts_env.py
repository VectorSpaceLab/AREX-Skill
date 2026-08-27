#!/usr/bin/env python3
"""Local LeptonAI mount/env/secret/ingress preflight checker.

This helper performs only local parsing and linting. It never constructs an
APIClient, never reads workspace credentials, and never contacts Lepton. Use it
before asking the user to approve workload, storage, secret, or ingress commands.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple

RESERVED_ENV_NAMES = {
    "LEPTON_WORKSPACE_ID",
    "LEPTON_WORKSPACE_TOKEN",
    "LEPTON_WORKSPACE_URL",
    "LEPTON_DEPLOYMENT_NAME",
    "LEPTON_JOB_NAME",
    "LEPTON_LOCAL_DEPLOYMENT_TOKEN",
}


@dataclass
class Finding:
    level: str
    message: str
    item: Optional[str] = None


@dataclass
class Report:
    mounts: List[dict] = field(default_factory=list)
    env: List[dict] = field(default_factory=list)
    secrets: List[dict] = field(default_factory=list)
    ip_allowlist: List[str] = field(default_factory=list)
    tokens: int = 0
    existing_endpoints: List[dict] = field(default_factory=list)
    set_endpoints: List[dict] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(item.level == "error" for item in self.findings)

    def add(self, level: str, message: str, item: Optional[str] = None) -> None:
        self.findings.append(Finding(level=level, message=message, item=item))


def _split_mount(value: str) -> Tuple[str, str, str]:
    parts = value.split(":", 2)
    if len(parts) != 3:
        raise ValueError(
            "expected FROM_PATH:MOUNT_PATH:VOLUME split on the first two colons; "
            "VOLUME should be node-local or node-<type>:<storage_name>"
        )
    source, mount_path, volume = (part.strip() for part in parts)
    if not source:
        raise ValueError("FROM_PATH cannot be empty")
    if not mount_path:
        raise ValueError("MOUNT_PATH cannot be empty")
    if not volume:
        raise ValueError("VOLUME cannot be empty")
    if volume == "node-local":
        return source, mount_path, volume
    if volume.startswith("node-"):
        volume_parts = volume.split(":")
        if len(volume_parts) == 1:
            raise ValueError(f"missing storage_name in VOLUME `{volume}`")
        if len(volume_parts) != 2:
            raise ValueError(
                f"VOLUME `{volume}` must contain exactly one colon after node-<type>"
            )
        storage_type = volume_parts[0][len("node-") :].strip()
        storage_name = volume_parts[1].strip()
        if not storage_type:
            raise ValueError(f"missing storage type in VOLUME `{volume}`")
        if not storage_name:
            raise ValueError(f"missing storage_name in VOLUME `{volume}`")
    return source, mount_path, volume


def _parse_key_value(value: str, *, allow_same: bool, item_name: str) -> Tuple[str, str]:
    if "=" in value:
        key, val = value.split("=", 1)
    elif allow_same:
        key = val = value
    else:
        raise ValueError(f"{item_name} must use NAME=VALUE form")
    key = key.strip()
    if not key:
        raise ValueError(f"{item_name} name cannot be empty")
    if key in RESERVED_ENV_NAMES:
        raise ValueError(f"{item_name} name `{key}` is reserved by Lepton")
    return key, val


def _parse_endpoint_weight(value: str) -> Tuple[str, int]:
    if ":" not in value:
        raise ValueError("expected ENDPOINT:WEIGHT")
    name, weight_text = value.rsplit(":", 1)
    name = name.strip()
    if not name:
        raise ValueError("endpoint name cannot be empty")
    try:
        weight = int(weight_text)
    except ValueError as exc:
        raise ValueError("weight must be an integer") from exc
    if weight < 0:
        raise ValueError("weight must be non-negative")
    return name, weight


def _parse_ip_values(values: Iterable[str], report: Report) -> None:
    for raw in values:
        for part in raw.split(","):
            item = part.strip()
            if not item:
                continue
            try:
                if "/" in item:
                    ipaddress.ip_network(item, strict=False)
                else:
                    ipaddress.ip_address(item)
            except ValueError:
                report.add("error", "invalid IP address or CIDR in --ip-whitelist", item)
            else:
                report.ip_allowlist.append(item)


def build_report(args: argparse.Namespace) -> Report:
    report = Report(tokens=len(args.token or []))

    for value in args.mount or []:
        try:
            source, mount_path, volume = _split_mount(value)
        except ValueError as exc:
            report.add("error", str(exc), value)
        else:
            report.mounts.append({"source": source, "mount_path": mount_path, "volume": volume})

    for value in args.env or []:
        try:
            name, val = _parse_key_value(value, allow_same=False, item_name="env")
        except ValueError as exc:
            report.add("error", str(exc), value)
        else:
            report.env.append({"name": name, "value": "<redacted>", "value_length": len(val)})

    for value in args.secret or []:
        try:
            name, secret_name = _parse_key_value(value, allow_same=True, item_name="secret")
        except ValueError as exc:
            report.add("error", str(exc), value)
        else:
            report.secrets.append({"env_name": name, "secret_name": secret_name})

    if args.public and args.ip_whitelist:
        report.add("error", "--public and --ip-whitelist are mutually exclusive")
    _parse_ip_values(args.ip_whitelist or [], report)

    for attr, target in (("existing_endpoint", report.existing_endpoints), ("set_endpoint", report.set_endpoints)):
        for value in getattr(args, attr) or []:
            try:
                name, weight = _parse_endpoint_weight(value)
            except ValueError as exc:
                report.add("error", str(exc), value)
            else:
                target.append({"endpoint": name, "weight": weight})

    if report.set_endpoints:
        total = sum(item["weight"] for item in report.set_endpoints)
        if total <= 0:
            report.add("error", "set-endpoints total weight must be greater than zero")
        proposed_names = {item["endpoint"] for item in report.set_endpoints}
        existing_names = {item["endpoint"] for item in report.existing_endpoints}
        omitted = sorted(existing_names - proposed_names)
        if omitted and not args.ack_complete_set:
            report.add(
                "error",
                "set-endpoints replaces the complete ingress endpoint list; omitted existing endpoints would be removed. Rerun with --ack-complete-set only after explicit user confirmation.",
                ", ".join(omitted),
            )
        for item in report.set_endpoints:
            percentage = (item["weight"] / total * 100.0) if total else 0.0
            item["traffic_percent"] = round(percentage, 3)

    if args.token:
        report.add("warning", f"{len(args.token)} token argument(s) provided; values are intentionally not printed")
    if args.public:
        report.add("warning", "public endpoint access should be an explicit user decision")
    if args.upload_path:
        report.add("warning", "upload/download paths can reveal data names; confirm before sharing logs", args.upload_path)
    return report


def as_jsonable(report: Report) -> dict:
    return {
        "ok": report.ok,
        "mounts": report.mounts,
        "env": report.env,
        "secrets": report.secrets,
        "ip_allowlist": report.ip_allowlist,
        "tokens": report.tokens,
        "existing_endpoints": report.existing_endpoints,
        "set_endpoints": report.set_endpoints,
        "findings": [finding.__dict__ for finding in report.findings],
    }


def print_text(report: Report) -> None:
    print("LeptonAI local preflight")
    print(f"status: {'ok' if report.ok else 'errors'}")
    if report.mounts:
        print("mounts:")
        for item in report.mounts:
            print(f"  - {item['source']} -> {item['mount_path']} via {item['volume']}")
    if report.env:
        print("env vars:")
        for item in report.env:
            print(f"  - {item['name']}=<redacted> ({item['value_length']} chars)")
    if report.secrets:
        print("secret refs:")
        for item in report.secrets:
            print(f"  - {item['env_name']} from secret {item['secret_name']}")
    if report.ip_allowlist:
        print("ip allowlist: " + ", ".join(report.ip_allowlist))
    if report.tokens:
        print(f"tokens: {report.tokens} provided, values redacted")
    if report.set_endpoints:
        print("set-endpoints distribution:")
        for item in report.set_endpoints:
            print(f"  - {item['endpoint']}: weight={item['weight']} traffic≈{item.get('traffic_percent', 0)}%")
    if report.findings:
        print("findings:")
        for item in report.findings:
            suffix = f" [{item.item}]" if item.item else ""
            print(f"  - {item.level}: {item.message}{suffix}")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate LeptonAI storage/mount/env/secret/ingress inputs locally.")
    parser.add_argument("--mount", action="append", help="Mount string FROM_PATH:MOUNT_PATH:VOLUME. May be repeated.")
    parser.add_argument("--env", action="append", help="Environment variable NAME=VALUE. May be repeated.")
    parser.add_argument("--secret", action="append", help="Secret env ref NAME=SECRET_NAME or NAME. May be repeated.")
    parser.add_argument("--public", action="store_true", help="Lint endpoint public access mode.")
    parser.add_argument("--ip-whitelist", action="append", help="IP address/CIDR or comma-separated list. May be repeated.")
    parser.add_argument("--token", action="append", help="Access token placeholder/value; count is reported but values are redacted.")
    parser.add_argument("--existing-endpoint", action="append", help="Existing ingress endpoint as ENDPOINT:WEIGHT. May be repeated.")
    parser.add_argument("--set-endpoint", action="append", help="Proposed complete ingress endpoint as ENDPOINT:WEIGHT. May be repeated.")
    parser.add_argument("--ack-complete-set", action="store_true", help="Acknowledge that omitted existing endpoints should be removed by set-endpoints.")
    parser.add_argument("--upload-path", help="Optional local/remote path to flag as sensitive in transfer plans.")
    parser.add_argument("--json", action="store_true", help="Print sanitized JSON output.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    report = build_report(args)
    if args.json:
        print(json.dumps(as_jsonable(report), indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
