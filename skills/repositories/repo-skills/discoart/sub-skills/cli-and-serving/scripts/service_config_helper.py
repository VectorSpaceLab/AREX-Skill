#!/usr/bin/env python3
"""Print a minimal DiscoArt Jina Flow config without launching a server.

This helper is intentionally side-effect free: it imports only the Python
standard library, writes YAML to stdout, and never opens ports, starts Jina,
downloads models, or touches the filesystem unless the caller redirects output.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, TextIO


def positive_int(value: str) -> int:
    """Argparse type for positive integers."""
    try:
        parsed = int(value)
    except ValueError as exc:  # pragma: no cover - argparse displays message
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def yaml_scalar(value: Any) -> str:
    """Render a small YAML scalar safely for this generated config."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    # Quote strings to keep env values such as RR0:2, 1, and disabled unambiguous.
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a minimal Jina Flow YAML for `python -m discoart serve`. "
            "The helper does not launch Jina or DiscoArt."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--protocol",
        choices=("http", "grpc", "websocket"),
        default="http",
        help="Jina gateway protocol to place under flow.with.protocol.",
    )
    parser.add_argument(
        "--port",
        type=positive_int,
        default=51001,
        help="Request port for the Jina gateway.",
    )
    parser.add_argument(
        "--monitoring-port",
        type=positive_int,
        default=51002,
        help="Prometheus/monitoring port to include when monitoring is enabled.",
    )
    parser.add_argument(
        "--no-monitoring",
        action="store_false",
        dest="monitoring",
        default=True,
        help="Set flow.with.monitoring to false and omit port_monitoring.",
    )
    parser.add_argument(
        "--no-cors",
        action="store_false",
        dest="cors",
        default=True,
        help="Set flow.with.cors to false.",
    )
    parser.add_argument(
        "--floating",
        action="store_true",
        help=(
            "Set the DiscoArt executor floating flag so /create returns immediately. "
            "Use only with external rate limiting."
        ),
    )
    parser.add_argument(
        "--replicas",
        type=positive_int,
        default=1,
        help="Number of DiscoArt executor replicas.",
    )
    parser.add_argument(
        "--cuda-visible-devices",
        default="0",
        help=(
            "Value for the DiscoArt executor CUDA_VISIBLE_DEVICES env var. "
            "Examples: 0, 0,1, RR0:2, RR0:3."
        ),
    )
    parser.add_argument(
        "--jina-log-level",
        default="debug",
        help="Value for JINA_LOG_LEVEL in the flow-level env block.",
    )
    parser.add_argument(
        "--wandb-mode",
        default="disabled",
        help="Value for WANDB_MODE in the flow-level env block.",
    )
    return parser


def emit_config(args: argparse.Namespace, stream: TextIO = sys.stdout) -> None:
    """Emit a DiscoArt service Flow YAML to stream."""
    lines = [
        "jtype: Flow",
        "with:",
        f"  protocol: {yaml_scalar(args.protocol)}",
        f"  monitoring: {yaml_scalar(args.monitoring)}",
        f"  cors: {yaml_scalar(args.cors)}",
        f"  port: {yaml_scalar(args.port)}",
    ]
    if args.monitoring:
        lines.append(f"  port_monitoring: {yaml_scalar(args.monitoring_port)}")
    lines.extend(
        [
            "  env:",
            f"    JINA_LOG_LEVEL: {yaml_scalar(args.jina_log_level)}",
            "    DISCOART_DISABLE_IPYTHON: \"1\"",
            "    DISCOART_DISABLE_RESULT_SUMMARY: \"1\"",
            f"    WANDB_MODE: {yaml_scalar(args.wandb_mode)}",
            "executors:",
            "  - name: discoart",
            "    uses: DiscoArtExecutor",
            "    env:",
            f"      CUDA_VISIBLE_DEVICES: {yaml_scalar(args.cuda_visible_devices)}",
            f"    replicas: {yaml_scalar(args.replicas)}",
            f"    floating: {yaml_scalar(args.floating)}",
            "  - name: poller",
            "    uses: ResultPoller",
        ]
    )
    stream.write("\n".join(lines))
    stream.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    emit_config(args)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
