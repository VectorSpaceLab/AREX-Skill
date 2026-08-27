#!/usr/bin/env python3
"""Dry-validate Solace Agent Mesh workflow app configs.

This helper is intentionally safe: it parses YAML, runs installed package schema
validation when available, and performs static DAG/template checks. It does not
start brokers, agents, gateways, workflow execution, tasks, LLM calls, or network
checks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - reported at runtime
    yaml = None

SUPPORTED_NODE_TYPES = {"agent", "workflow", "switch", "map", "loop"}
DURATION_RE = re.compile(r"^\s*\d+(?:\.\d+)?\s*[smhdSMHD]?\s*$")
TEMPLATE_RE = re.compile(r"\{\{\s*(.+?)\s*\}\}")

TINY_FIXTURE = """\
apps:
  - name: tiny_workflow_app
    app_module: solace_agent_mesh.workflow.app
    app_config:
      namespace: ${NAMESPACE}
      name: TinyWorkflow
      workflow:
        description: Tiny dry-validation fixture
        input_schema:
          type: object
          properties:
            text: {type: string}
          required: [text]
        nodes:
          - id: analyze
            type: agent
            agent_name: Analyzer
            input:
              text: "{{workflow.input.text}}"
          - id: summarize
            type: agent
            agent_name: Summarizer
            depends_on: [analyze]
            input:
              analysis: "{{analyze.output}}"
        output_mapping:
          result: "{{summarize.output}}"
