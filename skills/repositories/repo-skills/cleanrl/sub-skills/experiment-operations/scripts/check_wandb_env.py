#!/usr/bin/env python3
"""Check CleanRL operations credentials without printing secret values."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass

GROUPS = {
    "wandb": {
        "required_any": ["WANDB_API_KEY", "WANDB_MODE", "WANDB_DISABLED"],
        "optional": ["WANDB_PROJECT", "WANDB_ENTITY", "WANDB_TAGS", "WANDB_RUN_ID", "WANDB_RESUME"],
    },
    "aws": {
        "required_any": ["AWS_PROFILE", "AWS_ACCESS_KEY_ID"],
        "required_all_if_access_key": ["AWS_SECRET_ACCESS_KEY"],
        "optional": ["AWS_SESSION_TOKEN", "AWS_DEFAULT_REGION", "AWS_REGION", "AWS_BATCH_JOB_QUEUE"],
    },
    "hf": {
        "required_any": ["HF_TOKEN", "HUGGINGFACE_TOKEN", "HUGGING_FACE_HUB_TOKEN"],
        "optional": ["HF_HOME", "HF_HUB_DISABLE_TELEMETRY"],
    },
}

SECRET_PATTERNS = ("KEY", "SECRET", "TOKEN", "PASSWORD")
PLACEHOLDER_RE = re.compile(r"^(x+|<.*>|changeme|change-me|placeholder|dummy|none|null|test|example)$", re.IGNORECASE)


@dataclass(frozen=True)
class VariableStatus:
    name: str
    state: str
    sensitive: bool


def is_sensitive(name: str) -> bool:
    return any(pattern in name.upper() for pattern in SECRET_PATTERNS)


def classify_value(name: str, value: str | None, check_placeholders: bool) -> VariableStatus:
    sensitive = is_sensitive(name)
    if value is None or value == "":
        return VariableStatus(name=name, state="missing", sensitive=sensitive)
    stripped = value.strip()
    if check_placeholders and PLACEHOLDER_RE.match(stripped):
        return VariableStatus(name=name, state="placeholder-like", sensitive=sensitive)
    if name == "WANDB_DISABLED" and stripped.lower() in {"true", "1", "yes"}:
        return VariableStatus(name=name, state="set-disabled", sensitive=False)
    if name == "WANDB_MODE" and stripped.lower() == "offline":
        return VariableStatus(name=name, state="set-offline", sensitive=False)
    return VariableStatus(name=name, state="set-redacted" if sensitive else "set", sensitive=sensitive)


def collect_group(group_name: str, check_placeholders: bool) -> dict:
    spec = GROUPS[group_name]
    names = []
    for key in ("required_any", "required_all_if_access_key", "optional"):
        names.extend(spec.get(key, []))
    statuses = {name: classify_value(name, os.environ.get(name), check_placeholders) for name in dict.fromkeys(names)}

    required_any = spec.get("required_any", [])
    any_ready = any(statuses[name].state.startswith("set") for name in required_any)
    placeholder_required = [name for name in required_any if statuses[name].state == "placeholder-like"]
    missing = [] if any_ready else required_any

    if group_name == "aws" and statuses["AWS_ACCESS_KEY_ID"].state.startswith("set"):
        for name in spec.get("required_all_if_access_key", []):
            if not statuses[name].state.startswith("set"):
                missing.append(name)
            if statuses[name].state == "placeholder-like":
                placeholder_required.append(name)

    ready = not missing and not placeholder_required
    return {
        "group": group_name,
        "ready": ready,
        "missing_requirements": sorted(set(missing)),
        "placeholder_requirements": sorted(set(placeholder_required)),
        "variables": [status.__dict__ for status in statuses.values()],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate W&B/AWS/HF environment readiness without printing secret values.")
    parser.add_argument("--require-wandb", action="store_true", help="Fail if W&B online/offline/disabled state is not explicit.")
    parser.add_argument("--require-aws", action="store_true", help="Fail if AWS credentials/profile requirements are not met.")
    parser.add_argument("--require-hf", action="store_true", help="Fail if Hugging Face token requirements are not met.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--no-placeholder-check", action="store_true", help="Do not flag obvious placeholder values.")
    return parser.parse_args()


def render_text(results: list[dict], required: set[str]) -> str:
    lines = ["CleanRL operations environment check (values are never printed)."]
    for result in results:
        marker = "OK" if result["ready"] else "CHECK"
        requirement = "required" if result["group"] in required else "optional"
        lines.append(f"\n[{marker}] {result['group']} ({requirement})")
        if result["missing_requirements"]:
            lines.append("  missing requirement: " + ", ".join(result["missing_requirements"]))
        if result["placeholder_requirements"]:
            lines.append("  placeholder-like requirement: " + ", ".join(result["placeholder_requirements"]))
        for variable in result["variables"]:
            lines.append(f"  {variable['name']}: {variable['state']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    required = {
        group
        for group, enabled in {
            "wandb": args.require_wandb,
            "aws": args.require_aws,
            "hf": args.require_hf,
        }.items()
        if enabled
    }
    check_placeholders = not args.no_placeholder_check
    results = [collect_group(group, check_placeholders) for group in ("wandb", "aws", "hf")]
    failed_required = [result["group"] for result in results if result["group"] in required and not result["ready"]]

    payload = {"ok": not failed_required, "failed_required_groups": failed_required, "groups": results}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(render_text(results, required), end="")
    return 2 if failed_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
