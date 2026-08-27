#!/usr/bin/env python3
"""Check BentoML observability/operations config fragments locally.

The script accepts JSON or YAML and performs static checks for common BentoML
logging, metrics, monitoring, tracing, resource, traffic, and scaling mistakes.
It does not import BentoML, contact BentoCloud, or connect to collectors.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import yaml  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional dependency path
    yaml = None

VALID_TRACING_EXPORTERS = {"zipkin", "jaeger", "otlp"}
VALID_OTLP_PROTOCOLS = {"http", "grpc"}
VALID_OTLP_COMPRESSION = {"gzip", "none", "deflate"}
HEALTH_PATHS = {"/metrics", "/healthz", "/livez", "/readyz"}


def load_config(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json" or text.lstrip().startswith(("{", "[")):
        return json.loads(text)
    if yaml is None:
        raise RuntimeError("YAML input requires PyYAML; use JSON or install PyYAML")
    data = yaml.safe_load(text)
    return {} if data is None else data


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def is_positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def add(messages: list[str], level: str, path: str, message: str) -> None:
    messages.append(f"{level}: {path}: {message}")


def validate_url(messages: list[str], path: str, value: Any) -> None:
    if value in (None, ""):
        return
    if not isinstance(value, str):
        add(messages, "ERROR", path, "must be a URL string")
        return
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        add(messages, "WARN", path, "does not look like an absolute URL")


def get_service_configs(config: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(config, dict):
        raise TypeError("top-level config must be a mapping")
    services = config.get("services")
    if isinstance(services, dict):
        return {str(name): value for name, value in services.items() if isinstance(value, dict)}
    return {"<root>": config}


def check_metrics(messages: list[str], prefix: str, cfg: dict[str, Any]) -> None:
    metrics = cfg.get("metrics")
    if not isinstance(metrics, dict):
        return
    if metrics.get("enabled") is False:
        add(messages, "WARN", f"{prefix}.metrics.enabled", "metrics endpoint is disabled")
    namespace = metrics.get("namespace")
    if namespace is not None and not isinstance(namespace, str):
        add(messages, "ERROR", f"{prefix}.metrics.namespace", "must be a string")
    duration = metrics.get("duration")
    if not isinstance(duration, dict):
        return
    buckets = duration.get("buckets")
    exponential = [duration.get("min"), duration.get("max"), duration.get("factor")]
    if buckets is not None and any(value is not None for value in exponential):
        add(messages, "ERROR", f"{prefix}.metrics.duration", "buckets is mutually exclusive with min/max/factor")
    if buckets is not None:
        if not isinstance(buckets, list) or not all(is_positive_number(item) for item in buckets):
            add(messages, "ERROR", f"{prefix}.metrics.duration.buckets", "must be a list of positive numbers")
    for key in ("min", "max"):
        if duration.get(key) is not None and not is_positive_number(duration[key]):
            add(messages, "ERROR", f"{prefix}.metrics.duration.{key}", "must be a positive number")
    if duration.get("factor") is not None:
        factor = duration["factor"]
        if not is_positive_number(factor) or factor <= 1.0:
            add(messages, "ERROR", f"{prefix}.metrics.duration.factor", "must be greater than 1.0")


def check_logging(messages: list[str], prefix: str, cfg: dict[str, Any]) -> None:
    logging_cfg = cfg.get("logging")
    if not isinstance(logging_cfg, dict):
        return
    access = logging_cfg.get("access")
    if not isinstance(access, dict):
        return
    skip_paths = access.get("skip_paths")
    if skip_paths is not None:
        if not isinstance(skip_paths, list) or not all(isinstance(path, str) for path in skip_paths):
            add(messages, "ERROR", f"{prefix}.logging.access.skip_paths", "must be a list of strings")
        else:
            missing = sorted(HEALTH_PATHS.difference(skip_paths))
            if missing:
                add(messages, "INFO", f"{prefix}.logging.access.skip_paths", f"consider skipping noisy paths: {', '.join(missing)}")
    fmt = access.get("format")
    if isinstance(fmt, dict):
        for key in ("trace_id", "span_id"):
            if key in fmt and not isinstance(fmt[key], str):
                add(messages, "ERROR", f"{prefix}.logging.access.format.{key}", "must be a string format such as 032x or 016x")


def check_monitoring(messages: list[str], prefix: str, cfg: dict[str, Any]) -> None:
    monitoring = cfg.get("monitoring")
    if not isinstance(monitoring, dict):
        return
    monitor_type = monitoring.get("type")
    options = monitoring.get("options") if isinstance(monitoring.get("options"), dict) else {}
    if monitoring.get("enabled") is False:
        add(messages, "INFO", f"{prefix}.monitoring.enabled", "bentoml.monitor calls will use a no-op monitor")
    if monitor_type == "otlp":
        validate_url(messages, f"{prefix}.monitoring.options.endpoint", options.get("endpoint"))
        timeout = options.get("timeout")
        if timeout is not None and not is_positive_number(timeout):
            add(messages, "ERROR", f"{prefix}.monitoring.options.timeout", "must be a positive number")
    if monitor_type in (None, "default"):
        log_path = options.get("log_path")
        if log_path is not None and not isinstance(log_path, str):
            add(messages, "ERROR", f"{prefix}.monitoring.options.log_path", "must be a string path")


def check_tracing(messages: list[str], prefix: str, cfg: dict[str, Any]) -> None:
    tracing = cfg.get("tracing")
    if not isinstance(tracing, dict):
        return
    exporter = tracing.get("exporter_type")
    if exporter in (None, ""):
        add(messages, "INFO", f"{prefix}.tracing.exporter_type", "no tracing exporter configured")
        return
    if not isinstance(exporter, str) or exporter.lower() not in VALID_TRACING_EXPORTERS:
        add(messages, "ERROR", f"{prefix}.tracing.exporter_type", "must be one of zipkin, jaeger, otlp")
        return
    sample_rate = tracing.get("sample_rate")
    if sample_rate is None or sample_rate == 0:
        add(messages, "WARN", f"{prefix}.tracing.sample_rate", "no traces will be collected unless effective sample rate is above 0")
    elif not isinstance(sample_rate, (int, float)) or isinstance(sample_rate, bool) or not 0 <= sample_rate <= 1:
        add(messages, "ERROR", f"{prefix}.tracing.sample_rate", "must be between 0 and 1")
    timeout = tracing.get("timeout")
    if timeout is not None and not is_positive_int(timeout):
        add(messages, "ERROR", f"{prefix}.tracing.timeout", "must be a positive integer")
    excluded_urls = tracing.get("excluded_urls")
    if excluded_urls is not None and not isinstance(excluded_urls, (str, list)):
        add(messages, "ERROR", f"{prefix}.tracing.excluded_urls", "must be a string or list of strings")
    if exporter.lower() == "zipkin":
        validate_url(messages, f"{prefix}.tracing.zipkin.endpoint", (tracing.get("zipkin") or {}).get("endpoint"))
    if exporter.lower() == "jaeger":
        jaeger = tracing.get("jaeger") if isinstance(tracing.get("jaeger"), dict) else {}
        protocol = jaeger.get("protocol")
        if protocol is not None and protocol not in {"thrift", "grpc"}:
            add(messages, "ERROR", f"{prefix}.tracing.jaeger.protocol", "must be thrift or grpc")
        validate_url(messages, f"{prefix}.tracing.jaeger.collector_endpoint", jaeger.get("collector_endpoint"))
    if exporter.lower() == "otlp":
        otlp = tracing.get("otlp") if isinstance(tracing.get("otlp"), dict) else {}
        protocol = otlp.get("protocol")
        if protocol is not None and protocol not in VALID_OTLP_PROTOCOLS:
            add(messages, "ERROR", f"{prefix}.tracing.otlp.protocol", "must be http or grpc")
        compression = otlp.get("compression")
        if compression is not None and compression not in VALID_OTLP_COMPRESSION:
            add(messages, "ERROR", f"{prefix}.tracing.otlp.compression", "must be gzip, none, or deflate")
        validate_url(messages, f"{prefix}.tracing.otlp.endpoint", otlp.get("endpoint"))


def check_resources(messages: list[str], prefix: str, cfg: dict[str, Any]) -> None:
    resources = cfg.get("resources")
    if resources is None:
        return
    if not isinstance(resources, dict):
        add(messages, "ERROR", f"{prefix}.resources", "must be a mapping or null")
        return
    gpu = resources.get("gpu")
    if gpu is not None and not is_positive_number(gpu):
        add(messages, "ERROR", f"{prefix}.resources.gpu", "must be a positive number")
    for key in ("cpu", "memory", "gpu_type", "tpu_type"):
        if key in resources and resources[key] is not None and not isinstance(resources[key], (str, int, float)):
            add(messages, "ERROR", f"{prefix}.resources.{key}", "must be a scalar value")
    if gpu is not None and resources.get("gpu_type") is None:
        add(messages, "INFO", f"{prefix}.resources.gpu_type", "consider setting a BentoCloud GPU type or instance type for predictable scheduling")


def check_workers_and_traffic(messages: list[str], prefix: str, cfg: dict[str, Any]) -> None:
    workers = cfg.get("workers")
    if workers is not None and workers != "cpu_count" and not is_positive_int(workers):
        add(messages, "ERROR", f"{prefix}.workers", "must be a positive integer or cpu_count")
    traffic = cfg.get("traffic")
    if not isinstance(traffic, dict):
        return
    for key in ("timeout",):
        if traffic.get(key) is not None and not is_positive_number(traffic[key]):
            add(messages, "ERROR", f"{prefix}.traffic.{key}", "must be a positive number")
    for key in ("max_concurrency", "concurrency"):
        if traffic.get(key) is not None and not is_positive_int(traffic[key]):
            add(messages, "ERROR", f"{prefix}.traffic.{key}", "must be a positive integer")
    if traffic.get("external_queue") is True and traffic.get("concurrency") is None:
        add(messages, "ERROR", f"{prefix}.traffic.external_queue", "requires traffic.concurrency for BentoCloud queueing")


def check_scaling(messages: list[str], prefix: str, cfg: dict[str, Any]) -> None:
    scaling = cfg.get("scaling")
    if not isinstance(scaling, dict):
        return
    min_replicas = scaling.get("min_replicas")
    max_replicas = scaling.get("max_replicas")
    for key, value in (("min_replicas", min_replicas), ("max_replicas", max_replicas)):
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
            add(messages, "ERROR", f"{prefix}.scaling.{key}", "must be a non-negative integer")
    if isinstance(min_replicas, int) and isinstance(max_replicas, int) and min_replicas > max_replicas:
        add(messages, "ERROR", f"{prefix}.scaling", "min_replicas cannot exceed max_replicas")
    policy = scaling.get("policy")
    if isinstance(policy, dict):
        for key in ("scale_up_stabilization_window", "scale_down_stabilization_window"):
            value = policy.get(key)
            if value is not None and (not isinstance(value, int) or not 0 <= value <= 3600):
                add(messages, "ERROR", f"{prefix}.scaling.policy.{key}", "must be an integer from 0 to 3600")


def run_checks(config: Any) -> list[str]:
    messages: list[str] = []
    for name, service_cfg in get_service_configs(config).items():
        prefix = f"services.{name}" if name != "<root>" else "config"
        check_resources(messages, prefix, service_cfg)
        check_workers_and_traffic(messages, prefix, service_cfg)
        check_metrics(messages, prefix, service_cfg)
        check_logging(messages, prefix, service_cfg)
        check_monitoring(messages, prefix, service_cfg)
        check_tracing(messages, prefix, service_cfg)
        check_scaling(messages, prefix, service_cfg)
    return messages


def main() -> int:
    parser = argparse.ArgumentParser(description="Check BentoML observability and operations config shapes")
    parser.add_argument("config", type=Path, help="JSON or YAML config fragment")
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        messages = run_checks(config)
    except Exception as exc:
        print(f"ERROR: failed to read or validate {args.config}: {exc}", file=sys.stderr)
        return 2
    for message in messages:
        print(message)
    errors = [message for message in messages if message.startswith("ERROR:")]
    print(f"Summary: {len(errors)} error(s), {len(messages) - len(errors)} warning/info message(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
