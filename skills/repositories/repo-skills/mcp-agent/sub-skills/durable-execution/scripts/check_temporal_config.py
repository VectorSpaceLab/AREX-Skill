#!/usr/bin/env python3
"""Statically validate mcp-agent Temporal configuration.

The default checks do not connect to Temporal, start workers, or call providers.
Use --check-imports to verify the optional Temporal Python dependency is
installed in the current interpreter.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

SENSITIVE_NAMES = {"api_key", "token", "authorization", "secret", "password"}
VALID_EXECUTION_ENGINES = {"asyncio", "temporal"}
VALID_ID_REUSE_POLICIES = {
    "allow_duplicate",
    "allow_duplicate_failed_only",
    "reject_duplicate",
    "terminate_if_running",
}
VALID_RETRY_KEYS = {
    "maximum_attempts",
    "initial_interval",
    "backoff_coefficient",
    "maximum_interval",
    "non_retryable_error_types",
}
PROVIDER_NON_RETRYABLE_HINTS = {
    "AuthenticationError",
    "PermissionDeniedError",
    "BadRequestError",
    "NotFoundError",
    "UnprocessableEntityError",
    "InvalidArgument",
    "FailedPrecondition",
    "Unauthenticated",
    "HttpResponseError",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Statically validate mcp-agent Temporal configuration."
    )
    parser.add_argument("config", help="Path to mcp_agent.config.yaml or JSON config.")
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Import mcp_agent Temporal modules and temporalio without connecting to a server.",
    )
    parser.add_argument(
        "--expect-task-queue",
        help="Require temporal.task_queue to match this value.",
    )
    parser.add_argument(
        "--expect-namespace",
        help="Require temporal.namespace to match this value.",
    )
    parser.add_argument(
        "--require-retry-policy",
        action="store_true",
        help="Warn when no workflow_task_retry_policies are configured.",
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Return non-zero when warnings are present.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def strip_inline_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote == '"':
            escaped = True
            continue
        if char in {'"', "'"}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
            continue
        if char == "#" and quote is None and (index == 0 or line[index - 1].isspace()):
            return line[:index].rstrip()
    return line.rstrip()


def split_inline_list(value: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    for char in value:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\" and quote == '"':
            current.append(char)
            escaped = True
            continue
        if char in {'"', "'"}:
            current.append(char)
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
            continue
        if char == "," and quote is None:
            items.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    tail = "".join(current).strip()
    if tail:
        items.append(tail)
    return items


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(item) for item in split_inline_list(inner)]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", "~"}:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_simple_yaml(text: str) -> dict[str, Any]:
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("\t"):
            raise ValueError("tab indentation is not supported by the fallback YAML parser")
        stripped = strip_inline_comment(raw)
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        lines.append((indent, stripped.strip()))

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(lines):
            return {}, index
        is_list = lines[index][1].startswith("- ")
        if is_list:
            values: list[Any] = []
            while index < len(lines):
                current_indent, content = lines[index]
                if current_indent < indent or current_indent != indent or not content.startswith("- "):
                    break
                item = content[2:].strip()
                index += 1
                if item:
                    values.append(parse_scalar(item))
                elif index < len(lines) and lines[index][0] > current_indent:
                    child, index = parse_block(index, lines[index][0])
                    values.append(child)
                else:
                    values.append(None)
            return values, index

        values: dict[str, Any] = {}
        while index < len(lines):
            current_indent, content = lines[index]
            if current_indent < indent or current_indent != indent or content.startswith("- "):
                break
            if ":" not in content:
                raise ValueError(f"unsupported YAML line: {content!r}")
            key, raw_value = content.split(":", 1)
            key = key.strip().strip('"').strip("'")
            raw_value = raw_value.strip()
            index += 1
            if raw_value:
                values[key] = parse_scalar(raw_value)
            elif index < len(lines) and lines[index][0] > current_indent:
                child, index = parse_block(index, lines[index][0])
                values[key] = child
            else:
                values[key] = {}
        return values, index

    parsed, final_index = parse_block(0, lines[0][0] if lines else 0)
    if final_index != len(lines):
        raise ValueError("unsupported YAML indentation near line " + str(final_index + 1))
    if not isinstance(parsed, dict):
        raise ValueError("Top-level config must be a mapping/object.")
    return parsed


def load_document(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if path.suffix.lower() == ".json" or stripped.startswith(("{", "[")):
        data = json.loads(text)
    else:
        try:
            import yaml  # type: ignore
        except Exception:
            data = parse_simple_yaml(text)
        else:
            data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError("Top-level config must be a mapping/object.")
    return data


def issue(severity: str, where: str, message: str) -> dict[str, str]:
    return {"severity": severity, "where": where, "message": message}


def is_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    return (
        stripped.startswith("${")
        or stripped.startswith("!secret")
        or stripped.startswith("!user_secret")
        or stripped.startswith("!developer_secret")
        or stripped.startswith("<")
        or "${" in stripped
    )


def looks_sensitive(key: str) -> bool:
    lower_key = key.lower()
    return any(marker in lower_key for marker in SENSITIVE_NAMES)


def validate_sensitive_literals(value: Any, where: str, issues: list[dict[str, str]]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_where = f"{where}.{key}" if where else str(key)
            if looks_sensitive(str(key)) and isinstance(child, str) and child and not is_placeholder(child):
                issues.append(
                    issue(
                        "warning",
                        child_where,
                        "sensitive value appears literal; prefer environment or secrets placeholders.",
                    )
                )
            validate_sensitive_literals(child, child_where, issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_sensitive_literals(child, f"{where}[{index}]", issues)


def validate_temporal_block(
    config: dict[str, Any],
    *,
    expect_task_queue: str | None,
    expect_namespace: str | None,
    issues: list[dict[str, str]],
) -> None:
    temporal = config.get("temporal")
    if not isinstance(temporal, dict):
        issues.append(issue("error", "temporal", "execution_engine is temporal, so temporal config must be a mapping."))
        return

    host = temporal.get("host")
    if not isinstance(host, str) or not host.strip():
        issues.append(issue("error", "temporal.host", "must be a non-empty string such as 'localhost:7233'."))
    elif "://" in host:
        issues.append(issue("warning", "temporal.host", "TemporalSettings.host is a target host string; omit http:// or https:// unless your client wrapper expects it."))
    elif ":" not in host and not host.startswith("${"):
        issues.append(issue("warning", "temporal.host", "host usually includes a port, for example 'localhost:7233'."))

    namespace = temporal.get("namespace", "default")
    if not isinstance(namespace, str) or not namespace.strip():
        issues.append(issue("error", "temporal.namespace", "must be a non-empty string."))
    elif expect_namespace and namespace != expect_namespace:
        issues.append(issue("error", "temporal.namespace", f"expected {expect_namespace!r}, got {namespace!r}."))

    task_queue = temporal.get("task_queue")
    if not isinstance(task_queue, str) or not task_queue.strip():
        issues.append(issue("error", "temporal.task_queue", "must be a non-empty string matching the worker task queue."))
    elif expect_task_queue and task_queue != expect_task_queue:
        issues.append(issue("error", "temporal.task_queue", f"expected {expect_task_queue!r}, got {task_queue!r}."))

    max_concurrent = temporal.get("max_concurrent_activities")
    if max_concurrent is not None and (not isinstance(max_concurrent, int) or max_concurrent < 1):
        issues.append(issue("error", "temporal.max_concurrent_activities", "must be a positive integer when set."))

    timeout = temporal.get("timeout_seconds")
    if timeout is not None and (not isinstance(timeout, int) or timeout < 1):
        issues.append(issue("error", "temporal.timeout_seconds", "must be a positive integer number of seconds when set."))

    tls = temporal.get("tls")
    if tls is not None and not isinstance(tls, bool):
        issues.append(issue("error", "temporal.tls", "must be true or false when set."))

    id_reuse_policy = temporal.get("id_reuse_policy")
    if id_reuse_policy is not None and id_reuse_policy not in VALID_ID_REUSE_POLICIES:
        issues.append(
            issue(
                "error",
                "temporal.id_reuse_policy",
                f"invalid policy {id_reuse_policy!r}; expected one of {sorted(VALID_ID_REUSE_POLICIES)}.",
            )
        )

    rpc_metadata = temporal.get("rpc_metadata")
    if rpc_metadata is not None and not isinstance(rpc_metadata, dict):
        issues.append(issue("error", "temporal.rpc_metadata", "must be a mapping when set."))

    module_lists = [
        ("workflow_task_modules", config.get("workflow_task_modules")),
        ("temporal.workflow_task_modules", temporal.get("workflow_task_modules")),
    ]
    for where, modules in module_lists:
        if modules is None:
            continue
        if not isinstance(modules, list) or not all(isinstance(item, str) and item for item in modules):
            issues.append(issue("error", where, "must be a list of non-empty import path strings."))


def validate_retry_policies(
    config: dict[str, Any], *, require_retry_policy: bool, issues: list[dict[str, str]]
) -> None:
    policies = config.get("workflow_task_retry_policies")
    if policies is None:
        if require_retry_policy:
            issues.append(issue("warning", "workflow_task_retry_policies", "no retry policies configured."))
        return
    if not isinstance(policies, dict):
        issues.append(issue("error", "workflow_task_retry_policies", "must be a mapping."))
        return

    for name, policy in policies.items():
        where = f"workflow_task_retry_policies.{name}"
        if not isinstance(name, str) or not name:
            issues.append(issue("error", "workflow_task_retry_policies", "policy names must be non-empty strings."))
            continue
        if not isinstance(policy, dict):
            issues.append(issue("error", where, "policy must be a mapping."))
            continue
        unknown = sorted(set(policy) - VALID_RETRY_KEYS)
        if unknown:
            issues.append(issue("error", where, f"unknown retry policy keys: {', '.join(unknown)}."))
        maximum_attempts = policy.get("maximum_attempts")
        if maximum_attempts is not None and (not isinstance(maximum_attempts, int) or maximum_attempts < 1):
            issues.append(issue("error", f"{where}.maximum_attempts", "must be a positive integer when set."))
        backoff = policy.get("backoff_coefficient")
        if backoff is not None and (not isinstance(backoff, (int, float)) or backoff < 1):
            issues.append(issue("warning", f"{where}.backoff_coefficient", "usually should be a number >= 1."))
        non_retryable = policy.get("non_retryable_error_types")
        if non_retryable is not None:
            if not isinstance(non_retryable, list) or not all(isinstance(item, str) and item for item in non_retryable):
                issues.append(issue("error", f"{where}.non_retryable_error_types", "must be a list of non-empty exception class name strings."))
            elif name == "*" and any(item in PROVIDER_NON_RETRYABLE_HINTS for item in non_retryable):
                issues.append(issue("warning", where, "global non_retryable_error_types may be too broad for mixed activities."))


def check_imports(issues: list[dict[str, str]]) -> None:
    checks = [
        ("temporalio", ("workflow", "activity")),
        ("temporalio.common", ("RetryPolicy", "WorkflowIDReusePolicy")),
        ("mcp_agent.executor.temporal", ("TemporalExecutor", "create_temporal_worker_for_app")),
        ("mcp_agent.executor.workflow_task", ("workflow_task",)),
    ]
    for module_name, names in checks:
        try:
            module = importlib.import_module(module_name)
            missing = [name for name in names if not hasattr(module, name)]
            if missing:
                issues.append(issue("error", module_name, f"missing expected names: {', '.join(missing)}."))
        except Exception as exc:  # noqa: BLE001 - report optional dependency/import failures clearly
            issues.append(issue("error", module_name, f"import failed: {exc}"))


def summarize(issues: list[dict[str, str]]) -> tuple[int, int]:
    errors = sum(1 for item in issues if item["severity"] == "error")
    warnings = sum(1 for item in issues if item["severity"] == "warning")
    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config_path = Path(args.config).expanduser()
    issues: list[dict[str, str]] = []

    try:
        config = load_document(config_path)
    except Exception as exc:  # noqa: BLE001
        issues.append(issue("error", str(config_path), str(exc)))
        config = {}

    if config:
        execution_engine = config.get("execution_engine", "asyncio")
        if execution_engine not in VALID_EXECUTION_ENGINES:
            issues.append(issue("error", "execution_engine", f"invalid value {execution_engine!r}; expected asyncio or temporal."))
        elif execution_engine != "temporal":
            issues.append(issue("warning", "execution_engine", "config is not using Temporal; durable execution is disabled."))
        else:
            validate_temporal_block(
                config,
                expect_task_queue=args.expect_task_queue,
                expect_namespace=args.expect_namespace,
                issues=issues,
            )
        validate_retry_policies(config, require_retry_policy=args.require_retry_policy, issues=issues)
        validate_sensitive_literals(config, "", issues)

    if args.check_imports:
        check_imports(issues)

    errors, warnings = summarize(issues)
    ok = errors == 0 and (warnings == 0 or not args.fail_on_warnings)

    if args.json:
        print(json.dumps({"ok": ok, "errors": errors, "warnings": warnings, "issues": issues}, indent=2))
    else:
        for item in issues:
            stream = sys.stderr if item["severity"] == "error" else sys.stdout
            print(f"{item['severity'].upper()} {item['where']}: {item['message']}", file=stream)
        if ok:
            print(f"Temporal config check passed with {warnings} warning(s).")
        else:
            print(f"Temporal config check failed with {errors} error(s), {warnings} warning(s).", file=sys.stderr)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
