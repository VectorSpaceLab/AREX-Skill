#!/usr/bin/env python3
"""Static checker for LM Evaluation Harness task YAML decontamination fields.

This helper is intentionally safe: it never imports lm_eval, executes !function
references, downloads datasets, or runs evaluations. It inspects YAML-like text
for should_decontaminate and doc_to_decontamination_query hygiene.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - fallback for minimal environments
    yaml = None


CUSTOM_TAG_RE = re.compile(r"!\w+(?:\.\w+)*")
FIELD_RE = re.compile(r"^\s*(should_decontaminate|doc_to_decontamination_query)\s*:\s*(.*)$")
LIKELY_TARGET_TERMS = {"answer", "answers", "label", "labels", "target", "targets", "gold", "choice"}
LIKELY_SOURCE_TERMS = {
    "question",
    "query",
    "passage",
    "context",
    "story",
    "sentence",
    "text",
    "page",
    "premise",
    "article",
    "document",
    "goal",
    "body",
    "support",
}


def _load_yaml(path: Path) -> tuple[Any | None, str | None]:
    text = path.read_text(encoding="utf-8")
    if yaml is None:
        return None, "PyYAML is not available; using line-based fallback only."
    if CUSTOM_TAG_RE.search(text):
        return None, "Custom YAML tag detected; using line-based fallback to avoid executing repo-specific constructors."
    try:
        return yaml.safe_load(text), None
    except Exception as exc:  # noqa: BLE001
        return None, f"YAML parse failed; using line-based fallback: {exc}"


def _parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "on", "1"}:
            return True
        if lowered in {"false", "no", "off", "0"}:
            return False
    return None


def _clean_scalar(value: str) -> str:
    value = value.strip()
    if value in {"", "|", ">", "|-", ">-", "|+", ">+"}:
        return value
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def _line_fallback(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = FIELD_RE.match(line)
        if match:
            key, value = match.groups()
            result[key] = _clean_scalar(value.split(" #", 1)[0])
    return result


def _extract_config(path: Path) -> tuple[dict[str, Any], list[str]]:
    notes: list[str] = []
    loaded, warning = _load_yaml(path)
    if warning:
        notes.append(warning)
    if isinstance(loaded, dict):
        return loaded, notes
    return _line_fallback(path), notes


def _looks_target_only(query: str) -> bool:
    lowered = query.lower()
    source_hit = any(term in lowered for term in LIKELY_SOURCE_TERMS)
    target_hit = any(term in lowered for term in LIKELY_TARGET_TERMS)
    return target_hit and not source_hit


def check_file(path: Path) -> dict[str, Any]:
    config, notes = _extract_config(path)
    findings: list[dict[str, str]] = []

    should_raw = config.get("should_decontaminate")
    query_raw = config.get("doc_to_decontamination_query")
    should = _parse_bool(should_raw)
    query = "" if query_raw is None else str(query_raw).strip()

    if should_raw is None:
        findings.append({"level": "info", "message": "should_decontaminate is omitted; harness default is disabled."})
    elif should is None:
        findings.append({"level": "warning", "message": f"should_decontaminate is not boolean-like: {should_raw!r}."})

    if should is True and not query:
        findings.append({"level": "error", "message": "should_decontaminate is enabled but doc_to_decontamination_query is empty or missing."})
    elif should is False and query:
        findings.append({"level": "info", "message": "doc_to_decontamination_query is present but inactive because should_decontaminate is false."})
    elif should is True and query:
        findings.append({"level": "ok", "message": "enabled decontamination has a query field."})

    if query:
        if "\\n" in query:
            findings.append({"level": "info", "message": "query contains a backslash-n sequence; verify YAML quoting matches intended newline behavior."})
        if _looks_target_only(query):
            findings.append({"level": "warning", "message": "query appears target/label-oriented; prefer source prompt text for contamination matching."})
        if query in {"|", ">", "|-", ">-", "|+", ">+"}:
            findings.append({"level": "warning", "message": "line-based fallback saw a block scalar marker; inspect the full query manually."})

    for note in notes:
        findings.append({"level": "note", "message": note})

    worst = "ok"
    if any(item["level"] == "error" for item in findings):
        worst = "error"
    elif any(item["level"] == "warning" for item in findings):
        worst = "warning"

    return {
        "path": str(path),
        "status": worst,
        "should_decontaminate": should_raw,
        "doc_to_decontamination_query": query_raw,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Static decontamination-field checker for LM Evaluation Harness task YAML files.")
    parser.add_argument("paths", nargs="+", type=Path, help="Task YAML file(s) to inspect.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    results = []
    exit_code = 0
    for path in args.paths:
        if not path.exists() or not path.is_file():
            result = {"path": str(path), "status": "error", "findings": [{"level": "error", "message": "file does not exist or is not a regular file."}]}
            exit_code = 1
        else:
            result = check_file(path)
            if result["status"] == "error":
                exit_code = 1
        results.append(result)

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        for result in results:
            print(f"{result['path']}: {result['status']}")
            for finding in result["findings"]:
                print(f"  [{finding['level']}] {finding['message']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
