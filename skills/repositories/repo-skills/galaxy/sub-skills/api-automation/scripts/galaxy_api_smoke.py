#!/usr/bin/env python3
"""Safe dry-run-first Galaxy API smoke planner.

The script prints a redacted plan by default. It only contacts a Galaxy server
when --execute, --url, and --api-key/--api-key-env are supplied together.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

TERMINAL_OK_STATES = {"ok", "success", "scheduled"}
TERMINAL_BAD_STATES = {"error", "failed", "cancelled", "deleted"}


@dataclass
class RequestPlan:
    method: str
    path: str
    description: str
    body: dict[str, Any] | None = None


def normalize_base_url(url: str) -> str:
    trimmed = url.strip().rstrip("/")
    if trimmed.endswith("/api"):
        trimmed = trimmed[:-4]
    return trimmed


def redacted(value: str | None) -> str:
    if not value:
        return "<missing>"
    if len(value) <= 8:
        return "<redacted>"
    return f"{value[:4]}...{value[-4:]}"


def load_api_key(args: argparse.Namespace) -> str | None:
    if args.api_key:
        return args.api_key
    if args.api_key_env:
        return os.environ.get(args.api_key_env)
    return None


def api_url(base_url: str, path: str) -> str:
    path = path.lstrip("/")
    return f"{normalize_base_url(base_url)}/{path}"


def request_json(base_url: str, api_key: str | None, plan: RequestPlan, timeout: float) -> tuple[int, Any]:
    url = api_url(base_url, plan.path)
    data = None
    headers = {"Accept": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    if plan.body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(plan.body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=plan.method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
            return response.status, json.loads(payload) if payload else None
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", "replace")[:4096]
        try:
            parsed: Any = json.loads(payload)
        except json.JSONDecodeError:
            parsed = payload
        return exc.code, parsed


def build_plan(args: argparse.Namespace) -> list[RequestPlan]:
    plans = [
        RequestPlan("GET", "api/version", "Confirm Galaxy API route prefix and server availability."),
        RequestPlan("GET", "api/whoami", "Confirm the API key maps to the expected user before writes."),
    ]
    if args.create_history or args.workflow_id:
        plans.append(
            RequestPlan(
                "POST",
                "api/histories",
                "Create a disposable history for smoke objects.",
                {"name": args.history_name},
            )
        )
    if args.workflow_path:
        plans.append(
            RequestPlan(
                "POST",
                "api/workflows",
                "Import a workflow artifact; confirm source mode against OpenAPI before production use.",
                {"workflow": {"src": "from_path", "path": "<workflow-artifact>"}, "add_to_menu": False},
            )
        )
    if args.workflow_id:
        ds_map = parse_ds_map(args.dataset_map)
        plans.append(
            RequestPlan(
                "POST",
                f"api/workflows/{urllib.parse.quote(args.workflow_id, safe='')}/invocations",
                "Invoke a workflow with explicit input mappings, then poll invocation/jobs/outputs.",
                {
                    "history": "hist_id=<created-or-supplied-history-id>",
                    "inputs": {"<input-name-or-step-id>": {"src": "hda", "id": "<dataset-id>"}},
                    "inputs_by": "name",
                    "ds_map": ds_map or {"<legacy-step-id>": {"src": "hda", "id": "<dataset-id>"}},
                },
            )
        )
    return plans


def parse_ds_map(values: list[str]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for value in values:
        try:
            step, src, dataset_id = value.split("=", 2)
        except ValueError:
            raise SystemExit(f"Invalid --dataset-map {value!r}; expected STEP=SRC=ID, e.g. 0=hda=encoded_id")
        if src not in {"hda", "hdca", "ldda"}:
            raise SystemExit(f"Invalid dataset source {src!r}; expected hda, hdca, or ldda")
        result[step] = {"src": src, "id": dataset_id}
    return result


def print_plan(args: argparse.Namespace, plans: list[RequestPlan], api_key: str | None) -> None:
    print("Galaxy API smoke plan")
    print("=====================")
    print(f"Base URL: {normalize_base_url(args.url) if args.url else '<not supplied>'}")
    print(f"API key: {redacted(api_key)}")
    print(f"Mode: {'EXECUTE' if args.execute else 'dry-run'}")
    print("")
    for index, plan in enumerate(plans, 1):
        print(f"{index}. {plan.method} /{plan.path}")
        print(f"   Purpose: {plan.description}")
        if plan.body is not None:
            print("   Body shape:")
            print(indent(json.dumps(plan.body, indent=2, sort_keys=True), "     "))
    print("")
    print("Safety notes:")
    print("- This script never executes writes unless --execute is present.")
    print("- It sends API keys as x-api-key headers and never prints the full key.")
    print("- Confirm non-local URLs before creating histories, importing workflows, or invoking jobs.")


def indent(text: str, prefix: str) -> str:
    return "\n".join(prefix + line for line in text.splitlines())


def execute_probe(args: argparse.Namespace, plans: list[RequestPlan], api_key: str) -> int:
    write_methods = {"POST", "PUT", "PATCH", "DELETE"}
    if not args.allow_writes:
        plans = [plan for plan in plans if plan.method not in write_methods]
        print("Executing read-only probes only. Add --allow-writes for planned write calls.")
    exit_code = 0
    for plan in plans:
        print(f"\n{plan.method} /{plan.path} - {plan.description}")
        status, payload = request_json(args.url, api_key, plan, args.timeout)
        print(f"Status: {status}")
        print("Response:")
        print(indent(redact_json(payload), "  "))
        if status >= 400:
            exit_code = 1
        if args.sleep and plan is not plans[-1]:
            time.sleep(args.sleep)
    return exit_code


def redact_json(value: Any) -> str:
    def scrub(obj: Any) -> Any:
        if isinstance(obj, dict):
            result = {}
            for key, inner in obj.items():
                if key.lower() in {"key", "api_key", "token", "password", "secret"}:
                    result[key] = "<redacted>"
                else:
                    result[key] = scrub(inner)
            return result
        if isinstance(obj, list):
            return [scrub(item) for item in obj]
        return obj

    if isinstance(value, str):
        return value
    return json.dumps(scrub(value), indent=2, sort_keys=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan or run safe Galaxy API smoke checks. Defaults to dry-run output.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--url", help="Galaxy base URL, with or without trailing /api.")
    key_group = parser.add_mutually_exclusive_group()
    key_group.add_argument("--api-key", help="Galaxy API key. Prefer --api-key-env to avoid shell history leakage.")
    key_group.add_argument("--api-key-env", help="Environment variable containing the Galaxy API key.")
    parser.add_argument("--execute", action="store_true", help="Contact the server. Requires --url and an API key.")
    parser.add_argument("--allow-writes", action="store_true", help="When executing, allow planned POST/PUT/PATCH/DELETE calls.")
    parser.add_argument("--create-history", action="store_true", help="Include a disposable history creation step in the plan.")
    parser.add_argument("--history-name", default="Galaxy API smoke", help="Name for a disposable history creation step.")
    parser.add_argument("--workflow-path", help="Workflow artifact path for planning an import. Not read by this script.")
    parser.add_argument("--workflow-id", help="Stored workflow ID for planning an invocation.")
    parser.add_argument(
        "--dataset-map",
        action="append",
        default=[],
        metavar="STEP=SRC=ID",
        help="Workflow input mapping, e.g. 0=hda=encoded_dataset_id. May be repeated.",
    )
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout in seconds for each executed request.")
    parser.add_argument("--sleep", type=float, default=0.0, help="Optional sleep between executed requests.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    api_key = load_api_key(args)
    plans = build_plan(args)
    print_plan(args, plans, api_key)
    if not args.execute:
        return 0
    if not args.url:
        parser.error("--execute requires --url")
    if not api_key:
        parser.error("--execute requires --api-key or --api-key-env")
    return execute_probe(args, plans, api_key)


if __name__ == "__main__":
    sys.exit(main())
