#!/usr/bin/env python3
"""Check OpenLLMetry semantic-convention constants and enums.

The checker is safe: it only imports the semantic-convention modules, compares
public constant/enum values against the source that defines them, and can emit a
JSON report for automation.
"""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import sys
from enum import Enum
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
from typing import Any

LOCAL_MODULE = "opentelemetry.semconv_ai"
UPSTREAM_MODULE = "opentelemetry.semconv._incubating.attributes.gen_ai_attributes"

LOCAL_CLASS_NAMES = (
    "SpanAttributes",
    "GenAISystem",
    "Meters",
    "Events",
    "EventAttributes",
    "LLMRequestTypeValues",
    "TraceloopSpanKindValues",
    "GenAICustomOperationName",
    "GenAITaskStatus",
)

UPSTREAM_CLASS_NAMES = (
    "GenAiSystemValues",
    "GenAiOperationNameValues",
)

UPSTREAM_MODULE_NAMES = (
    "GEN_AI_PROVIDER_NAME",
    "GEN_AI_SYSTEM",
    "GEN_AI_INPUT_MESSAGES",
    "GEN_AI_OUTPUT_MESSAGES",
    "GEN_AI_TOOL_DEFINITIONS",
    "GEN_AI_OPERATION_NAME",
    "GEN_AI_RESPONSE_FINISH_REASONS",
    "GEN_AI_USAGE_INPUT_TOKENS",
    "GEN_AI_USAGE_OUTPUT_TOKENS",
    "GEN_AI_USAGE_CACHE_READ_INPUT_TOKENS",
    "GEN_AI_USAGE_CACHE_CREATION_INPUT_TOKENS",
)

# Cross-checks that the local curated enum aligns with upstream where it should.
LOCAL_TO_UPSTREAM_SYSTEMS = (
    ("OPENAI", "OPENAI"),
    ("ANTHROPIC", "ANTHROPIC"),
    ("COHERE", "COHERE"),
    ("MISTRALAI", "MISTRAL_AI"),
    ("GROQ", "GROQ"),
    ("WATSONX", "IBM_WATSONX_AI"),
    ("AZURE", "AZ_AI_OPENAI"),
    ("AWS", "AWS_BEDROCK"),
    ("GOOGLE", "GCP_GEN_AI"),
)

MISSING = object()


def _module_source(module: Any) -> str:
    """Return module source text when available."""

    try:
        return inspect.getsource(module)
    except (OSError, TypeError):
        path = inspect.getsourcefile(module) or inspect.getfile(module)
        if not path:
            raise RuntimeError(f"Cannot locate source for {module.__name__}")
        return Path(path).read_text()


def _literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _assignment_name_value(node: ast.AST) -> tuple[str | None, Any]:
    """Return an uppercase assignment target and literal value, if present."""

    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        value_node = node.value
    elif isinstance(node, ast.AnnAssign):
        target = node.target
        value_node = node.value
    else:
        return None, None

    if not isinstance(target, ast.Name) or not target.id.isupper() or value_node is None:
        return None, None

    value = _literal(value_node)
    if value is None:
        return None, None
    return target.id, value


