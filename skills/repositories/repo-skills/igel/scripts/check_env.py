#!/usr/bin/env python3
"""Safe smoke checker for the generated Igel skill library.

This helper verifies the installed package, the CLI help surface, and optional
Auto-ML imports without training, downloading data, or depending on a source
checkout.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from importlib import metadata
from typing import List, Optional


@dataclass
class CheckResult:
    name: str
    ok: bool
    command: Optional[str] = None
    output: Optional[str] = None


def run_command(args: List[str]) -> CheckResult:
    proc = subprocess.run(args, capture_output=True, text=True)
    text = (proc.stdout or "") + (proc.stderr or "")
    return CheckResult(
        name=" ".join(args),
        ok=proc.returncode == 0,
        command=" ".join(args),
        output=text.strip() or None,
    )


def check_imports(auto_ml: bool) -> List[CheckResult]:
    results: List[CheckResult] = []
    try:
        import igel  # type: ignore

        results.append(
            CheckResult(
                name="import igel",
                ok=True,
                command="python -I -c 'import igel'",
                output=f"igel {getattr(igel, '__version__', 'unknown')} from {igel.__file__}",
            )
        )
    except Exception as exc:  # pragma: no cover - environment specific
        results.append(
            CheckResult(
                name="import igel",
                ok=False,
                command="python -I -c 'import igel'",
                output=f"{exc.__class__.__name__}: {exc}",
            )
        )
        return results

    if auto_ml:
        try:
            from igel.auto import IgelCNN  # type: ignore
            from igel.auto.models import Models  # type: ignore

            results.append(
                CheckResult(
                    name="import igel.auto",
                    ok=True,
                    command="python -I -c 'from igel.auto import IgelCNN'",
                    output=f"IgelCNN signature: {IgelCNN.__name__} and tasks: {list(getattr(Models, 'models_map', {}).keys())}",
                )
            )
        except Exception as exc:  # pragma: no cover - environment specific
            results.append(
                CheckResult(
                    name="import igel.auto",
                    ok=False,
                    command="python -I -c 'from igel.auto import IgelCNN'",
                    output=f"{exc.__class__.__name__}: {exc}",
                )
            )
    return results


def check_cli() -> List[CheckResult]:
    commands = [
        [sys.executable, "-m", "pip", "check"],
        [sys.executable, "-m", "igel", "--help"],
        [sys.executable, "-m", "igel", "fit", "--help"],
        [sys.executable, "-m", "igel", "serve", "--help"],
        [sys.executable, "-m", "igel", "models"],
        [sys.executable, "-m", "igel", "metrics"],
    ]
    results = []
    for command in commands:
        results.append(run_command(command))
    return results


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-check the installed Igel package and CLI.")
    parser.add_argument("--auto-ml", action="store_true", help="Also check igel.auto imports and task names.")
    parser.add_argument("--json", action="store_true", help="Print the report as JSON.")
    args = parser.parse_args(argv)

    report = {
        "python": sys.version.split()[0],
        "distribution": None,
        "imports": [],
        "cli": [],
        "ok": True,
    }

    try:
        report["distribution"] = metadata.version("igel")
    except Exception:
        report["distribution"] = None

    import_results = check_imports(args.auto_ml)
    cli_results = check_cli()
    report["imports"] = [asdict(result) for result in import_results]
    report["cli"] = [asdict(result) for result in cli_results]
    report["ok"] = all(item["ok"] for item in report["imports"] + report["cli"])

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Igel smoke checker for Python {report['python']}")
        if report["distribution"]:
            print(f"Distribution: igel {report['distribution']}")
        for section_name in ("imports", "cli"):
            print(f"\n{section_name.upper()}")
            for item in report[section_name]:
                status = "ok" if item["ok"] else "fail"
                print(f"[{status}] {item['name']}")
                if item.get("output"):
                    print(item["output"])
                    print()

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
