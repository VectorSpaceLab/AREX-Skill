#!/usr/bin/env python3
"""Generate a safe ClearML HttpRouter plan/snippet without starting a server."""

from __future__ import annotations

import argparse
import json
import re
import textwrap
from typing import Any, Dict
from urllib.parse import urlparse


PATH_RE = re.compile(r"^/[A-Za-z0-9_./{}:-]*$")


def validate_source_path(value: str) -> str:
    if not value.startswith("/"):
        raise argparse.ArgumentTypeError("source path must start with '/'")
    if not PATH_RE.match(value):
        raise argparse.ArgumentTypeError("source path contains unsupported characters")
    return value.rstrip("/") or "/"


def validate_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise argparse.ArgumentTypeError("target URLs must be absolute http(s) URLs")
    return value.rstrip("/")


def parse_telemetry(value: str) -> Any:
    lowered = value.strip().lower()
    if lowered in {"false", "off", "no", "0"}:
        return False
    if lowered in {"true", "on", "yes", "1"}:
        return True
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(
            "telemetry must be true, false, or a JSON object"
        ) from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("telemetry JSON must be an object")
    return parsed


def literal(value: Any) -> str:
    return repr(value)


def build_snippet(args: argparse.Namespace, telemetry: Any) -> str:
    callback_block = ""
    callback_args = ""
    if args.callbacks:
        callback_block = '''
import time


def request_callback(request, persistent_state):
    persistent_state["started_at"] = time.time()


def response_callback(response, request, persistent_state):
    started_at = persistent_state.pop("started_at", None)
    if started_at is not None:
        print("proxy latency", time.time() - started_at)


def error_callback(request, error, persistent_state):
    persistent_state["last_error"] = repr(error)
'''
        callback_args = """
    request_callback=request_callback,
    response_callback=response_callback,
    error_callback=error_callback,"""

    default_target_line = ""
    if args.default_target:
        default_target_line = f"\n    default_target={literal(args.default_target)},"

    deploy_block = ""
    if args.deploy:
        deploy_block = f'''
endpoint = router.deploy(
    wait={args.wait!r},
    wait_interval_seconds={args.wait_interval_seconds!r},
    wait_timeout_seconds={args.wait_timeout_seconds!r},
    static_route={literal(args.static_route)},
)
print(endpoint)
'''
    else:
        deploy_block = '''
# Live step, intentionally omitted from this plan:
# endpoint = router.deploy(wait=True)
'''

    snippet = f'''
from clearml import Task
{callback_block}
task = Task.init(project_name={literal(args.project)}, task_name={literal(args.task_name)})
router = task.get_http_router()
router.set_local_proxy_parameters(
    incoming_port={args.incoming_port!r},{default_target_line}
    log_level={literal(args.log_level)},
    access_log={args.access_log!r},
    enable_streaming={args.enable_streaming!r},
)
router.create_local_route(
    source={literal(args.source)},
    target={literal(args.target)},{callback_args}
    endpoint_telemetry={literal(telemetry)},
)
{deploy_block}
'''
    return textwrap.dedent(snippet).strip() + "\n"


def build_summary(args: argparse.Namespace, telemetry: Any) -> Dict[str, Any]:
    return {
        "project": args.project,
        "task_name": args.task_name,
        "incoming_port": args.incoming_port,
        "source": args.source,
        "target": args.target,
        "default_target": args.default_target,
        "callbacks": args.callbacks,
        "endpoint_telemetry": telemetry,
        "deploy_included": args.deploy,
        "safe_behavior": [
            "does not import ClearML",
            "does not start uvicorn or FastAPI",
            "does not bind ports",
            "does not contact a ClearML server",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print a ClearML HttpRouter route plan/snippet without running it."
    )
    parser.add_argument("--project", default="Serving", help="Task project name for the snippet")
    parser.add_argument("--task-name", default="HTTP proxy", help="Task name for the snippet")
    parser.add_argument("--incoming-port", type=int, default=9000, help="Local proxy listening port")
    parser.add_argument("--source", type=validate_source_path, required=True, help="Proxy source path, e.g. /v1/predict")
    parser.add_argument("--target", type=validate_url, required=True, help="Upstream target URL")
    parser.add_argument("--default-target", type=validate_url, help="Optional default target for unmatched paths")
    parser.add_argument("--telemetry", type=parse_telemetry, default="false", help="true, false, or a JSON telemetry object")
    parser.add_argument("--callbacks", action="store_true", help="Include request/response/error callback skeletons")
    parser.add_argument("--deploy", action="store_true", help="Include the live deploy call in the printed snippet")
    parser.add_argument("--wait", action="store_true", help="Use wait=True when --deploy is set")
    parser.add_argument("--wait-interval-seconds", type=float, default=3.0, help="Endpoint wait poll interval")
    parser.add_argument("--wait-timeout-seconds", type=float, default=90.0, help="Endpoint wait timeout")
    parser.add_argument("--static-route", help="Optional server-side static route name for deploy")
    parser.add_argument("--log-level", default="warning", help="Uvicorn log level for the snippet")
    parser.add_argument("--access-log", action=argparse.BooleanOptionalAction, default=False, help="Enable uvicorn access log")
    parser.add_argument("--enable-streaming", action=argparse.BooleanOptionalAction, default=True, help="Enable streaming proxy responses")
    parser.add_argument("--json", action="store_true", help="Print JSON with summary and snippet")
    args = parser.parse_args()

    if not 1 <= args.incoming_port <= 65535:
        parser.error("--incoming-port must be between 1 and 65535")
    if args.static_route and not args.deploy:
        parser.error("--static-route only applies when --deploy is set")
    if args.wait and not args.deploy:
        parser.error("--wait only applies when --deploy is set")

    telemetry = args.telemetry
    snippet = build_snippet(args, telemetry)
    summary = build_summary(args, telemetry)

    if args.json:
        print(json.dumps({**summary, "snippet": snippet}, indent=2, sort_keys=True))
    else:
        print("ClearML HttpRouter plan")
        for key, value in summary.items():
            if key == "safe_behavior":
                continue
            print(f"- {key}: {value!r}")
        print("- safe behavior: " + "; ".join(summary["safe_behavior"]))
        print("\nSnippet:\n")
        print(snippet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
