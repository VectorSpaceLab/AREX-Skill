#!/usr/bin/env python3
"""Emit a BentoML resource, telemetry, scaling, and gateway plan template.

This is a local planning helper only. It does not call BentoCloud, inspect GPUs,
or contact external observability systems.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    plan: dict[str, Any] = {
        "service": {
            "name": args.service_name,
            "target_environment": args.target,
            "assumptions": [
                "Separate local runtime controls from BentoCloud scheduling controls.",
                "Do not put credentials or private endpoints in source-controlled service code.",
            ],
        },
        "local_runtime": {
            "workers": args.workers,
            "traffic": {
                "timeout_seconds": args.timeout,
                "max_concurrency": args.max_concurrency,
            },
            "health_checks": ["/livez", "/readyz", "/healthz"],
            "metrics_endpoint": "/metrics",
        },
        "resources": {
            "cpu": args.cpu,
            "memory": args.memory,
            "gpu_count": args.gpu,
            "gpu_type": args.gpu_type,
            "gpu_runtime_notes": [
                "BentoCloud scheduling uses resources.gpu and resources.gpu_type.",
                "Local/container GPU use also requires runtime GPU exposure and framework CUDA packages.",
                "Map BentoML worker_index to zero-based CUDA IDs carefully for multi-worker GPU services.",
            ],
        },
        "observability": {
            "logging": {
                "access_enabled": True,
                "skip_paths": ["/metrics", "/healthz", "/livez", "/readyz"],
                "library_logger": "bentoml",
            },
            "metrics": {
                "enabled": True,
                "namespace": args.metrics_namespace,
                "custom_metric_checks": [
                    "Use bentoml.metrics or defer prometheus_client access in multi-worker services.",
                    "Generate at least one request before expecting request counters.",
                ],
            },
            "monitoring": {
                "type": args.monitoring_type,
                "local_log_path": "monitoring",
                "external_requirements": "OTLP/plugins/collectors require deployment-specific infrastructure and credentials.",
            },
            "tracing": {
                "exporter_type": args.tracing_exporter,
                "sample_rate_for_debug": 1.0 if args.tracing_exporter else None,
                "dependency_note": "Install the matching bentoml tracing extra in the runtime image when tracing is enabled.",
            },
        },
        "bentocloud_scaling": {
            "traffic_concurrency": args.cloud_concurrency,
            "external_queue": args.external_queue,
            "min_replicas": args.min_replicas,
            "max_replicas": args.max_replicas,
            "policy": {
                "scale_up_stabilization_window": args.scale_up_window,
                "scale_down_stabilization_window": args.scale_down_window,
            },
            "notes": [
                "Set traffic.concurrency to drive BentoCloud autoscaling for GPU/LLM workloads.",
                "external_queue requires traffic.concurrency and can increase latency.",
                "Scale-to-zero uses min_replicas=0 and may add cold-start delay.",
            ],
        },
        "gateway": {
            "needed": args.gateway,
            "protocol": args.gateway_protocol if args.gateway else None,
            "load_balancing_strategy": args.gateway_strategy if args.gateway else None,
            "planning_checks": [
                "Confirm direct upstream deployment health before debugging gateway routing.",
                "Confirm request model/protocol fields match upstream capabilities.",
                "Gateways require BentoCloud account access and are not managed by this local script.",
            ] if args.gateway else [],
        },
        "verification_plan": [
            "Run isolated unit tests with heavy models mocked when needed.",
            "Run ASGI/HTTP behavior tests for route status and response shape.",
            "Start a local service and check /livez, /readyz, /healthz, and /metrics.",
            "Generate one request and verify default request metrics and any custom metrics.",
            "If tracing is enabled, confirm exporter dependency, sample rate, endpoint, and environment variables.",
            "Run BentoCloud E2E only with explicit credentials, cost approval, and cleanup logic.",
        ],
    }
    return plan


def emit_markdown(plan: dict[str, Any]) -> str:
    service = plan["service"]
    resources = plan["resources"]
    scaling = plan["bentocloud_scaling"]
    observability = plan["observability"]
    gateway = plan["gateway"]
    lines = [
        f"# BentoML Operations Plan: {service['name']}",
        "",
        f"- Target environment: `{service['target_environment']}`",
        f"- Workers: `{plan['local_runtime']['workers']}`",
        f"- Timeout seconds: `{plan['local_runtime']['traffic']['timeout_seconds']}`",
        f"- Local max concurrency: `{plan['local_runtime']['traffic']['max_concurrency']}`",
        "",
        "## Resources",
        "",
        f"- CPU: `{resources['cpu']}`",
        f"- Memory: `{resources['memory']}`",
        f"- GPU count: `{resources['gpu_count']}`",
        f"- GPU type: `{resources['gpu_type']}`",
        "",
        "## Observability",
        "",
        f"- Metrics namespace: `{observability['metrics']['namespace']}`",
        f"- Monitoring type: `{observability['monitoring']['type']}`",
        f"- Tracing exporter: `{observability['tracing']['exporter_type']}`",
        "- Health endpoints: `/livez`, `/readyz`, `/healthz`",
        "- Metrics endpoint: `/metrics`",
        "",
        "## BentoCloud Scaling",
        "",
        f"- Concurrency target: `{scaling['traffic_concurrency']}`",
        f"- External queue: `{scaling['external_queue']}`",
        f"- Replica range: `{scaling['min_replicas']}` to `{scaling['max_replicas']}`",
        f"- Scale-up window: `{scaling['policy']['scale_up_stabilization_window']}` seconds",
        f"- Scale-down window: `{scaling['policy']['scale_down_stabilization_window']}` seconds",
        "",
        "## Gateway",
        "",
        f"- Needed: `{gateway['needed']}`",
        f"- Protocol: `{gateway['protocol']}`",
        f"- Strategy: `{gateway['load_balancing_strategy']}`",
        "",
        "## Verification Plan",
        "",
    ]
    lines.extend(f"- {item}" for item in plan["verification_plan"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit a BentoML operations planning template")
    parser.add_argument("--service-name", default="MyService")
    parser.add_argument("--target", choices=["local", "container", "bentocloud", "gateway"], default="bentocloud")
    parser.add_argument("--workers", default="1")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--max-concurrency", type=int, default=50)
    parser.add_argument("--cpu", default="2")
    parser.add_argument("--memory", default="4Gi")
    parser.add_argument("--gpu", type=float, default=0)
    parser.add_argument("--gpu-type", default=None)
    parser.add_argument("--metrics-namespace", default="bentoml_service")
    parser.add_argument("--monitoring-type", default="default", choices=["default", "otlp", "plugin"])
    parser.add_argument("--tracing-exporter", default=None, choices=[None, "zipkin", "jaeger", "otlp"])
    parser.add_argument("--cloud-concurrency", type=int, default=32)
    parser.add_argument("--external-queue", action="store_true")
    parser.add_argument("--min-replicas", type=int, default=1)
    parser.add_argument("--max-replicas", type=int, default=4)
    parser.add_argument("--scale-up-window", type=int, default=180)
    parser.add_argument("--scale-down-window", type=int, default=600)
    parser.add_argument("--gateway", action="store_true")
    parser.add_argument("--gateway-protocol", default="OpenAI Chat Completions")
    parser.add_argument("--gateway-strategy", default="capacity-based round robin")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.min_replicas < 0 or args.max_replicas < 0 or args.min_replicas > args.max_replicas:
        print("replica bounds must be non-negative and min must not exceed max", file=sys.stderr)
        return 2
    if not 0 <= args.scale_up_window <= 3600 or not 0 <= args.scale_down_window <= 3600:
        print("stabilization windows must be between 0 and 3600 seconds", file=sys.stderr)
        return 2

    plan = build_plan(args)
    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(emit_markdown(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
