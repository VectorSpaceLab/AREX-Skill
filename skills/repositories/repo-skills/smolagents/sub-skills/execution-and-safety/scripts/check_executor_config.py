#!/usr/bin/env python3
"""Safely inspect smolagents executor configuration choices.

This helper is intentionally local and conservative. By default it validates
executor names, import patterns, and optional extras guidance without starting
Docker, E2B, Modal, or Blaxel. Pass --tiny-local-check to run a tiny
LocalPythonExecutor smoke test for local configurations only.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from dataclasses import dataclass

EXECUTOR_EXTRAS = {
    "local": None,
    "docker": "smolagents[docker]",
    "e2b": "smolagents[e2b]",
    "modal": "smolagents[modal]",
    "blaxel": "smolagents[blaxel]",
}

REMOTE_EXECUTORS = {"docker", "e2b", "modal", "blaxel"}
HIGH_RISK_ROOTS = {
    "builtins",
    "importlib",
    "io",
    "multiprocessing",
    "os",
    "pathlib",
    "pickle",
    "pty",
    "shlex",
    "shutil",
    "socket",
    "subprocess",
    "sys",
}
IMPORT_PATTERN = re.compile(r"^(\*|[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*(?:\.\*)?)$")


@dataclass
class Finding:
    level: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--executor-type",
        default="local",
        choices=sorted(EXECUTOR_EXTRAS),
        help="Executor type to validate. This script never starts remote executors.",
    )
    parser.add_argument(
        "--imports",
        nargs="*",
        default=[],
        help="Additional authorized imports to review, such as math, numpy.random, numpy.*, or *.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30,
        help="Planned local timeout. Use a positive value for untrusted code.",
    )
    parser.add_argument(
        "--max-print-outputs-length",
        type=int,
        default=50_000,
        help="Planned stdout capture cap for local execution.",
    )
    parser.add_argument(
        "--allow-pickle",
        action="store_true",
        help="Flag that remote allow_pickle=True is planned; reported as a security warning.",
    )
    parser.add_argument(
        "--check-installed",
        action="store_true",
        help="Check local import availability with importlib.util.find_spec. No imports are executed.",
    )
    parser.add_argument(
        "--tiny-local-check",
        action="store_true",
        help="Run a tiny LocalPythonExecutor smoke test for executor-type local only.",
    )
    parser.add_argument(
        "--explain-only",
        action="store_true",
        help="Print guidance and skip the tiny local smoke test even if requested.",
    )
    return parser.parse_args()


def validate_import_patterns(imports: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for import_name in imports:
        if not IMPORT_PATTERN.match(import_name):
            findings.append(Finding("error", f"Invalid import pattern: {import_name!r}"))
            continue
        if import_name == "*":
            findings.append(Finding("warning", "Wildcard '*' authorizes every installed import; prefer a sandbox."))
            continue
        root = import_name.split(".", 1)[0]
        if root in HIGH_RISK_ROOTS:
            findings.append(
                Finding(
                    "warning",
                    f"{import_name!r} has high-risk capabilities; prefer remote execution or a narrower design.",
                )
            )
        if import_name.endswith(".*"):
            findings.append(
                Finding("info", f"{import_name!r} authorizes a package tree; prefer explicit submodules when practical.")
            )
    return findings


def check_installed(imports: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for import_name in imports:
        if import_name == "*":
            continue
        root = import_name.removesuffix(".*").split(".", 1)[0]
        if importlib.util.find_spec(root) is None:
            findings.append(Finding("error", f"Base module {root!r} is not importable in this Python environment."))
    return findings


def validate_general_config(args: argparse.Namespace) -> list[Finding]:
    findings: list[Finding] = []
    extra = EXECUTOR_EXTRAS[args.executor_type]
    if extra:
        findings.append(Finding("info", f"Executor {args.executor_type!r} requires installing the {extra!r} extra."))
    if args.executor_type in REMOTE_EXECUTORS:
        findings.append(
            Finding(
                "info",
                "Remote executors are not started by this helper; verify service credentials/daemon separately.",
            )
        )
    if args.allow_pickle:
        findings.append(
            Finding(
                "warning",
                "allow_pickle=True can execute arbitrary code during deserialization; keep False unless fully trusted.",
            )
        )
    if args.timeout_seconds <= 0:
        findings.append(Finding("warning", "Non-positive timeout is unsafe for untrusted local execution."))
    if args.max_print_outputs_length <= 0:
        findings.append(Finding("warning", "Non-positive print cap may hide logs; use a positive stdout limit."))
    if args.max_print_outputs_length > 200_000:
        findings.append(Finding("info", "Large stdout caps can expose noisy or sensitive output."))
    return findings


def run_tiny_local_check(imports: list[str], timeout_seconds: float, max_print_outputs_length: int) -> list[Finding]:
    findings: list[Finding] = []
    try:
        from smolagents.local_python_executor import LocalPythonExecutor
    except Exception as exc:  # pragma: no cover - depends on caller environment
        return [Finding("error", f"Could not import smolagents LocalPythonExecutor: {exc}")]

    try:
        timeout_value = int(timeout_seconds) if timeout_seconds > 0 else 1
        executor = LocalPythonExecutor(
            additional_authorized_imports=imports,
            timeout_seconds=timeout_value,
            max_print_outputs_length=max_print_outputs_length,
        )
        executor.send_tools({})
        result = executor("print('smoke-ok')\n1 + 1")
    except Exception as exc:
        findings.append(Finding("error", f"Tiny local executor check failed: {type(exc).__name__}: {exc}"))
    else:
        if result.output == 2 and "smoke-ok" in result.logs:
            findings.append(Finding("ok", "Tiny local executor check passed."))
        else:
            findings.append(Finding("error", "Tiny local executor check returned unexpected output."))
    return findings


def print_findings(findings: list[Finding]) -> None:
    for finding in findings:
        print(f"[{finding.level.upper()}] {finding.message}")


def main() -> int:
    args = parse_args()
    findings = []
    findings.extend(validate_general_config(args))
    findings.extend(validate_import_patterns(args.imports))
    if args.check_installed:
        findings.extend(check_installed(args.imports))
    if args.tiny_local_check and not args.explain_only:
        if args.executor_type != "local":
            findings.append(Finding("warning", "Tiny local check skipped because executor type is remote."))
        else:
            findings.extend(run_tiny_local_check(args.imports, args.timeout_seconds, args.max_print_outputs_length))

    if not findings:
        findings.append(Finding("ok", "Configuration parsed without warnings."))
    print_findings(findings)
    return 1 if any(finding.level == "error" for finding in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