def _extract_source_symbols(source: str) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Extract uppercase module constants and class member constants from source."""

    module_constants: dict[str, Any] = {}
    class_constants: dict[str, dict[str, Any]] = {}
    tree = ast.parse(source)

    for node in tree.body:
        name, value = _assignment_name_value(node)
        if name is not None:
            module_constants[name] = value
        elif isinstance(node, ast.ClassDef):
            members: dict[str, Any] = {}
            for stmt in node.body:
                member_name, member_value = _assignment_name_value(stmt)
                if member_name is not None:
                    members[member_name] = member_value
            if members:
                class_constants[node.name] = members

    return module_constants, class_constants


def _live_class_members(cls: Any) -> dict[str, Any]:
    if isinstance(cls, type) and issubclass(cls, Enum):
        return {name: member.value for name, member in cls.__members__.items()}
    return {
        name: value
        for name, value in vars(cls).items()
        if name.isupper() and not name.startswith("_") and isinstance(value, str)
    }


def _live_module_constants(module: Any, names: tuple[str, ...]) -> dict[str, Any]:
    return {name: getattr(module, name, MISSING) for name in names}


def _check_mapping(
    scope: str,
    subject: str,
    expected: dict[str, Any],
    actual: dict[str, Any],
    checks: list[dict[str, Any]],
) -> bool:
    ok = True
    for name, expected_value in expected.items():
        actual_value = actual.get(name, MISSING)
        passed = actual_value == expected_value
        checks.append(
            {
                "scope": scope,
                "subject": subject,
                "name": name,
                "expected": expected_value,
                "actual": None if actual_value is MISSING else actual_value,
                "ok": passed,
            }
        )
        ok = ok and passed
    return ok


def _check_present(
    scope: str,
    subject: str,
    names: tuple[str, ...],
    actual: dict[str, Any],
    checks: list[dict[str, Any]],
) -> bool:
    ok = True
    for name in names:
        actual_value = actual.get(name, MISSING)
        passed = actual_value is not MISSING
        checks.append(
            {
                "scope": scope,
                "subject": subject,
                "name": name,
                "expected": "present",
                "actual": None if actual_value is MISSING else actual_value,
                "ok": passed,
            }
        )
        ok = ok and passed
    return ok


def _run_checks() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []

    try:
        local_module = import_module(LOCAL_MODULE)
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "ok": False,
            "error": f"Failed to import {LOCAL_MODULE}: {exc}",
            "checks": checks,
            "warnings": warnings,
        }

    try:
        upstream_module = import_module(UPSTREAM_MODULE)
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "ok": False,
            "error": f"Failed to import {UPSTREAM_MODULE}: {exc}",
            "checks": checks,
            "warnings": warnings,
        }

    local_source = _module_source(local_module)
    upstream_source = _module_source(upstream_module)
    local_module_constants, local_class_constants = _extract_source_symbols(local_source)
    upstream_module_constants, upstream_class_constants = _extract_source_symbols(upstream_source)

    ok = True

    # Local module-level constant.
    ok = _check_mapping(
        "local",
        LOCAL_MODULE,
        {"SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY": local_module_constants.get("SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY")},
        _live_module_constants(local_module, ("SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY",)),
        checks,
    ) and ok

    # Local public classes/enums.
    for class_name in LOCAL_CLASS_NAMES:
        source_members = local_class_constants.get(class_name)
        if not source_members:
            checks.append(
                {
                    "scope": "local",
                    "subject": class_name,
                    "name": "<class source>",
                    "expected": "present",
                    "actual": None,
                    "ok": False,
                }
            )
            ok = False
            continue
        live_cls = getattr(local_module, class_name, None)
        if live_cls is None:
            checks.append(
                {
                    "scope": "local",
                    "subject": class_name,
                    "name": "<class import>",
                    "expected": "present",
                    "actual": None,
                    "ok": False,
                }
            )
            ok = False
            continue
        actual_members = _live_class_members(live_cls)
        ok = _check_mapping("local", class_name, source_members, actual_members, checks) and ok

    # Upstream required module constants.
    ok = _check_mapping(
        "upstream",
        UPSTREAM_MODULE,
        {name: upstream_module_constants.get(name) for name in UPSTREAM_MODULE_NAMES},
        _live_module_constants(upstream_module, UPSTREAM_MODULE_NAMES),
        checks,
    ) and ok

    # Upstream public enums.
    for class_name in UPSTREAM_CLASS_NAMES:
        source_members = upstream_class_constants.get(class_name)
        if not source_members:
            checks.append(
                {
                    "scope": "upstream",
                    "subject": class_name,
                    "name": "<class source>",
                    "expected": "present",
                    "actual": None,
                    "ok": False,
                }
            )
            ok = False
            continue
        live_cls = getattr(upstream_module, class_name, None)
        if live_cls is None:
            checks.append(
                {
                    "scope": "upstream",
                    "subject": class_name,
                    "name": "<class import>",
                    "expected": "present",
                    "actual": None,
                    "ok": False,
                }
            )
            ok = False
            continue
        actual_members = _live_class_members(live_cls)
        ok = _check_mapping("upstream", class_name, source_members, actual_members, checks) and ok

    # Cross-check local vs upstream aligned vendor values.
    try:
        local_system = getattr(local_module, "GenAISystem")
        upstream_systems = getattr(upstream_module, "GenAiSystemValues")
        for local_name, upstream_name in LOCAL_TO_UPSTREAM_SYSTEMS:
            actual = getattr(local_system, local_name).value
            expected = getattr(upstream_systems, upstream_name).value
            passed = actual == expected
            checks.append(
                {
                    "scope": "cross-check",
                    "subject": "GenAISystem",
                    "name": f"{local_name}->{upstream_name}",
                    "expected": expected,
                    "actual": actual,
                    "ok": passed,
                }
            )
            ok = ok and passed
    except Exception as exc:  # pragma: no cover - defensive
        checks.append(
            {
                "scope": "cross-check",
                "subject": "GenAISystem",
                "name": "alignment",
                "expected": "present",
                "actual": str(exc),
                "ok": False,
            }
        )
        ok = False

    # Intentional divergence around finish-reason naming.
    local_span = getattr(local_module, "SpanAttributes")
    upstream_attrs = upstream_module
    checks.append(
        {
            "scope": "cross-check",
            "subject": "finish-reason naming",
            "name": "local-singular",
            "expected": "gen_ai.response.finish_reason",
            "actual": getattr(local_span, "GEN_AI_RESPONSE_FINISH_REASON", None),
            "ok": getattr(local_span, "GEN_AI_RESPONSE_FINISH_REASON", None) == "gen_ai.response.finish_reason",
        }
    )
    checks.append(
        {
            "scope": "cross-check",
            "subject": "finish-reason naming",
            "name": "upstream-plural",
            "expected": "gen_ai.response.finish_reasons",
            "actual": getattr(upstream_attrs, "GEN_AI_RESPONSE_FINISH_REASONS", None),
            "ok": getattr(upstream_attrs, "GEN_AI_RESPONSE_FINISH_REASONS", None)
            == "gen_ai.response.finish_reasons",
        }
    )

    report = {
        "ok": ok,
        "modules": {
            LOCAL_MODULE: {
                "version": _package_version("opentelemetry-semantic-conventions-ai"),
            },
            UPSTREAM_MODULE: {
                "version": _package_version("opentelemetry-semantic-conventions"),
            },
        },
        "checks": checks,
        "warnings": warnings,
    }
    if not ok:
        report["summary"] = {
            "checked": len(checks),
            "failed": sum(1 for item in checks if not item["ok"]),
        }
    else:
        report["summary"] = {"checked": len(checks), "failed": 0}
    return report


def _package_version(name: str) -> str | None:
    try:
        return package_version(name)
    except PackageNotFoundError:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report.",
    )
    args = parser.parse_args(argv)

    report = _run_checks()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        if report.get("ok"):
            print(f"OK {report['summary']['checked']} checks passed")
        else:
            print(f"FAIL {report['summary']['failed']} of {report['summary']['checked']} checks failed", file=sys.stderr)
            for item in report["checks"]:
                if not item["ok"]:
                    print(
                        f"- {item['scope']}:{item['subject']}:{item['name']} expected {item['expected']!r} got {item['actual']!r}",
                        file=sys.stderr,
                    )
    return 0 if report.get("ok") else 1


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