"""


@dataclass
class WorkflowConfigCandidate:
    source: str
    app_label: str
    app_name: str | None
    app_config: dict[str, Any]


@dataclass
class ValidationReport:
    source: str
    app_label: str
    app_name: str | None
    package_available: bool = False
    package_validation: str = "not-run"
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors and self.package_validation != "failed"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "app_label": self.app_label,
            "app_name": self.app_name,
            "ok": self.ok,
            "package_available": self.package_available,
            "package_validation": self.package_validation,
            "errors": self.errors,
            "warnings": self.warnings,
            "details": self.details,
        }


class UnknownTagSafeLoader(yaml.SafeLoader if yaml else object):  # type: ignore[misc]
    """YAML loader that preserves unknown tagged values as plain data."""


def _install_yaml_constructors() -> None:
    if yaml is None:
        return

    def construct_unknown(loader: Any, tag_suffix: str, node: Any) -> Any:
        if isinstance(node, yaml.ScalarNode):
            return loader.construct_scalar(node)
        if isinstance(node, yaml.SequenceNode):
            return loader.construct_sequence(node)
        if isinstance(node, yaml.MappingNode):
            return loader.construct_mapping(node)
        return None

    UnknownTagSafeLoader.add_multi_constructor("!", construct_unknown)


_install_yaml_constructors()


def strip_bare_include_lines(text: str) -> str:
    """Comment out SAM-style bare !include lines that are not standard YAML."""
    out: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("!include "):
            out.append("# " + line)
        else:
            out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def load_yaml(text: str) -> Any:
    if yaml is None:
        raise RuntimeError("PyYAML is not installed; install pyyaml or run in the SAM environment")
    return yaml.load(strip_bare_include_lines(text), Loader=UnknownTagSafeLoader)


def leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def unquote_scalar(value: str) -> str:
    value = value.strip()
    if (value.startswith("'") and value.endswith("'")) or (
        value.startswith('"') and value.endswith('"')
    ):
        return value[1:-1]
    return value


def discover_candidates_from_loaded(data: Any, source: str) -> list[WorkflowConfigCandidate]:
    candidates: list[WorkflowConfigCandidate] = []
    if not isinstance(data, dict):
        return candidates

    if isinstance(data.get("apps"), list):
        for index, app in enumerate(data["apps"]):
            if not isinstance(app, dict):
                continue
            if str(app.get("app_module", "")).strip() != "solace_agent_mesh.workflow.app":
                continue
            cfg = app.get("app_config")
            if isinstance(cfg, dict):
                label = str(app.get("name") or f"apps[{index}]")
                candidates.append(
                    WorkflowConfigCandidate(
                        source=source,
                        app_label=label,
                        app_name=str(cfg.get("name")) if cfg.get("name") is not None else None,
                        app_config=cfg,
                    )
                )
        return candidates

    if isinstance(data.get("app_config"), dict):
        cfg = data["app_config"]
        if isinstance(cfg.get("workflow"), dict):
            candidates.append(
                WorkflowConfigCandidate(
                    source=source,
                    app_label="app_config",
                    app_name=str(cfg.get("name")) if cfg.get("name") is not None else None,
                    app_config=cfg,
                )
            )
        return candidates

    if isinstance(data.get("workflow"), dict):
        candidates.append(
            WorkflowConfigCandidate(
                source=source,
                app_label="direct-app-config",
                app_name=str(data.get("name")) if data.get("name") is not None else None,
                app_config=data,
            )
        )

    return candidates


def sanitize_aliases_for_fragment(fragment: str) -> str:
    """Make an extracted app_config block parseable without external anchors."""
    sanitized: list[str] = []
    for line in fragment.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            sanitized.append(line)
            continue
        if re.search(r"<<\s*:\s*\*", line):
            # Merge aliases usually import shared broker/service/model config. They are
            # irrelevant for workflow DAG schema validation and may point to includes.
            continue
        line = re.sub(r":\s*\{\s*<<\s*:\s*\*[^}]+\}\s*(#.*)?$", r": {} \1", line)
        line = re.sub(r":\s*\*([A-Za-z0-9_.-]+)\s*(#.*)?$", r': "__alias_\1__" \2', line)
        sanitized.append(line)
    return "\n".join(sanitized) + "\n"


def split_app_blocks(text: str) -> list[list[str]]:
    lines = text.splitlines()
    apps_index: int | None = None
    for i, line in enumerate(lines):
        if re.match(r"^apps\s*:\s*(?:#.*)?$", line):
            apps_index = i
            break
    if apps_index is None:
        return []

    blocks: list[list[str]] = []
    current: list[str] | None = None
    item_indent: int | None = None

    for line in lines[apps_index + 1 :]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            if current is not None:
                current.append(line)
            continue

        indent = leading_spaces(line)
        if indent == 0 and not line.startswith("-"):
            if current is not None:
                blocks.append(current)
            break

        if re.match(r"^\s*-\s+", line):
            if item_indent is None:
                item_indent = indent
            if indent == item_indent:
                if current is not None:
                    blocks.append(current)
                current = [line]
            elif current is not None:
                current.append(line)
        elif current is not None:
            current.append(line)

    if current is not None and (not blocks or blocks[-1] is not current):
        blocks.append(current)
    return blocks


def extract_app_config_fragment(block: list[str]) -> str | None:
    for i, line in enumerate(block):
        m = re.match(r"^(\s*)app_config\s*:\s*(?:#.*)?$", line)
        if not m:
            continue
        indent = len(m.group(1))
        collected = [line]
        for next_line in block[i + 1 :]:
            stripped = next_line.strip()
            if stripped and not stripped.startswith("#") and leading_spaces(next_line) <= indent:
                break
            collected.append(next_line)
        return textwrap.dedent("\n".join(collected)) + "\n"
    return None


def discover_candidates_by_text(text: str, source: str) -> list[WorkflowConfigCandidate]:
    candidates: list[WorkflowConfigCandidate] = []
    for index, block in enumerate(split_app_blocks(text)):
        block_text = "\n".join(block)
        if "app_module:" not in block_text or "solace_agent_mesh.workflow.app" not in block_text:
            continue
        app_label = f"apps[{index}]"
        m = re.search(r"^\s*-\s*name\s*:\s*(.+?)\s*(?:#.*)?$", block_text, re.MULTILINE)
        if m:
            app_label = unquote_scalar(m.group(1))
        fragment = extract_app_config_fragment(block)
        if not fragment:
            continue
        try:
            data = load_yaml(sanitize_aliases_for_fragment(fragment))
        except Exception as exc:
            # Leave a marker candidate so the user gets a focused error.
            candidates.append(
                WorkflowConfigCandidate(
                    source=source,
                    app_label=app_label,
                    app_name=None,
                    app_config={"__extract_error__": str(exc)},
                )
            )
            continue
        cfg = data.get("app_config") if isinstance(data, dict) else None
        if isinstance(cfg, dict):
            candidates.append(
                WorkflowConfigCandidate(
                    source=source,
                    app_label=app_label,
                    app_name=str(cfg.get("name")) if cfg.get("name") is not None else None,
                    app_config=cfg,
                )
            )
    return candidates


def read_candidates(path: Path) -> tuple[list[WorkflowConfigCandidate], list[str]]:
    text = path.read_text(encoding="utf-8")
    notes: list[str] = []
    candidates: list[WorkflowConfigCandidate] = []
    try:
        data = load_yaml(text)
        candidates = discover_candidates_from_loaded(data, str(path))
    except Exception as exc:
        notes.append(f"direct YAML load failed: {exc}")

    if not candidates:
        text_candidates = discover_candidates_by_text(text, str(path))
        if text_candidates:
            notes.append("used heuristic workflow app_config extraction")
            candidates = text_candidates

    return candidates, notes


def iter_templates(value: Any, location: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        for match in TEMPLATE_RE.finditer(value):
            yield location, match.group(1).strip()
    elif isinstance(value, dict):
        for k, v in value.items():
            child = f"{location}.{k}" if location else str(k)
            yield from iter_templates(v, child)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            child = f"{location}[{i}]" if location else f"[{i}]"
            yield from iter_templates(v, child)


def get_depends(node: dict[str, Any]) -> list[str]:
    deps = node.get("depends_on", node.get("dependencies", []))
    if deps is None:
        return []
    if isinstance(deps, str):
        return [deps]
    if isinstance(deps, list):
        return [str(d) for d in deps]
    return []


def get_alias_value(obj: dict[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in obj:
            return obj[name]
    return default


def validate_duration(value: Any, label: str, report: ValidationReport) -> None:
    if value is None:
        return
    if isinstance(value, (int, float)):
        if value < 0:
            report.errors.append(f"{label} must not be negative")
        return
    if not isinstance(value, str) or not DURATION_RE.match(value):
        report.errors.append(
            f"{label} has invalid duration {value!r}; use seconds or a suffix such as 30s, 5m, 1h, 1d"
        )


def validate_retry_strategy(value: Any, label: str, report: ValidationReport) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        report.errors.append(f"{label} must be an object")
        return
    if "limit" in value and (not isinstance(value["limit"], int) or value["limit"] < 0):
        report.errors.append(f"{label}.limit must be a non-negative integer")
    policy = get_alias_value(value, "retry_policy", "retryPolicy")
    if policy is not None and policy not in {"Always", "OnFailure", "OnError"}:
        report.errors.append(f"{label}.retryPolicy must be one of Always, OnFailure, OnError")
    backoff = value.get("backoff")
    if backoff is not None:
        if not isinstance(backoff, dict):
            report.errors.append(f"{label}.backoff must be an object")
        else:
            validate_duration(backoff.get("duration"), f"{label}.backoff.duration", report)
            validate_duration(get_alias_value(backoff, "max_duration", "maxDuration"), f"{label}.backoff.maxDuration", report)
            if "factor" in backoff and not isinstance(backoff["factor"], (int, float)):
                report.errors.append(f"{label}.backoff.factor must be numeric")


def validate_templates(
    value: Any,
    label: str,
    node_ids: set[str],
    report: ValidationReport,
    producer_deps: set[str] | None = None,
) -> None:
    for loc, path in iter_templates(value, label):
        root = path.split(".", 1)[0]
        if root == "workflow":
            continue
        if root in {"_map_item", "_map_index", "_loop_iteration", "item"}:
            continue
        if not root:
            continue
        if root not in node_ids:
            report.warnings.append(f"{loc} template references unknown node or context {root!r}: {{{{{path}}}}}")
        elif producer_deps is not None and root not in producer_deps:
            report.warnings.append(
                f"{loc} reads {root!r} but the node does not list it in depends_on; add a dependency or make the reference optional"
            )


def detect_cycles(deps: dict[str, list[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def dfs(node: str) -> None:
        if node in visiting:
            if node in stack:
                cycles.append(stack[stack.index(node) :] + [node])
            return
        if node in visited:
            return
        visiting.add(node)
        stack.append(node)
        for dep in deps.get(node, []):
            if dep in deps:
                dfs(dep)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in deps:
        dfs(node)
    return cycles


def reachable_nodes(deps: dict[str, list[str]], inner_nodes: set[str]) -> set[str]:
    reverse: dict[str, list[str]] = {node: [] for node in deps}
    for node, node_deps in deps.items():
        for dep in node_deps:
            if dep in reverse:
                reverse[dep].append(node)
    initial = [node for node, node_deps in deps.items() if not node_deps and node not in inner_nodes]
    seen: set[str] = set()
    queue = list(initial)
    while queue:
        node = queue.pop(0)
        if node in seen:
            continue
        seen.add(node)
        queue.extend(reverse.get(node, []))
    return seen


def validate_static(candidate: WorkflowConfigCandidate, report: ValidationReport) -> None:
    cfg = candidate.app_config
    if "__extract_error__" in cfg:
        report.errors.append(f"failed to extract app_config: {cfg['__extract_error__']}")
        return

    if not isinstance(cfg.get("name"), str) or not cfg.get("name"):
        report.errors.append("app_config.name is required and must be a non-empty string")
    if not isinstance(cfg.get("namespace"), str) or not cfg.get("namespace"):
        report.errors.append("app_config.namespace is required and must be a non-empty string")

    for key in [
        "max_workflow_execution_time_seconds",
        "default_node_timeout_seconds",
        "node_cancellation_timeout_seconds",
        "default_max_map_items",
    ]:
        if key in cfg and (not isinstance(cfg[key], int) or cfg[key] < 0):
            report.errors.append(f"app_config.{key} must be a non-negative integer number of seconds/items")

    workflow = cfg.get("workflow")
    if not isinstance(workflow, dict):
        report.errors.append("app_config.workflow is required and must be an object")
        return

    if not workflow.get("description"):
        report.errors.append("workflow.description is required")
    nodes = workflow.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        report.errors.append("workflow.nodes is required and must be a non-empty list")
        return
    output_mapping = get_alias_value(workflow, "output_mapping", "outputMapping")
    if not isinstance(output_mapping, dict):
        report.errors.append("workflow.output_mapping/outputMapping is required and must be an object")

    validate_retry_strategy(get_alias_value(workflow, "retry_strategy", "retryStrategy"), "workflow.retryStrategy", report)
    max_depth = get_alias_value(workflow, "max_call_depth", "maxCallDepth")
    if max_depth is not None and (not isinstance(max_depth, int) or max_depth < 1):
        report.errors.append("workflow.max_call_depth/maxCallDepth must be an integer >= 1")

    node_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    normalized_nodes: list[dict[str, Any]] = []
    for index, raw_node in enumerate(nodes):
        if not isinstance(raw_node, dict):
            report.errors.append(f"workflow.nodes[{index}] must be an object")
            continue
        normalized_nodes.append(raw_node)
        node_id = raw_node.get("id")
        if not isinstance(node_id, str) or not node_id:
            report.errors.append(f"workflow.nodes[{index}].id is required and must be a non-empty string")
            continue
        if node_id in node_ids:
            duplicate_ids.add(node_id)
        node_ids.add(node_id)

    for node_id in sorted(duplicate_ids):
        report.errors.append(f"duplicate node id {node_id!r}")

    deps_by_node: dict[str, list[str]] = {}
    inner_nodes: set[str] = set()
    for node in normalized_nodes:
        node_id = str(node.get("id"))
        deps = get_depends(node)
        deps_by_node[node_id] = deps
        for dep in deps:
            if dep not in node_ids:
                report.errors.append(f"node {node_id!r} depends on non-existent node {dep!r}")
            if dep == node_id:
                report.errors.append(f"node {node_id!r} must not depend on itself")

    for cycle in detect_cycles(deps_by_node):
        report.errors.append("dependency cycle detected: " + " -> ".join(cycle))

    for node in normalized_nodes:
        node_id = str(node.get("id"))
        node_type = node.get("type")
        label = f"node {node_id!r}"
        deps = set(get_depends(node))

        if node_type not in SUPPORTED_NODE_TYPES:
            report.errors.append(f"{label} has unsupported type {node_type!r}; expected one of {sorted(SUPPORTED_NODE_TYPES)}")
            continue

        if node_type in {"agent", "workflow"}:
            if node_type == "agent" and not node.get("agent_name"):
                report.errors.append(f"{label} type 'agent' requires agent_name")
            if node_type == "workflow" and not node.get("workflow_name"):
                report.errors.append(f"{label} type 'workflow' requires workflow_name")
            if node_type == "workflow" and node.get("workflow_name") == cfg.get("name"):
                report.errors.append(f"{label} directly invokes its own workflow name {cfg.get('name')!r}")
            if "input_schema" in node or "output_schema" in node:
                report.warnings.append(
                    f"{label} has node-level input_schema/output_schema; installed node schema uses input_schema_override/output_schema_override"
                )
            validate_duration(node.get("timeout"), f"{label}.timeout", report)
            validate_retry_strategy(get_alias_value(node, "retry_strategy", "retryStrategy"), f"{label}.retryStrategy", report)
            if len(deps) > 1 and "input" not in node:
                report.warnings.append(f"{label} has multiple dependencies but no explicit input mapping")
            validate_templates(node.get("input"), f"{label}.input", node_ids, report, deps)
            validate_templates(node.get("instruction"), f"{label}.instruction", node_ids, report, deps)
            validate_templates(node.get("when"), f"{label}.when", node_ids, report, deps)

        elif node_type == "switch":
            cases = node.get("cases")
            if not isinstance(cases, list) or not cases:
                report.errors.append(f"{label} type 'switch' requires a non-empty cases list")
                cases = []
            branch_targets: list[tuple[str, str]] = []
            for i, case in enumerate(cases):
                if not isinstance(case, dict):
                    report.errors.append(f"{label}.cases[{i}] must be an object")
                    continue
                condition = get_alias_value(case, "condition", "when")
                target = get_alias_value(case, "node", "then")
                if not isinstance(condition, str) or not condition:
                    report.errors.append(f"{label}.cases[{i}] requires condition/when")
                else:
                    validate_templates(condition, f"{label}.cases[{i}].condition", node_ids, report, deps)
                if not isinstance(target, str) or not target:
                    report.errors.append(f"{label}.cases[{i}] requires node/then")
                else:
                    branch_targets.append((f"cases[{i}]", target))
            default = node.get("default")
            if default is not None:
                if not isinstance(default, str) or not default:
                    report.errors.append(f"{label}.default must be a node id string")
                else:
                    branch_targets.append(("default", default))
            for branch_name, target in branch_targets:
                if target not in node_ids:
                    report.errors.append(f"{label} references non-existent {branch_name} target {target!r}")
                    continue
                target_node = next((n for n in normalized_nodes if n.get("id") == target), None)
                target_deps = get_depends(target_node or {})
                if node_id not in target_deps:
                    report.errors.append(
                        f"{label} routes to {target!r} ({branch_name}), but {target!r} does not list {node_id!r} in depends_on"
                    )

        elif node_type == "map":
            sources = [name for name in ["items", "withParam", "withItems"] if node.get(name) is not None]
            if len(sources) == 0:
                report.errors.append(f"{label} type 'map' requires exactly one of items, withParam, withItems")
            elif len(sources) > 1:
                report.errors.append(f"{label} type 'map' accepts only one item source; found {sources}")
            target = node.get("node")
            if not isinstance(target, str) or not target:
                report.errors.append(f"{label} type 'map' requires node target")
            elif target not in node_ids:
                report.errors.append(f"{label} references non-existent map target {target!r}")
            else:
                inner_nodes.add(target)
            validate_templates(node.get("items"), f"{label}.items", node_ids, report, deps)
            if "withParam" in node:
                validate_templates(node.get("withParam"), f"{label}.withParam", node_ids, report, deps)
            max_items = get_alias_value(node, "max_items", "maxItems")
            if max_items is not None and (not isinstance(max_items, int) or max_items < 0):
                report.errors.append(f"{label}.max_items/maxItems must be a non-negative integer")
            concurrency = get_alias_value(node, "concurrency_limit", "concurrencyLimit")
            if concurrency is not None and (not isinstance(concurrency, int) or concurrency < 1):
                report.errors.append(f"{label}.concurrency_limit/concurrencyLimit must be an integer >= 1")

        elif node_type == "loop":
            target = node.get("node")
            if not isinstance(target, str) or not target:
                report.errors.append(f"{label} type 'loop' requires node target")
            elif target not in node_ids:
                report.errors.append(f"{label} references non-existent loop target {target!r}")
            else:
                inner_nodes.add(target)
            if not isinstance(node.get("condition"), str) or not node.get("condition"):
                report.errors.append(f"{label} type 'loop' requires condition")
            else:
                validate_templates(node.get("condition"), f"{label}.condition", node_ids, report, set(node_ids))
            max_iterations = get_alias_value(node, "max_iterations", "maxIterations")
            if max_iterations is not None and (not isinstance(max_iterations, int) or max_iterations < 1):
                report.errors.append(f"{label}.max_iterations/maxIterations must be an integer >= 1")
            validate_duration(node.get("delay"), f"{label}.delay", report)

    if not [node for node, dep_list in deps_by_node.items() if not dep_list and node not in inner_nodes]:
        report.errors.append("workflow has no initial node; check dependencies and cycles")
    seen = reachable_nodes(deps_by_node, inner_nodes)
    for node_id in sorted(set(deps_by_node) - seen - inner_nodes):
        report.warnings.append(f"node {node_id!r} is not reachable from any initial node through depends_on")

    on_exit = get_alias_value(workflow, "on_exit", "onExit")
    exit_refs: list[tuple[str, str]] = []
    if isinstance(on_exit, str):
        exit_refs.append(("onExit", on_exit))
    elif isinstance(on_exit, dict):
        for key in ["always", "on_success", "onSuccess", "on_failure", "onFailure", "on_cancel", "onCancel"]:
            if isinstance(on_exit.get(key), str):
                exit_refs.append((f"onExit.{key}", on_exit[key]))
    elif on_exit is not None:
        report.errors.append("workflow.on_exit/onExit must be a node id string or an object")
    for loc, node_id in exit_refs:
        if node_id not in node_ids:
            report.errors.append(f"{loc} references non-existent node {node_id!r}")

    validate_templates(output_mapping, "workflow.output_mapping", node_ids, report)
    report.details.update(
        {
            "node_count": len(normalized_nodes),
            "node_ids": sorted(node_ids),
            "inner_nodes": sorted(inner_nodes),
        }
    )


def validate_with_package(candidate: WorkflowConfigCandidate, report: ValidationReport) -> None:
    try:
        from solace_agent_mesh.workflow.app import WorkflowAppConfig  # type: ignore
    except Exception as exc:
        report.package_available = False
        report.package_validation = "not-available"
        report.warnings.append(f"installed package validation unavailable: {exc}")
        return

    report.package_available = True
    try:
        if hasattr(WorkflowAppConfig, "model_validate_and_clean"):
            WorkflowAppConfig.model_validate_and_clean(candidate.app_config)
        else:
            WorkflowAppConfig.model_validate(candidate.app_config)
        report.package_validation = "passed"
    except Exception as exc:
        report.package_validation = "failed"
        report.errors.append(f"installed WorkflowAppConfig validation failed: {exc}")


def filter_candidates(candidates: list[WorkflowConfigCandidate], app: str | None) -> list[WorkflowConfigCandidate]:
    if app is None:
        return candidates
    selected = [
        c
        for c in candidates
        if c.app_name == app or c.app_label == app or Path(c.app_label).name == app
    ]
    return selected


def validate_path(path: Path, app: str | None, skip_package: bool) -> tuple[list[ValidationReport], list[str]]:
    candidates, notes = read_candidates(path)
    candidates = filter_candidates(candidates, app)
    reports: list[ValidationReport] = []
    if not candidates:
        report = ValidationReport(source=str(path), app_label=app or "<none>", app_name=app)
        report.errors.append("no workflow app_config found; expected apps[].app_module: solace_agent_mesh.workflow.app or a direct app_config/workflow object")
        for note in notes:
            report.warnings.append(note)
        return [report], notes

    for candidate in candidates:
        report = ValidationReport(source=candidate.source, app_label=candidate.app_label, app_name=candidate.app_name)
        for note in notes:
            report.warnings.append(note)
        validate_static(candidate, report)
        if not skip_package:
            validate_with_package(candidate, report)
        else:
            report.package_validation = "skipped"
        reports.append(report)
    return reports, notes


def print_text_reports(reports: list[ValidationReport]) -> None:
    for index, report in enumerate(reports):
        if index:
            print()
        status = "OK" if report.ok else "FAILED"
        name = report.app_name or report.app_label
        print(f"[{status}] {name} ({report.source})")
        print(f"  package_validation: {report.package_validation}")
        if report.details:
            print(f"  node_count: {report.details.get('node_count', 0)}")
        if report.errors:
            print("  errors:")
            for err in report.errors:
                print(f"    - {err}")
        if report.warnings:
            print("  warnings:")
            for warn in report.warnings:
                print(f"    - {warn}")


def run_self_test(skip_package: bool) -> int:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="sam-workflow-validator-") as tmp:
        path = Path(tmp) / "tiny_workflow.yaml"
        path.write_text(TINY_FIXTURE, encoding="utf-8")
        reports, _ = validate_path(path, app=None, skip_package=skip_package)
        print_text_reports(reports)
        return 0 if all(r.ok for r in reports) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dry-validate Solace Agent Mesh workflow YAML/configs without starting services.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("paths", nargs="*", type=Path, help="YAML files to validate")
    parser.add_argument("--app", help="Select a workflow by app_config.name or apps[].name")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--skip-package-validation", action="store_true", help="Run only static validation")
    parser.add_argument("--self-test", action="store_true", help="Validate an embedded tiny fixture and exit")
    parser.add_argument("--print-tiny-fixture", action="store_true", help="Print the embedded tiny fixture and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.print_tiny_fixture:
        print(TINY_FIXTURE, end="")
        return 0
    if args.self_test:
        return run_self_test(skip_package=args.skip_package_validation)
    if not args.paths:
        parser.error("provide at least one YAML path, --self-test, or --print-tiny-fixture")

    all_reports: list[ValidationReport] = []
    for path in args.paths:
        if not path.exists():
            report = ValidationReport(source=str(path), app_label=args.app or "<missing>", app_name=args.app)
            report.errors.append("file does not exist")
            all_reports.append(report)
            continue
        if not path.is_file():
            report = ValidationReport(source=str(path), app_label=args.app or "<not-file>", app_name=args.app)
            report.errors.append("path is not a file")
            all_reports.append(report)
            continue
        reports, _ = validate_path(path, app=args.app, skip_package=args.skip_package_validation)
        all_reports.extend(reports)

    if args.json:
        print(json.dumps([r.to_jsonable() for r in all_reports], indent=2, sort_keys=True))
    else:
        print_text_reports(all_reports)

    return 0 if all(r.ok for r in all_reports) else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
