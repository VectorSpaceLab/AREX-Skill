#!/usr/bin/env python3
"""Run a deterministic installed-package smoke for giskard.checks.

The script intentionally avoids provider SDK calls, network access, credentials,
and repository-relative files. It validates that Scenario, StringMatching,
Equals, and Suite.run work against a local deterministic target. Exit status is
nonzero when any assertion fails so callers can use it in automation.
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

# Set telemetry opt-out before importing giskard packages.
os.environ.setdefault("DO_NOT_TRACK", "1")
os.environ.setdefault("GISKARD_TELEMETRY_DISABLED", "1")
os.environ.setdefault("GISKARD_CHECKS_DISABLE_RICH_PRETTY", "1")

try:
    import giskard.checks as checks
    from giskard.checks import Equals, Scenario, StringMatching, Suite
except Exception as exc:  # pragma: no cover - diagnostic path
    print("ERROR: failed to import giskard.checks.", file=sys.stderr)
    print(f"       {type(exc).__name__}: {exc}", file=sys.stderr)
    print("       Install giskard-checks or the root giskard package in this Python environment.", file=sys.stderr)
    sys.exit(2)


def _format_scenario_failures(result: Any) -> str:
    messages: list[str] = []
    for step_index, step in enumerate(getattr(result, "steps", []), start=1):
        if getattr(step, "error", None) is not None:
            messages.append(f"step {step_index} error: {step.error.summary()}")
        for check_result in getattr(step, "results", []):
            if not getattr(check_result, "passed", False):
                messages.append(
                    "step {idx} {status}: {message} details={details}".format(
                        idx=step_index,
                        status=getattr(check_result, "status", "unknown"),
                        message=getattr(check_result, "message", None),
                        details=getattr(check_result, "details", {}),
                    )
                )
    return "\n".join(messages) if messages else repr(result)


def _suite_target(inputs: str) -> str:
    return f"Echo: {inputs}"


async def _run_smoke() -> int:
    scenario = (
        Scenario("checks_evals_smoke")
        .interact(
            inputs="hello",
            outputs=lambda inputs: {
                "answer": f"Echo: {inputs}",
                "status": "ok",
            },
        )
        .check(StringMatching(keyword="Echo", text_key="trace.last.outputs.answer"))
        .check(Equals(expected_value="ok", key="trace.last.outputs.status"))
    )

    scenario_result = await scenario.run()
    if not scenario_result.passed:
        print("ERROR: deterministic Scenario smoke failed.", file=sys.stderr)
        print(_format_scenario_failures(scenario_result), file=sys.stderr)
        return 1

    suite_scenario = (
        Scenario("suite_echo")
        .interact("world")
        .check(Equals(expected_value="Echo: world", key="trace.last.outputs"))
    )
    suite_result = await Suite(name="checks_evals_suite", target=_suite_target).append(
        suite_scenario
    ).run(verbose=False)

    if suite_result.passed_count != 1 or suite_result.failed_count or suite_result.errored_count:
        print("ERROR: deterministic Suite smoke failed.", file=sys.stderr)
        for result in suite_result.results:
            if not result.passed:
                print(f"Scenario {result.scenario_name!r} failed:", file=sys.stderr)
                print(_format_scenario_failures(result), file=sys.stderr)
        return 1

    print(
        "OK: giskard.checks {version} deterministic smoke passed "
        "(scenario={scenario_status}, suite_pass_rate={pass_rate:.2f}).".format(
            version=getattr(checks, "__version__", "unknown"),
            scenario_status=scenario_result.status.value,
            pass_rate=suite_result.pass_rate,
        )
    )
    return 0


def main() -> int:
    try:
        return asyncio.run(_run_smoke())
    except Exception as exc:  # pragma: no cover - diagnostic path
        print("ERROR: unexpected exception while running checks smoke.", file=sys.stderr)
        print(f"       {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
