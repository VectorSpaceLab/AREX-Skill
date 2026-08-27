#!/usr/bin/env python3
"""Offline validator for Solace Agent Mesh evaluation suites.

This helper validates the file-level shape of a `sam eval` suite and its test
case files without contacting a broker, gateway, REST API, or LLM provider.
It accepts JSON and, when PyYAML is installed, YAML input for preflight. The
live SAM loader is stricter and currently expects JSON suite files.

Examples:
  python validate_eval_inputs.py path/to/suite.json
  python validate_eval_inputs.py path/to/suite.json --check-env --strict
  python validate_eval_inputs.py --self-test
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

try:  # Optional: SAM installs PyYAML, but keep a clear fallback for stdlib users.
    import yaml  # type: ignore
except Exception:  # pragma: no cover - depends on caller environment
    yaml = None


class Finding:
    def __init__(self, severity: str, path: str, message: str) -> None:
        self.severity = severity
        self.path = path
        self.message = message

    def as_dict(self) -> dict[str, str]:
        return {"severity": self.severity, "path": self.path, "message": self.message}

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.path}: {self.message}"


def load_data(path: Path, findings: list[Finding]) -> Any | None:
    if not path.exists():
        findings.append(Finding("error", str(path), "file does not exist"))
        return None
    text = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() in {".yaml", ".yml"}:
            if yaml is None:
                findings.append(
                    Finding(
                        "error",
                        str(path),
                        "YAML input needs PyYAML; install PyYAML or convert this file to JSON",
                    )
                )
                return None
            return yaml.safe_load(text)
        return json.loads(text)
    except Exception as exc:
        findings.append(Finding("error", str(path), f"could not parse file: {exc}"))
        return None


def require_mapping(value: Any, path: str, findings: list[Finding]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        findings.append(Finding("error", path, "expected an object/mapping"))
        return None
    return value


def require_list(value: Any, path: str, findings: list[Finding]) -> list[Any] | None:
    if not isinstance(value, list):
        findings.append(Finding("error", path, "expected a list"))
        return None
    return value


def scan_env_refs(value: Any, path: str, findings: list[Finding], check_env: bool) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            item_path = f"{path}.{key}"
            if isinstance(key, str) and key.endswith("_VAR"):
                if not isinstance(item, str) or not item:
                    findings.append(Finding("error", item_path, "_VAR entries must name a non-empty environment variable"))
                elif check_env and item not in os.environ:
                    findings.append(Finding("warning", item_path, f"environment variable {item!r} is not set"))
            scan_env_refs(item, item_path, findings, check_env)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            scan_env_refs(item, f"{path}[{i}]", findings, check_env)


def validate_artifact(item: Any, case_dir: Path, case_path: str, findings: list[Finding]) -> None:
    art = require_mapping(item, case_path, findings)
    if art is None:
        return
    art_type = art.get("type")
    art_path = art.get("path")
    if art_type not in {"file", "url", "text"}:
        findings.append(Finding("error", f"{case_path}.type", "must be one of: file, url, text"))
    if not isinstance(art_path, str) or not art_path:
        findings.append(Finding("error", f"{case_path}.path", "artifact path/content reference is required"))
        return
    if art_type == "file":
        candidate = Path(art_path)
        if candidate.is_absolute():
            findings.append(Finding("error", f"{case_path}.path", "file artifacts should be relative to the test case file"))
            return
        if ".." in candidate.parts:
            findings.append(Finding("error", f"{case_path}.path", "file artifact paths must not traverse upward with '..'"))
            return
        resolved = (case_dir / candidate).resolve()
        try:
            resolved.relative_to(case_dir.resolve())
        except ValueError:
            findings.append(Finding("error", f"{case_path}.path", "file artifact path escapes the test case directory"))
            return
        if not resolved.exists():
            findings.append(Finding("warning", f"{case_path}.path", "file artifact does not exist yet"))


def validate_test_case(path: Path, findings: list[Finding]) -> None:
    data = load_data(path, findings)
    case = require_mapping(data, str(path), findings)
    if case is None:
        return
    for key in ["test_case_id", "query", "target_agent"]:
        if not isinstance(case.get(key), str) or not case.get(key):
            findings.append(Finding("error", f"{path}:{key}", "required non-empty string is missing"))
    wait_time = case.get("wait_time")
    if wait_time is not None:
        if not isinstance(wait_time, (int, float)) or wait_time <= 0:
            findings.append(Finding("error", f"{path}:wait_time", "wait_time must be a positive number"))
        elif wait_time > 300:
            findings.append(Finding("warning", f"{path}:wait_time", "live loader caps wait_time at 300 seconds"))
    artifacts = case.get("artifacts", [])
    artifacts_list = require_list(artifacts, f"{path}:artifacts", findings)
    if artifacts_list is not None:
        for idx, artifact in enumerate(artifacts_list):
            validate_artifact(artifact, path.parent, f"{path}:artifacts[{idx}]", findings)
    evaluation = case.get("evaluation", {})
    if evaluation is not None and not isinstance(evaluation, dict):
        findings.append(Finding("error", f"{path}:evaluation", "evaluation must be an object when provided"))


def validate_suite(path: Path, check_env: bool) -> list[Finding]:
    findings: list[Finding] = []
    suite_data = load_data(path, findings)
    suite = require_mapping(suite_data, str(path), findings)
    if suite is None:
        return findings

    if path.suffix.lower() in {".yaml", ".yml"}:
        findings.append(Finding("warning", str(path), "YAML accepted by this preflight helper; live sam eval expects JSON"))

    if not isinstance(suite.get("broker"), dict):
        findings.append(Finding("error", "suite.broker", "broker object is required"))

    if not isinstance(suite.get("results_dir_name"), str) or not suite.get("results_dir_name"):
        findings.append(Finding("error", "suite.results_dir_name", "required non-empty string is missing"))

    test_cases = require_list(suite.get("test_cases"), "suite.test_cases", findings)
    if test_cases is not None:
        if not test_cases:
            findings.append(Finding("error", "suite.test_cases", "at least one test case path is required"))
        for idx, rel in enumerate(test_cases):
            item_path = f"suite.test_cases[{idx}]"
            if not isinstance(rel, str) or not rel:
                findings.append(Finding("error", item_path, "test case path must be a non-empty string"))
                continue
            case_path = Path(rel)
            if case_path.is_absolute():
                findings.append(Finding("error", item_path, "test case paths should be relative to the suite file"))
                continue
            resolved = (path.parent / case_path).resolve()
            validate_test_case(resolved, findings)

    has_remote = isinstance(suite.get("remote"), dict)
    has_agents = "agents" in suite
    has_models = "llm_models" in suite
    if has_remote:
        if has_agents or has_models:
            findings.append(Finding("error", "suite", "remote mode must not also define agents or llm_models"))
        remote = suite["remote"]
        for key in ["EVAL_REMOTE_URL_VAR", "EVAL_REMOTE_URL", "EVAL_NAMESPACE_VAR", "EVAL_NAMESPACE"]:
            if key in remote:
                break
        else:
            findings.append(Finding("warning", "suite.remote", "remote mode should define URL and namespace values or _VAR references"))
    else:
        agents = require_list(suite.get("agents"), "suite.agents", findings)
        models = require_list(suite.get("llm_models"), "suite.llm_models", findings)
        if agents is not None and not agents:
            findings.append(Finding("error", "suite.agents", "local mode needs at least one agent config"))
        if models is not None and not models:
            findings.append(Finding("error", "suite.llm_models", "local mode needs at least one model config"))

    runs = suite.get("runs")
    if runs is not None and (not isinstance(runs, int) or runs < 1):
        findings.append(Finding("error", "suite.runs", "runs must be a positive integer"))
    workers = suite.get("workers")
    if workers is not None and (not isinstance(workers, int) or workers < 1):
        findings.append(Finding("error", "suite.workers", "workers must be a positive integer"))

    scan_env_refs(suite, "suite", findings, check_env)
    return findings


def run_self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        case = root / "case.json"
        case.write_text(
            json.dumps(
                {
                    "test_case_id": "case-1",
                    "query": "hello",
                    "target_agent": "OrchestratorAgent",
                    "evaluation": {"expected_response": "hello"},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        suite = root / "suite.json"
        suite.write_text(
            json.dumps(
                {
                    "broker": {
                        "SOLACE_BROKER_URL_VAR": "SOLACE_BROKER_URL",
                        "SOLACE_BROKER_VPN_VAR": "SOLACE_BROKER_VPN",
                        "SOLACE_BROKER_USERNAME_VAR": "SOLACE_BROKER_USERNAME",
                        "SOLACE_BROKER_PASSWORD_VAR": "SOLACE_BROKER_PASSWORD",
                    },
                    "agents": ["configs/agents/main_orchestrator.yaml"],
                    "llm_models": [{"name": "sample", "env": {"LLM_SERVICE_PLANNING_MODEL_NAME": "dummy"}}],
                    "test_cases": ["case.json"],
                    "results_dir_name": "self-test-results",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        findings = validate_suite(suite, check_env=False)
        errors = [f for f in findings if f.severity == "error"]
        if errors:
            for finding in findings:
                print(finding, file=sys.stderr)
            return 1
        print("self-test passed")
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline preflight validator for SAM evaluation suite/test case files.")
    parser.add_argument("suite", nargs="?", help="Path to a sam eval suite file (JSON; YAML accepted for preflight when PyYAML is installed).")
    parser.add_argument("--check-env", action="store_true", help="Warn when environment variables referenced by *_VAR keys are not currently set.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when warnings are present, not only errors.")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON instead of human-readable text.")
    parser.add_argument("--self-test", action="store_true", help="Run a tiny embedded fixture and exit.")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()
    if not args.suite:
        parser.error("suite path is required unless --self-test is used")

    findings = validate_suite(Path(args.suite).resolve(), check_env=args.check_env)
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]

    if args.json:
        print(json.dumps({"errors": len(errors), "warnings": len(warnings), "findings": [f.as_dict() for f in findings]}, indent=2))
    else:
        if findings:
            for finding in findings:
                print(finding)
        else:
            print("No issues found by offline preflight.")
        print(f"Summary: {len(errors)} error(s), {len(warnings)} warning(s)")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
