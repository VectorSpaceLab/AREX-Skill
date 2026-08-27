#!/usr/bin/env python3
"""Print SimpleTuner WebUI/API curl skeletons without making network calls."""

from __future__ import annotations

import argparse
import json
import shlex
from collections.abc import Iterable, Sequence

VALID_MODES = {"training", "queue", "both"}


def _normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if not normalized:
        raise ValueError("--base-url must not be empty")
    return normalized


def _shell_join(tokens: Iterable[str]) -> str:
    return shlex.join(list(tokens))


def _api_headers(api_key_placeholder: str | None) -> list[str]:
    if not api_key_placeholder:
        return []
    placeholder = api_key_placeholder.strip()
    if not placeholder:
        return []
    return [f"X-API-Key: {placeholder}"]


def _curl(
    method: str,
    url: str,
    *,
    headers: Sequence[str] = (),
    json_body: object | None = None,
    forms: Sequence[tuple[str, str]] = (),
) -> str:
    tokens = ["curl", "-s"]
    if method != "GET":
        tokens.extend(["-X", method])
    tokens.append(url)
    for header in headers:
        tokens.extend(["-H", header])
    if json_body is not None:
        tokens.extend(["-H", "Content-Type: application/json"])
        tokens.extend(["--data-binary", json.dumps(json_body, sort_keys=True)])
    for name, value in forms:
        tokens.extend(["-F", f"{name}={value}"])
    return _shell_join(tokens)


def _print_section(title: str, lines: Sequence[str]) -> None:
    print()
    print(f"# {title}")
    for line in lines:
        print(line)


def _training_lines(base_url: str, config_name: str, headers: Sequence[str], include_stop: bool) -> list[str]:
    lines = [
        "# Inspect API schema and current state before changing anything.",
        _curl("GET", f"{base_url}/openapi.json", headers=headers),
        _curl("GET", f"{base_url}/api/training/status", headers=headers),
        _curl("GET", f"{base_url}/api/configs/{config_name}", headers=headers),
        "# Activate the intended environment, then validate before launch.",
        _curl("POST", f"{base_url}/api/configs/{config_name}/activate", headers=headers),
        _curl(
            "POST",
            f"{base_url}/api/training/validate",
            headers=headers,
            forms=(("__active_tab__", "model"), ("--num_train_epochs", "0")),
        ),
        "# Launch only after reviewing validation output and runtime cost/hardware impact.",
        _curl(
            "POST",
            f"{base_url}/api/training/start",
            headers=headers,
            forms=(("__active_tab__", "model"), ("--num_train_epochs", "0")),
        ),
        _curl("GET", f"{base_url}/api/training/status", headers=headers),
        _curl("GET", f"{base_url}/api/training/events?since_index=0", headers=headers),
        "# Optional active-job triggers; they fail if no job is active.",
        _curl("POST", f"{base_url}/api/training/validation/run", headers=headers),
        _curl("POST", f"{base_url}/api/training/checkpoint/run", headers=headers),
    ]
    if include_stop:
        lines.extend(
            [
                "# Stop/cancel only with explicit approval from the run owner.",
                _curl("POST", f"{base_url}/api/training/stop", headers=headers),
                _curl(
                    "POST",
                    f"{base_url}/api/training/cancel",
                    headers=headers,
                    forms=(("job_id", "<JOB_ID>"),),
                ),
            ]
        )
    return lines


def _queue_lines(base_url: str, config_name: str, headers: Sequence[str], include_stop: bool) -> list[str]:
    lines = [
        "# Read-only queue and GPU/worker state probes.",
        _curl("GET", f"{base_url}/api/queue/stats", headers=headers),
        _curl("GET", f"{base_url}/api/queue/me", headers=headers),
        _curl("GET", f"{base_url}/api/system/status?include_allocation=true", headers=headers),
        _curl("GET", f"{base_url}/api/admin/workers", headers=headers),
        "# Submit only after reviewing target, queue limits, and GPU/worker availability.",
        _curl(
            "POST",
            f"{base_url}/api/queue/submit",
            headers=headers,
            json_body={"config_name": config_name, "target": "auto", "no_wait": False, "any_gpu": False},
        ),
        _curl("GET", f"{base_url}/api/queue/position/<JOB_ID>", headers=headers),
        "# Admin-only examples; review policy before changing scheduler state.",
        _curl(
            "POST",
            f"{base_url}/api/queue/concurrency",
            headers=headers,
            json_body={"local_gpu_max_concurrent": None, "local_job_max_concurrent": 1},
        ),
        _curl("POST", f"{base_url}/api/queue/process", headers=headers),
    ]
    if include_stop:
        lines.extend(
            [
                "# Cancel only with explicit approval from the job owner/admin.",
                _curl("POST", f"{base_url}/api/queue/<JOB_ID>/cancel", headers=headers),
            ]
        )
    return lines


def build_plan(args: argparse.Namespace) -> str:
    base_url = _normalize_base_url(args.base_url)
    config_name = args.config_name.strip()
    if not config_name:
        raise ValueError("--config-name must not be empty")
    headers = _api_headers(args.api_key_placeholder)

    sections: list[tuple[str, list[str]]] = []
    if args.mode in {"training", "both"}:
        sections.append(("Training API skeleton", _training_lines(base_url, config_name, headers, args.include_stop)))
    if args.mode in {"queue", "both"}:
        sections.append(("Queue and worker API skeleton", _queue_lines(base_url, config_name, headers, args.include_stop)))

    output_lines = [
        "# SimpleTuner API operation plan",
        "# Review placeholders, auth, target server, and operational impact before running these commands.",
        "# This script prints text only and performs no network calls.",
    ]
    for title, lines in sections:
        output_lines.append("")
        output_lines.append(f"# {title}")
        output_lines.extend(lines)
    return "\n".join(output_lines)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print SimpleTuner WebUI/API curl command skeletons without running them.",
        epilog=(
            "Examples:\n"
            "  build_api_training_plan.py --base-url http://localhost:8001 --config-name flux-lora --mode training\n"
            "  build_api_training_plan.py --config-name flux-lora --mode queue --api-key-placeholder st_your_key_here\n"
            "  build_api_training_plan.py --config-name flux-lora --mode both --include-stop"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8001",
        help="Base URL for the SimpleTuner server to print in skeletons.",
    )
    parser.add_argument(
        "--config-name",
        default="my-training-config",
        help="Training environment/config name to print in skeletons.",
    )
    parser.add_argument(
        "--mode",
        choices=sorted(VALID_MODES),
        default="both",
        help="Which skeleton group to print: training, queue, or both.",
    )
    parser.add_argument(
        "--api-key-placeholder",
        default="",
        help="If set, include an X-API-Key header using this placeholder value.",
    )
    parser.add_argument(
        "--include-stop",
        action="store_true",
        help="Include stop/cancel command skeletons that require extra approval before use.",
    )
    return parser


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()
    try:
        print(build_plan(args))
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
